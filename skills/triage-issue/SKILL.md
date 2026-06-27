---
name: triage-issue
description: Classify and label a single GitHub issue by type, component, platform, provider, urgency, and importance.
allowed-tools: Bash(gh:*, gh-cached:*, scripts/get-env:*), Read, Write
argument-hint: "<issue-number> [repository]"
---

# Triage Issue

Reviews a single open issue in a GitHub repository and classifies it across multiple dimensions: type, area, platform, provider, severity qualifiers, urgency, and importance.
Applies labels and posts a clarification comment when the issue lacks enough information to classify.
This is the per-issue core of `triage-issues`. Use it directly for event-driven triage on issue open, or for invocation from other skills that need to triage one issue without scanning the whole backlog.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the issue from `$ISSUE_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with write access to the target repository
- An issue number (`$1`) to triage
- Repository in `owner/repo` format (`$2`), or omit to use the repository in the current working directory
- Follow `skills/github-post-attribution/SKILL.md` to resolve commit SHA and append attribution footers to every comment posted to GitHub

## Workflow

```
Read issue $1: title + description + comments
              |
              v
Classify: type / area / platform / provider
        / severity / repro / urgency / importance
              |
              v
 Sufficient info?
   /          \
 Yes            No
  |              |
  v              v
Apply labels   Apply needs-info / needs-repro
              + post clarification comment
              |
              v
 Check for duplicates (against all open + closed issues)
              |
              v
 Duplicates found?
   /          \
 Yes            No
  |              |
  v              |
Apply duplicate  |
label (if perms) |
+ post comment   |
  |              |
  v              v
