---
name: trace-issues
description: Build a traceability matrix across a GitHub repository by tracing each issue to its linked PRs and commits and then to the code that implements it, and verifying whether each issue's intents (and acceptance criteria, when present) are still addressed in the current codebase. Use when the user says /trace-issues, "trace issues to code", "build a traceability matrix", "which PRs implemented these issues", "trace the repository", "are the issue intents addressed in the code", or wants a per-issue table of intents, PRs, and code coverage. Works without an SDLC directory; the GitHub-native counterpart of propagate-changes.
allowed-tools: Bash(gh:*, git:*, ghx:*, ~/.agents/scripts/get-env:*), Read, Write, Glob, Grep
argument-hint: "[owner/repo] [--state all|open|closed] [--label <name>] [--author <user>] [--query <text>] [--limit <n>] [--focus <issue-number>] [--clone] [--out <path>]"
---

# Trace Issues

Builds a traceability matrix across a GitHub repository.
For every issue in scope it traces the chain issue -> PR -> commit -> code, extracts the issue's intents (and formal acceptance criteria when present), and verifies whether each intent is still addressed in the **current** codebase.
The output is one table: per issue, its linked PRs, its intents, and a Met / Partially met / Not met verdict with code evidence.

This is the GitHub-native counterpart of `propagate-changes`.
`propagate-changes` walks the `.sdlc/` artifact chain (issue -> requirements -> spec -> plan -> tasks -> tests -> code) in both directions and requires a populated `.sdlc/` directory.
This skill needs no `.sdlc/`: it reconstructs the trace from GitHub's own objects (issues, PRs, commits, closing references) and the code as it exists today.

It differs from neighboring skills in a single dimension each:

| Skill | What it does | Why this skill is different |
|---|---|---|
| `check-issues-status` | Batch "is each issue already done" triage for staleness | Does not trace to PRs, does not collect acceptance criteria, does not build a matrix |
| `check-issue-status` | Verifies one issue against the code | Single issue, no PR trace, no repository-wide matrix |
| `validate-pr` / `verify-pr` | Review one PR against its linked issue at PR time (validate-pr: right product; verify-pr: criteria conformance) | One PR at a time, checks the PR diff, not whether the intent survives in current code |
| `propagate-changes` | Traceability across the `.sdlc/` artifact chain | Requires `.sdlc/`; this uses GitHub objects and works on any repo |

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md` (only the output-path and context-reading conventions; this skill never reads or writes `.sdlc/features/`).
- `gh` CLI authenticated with read access to the target repository.
- `git` available.
- A local checkout of the target repository is preferred, because verifying intents against the code requires the code.
  - If the working directory's `origin` remote matches the target repo, use it.
  - If it does not match and `--clone` is set, shallow-clone the repo to `/tmp/trace-issues/<owner>-<repo>` and work there.
  - If it does not match and `--clone` is not set, warn and stop (code evidence would be from the wrong repo), and suggest `--clone`.
- Read any files under `.sdlc/context/` (`architecture.md`, `vocabulary.md`, `conventions.md`) for hints that help locate code.

## Scope

Resolve the target from the positional `owner/repo`, then `$REPO`, then the current directory's `git remote get-url origin`.

| Flag | Purpose | Default |
|---|---|---|
| `--state all\|open\|closed` | Which issue states to include | `all` (a trace is most useful across shipped work, so closed issues are included) |
| `--label <name>` | Filter to issues with a label | none |
| `--author <user>` | Filter to issues authored by a user | none |
| `--query <text>` | Free-text search over issue titles and bodies | none |
| `--limit <n>` | Cap issues processed | 50 |
| `--focus <issue-number>` | Build the trace for a single issue only (skips the search) | none |
| `--clone` | Shallow-clone the target repo if not already checked out | off |
| `--out <path>` | Where to write the report | `traceability-report.md` in the working directory |

Filters compose: `--label bug --author jane` restricts to bugs authored by jane.

## Workflow

```
Resolve target + scope + filters
        |
        v
Ensure code access (local checkout, or --clone to /tmp)
        |
        v
gh search issues --json repository,number,title,state  (or --focus <n>)
        |
        v
For each issue:
  1. Collect linked PRs (timeline cross-refs + closing keywords)  -> issue->PR map
  2. For each PR: mergeCommit + commits + files/functions touched  -> PR->code map
  3. Extract intents / acceptance criteria from the issue body
  4. Verify each intent against CURRENT code (not the PR-time diff)
        |
        v
Classify orphans (orphan issue, orphan code, broken trace)
        |
        v
