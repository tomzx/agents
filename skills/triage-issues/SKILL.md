---
name: triage-issues
description: Classify and label incoming GitHub issues by type, component, platform, provider, urgency, and importance.
allowed-tools: Bash(gh:*, gh-cached:*, scripts/get-env:*), Read, Write
argument-hint: "[repository]"
---

# Triage Issues

Reviews open, unlabeled issues in a GitHub repository and classifies each across multiple dimensions: type, area, platform, provider, severity qualifiers, urgency, and importance.
Applies labels and posts a clarification comment when an issue lacks enough information to classify.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- Repository in `owner/repo` format (`$1`), or omit to use the repository in the current working directory
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

## Workflow

```
List open issues via gh-cached --json
             |
             v
Filter: exclude issues with area:* labels
(untriaged = no area label applied)
             |
             v
Fetch repo metadata (labels, issue types, fields)
             |
            v
  For each issue:
    Read title + description + comments
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
echo '{"type": "<TypeName>"}' | gh api --method PATCH repos/<owner>/<repo>/issues/<number> --input -
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
- After creating a label, add it to the label catalog so subsequent issues in the same run can reuse it

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
| Urgent | `high-priority` | `priority:high`, `P0` |
| High | `high-priority` | `priority:high`, `P1` |
| Medium | `med-priority` | `priority:medium`, `P2` |
| Low | `low-priority` | `priority:low`, `P3` |

Use the closest match from the repo's label set.

## Steps

1. Determine the repository's visibility (private or public):
   ```
   gh repo view [--repo $1] --json isPrivate --jq '.isPrivate'
   ```
   Store the result as `is_private`. Urgency and importance classification are only performed for private repositories. Priority is classified for all repositories.
2. Fetch the repository's available issue types and issue fields (once, before processing issues):
   ```
   gh api graphql -f query='{ repository(owner:"<owner>", name:"<repo>") { issueTypes(first: 20) { nodes { id name } } issueFields(first: 20) { nodes { ... on IssueFieldSingleSelect { id name options { id name } } } } } }'
   ```
   Store the issue type name-to-ID map and the Priority field ID with its option ID-to-name map.
3. Fetch the repository's labels to build the label catalog (once, before processing issues):
   ```
   gh label list [--repo $1] --limit 100 --json name,description
   ```
   Parse labels into the dimension catalogs described in the Label Discovery section.
4. List open issues that need triage (those without an `area:` label are considered untriaged):
   ```
   gh-cached issue list [--repo $1] --json | jq '[.[] | select([.labels[] | startswith("area:")] | any | not)]'
   ```
   This filters out issues that already have at least one `area:` label, as those are considered triaged.
5. For each issue, read its full description and comments.
6. Classify the issue across all applicable dimensions: type, area, platform, provider, severity qualifiers, repro status, priority. If `is_private` is true, also classify urgency and importance.
7. If a clear area is identified but no matching `area:*` label exists in the repo, create it:
   ```
   gh label create "area:<name>" [--repo $1] --description "<short description>" --color "<hex>"
   ```
   Add the new label to the label catalog for reuse. Only create when confident in the area classification.
8. If the issue is too vague to classify:
   - Apply `needs-info` label (if available)
   - For bugs without repro steps, apply `needs-repro` label (if available)
   - Post a comment asking for: steps to reproduce (bugs), use case details (features), or more context
9. Apply the appropriate labels:
   ```
   gh issue edit <number> [--repo $1] --add-label "<type>" --add-label "<area>" --add-label "<platform>" --add-label "<provider>" --add-label "<severity>" --add-label "<repro>" --add-label "<urgency>" --add-label "<importance>" --add-label "<priority>"
   ```
   Only include labels for dimensions where a match was found. Omit urgency and importance labels for public repositories.
10. Set the GitHub Issue Type via REST API (if a matching type is available):
    ```
    echo '{"type": "<TypeName>"}' | gh api --method PATCH repos/<owner>/<repo>/issues/<number> --input -
    ```
11. Set the Priority field via GraphQL `setIssueFieldValue` mutation (if a Priority field was found in step 2), or fall back to priority labels:
    - Look up the Priority option ID for the derived priority level (Urgent/High/Medium)
    - Get the issue node ID: `gh api repos/<owner>/<repo>/issues/<number> --jq '.node_id'`
    - Call `setIssueFieldValue` with the issue node ID, Priority field ID, and option ID
12. Output a triage summary table.

## Output Format

```markdown
## Triage Summary