Output triage summary
```

## Label Discovery

All dimensional labels (area, platform, provider, perf) are repo-specific and must be discovered from the repository's existing labels before classification begins. Area labels can also be created when a clear new area is identified (see Area Label Creation below).

Fetch the repository's labels once during setup:
```
gh label list [--repo <repo>] --limit 100 --json name,description
```

Build a label catalog by recognizing prefixed namespaces and descriptive labels:

| Dimension | Detection Heuristics | Examples |
|---|---|---|
| Area | `area:*` or `component:*` prefix, or description containing `component` | `area:core`, `area:ui`, `component: server` |
| Platform | `platform:*` prefix | `platform:windows`, `platform:macos`, `platform:linux` |
| Provider | `api:*` prefix | `api:bedrock`, `api:vertex`, `api:anthropic` |
| Performance | `perf:*` prefix | `perf:memory`, `perf:cpu`, `perf:reliability` |

Also detect these functional labels if they exist in the repo: `needs-info`, `needs-repro`, `has-repro`, `regression`, `data-loss`, `stale`, `duplicate`, `invalid`.

## Classification

### Type Labels

| Type | Criteria |
|---|---|
| `bug` | Something is broken or behaves unexpectedly |
| `feature` | New functionality requested |
| `question` | User seeking clarification or guidance |
| `chore` | Maintenance, refactoring, or dependency updates |
| `documentation` | Docs are missing, wrong, or unclear |
| `security` | Vulnerability or security concern |

### Issue Type Mapping

Map the classified type to the closest GitHub Issue Type for the repository.
First fetch available issue types, then apply the mapping:

```
gh api graphql -f query='{ repository(owner:"<owner>", name:"<repo>") { issueTypes(first: 20) { nodes { id name } } } }'
```

| Classified Type | GitHub Issue Type (preferred) |
|---|---|
| `bug` | Bug |
| `feature` | Feature |
| `question` | Task |
| `chore` | Task |
| `documentation` | Task |
| `security` | Bug |

Use the closest match from the available issue types. If no matching type exists, skip issue type assignment.

Set the issue type via REST API (accepts the type name as a string):
```
echo '{"type": "<typeName>"}' | gh api --method PATCH repos/<owner>/<repo>/issues/<number> --input -
```

### Area Labels

For large or monolithic repositories, the area an issue relates to is the most actionable classification.
Areas are discovered from the repo's `area:*` or `component:*` prefixed labels during setup.

Map the issue's content to the best-matching area label(s):
- File paths in stack traces or reproduction steps (e.g., `src/server/` -> `area:api`, `extensions/vscode/` -> `area:vscode`)
- Explicit mentions of a subsystem or product surface
- Keywords like "dialog", "menu", "panel", "button" -> `area:ui`
- Keywords like "endpoint", "response", "request", "API" -> `area:api`
- Keywords like "extension", "plugin", "add-on" -> `area:plugins` or `area:vscode`
- Keywords like "install", "setup", "getting started" -> `area:installation`
- Keywords like "login", "auth", "token", "credential" -> `area:auth`
- Keywords like "permission", "access", "sandbox" -> `area:permissions`

Apply **at most 2 area labels** per issue. If no existing area label matches but a clear area can be identified from the issue content, create one (see Area Label Creation below). If no area can be determined with reasonable confidence, skip area labeling rather than guessing.

#### Area Label Creation

When classification identifies a clear area that has no matching label in the repo, create it before applying. This keeps the triage process self-contained and avoids deferring work.

Create a new area label:
```
gh label create "area:<name>" [--repo <repo>] --description "<short description>" --color "<hex>"
```

Guidelines:
- Use the `area:` prefix for all newly created area labels
- Derive a short, descriptive name from the issue content (e.g., `area:networking`, `area:storage`, `area:cli`)
- Write a one-line description explaining what the area covers
- Assign a color. Use a consistent color for all `area:*` labels (e.g., `0075ca` or pick from the repo's existing area label colors)
- Only create labels you are confident about. If the area is ambiguous, skip creation and apply no area label

### Platform Labels

Detect the operating system or runtime environment from the issue content.
Only apply if the repo has matching `platform:*` labels.

Detection signals:
- OS mentions: "Windows", "macOS", "Linux", "Ubuntu", "Fedora", "WSL"
- IDE mentions: "VS Code", "IntelliJ", "JetBrains", "Neovim", "Vim"
- Environment mentions: "Docker", "CI", "GitHub Actions"
- Mobile mentions: "iOS", "Android"
- Browser mentions: "Chrome", "Firefox", "Safari", "web"
- Error messages containing OS-specific paths (e.g., `C:\Users\` -> Windows, `/Users/` -> macOS, `/home/` -> Linux)

Apply **at most 2 platform labels** per issue. Only apply when there is clear evidence, not speculation.

### Provider Labels

For multi-provider/multi-backend projects, detect which API provider or backend the issue involves.
Only apply if the repo has matching `api:*` labels.

Detection signals:
- Explicit provider names: "Bedrock", "Vertex", "OpenAI", "Anthropic", "Azure", "GCP", "AWS"
- Configuration snippets referencing a provider (e.g., `--provider bedrock`, `ANTHROPIC_API_KEY`)
- Error messages containing provider-specific identifiers or endpoints

### Severity Qualifier Labels

Optional labels that escalate a bug beyond its base classification.
Only apply if they exist in the repo's label set.

| Label | Criteria | Detection Signals |
|---|---|---|
| `regression` | Functionality that used to work but broke | "used to work", "was fine before", "broke after update", "after upgrading", "previous version", bisect mentions |
| `data-loss` | User data is lost or corrupted | "lost my", "data gone", "file deleted", "corrupted", "overwritten", "wiped" |

### Reproduction Labels

Track whether a bug has actionable reproduction information.
Only apply if they exist in the repo's label set.

| Label | Criteria |
|---|---|
| `has-repro` | Bug report includes clear, detailed reproduction steps |
| `needs-repro` | Bug report lacks reproduction steps needed to investigate |

Apply `has-repro` when the issue contains numbered steps, code snippets, or commands that reliably reproduce the problem.
Apply `needs-repro` when a bug is reported but lacks sufficient reproduction information.

### Triage State Labels

Track issues that need follow-up from reporters.
Only apply if they exist in the repo's label set.

| Label | Criteria |
|---|---|
| `needs-info` | Issue is too vague to classify or act on |

Apply `needs-info` alongside posting a clarification comment. Remove `needs-info` once the reporter provides sufficient detail (on re-triage).

### Duplicate Detection

Before running duplicate detection, check the issue's existing comments for a prior duplicate comment from the current authenticated user or any bot account. If one already exists, skip duplicate detection entirely.

Compare the issue against all other issues (open and closed) to identify potential duplicates. This check runs regardless of write permissions, as posting duplicate-suggestion comments requires only comment access (which is typically available even without triage perms on public repos).

Detection signals (weigh multiple signals together; require at least 2 to flag):
- Very similar titles (high word overlap after removing stop words)
- Same stack trace or error message
- Same reproduction steps or code snippets
- Same file paths or function names in error context
- Reporter explicitly mentions "same issue as #NNN"

Report at most 5 potential duplicates (sorted by similarity, strongest match first).

When duplicates are detected:
1. If `has_triage` is true: apply the `duplicate` label (if available) to the current issue, and post a duplicate comment with auto-closure notice.
2. If `has_triage` is false: post a suggestion comment listing the potential duplicates, framed as a suggestion rather than authoritative classification.

Comment format for duplicate detection (when `has_triage` is true):
```
Potential duplicates:
1. #<original1> - <1-sentence explanation of similarity>
2. #<original2> - <1-sentence explanation of similarity>

