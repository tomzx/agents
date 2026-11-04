---
name: create-pr-walkthrough
description: Generate a self-contained HTML page that walks a reviewer through a large pull request, covering what it does and why, a suggested reading order, per-file annotated diff hunks, and the risks, findings, and open questions from the sibling review reports. Use when a PR is large enough that a linear diff is hard to follow, or when the user says /create-pr-walkthrough, "walk me through this PR", "explain this PR", "give me a reading order", or "make a PR walkthrough page".
allowed-tools: Bash(gh:*, git:*, python3:*, uv:*), Read, Write, Edit, Glob, Grep
argument-hint: "<pr-number> [repository] [--force] | <pr-url>"
---

# Create PR Walkthrough

Builds a single self-contained HTML page that turns a large pull request into a guided read: an overview of what the PR does and why, a suggested reading order that groups files into clusters, the annotated diff for each file, and the risks, findings, and open questions a reviewer should know before reading the code.
The page works offline (inline CSS and JS, no external requests) and is meant for reading in a browser beside the PR.

This skill explains the change; it does not review it.
The review verdicts belong to `validate-pr`, `verify-pr`, and `review-pr`, and the risk estimate belongs to `assess-pr-risk`.
The walkthrough may quote those reports and must not contradict them.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md` (PR Review Reports for the report directory).
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read access to the target repository.
- `git` available when the GitHub diff endpoint refuses a very large PR.
- Python 3.10+ (the renderer is a stdlib-only script).
- Sibling reports are optional. Read whichever exist under `$PR_REVIEW_DIR` before filling the narrative, and never invent findings for a step that did not run.

## Size gate

Generate the page when the PR has at least **200 changed lines** or at least **10 changed files**.
That threshold is a starting point, not a rule: use judgment first.

Generate even below the threshold when the change is hard to follow linearly: concurrency, a state machine, a security boundary, a protocol, a migration, or a small diff that touches many call sites.

Skip even above the threshold when the diff is mechanical: a lockfile bump, generated code, a mass rename, or formatting only.
When you skip, say why in one line.

The user can always force the page with `--force`.
When `review-pr-full` dispatches this skill, it has already applied a cheap size check; the size gate below is still the skill's to apply, so a mechanical diff can still be skipped with a one-line reason.

## Workflow

```
Resolve PR argument
        |
        v
Scaffold: fetch metadata + diff, parse hunks, write narrative.json
        |
        v
Size gate (judgment first) ---- skip ----> report why and stop
        |
        v
Read the diff and the sibling reports
        |
        v
Fill narrative.json (summary, reading order, file purposes, hunk notes, risks)
        |
        v
Render the self-contained HTML page
        |
        v
Report the path (never open it)
```

## Steps

### 1. Resolve the PR argument

Accept one of:

- A PR URL: `https://github.com/owner/repo/pull/42`
- A PR number with a repository: `42 owner/repo`
- A PR number alone: `42` (uses `$REPO` from the environment)

If only a PR number is given and `$REPO` is not set, stop and ask for the repository.
The optional `--force` flag is an instruction to build the page regardless of the size gate.

Define the output location per `sdlc/references/shared.md`:

```bash
PR_REVIEW_DIR="$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER"
```

### 2. Scaffold the narrative

Run the renderer's `scaffold` command.
It fetches the PR metadata and diff, parses the diff into files and hunks, computes the size decision, saves the diff, and writes a `narrative.json` skeleton:

```bash
python3 ~/.agents/skills/create-pr-walkthrough/scripts/pr_walkthrough.py scaffold \
  --pr "$PR_NUMBER" --repo "$REPO" \
  --worktree "${WORKTREE_DIR:-}" \
  --out-dir "$PR_REVIEW_DIR/walkthrough"
```

When `WORKTREE_DIR` is set (for example by `review-pr-full`), pass it so the git fallback runs in the PR checkout.
To work offline, or to reuse an already-fetched diff, pass `--diff-file <path>` and `--meta-file <path>` (the latter is saved `gh pr view --json` output).

The script prints one machine-readable line:

```
WALKTHROUGH_SIZE {"large": true|false, "reasons": [...], "files": 12, "additions": 340, "deletions": 120, "changed_lines": 460, ...}
```

Apply the size gate from that line, using the judgment rules above.
If `--force` was passed, treat the decision as LARGE.
If the existing `narrative.json` matches the current head, the scaffold reuses it so filled annotations are not wiped; pass `--rebuild` to rebuild it from scratch.
If you skip, report the counts and the reason, and stop.

### 3. Read the change

Read `$PR_REVIEW_DIR/walkthrough/pr.diff` end to end.
For context the diff does not carry, read the touched files in `WORKTREE_DIR` (or the local checkout) and the linked issue.
Then read whichever of these reports exist:

| Report | Use |
|---|---|
| `assess-pr-risk.report.md` | risk, confidence, and recommended route |
| `summarize-behavior-changes.report.md` | what behaves differently after merge, affected consumers, breaking changes |
| `analyze-test-coverage.report.md` | what the tests prove and what they miss |
| `validate-pr.report.md` | whether the PR solves the right problem |
| `verify-pr.report.md` | which acceptance criteria are met |
| `review-pr.report.md` | craft findings and their severity |

The scaffold already copies the report paths into `sources` and the assess marker into `assess`.
Read the files themselves for the detail; do not stop at the paths.

### 4. Fill the narrative

Edit `$PR_REVIEW_DIR/walkthrough/narrative.json`.
The scaffold pre-populates `meta` and one entry per changed file under `files`; edit those entries in place instead of rewriting the file from scratch.
Leave `meta`, `sources`, and `assess` as the scaffold wrote them (the renderer uses them for the header and stats).

Fill these fields:

| Field | What to write |
|---|---|
| `summary` | Two to four sentences: what the PR does, in the reviewer's terms. |
| `why` | The problem it solves and the intended outcome. One short paragraph. |
| `reading_order` | Two to five clusters that order the files by what the reader needs first. Each has `title`, `why`, and `files`. |
| `files[].purpose` | One or two sentences on why this file changed, not a restatement of the diff. |
| `files[].annotations` | A map from hunk index (as a string) to the explanation for that hunk. Annotate only the hunks that carry a decision, a risk, or a surprise. |
| `files[].risks` | Short, concrete things to watch for in this file. |
| `risks` | Cross-file risks, each with `level`, `title`, `detail`, and `source`. |
| `findings` | Actionable findings, each with `severity`, `title`, `detail`, and optionally `file`, `line`, and `source`. |
| `questions` | Open questions the reviewer should resolve while reading. |
| `verdict` | One or two sentences on where the review stands. Quote the sibling reports; do not issue a new verdict. |

Reading-order rules:

- Order by dependency, not by directory: the contract or interface first, then the implementation, then tests, then docs and generated files.
- Title each cluster by what the reader learns ("The request path", "The retry policy"), not by folder name.
- Put an unrelated or distracting change in its own late cluster so it does not hide the main work.

Annotation rules:

- Explain why the code is the way it is, what alternative it rules out, or what could break. The diff already shows what changed.
- Cite the concrete consequence ("a 400 from the provider is retried three times") instead of a general concern ("error handling could be better").
- Do not annotate imports, formatting, renames, or lockfile noise.
- Keep every annotation to one to three sentences.
- Write literally and in the active voice. No em-dashes.

Risk and finding rules:

- Attribute each item to the report it came from in `source`.
- Keep the severity vocabulary from the reports: `must` / `should` / `may` for findings, `high` / `medium` / `low` for risks.
- Do not add an item the reports do not support. If the reports are missing, leave the section empty rather than speculate.

### 5. Render the page

```bash
python3 ~/.agents/skills/create-pr-walkthrough/scripts/pr_walkthrough.py render \
  --narrative "$PR_REVIEW_DIR/walkthrough/narrative.json" \
  --diff "$PR_REVIEW_DIR/walkthrough/pr.diff" \
  --out "$PR_REVIEW_DIR/pr-walkthrough.html"
```