| Issue | Title | Type | Area | Platform | Provider | Severity | Repro | Priority | Action |
|---|---|---|---|---|---|---|---|---|---|
| #42 | Login crash on mobile | bug | area:ui | platform:ios | - | - | has-repro | Urgent | Labeled, type set, priority set |
| #43 | Files deleted after update | bug | area:core | platform:macos | - | data-loss, regression | has-repro | Urgent | Labeled, type set, priority set |
| #44 | Add dark mode | feature | area:ui | - | - | - | - | Medium | Labeled, type set, priority set |
| #45 | Bedrock request timeout | bug | area:api | - | api:bedrock | - | has-repro | High | Labeled, type set, priority set |
| #46 | Something broke | bug | - | platform:windows | - | - | needs-repro | - | needs-info, needs-repro applied, comment posted |
```

## Example Usage

**Scenario 1: Repository with a backlog of unlabeled issues**
```
/triage-issues owner/myrepo
```
Lists all open issues, classifies each, and applies type + area + platform + provider + urgency + importance labels.

**Scenario 2: Vague bug report**
```
/triage-issues
```
Issue #10 says "it doesn't work." Apply `needs-info` and `needs-repro` labels, then post comment: "Could you describe the expected behavior, what you observed instead, and the steps to reproduce?"

**Scenario 3: Regression with data loss**
```
/triage-issues
```
Issue #22 says "After upgrading to v2, my config file was wiped." Classify as bug, apply `regression`, `data-loss`, and `has-repro` labels. Assign Urgent priority.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh repo view [--repo <repo>] --json isPrivate --jq '.isPrivate'` | Check if repository is private |
| `gh api graphql -f query='{ repository(owner:"<o>", name:"<r>") { issueTypes(first: 20) { nodes { id name } } issueFields(first: 20) { nodes { ... on IssueFieldSingleSelect { id name options { id name } } } } } }'` | Fetch available issue types and fields |
| `gh label list [--repo <repo>] --limit 100 --json name,description` | Fetch repo labels for dimension discovery |
| `gh label create "area:<name>" [--repo <repo>] --description "<desc>" --color "<hex>"` | Create a new area label |
| `gh-cached issue list [--repo <repo>] --json \| jq '[.[] \| select([.labels[] \| startswith("area:")] \| any \| not)]'` | List untriaged open issues (no area label) |
| `gh-cached issue view <number> [--repo <repo>] --comments` | Read issue details and comments (cached) |
| `gh api repos/<owner>/<repo>/issues/<number> --jq '.node_id'` | Get issue node ID for GraphQL mutations |
| `echo '{"type": "<name>"}' \| gh api --method PATCH repos/<owner>/<repo>/issues/<number> --input -` | Set issue type by name |
| `gh api graphql -f query='mutation($issueId: ID!, $fieldId: ID!, $optionId: ID!) { setIssueFieldValue(input: { issueId: $issueId, issueFields: [{ fieldId: $fieldId, singleSelectOptionId: $optionId }] }) { issue { issueFieldValues(first: 10) { nodes { ... on IssueFieldValueSingleSelect { name field { ... on IssueFieldSingleSelect { name } } } } } } } }' -f issueId=<ID> -f fieldId=<FIELD_ID> -f optionId=<OPTION_ID>` | Set org-level issue field (e.g. Priority) |
| `gh issue edit <number> [--repo <repo>] --add-label "<label>"` | Apply a label to an issue |
| `gh issue comment <number> [--repo <repo>] --body "..."` | Post a clarification comment |