<1-2 sentence explanation of why this issue appears to be a duplicate of the above.>

This issue will be automatically closed as a duplicate in 3 days.

If this issue is a duplicate, please close it and 👍 the existing issue instead.
To prevent auto-closure, add a comment or 👎 this comment.

---

Triaged with [triage-issue](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
```

Comment format for duplicate suggestions (when `has_triage` is false):
```
Potential duplicates:
1. #<original1> - <1-sentence explanation of similarity>
2. #<original2> - <1-sentence explanation of similarity>

<1-2 sentence explanation of why this issue appears to be a duplicate of the above.>

If this issue is a duplicate, please close it and 👍 the existing issue instead.

---

Triaged with [triage-issue](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
```

### Urgency Labels

Only apply urgency labels to issues in **private repositories**. Skip urgency classification for public repositories.

| Label | Criteria |
|---|---|
| `urgent` | Blocking production or multiple users right now |
| `not-urgent` | Can be scheduled without immediate impact |

### Importance Labels

Only apply importance labels to issues in **private repositories**. Skip importance classification for public repositories.

| Label | Criteria |
|---|---|
| `important` | High business value or affects core functionality |
| `not-important` | Nice-to-have or low business impact |

### Priority Mapping

Derive a priority from the urgency and importance classification. For public repositories (where urgency and importance are not set), classify priority directly from the issue content.

| Urgency | Importance | Priority |
|---|---|---|
| `urgent` | `important` | Urgent |
| `urgent` | `not-important` | High |
| `not-urgent` | `important` | High |
| `not-urgent` | `not-important` | Medium |

Priority can be set via two mechanisms (try in order):

1. **Org-level Priority field** (preferred): Discover via GraphQL and set with `setIssueFieldValue` mutation.
2. **Priority labels** (fallback): If the repo has `high-priority`, `medium-priority`, `low-priority` labels, apply the matching label.

#### Org-level Priority Field

Priority is an organization-level issue field (not a project field).
Discover available fields and their option IDs via GraphQL:

```
gh api graphql -f query='{ repository(owner:"<owner>", name:"<repo>") { issueFields(first: 20) { nodes { ... on IssueFieldSingleSelect { id name options { id name } } } } } }'
```

If a field named "Priority" exists, set it using the `setIssueFieldValue` GraphQL mutation:

```
gh api graphql -f query='mutation($issueId: ID!, $fieldId: ID!, $optionId: ID!) { setIssueFieldValue(input: { issueId: $issueId, issueFields: [{ fieldId: $fieldId, singleSelectOptionId: $optionId }] }) { issue { issueFieldValues(first: 10) { nodes { ... on IssueFieldValueSingleSelect { name field { ... on IssueFieldSingleSelect { name } } } } } } } }' -f issueId=<ISSUE_NODE_ID> -f fieldId=<PRIORITY_FIELD_ID> -f optionId=<OPTION_ID>
```

If no Priority field exists on the repository, fall back to priority labels.

#### Priority Labels

Map the derived priority to the repo's priority labels:

| Derived Priority | Label (preferred) | Alternatives |
|---|---|---|
| Urgent | `priority:high` | `high-priority`, `P0` |
| High | `priority:high` | `high-priority`, `P1` |
| Medium | `priority:medium` | `medium-priority`, `P2` |
| Low | `priority:low` | `low-priority`, `P3` |

Use the closest match from the repo's label set.

## Steps

1. Determine the repository's visibility and your write access:
   ```
   gh repo view [--repo $2] --json isPrivate --jq '.isPrivate'
   gh api repos/<owner>/<repo> --jq '{push: .permissions.push, triage: .permissions.triage, admin: .permissions.admin, maintain: .permissions.maintain}'
   ```
   Store `is_private` (urgency and importance are only classified for private repos). Compute three access flags:
   - `has_push` = `push` or `admin` or `maintain` is true. Gates label creation.
   - `has_triage` = any of `push`, `triage`, `admin`, or `maintain` is true. Gates label application, issue type setting, and priority setting.
   - `can_comment` = `has_triage` is true, OR the repository is public (anyone can comment on public repos). Gates comment posting and duplicate-suggestion comments.
   If `has_triage` is false and `can_comment` is false, output a read-only triage summary and skip all write operations including comments. If `has_triage` is false but `can_comment` is true, skip label/type/priority operations but still post duplicate-suggestion comments and needs-info clarification comments.
2. Fetch the repository's available issue types and issue fields (once, before processing the issue):
   ```
   gh api graphql -f query='{ repository(owner:"<owner>", name:"<repo>") { issueTypes(first: 20) { nodes { id name } } issueFields(first: 20) { nodes { ... on IssueFieldSingleSelect { id name options { id name } } } } } }'
   ```
   Store the issue type name-to-ID map and the Priority field ID with its option ID-to-name map.
3. Fetch the repository's labels to build the label catalog:
   ```
   gh label list [--repo $2] --limit 100 --json name,description
   ```
   Parse labels into the dimension catalogs described in the Label Discovery section.
4. Read the issue's full description and comments:
   ```
   gh-cached issue view $1 [--repo $2] --comments
   ```
   If the issue already has at least one `area:*` label, it is considered triaged. Output "Already triaged" and stop without modifying the issue.
5. Classify the issue across all applicable dimensions: type, area, platform, provider, severity qualifiers, repro status, priority. If `is_private` is true, also classify urgency and importance.
6. If a clear area is identified but no matching `area:*` label exists in the repo and `has_push` is true, create it:
   ```
   gh label create "area:<name>" [--repo $2] --description "<short description>" --color "<hex>"
   ```
   Only create when confident in the area classification. If `has_push` is false, skip creation and note the missing label in the triage summary instead.
7. If the issue is too vague to classify:
   - If `has_triage` is true: apply `needs-info` label (if available), and for bugs without repro steps apply `needs-repro` label (if available)
   - If `can_comment` is true: post a comment asking for: steps to reproduce (bugs), use case details (features), or more context. Append attribution footer per `github-post-attribution`.
8. If `has_triage` is true, apply the appropriate labels:
   ```
   gh issue edit $1 [--repo $2] --add-label "<type>" --add-label "<area>" --add-label "<platform>" --add-label "<provider>" --add-label "<severity>" --add-label "<repro>" --add-label "<urgency>" --add-label "<importance>" --add-label "<priority>"
   ```
   Only include labels for dimensions where a match was found. Omit urgency and importance labels for public repositories.
9. If `has_triage` is true, set the GitHub Issue Type via REST API (if a matching type is available):
   ```
   echo '{"type": "<TypeName>"}' | gh api --method PATCH repos/<owner>/<repo>/issues/$1 --input -
   ```
10. If `has_triage` is true, set the Priority field via GraphQL `setIssueFieldValue` mutation (if a Priority field was found in step 2), or fall back to priority labels:
    - Look up the Priority option ID for the derived priority level (Urgent/High/Medium)
    - Get the issue node ID: `gh api repos/<owner>/<repo>/issues/$1 --jq '.node_id'`
    - Call `setIssueFieldValue` with the issue node ID, Priority field ID, and option ID
11. Duplicate detection (runs regardless of `has_triage`):
    - Check the issue's existing comments for a prior duplicate comment from the current authenticated user or any bot account. If found, skip duplicate detection entirely.
    - Compare the issue against all other issues (open and closed):
      ```
      gh-cached issue list [--repo $2] --state all --json
      ```
    - Use the detection signals from the Duplicate Detection section (require at least 2 signals to flag)
    - Skip if the issue already has a `duplicate` label or a maintainer has already linked it
    - For each potential duplicate pair (this issue -> older/original issue):
      - If `has_triage` is true: apply `duplicate` label to this issue (if the label exists in the repo) and post a comment linking to the original with attribution footer
      - If `has_triage` is false but `can_comment` is true: post a suggestion comment (framed as a suggestion, not authoritative) with attribution footer
      - If `can_comment` is false: note the potential duplicate in the triage summary only
12. Output the single-issue triage summary.

## Output Format

```markdown
## Triage Summary

| Issue | Title | Type | Area | Platform | Provider | Severity | Repro | Priority | Duplicate | Action |
|---|---|---|---|---|---|---|---|---|---|---|
| #42 | Login crash on mobile | bug | area:ui | platform:ios | - | - | has-repro | Urgent | - | Labeled, type set, priority set |
```

When invoked from `triage-issues`, the orchestrator assembles each per-issue summary row into a combined table.

## Outcome

If `$OUTCOME_YAML` is set, emit your routing verdict there per `skills/sdlc/references/shared.md`, derived from the classified type:

| Verdict | Classified type |
|---|---|
| `feature` | feature |
| `bug` | bug |
| `needs-info` | too vague to classify |
| `other` | question, chore, documentation, security |

## Example Usage

**Scenario 1: Triaging a specific issue from a webhook**
```
/triage-issue 42 owner/myrepo
```
Reads issue #42, classifies it, applies type + area + platform + provider + priority labels, and sets the issue type.

**Scenario 2: Vague bug report**
```
/triage-issue 10
```
Issue #10 says "it doesn't work." Apply `needs-info` and `needs-repro` labels, then post comment: "Could you describe the expected behavior, what you observed instead, and the steps to reproduce?"

**Scenario 3: Regression with data loss**
```
/triage-issue 22
```
Issue #22 says "After upgrading to v2, my config file was wiped." Classify as bug, apply `regression`, `data-loss`, and `has-repro` labels. Assign Urgent priority.

**Scenario 4: Read-only mode with duplicate detection (no triage permissions)**
```
/triage-issue 88 owner/publicrepo
```
User lacks triage permissions on a public repo. Issue #88 reports the same crash as #12. Since `can_comment` is true (public repo), post a suggestion comment: "This issue appears similar to #12 (both report a crash on startup with the same error message). If this is a duplicate, consider closing this issue in favor of the existing one." Labels and issue types are skipped.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh repo view [--repo <repo>] --json isPrivate --jq '.isPrivate'` | Check if repository is private |
| `gh api repos/<owner>/<repo> --jq '{push: .permissions.push, triage: .permissions.triage, admin: .permissions.admin, maintain: .permissions.maintain}'` | Check write access (has_push = push/admin/maintain, has_triage = any of push/triage/admin/maintain, can_comment = has_triage OR repo is public) |
| `gh api graphql -f query='{ repository(owner:"<o>", name:"<r>") { issueTypes(first: 20) { nodes { id name } } issueFields(first: 20) { nodes { ... on IssueFieldSingleSelect { id name options { id name } } } } } }'` | Fetch available issue types and fields |
| `gh label list [--repo <repo>] --limit 100 --json name,description` | Fetch repo labels for dimension discovery |
| `gh label create "area:<name>" [--repo <repo>] --description "<desc>" --color "<hex>"` | Create a new area label |
| `gh-cached issue view <number> [--repo <repo>] --comments` | Read issue details and comments (cached) |
| `gh-cached issue list [--repo <repo>] --state all --json` | Fetch full issue corpus for duplicate comparison |
| `gh api repos/<owner>/<repo>/issues/<number> --jq '.node_id'` | Get issue node ID for GraphQL mutations |
| `echo '{"type": "<name>"}' \| gh api --method PATCH repos/<owner>/<repo>/issues/<number> --input -` | Set issue type by name |
| `gh api graphql -f query='mutation($issueId: ID!, $fieldId: ID!, $optionId: ID!) { setIssueFieldValue(input: { issueId: $issueId, issueFields: [{ fieldId: $fieldId, singleSelectOptionId: $optionId }] }) { issue { issueFieldValues(first: 10) { nodes { ... on IssueFieldValueSingleSelect { name field { ... on IssueFieldSingleSelect { name } } } } } } } }' -f issueId=<ID> -f fieldId=<FIELD_ID> -f optionId=<OPTION_ID>` | Set org-level issue field (e.g. Priority) |
| `gh issue edit <number> [--repo <repo>] --add-label "<label>"` | Apply a label to an issue |
| `gh issue comment <number> [--repo <repo>] --body "..."` | Post a clarification comment (append attribution footer per `github-post-attribution`) |