Build matrix + write report (--out), present summary
```

## Steps

### 1. Parse arguments and ensure code access

Resolve the target repo, the filters, the limit, the `--focus` issue (if any), the `--out` path, and the `--clone` flag.

Determine the working directory's repository so code inspection targets the right checkout:

```bash
git remote get-url origin
```

Record its `{owner}/{repository}` as `CWD_REPO`.

- If `CWD_REPO` equals the target repo, set `WORK_DIR` to the current directory and proceed.
- If they differ and `--clone` is set:

  ```bash
  REPO_DIR="/tmp/trace-issues/$(echo $TARGET_REPO | tr '/' '-')"
  git clone --depth 50 "https://github.com/$TARGET_REPO.git" "$REPO_DIR"
  ```

  Set `WORK_DIR` to `$REPO_DIR`. All subsequent `Glob`, `Grep`, and `Read` operations run inside `$WORK_DIR`.
- If they differ and `--clone` is not set, warn the user and stop. Do not inspect code from the wrong repo.

### 2. Gather issues

If `--focus <n>` is given, skip the search and use that single issue.

Otherwise build one `gh search issues` call covering all filters:

```bash
gh search issues \
  --state <state> \
  --limit <limit> \
  --json repository,number,title,state \
  [--repo <owner/repo>] \
  [--author <user>] \
  [--label <name>] \
  ["<query>"]
```

Include `--repo`, `--author`, `--label`, and the query text only when provided.
If the search returns no results, report "No issues matched the scope." and stop.

### 3. Build the issue -> PR link map

For each issue, collect every linked PR using the most reliable source first (the same approach as `check-linked-pr`), then a keyword fallback.

Primary: the issue timeline cross-references whose source is a pull request:

```bash
gh api "repos/$OWNER/$REPO/issues/$NUMBER/timeline" --paginate \
  --jq '[.[]
    | select(.event == "cross-referenced")
    | select(.source.issue.pull_request != null)
    | {number: .source.issue.number, title: .source.issue.title,
       state: .source.issue.state, merged: (.source.issue.pull_request.merged_at != null),
       author: .source.issue.user.login, url: .source.issue.html_url}]'
```

Fallback (when the timeline is empty): search PRs that mention the issue number:

```bash
ghx pr list --repo $REPO --search "$NUMBER is:pr" --state all --limit 20
```

Deduplicate by PR number. For each linked PR, record number, title, state, merged flag, and URL.
A merged PR is the strongest trace signal. An open PR means the work may be in progress. A closed-unmerged PR means the attempt was abandoned.

### 4. Trace each PR to code

For each linked PR, gather the merge commit, the commits, and the files it touched:

```bash
gh pr view $PR_NUMBER --repo $REPO \
  --json number,title,state,merged,mergeCommit,commits,files,baseRefName,headRefName
```

From this, build a per-PR record of:
- The merge commit SHA (or the squashed commit SHA), if merged.
- The list of commits (SHAs and messages), useful when the work was not squashed.
- The changed files with additions and deletions.

Then resolve the **symbols** the PR touched, not just file paths. For each changed file in a supported language, map the diff hunks to functions, classes, methods, routes, or endpoints. Prefer `git log`/`git show` inside `WORK_DIR` to see the actual diff for a merged PR:

```bash
git -C "$WORK_DIR" log --oneline -- <path>
git -C "$WORK_DIR" show <merge-sha> -- <path>
```

Record, per PR: `{ pr, merge_sha, files: [{ path, symbols: [...] }] }`.
This is the PR -> code map used as a starting pointer for verification.

### 5. Extract intents and acceptance criteria from each issue

Fetch the full issue body:

```bash
gh issue view $NUMBER --repo $REPO --json number,title,body,state,labels,author
```

Distill the issue into 1 to N discrete **intents**, each a single testable assertion about what the code should do.
Use two extraction modes, in priority order (this merges the structured-criteria parsing of `validate-pr`/`verify-pr` with the format-agnostic claim extraction of `check-issue-status`):

**Mode A, structured acceptance criteria (preferred).**
Look for the format produced by `/create-issue`: an `# Acceptance Criteria` heading with `## Must` and (optionally) `## Should` subsections of `- [ ]` checklist items.
Parse each item into an intent record: the verbatim criterion text, its priority (Must / Should), and the source issue number.
Record `extraction: structured`.