The renderer writes one HTML file with inline CSS and JS: a sticky sidebar with search and file navigation, a reading progress bar, light and dark themes, a suggested reading order, the risk and findings panels, and one section per file with its annotated hunks.
It also embeds a marker comment at the top of the file, `<!-- {"step":"create-pr-walkthrough","sha":"<head sha>","generated_at":"..."} -->`, so a re-run can tell whether the page already matches the current head.

The renderer does not open the page and the skill must not open it either: do not launch a browser, do not open it in the OpenChamber browser panel, and do not print a command that opens it.
Report the path and stop.
Do not post the page to GitHub and do not modify the reviewed repository.

### 6. Report

Report the page path and a short account of what it covers:

```
PR walkthrough: {PR_REVIEW_DIR}/pr-walkthrough.html
{files} files, +{additions} -{deletions} ({changed_lines} changed lines)
Clusters: {titles}
Annotated {n} files and {m} hunks.
```

If you skipped the page, say why in one line and stop.

## Output Format

The artifact is `$PR_REVIEW_DIR/pr-walkthrough.html`.
The intermediate `narrative.json` and `pr.diff` stay in `$PR_REVIEW_DIR/walkthrough/` for re-renders and are not part of the deliverable.

The narrative schema the renderer reads:

```json
{
  "meta": { "repo": "owner/repo", "pr": 42, "title": "...", "author": "...", "url": "...",
            "base_ref": "main", "head_ref": "feature", "head_sha": "...", "commits": 4,
            "closing_issues": [37], "generated_at": "...",
            "stats": { "files": 12, "additions": 340, "deletions": 120, "changed_lines": 460 } },
  "summary": "...",
  "why": "...",
  "reading_order": [
    { "title": "The request path", "why": "Read the contract first, then follow it inward.",
      "files": ["src/routes.py", "src/client.py"] }
  ],
  "files": [
    { "path": "src/client.py", "change_type": "modified", "purpose": "...",
      "annotations": { "0": "...", "2": "..." }, "risks": ["..."] }
  ],
  "assess": { "risk": "high", "confidence": "medium", "verdict": "investigate" },
  "risks": [ { "level": "high", "title": "...", "detail": "...", "source": "assess-pr-risk" } ],
  "findings": [ { "severity": "must", "title": "...", "detail": "...",
                  "file": "src/client.py", "line": 8, "source": "review-pr" } ],
  "questions": ["..."],
  "verdict": "..."
}
```

## Example Usage

**Scenario 1: Large feature PR**

```
/create-pr-walkthrough 42 acme/api
```

The scaffold reports 18 files and 940 changed lines, so the page is built.
The reading order starts with the new schema and the route contract, then the client, then the migration, then tests and generated fixtures.
The client's retry loop gets an annotation naming the existing helper it duplicates; the page links the `must` finding about the hardcoded key to its file and line.

**Scenario 2: Large but mechanical PR**

```
/create-pr-walkthrough 88 acme/api
```

The scaffold reports 40 files and 2,100 changed lines, almost all in a lockfile and generated clients.
The agent skips the page, says the diff is mechanical, and points at the source diff instead.

**Scenario 3: Small but hard to follow**

```
/create-pr-walkthrough 55 acme/api
```

The scaffold reports 6 files and 140 changed lines, below the threshold.
The change adds a lock ordering rule across three call sites, so the agent builds the page anyway and uses the reading order to sequence the call sites.

**Scenario 4: Forced**

```
/create-pr-walkthrough 42 acme/api --force
```

Builds the page regardless of the size decision.

## Related Skills

| Skill | Relationship |
|---|---|
| `review-pr-full` | Orchestrator that dispatches this skill after the review chain for large PRs, then commits the HTML with the reports. |
| `review-pr` | Code-craft review whose findings the walkthrough quotes for the findings panel. |
| `assess-pr-risk` | Risk and confidence source for the assess panel and the risk list. |
| `summarize-behavior-changes` | Source for behavior changes, affected consumers, and breaking changes. |
| `analyze-test-coverage` | Source for what the tests prove and what they miss. |
| `validate-pr` | Source for whether the PR solves the right problem. |
| `verify-pr` | Source for acceptance-criteria conformance. |
| `create-mermaid-visualization` | For a diagram inside an article or document; this skill produces the whole walkthrough page instead. |