**Mode B, format-agnostic (fallback).**
If the issue has no structured criteria, read the whole body (prose, error logs, checklists, screenshots' alt text, a single sentence) and distill discrete behavioral claims.
For a bug, each intent is the desired behavior ("X should happen"), not the symptom.
For a feature, each intent is one capability the code should provide.
Record `extraction: inferred`, and note that the criteria were inferred rather than structured.

If the body is too vague to extract any intent, record the issue as `unparseable`, carry a single intent of "(issue too vague to extract intents)", and move on. Do not guess.

### 6. Verify each intent against the current code

The code as it exists **today** is the ground truth (the principle from `propagate-changes`).
A PR's diff shows what was added at merge time, but that code may have been renamed, moved, or deleted since.
Verification checks the current codebase, not the historical diff.

For each intent, derive 2 to 4 search signals (identifiers, file paths, distinctive strings such as error messages or UI labels, domain nouns from `.sdlc/context/vocabulary.md`).
Use the PR -> code map from step 4 as the first pointer: start at the files and symbols the linked PR touched, then confirm the behavior is still present.

Search with `Glob` (file names) and `Grep` (content), or `rg` directly:

```bash
rg -n --type py "def export_csv" "$WORK_DIR"
rg -n "AUDIT_LOG_EXPORTED" "$WORK_DIR"
```

Read each match with `Read` and record `file:line`.

Assign a status to each intent using only what the current code shows:

| Status | Meaning |
|---|---|
| **Met** | The code today does what the intent asks. Capture the proof (`file:line`, a function body, a route, a config value, or a test that asserts it). |
| **Partially met** | Some of the intent is satisfied but a required part is missing. Capture both the present part and the gap. |
| **Not met** | Nothing in the current code provides this behavior. Capture what was searched and why it is absent. |

When a linked merged PR implemented the intent but the code is now absent, this is an important finding: the intent **regressed**. Note the PR that introduced it and search the history for a likely removal (a later PR or commit that deleted it):

```bash
git -C "$WORK_DIR" log --oneline -S "<distinctive symbol or string>" -- <path>
```

Record the likely removal (commit SHA and message) as evidence.

Prefer static evidence. Run a single targeted test only when an intent is about runtime behavior and static reading is ambiguous:

```bash
pytest -q "$WORK_DIR/path/to/test_export.py::test_csv_export"
```

Never run broad suites or anything destructive.

### 7. Determine the per-issue verdict

Combine the per-intent statuses into one verdict per issue (the rule from `check-issue-status`):

| Intent statuses | Verdict |
|---|---|
| All Met | `addressed` |
| Mix of Met and Partially met, none Not met | `partial` |
| Any Not met | `not-addressed` |

If the issue has no linked PR and is open, the verdict is usually `not-addressed` (no work trace). If it has no linked PR but is closed, flag it as a `closed-without-trace` anomaly worth investigating.

### 8. Classify orphans

Apply the orphan classes from `propagate-changes`, adapted to the GitHub-native trace:

| Class | Meaning | Severity | Default recommendation |
|---|---|---|---|
| Orphan upstream (unrealized intent) | An issue intent has no realization in the current code | High | Implement it, or close the issue as wontfix |
| Orphan downstream (orphan code) | A merged PR's code traces to no issue intent | Medium | Confirm the PR was in scope; the issue may be missing or the AC under-specified |
| Broken trace | A PR is linked but cannot be mapped to any code (force-pushed away, branch deleted, never merged) | Low | Note the gap; rely on the issue body |
| Regressed intent | A merged PR implemented the intent, but the code was removed later | High | Re-open or re-file the issue; link the removal commit |

### 9. Build the matrix and write the report

The master table is the core deliverable. One row per intent, grouped by issue:

```markdown
## Traceability Matrix

| Issue | Title | Linked PR(s) | Intent (priority) | Addressed? | Evidence |
|---|---|---|---|---|---|
| #42 | Add CSV export | #51 (merged) | export audit logs as CSV (Must) | Yes | src/export/csv.go:88 |
| #42 | Add CSV export | #51 (merged) | stream rows > 1M (Should) | No | removed in #67 abc1234 (refactor) |
| #7 | Dark mode | (none) | dark theme toggle | No | no theme/color-scheme code found |
| #30 | Rate limiting | #44 (merged) | per-user limit (Must) | Yes | middleware/ratelimit.py:20 |
| #30 | Rate limiting | #44 (merged) | per-IP limit (Must) | Partial | per-IP config key absent |
```

Then add the per-issue detail sections (full intent list with extraction mode, PR list with state and merge SHA, code locations, and notes), the orphan-classification summary table, and the recommended actions.

Write the full report to `--out` (default `traceability-report.md` in the working directory). Present the matrix and the summary to the user.

The report frontmatter:

```markdown
---
date: "<YYYY-MM-DD>"
repo: "<owner/repo>"
code_ref: "<git rev-parse --short HEAD in WORK_DIR>"
scope: "<state, filters, limit>"
issues_traced: <n>
status: complete
---
```

The `code_ref` records which commit the code was verified against, so a later run can tell whether the code moved.

### 10. Recommend actions

Surface the actionable findings:

| Finding | Suggested action |
|---|---|
| `not-addressed` issue with no PR | Clear to work on, or close as stale |
| `partial` issue | Narrow the issue or open a follow-up for the gap |
| Regressed intent | Re-open the issue and link the removal commit |
| Orphan code (merged PR with no issue) | Confirm scope; document or open a retroactive issue |
| Closed-without-trace issue | Investigate whether it was resolved out of band |

Do not post anything to GitHub. This skill is read-only with respect to GitHub. If the user wants to act, point them to `check-issue-status` (to post a close suggestion), `create-issue`, or the `sdlc` orchestrator.

## Failure Modes

| Mode | Response |
|---|---|
| **Working directory is not the target repo and `--clone` is off** | Warn and stop; suggest `--clone` |
| **`--clone` and the repo is private or unreachable** | Report the clone error and stop |
| **Issue too vague to extract intents** | Record `unparseable`, carry a placeholder intent, move on |
| **Issue closed with no linked PR** | Flag `closed-without-trace`; do not guess a trace |
| **PR linked but branch deleted / force-pushed** | Mark the trace `broken`; fall back to the issue body only |
| **Large repository (>limit issues)** | Process up to `--limit`, note the remainder, suggest re-running with a higher limit or a narrower filter |
| **Rate limiting** | Process issues sequentially; retry on 403/429 with backoff |

## Example Usage

**Scenario 1: Whole repository, all issues**
```
/trace-issues owner/myrepo
```
Gathers all issues (open and closed), traces each to its PRs and code, verifies intents against the current checkout, writes `traceability-report.md`, and presents the matrix.

**Scenario 2: Current repository, default**
```
/trace-issues
```
Target resolves to the current directory's `origin`. Same flow.

**Scenario 3: Any repo, no local checkout**
```
/trace-issues owner/theirrepo --clone
```
Not checked out locally, so shallow-clones to `/tmp/trace-issues/owner-theirrepo` and traces there.

**Scenario 4: Focus on one issue**
```
/trace-issues owner/myrepo --focus 42
```
Skips the search and builds the full trace for issue #42 only: its PRs, its acceptance criteria, and a Met/Partial/Not-met table.

**Scenario 5: Filtered scope**
```
/trace-issues owner/myrepo --label bug --state closed --limit 100
```
Traces the last 100 closed bugs to confirm each fix still lives in the code. Surfaces regressed intents where a fix was later removed.

**Scenario 6: Catch a regression**
```
/trace-issues owner/myrepo
```
Issue #42's Must criterion "stream rows > 1M" was implemented by merged PR #51, but the matrix shows Not met because a later refactor (#67) deleted the streaming path. The report records the removal commit and recommends re-opening #42.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `propagate-changes` | The `.sdlc/` artifact-chain counterpart. This skill is its GitHub-native twin: same trace-both-ways idea, no `.sdlc/` required. |
| `check-issue-status` | Owns single-issue code inspection. This skill reuses its intent-extraction and Met/Partial/Not-met logic but adds PR tracing and a repository-wide matrix. |
| `check-issues-status` | Batch "is it done" triage. This skill reuses its scope/modes and gathering, but builds traces and collects acceptance criteria instead of only verdicting. |
| `validate-pr` / `verify-pr` | Single-PR validation against an issue at PR time. This skill verifies the current code across all issues, catching regressions that happen after a PR merges. |
| `check-linked-pr` | Owns issue-to-PR timeline linkage. This skill reuses that linkage as the first hop of the trace. |
| `audit-functional-suitability` | Whole-corpus functional audit against a requirements corpus plus honesty markers (TODOs, stubs). This skill traces GitHub issues to code; that one audits implementation completeness. |

## Useful Commands Reference

| Command | Purpose |
|---|---|
| `gh search issues --json repository,number,title,state ...` | Gather issues across the scope |
| `gh issue view <n> --json number,title,body,state,labels,author` | Fetch an issue body for intent extraction |
| `gh api repos/{o}/{r}/issues/<n>/timeline --paginate --jq ...` | Issue timeline, extract PR cross-references |
| `ghx pr list --repo <repo> --search "<n> is:pr" --state all` | PRs mentioning an issue (fallback) |
| `gh pr view <n> --json mergeCommit,commits,files,...` | PR merge commit, commits, and changed files |
| `git -C <dir> show <sha> -- <path>` | Diff of a merged PR at the code level |
| `git -C <dir> log --oneline -S "<symbol>" -- <path>` | Find when a symbol/string was added or removed (regression hunting) |
| `rg -n "<signal>" <dir>` | Locate current code backing an intent |
