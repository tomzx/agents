---
name: summarize-behavior-changes
description: Summarize the behavior changes a pull request introduces: what changed, from what to what, which consumers it affects, and which changes are breaking. Self-contained (diff and codebase only), so it runs in parallel with analyze-test-coverage and assess-pr-risk. Use when the user asks "what does this PR change", "behavior change summary", "what will behave differently after merge", "does this change behavior", or wants a reviewer-facing or release-facing summary of a PR's effects.
allowed-tools: Bash(git:*, ghx:*, gh:*, ~/.agents/scripts/should-post-to-github:*, ~/.agents/scripts/review-progress:*), Read, Write, Glob, Grep
argument-hint: "<pr-number> [repository] | <diff-ref | worktree-dir>"
---

# Summarize Behavior Changes

Answers one question about a pull request: **what will behave differently once this merges?**
It reads the diff and the surrounding code and produces a structured, human-readable summary of every behavior change: what changed, from what to what, which consumers it affects, and whether it is breaking.
This is the "what does it do" companion to the other review steps: `/analyze-test-coverage` asks whether the changes are tested, `/assess-pr-risk` asks how risky they are, `/validate-pr` asks whether they are the right product, `/verify-pr` asks whether they meet the criteria, and `/review-pr` asks whether they are well built.
None of those answer "what will behave differently", which is what a reviewer, release-note author, or on-call engineer needs first.

It is **descriptive, not judgmental**: it reports behavior changes and flags the ones that are breaking or undeclared, but it does not score risk, judge craft, or gate anything.
Its marker verdict is always `informational`, and it never halts the pipeline.

It is self-contained: it gathers evidence from the diff and the codebase only, so `review-pr-full` dispatches it in parallel with `analyze-test-coverage` and `assess-pr-risk`.
It never reads or waits for sibling reports.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md` (PR Review Reports for report location and posting rules).
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read access to the target repository
- `git worktree` available
- Self-contained evidence: the summary needs only the diff and the codebase; it never reads or waits for sibling reports (`analyze-test-coverage`, `validate-pr`, `verify-pr`, `review-pr`, `assess-pr-risk`)
- Orchestrators (`review-pr-full`, `review-requested-prs`) dispatch this skill concurrently with the analyze-test-coverage -> validate -> verify -> review chain and provide `WORKTREE_DIR`

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `summarize-behavior-changes`.

### Communication guidelines (outbound text)

Before composing any text posted or drafted on the user's behalf, apply [`communication-guidelines/SKILL.md`](../communication-guidelines/SKILL.md).

## Workflow

```
Fetch PR metadata + diff ($1)
          |
          v
CLOSED or MERGED? --> note and stop
          |
          v
Create git worktree on PR branch
          |
          v
Collect the diff; split changed
files into behavior-bearing and
behavior-preserving
          |
          v
Enumerate behavior changes
(what, before -> after, consumer)
          |
          v
Call out breaking changes and
removals; list what is NOT
a behavior change
          |
          v
Write summarize-behavior-changes.<sha>.md
(verdict: informational)
Post if should-post-to-github allows
          |
          v
Clean up worktree
```

## Steps

### 1. Fetch PR metadata and diff

Set `PR_NUMBER="$1"` and `REPO="$2"` (or `$REPO` from the environment) when invoked as `/summarize-behavior-changes 42 acme/api`.

```bash
ghx pr view $PR_NUMBER --repo "$REPO" --comments --refresh
gh pr view $PR_NUMBER --repo "$REPO" --json headRefOid,headRepository,closingIssuesReferences,files,title,body
gh pr diff $PR_NUMBER --repo "$REPO"
```

Extract from the `gh pr view --json` output:
- `HEAD_COMMIT`: the `headRefOid` (latest commit SHA, full)
- `SHORT_SHA`: first 7 characters of `HEAD_COMMIT`
- `PR_AUTHOR`: the `author.login`
- `HEAD_REPO`: the `headRepository.nameWithOwner`
- `HEAD_BRANCH`: the `headRefName`
- `HEAD_TREE`: content snapshot of the head commit: `git fetch "https://github.com/$HEAD_REPO.git" "$HEAD_BRANCH" >/dev/null 2>&1 || true; git rev-parse "$HEAD_COMMIT^{tree}"`
- `ISSUE_NUMBER`: the first linked issue number from `closingIssuesReferences` (or empty)
- `PR_TITLE`, `PR_BODY`, and `PR_STATE`: `OPEN`, `CLOSED`, or `MERGED`

If `PR_STATE` is `CLOSED` or `MERGED`, note it and stop; the summary is for open PRs.

Define the report directory once: `PR_REVIEW_DIR="$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER"` (see `sdlc/references/shared.md`, PR Review Reports).

Publish the in-progress marker before analyzing, and remove it before returning on every path (see `sdlc/references/shared.md`, In-progress marker):

```bash
mkdir -p "$PR_REVIEW_DIR"
~/.agents/scripts/review-progress start --step summarize-behavior-changes --repo "$REPO" --pr "$PR_NUMBER" --sha "$HEAD_COMMIT"
```

### 2. Create a git worktree on the PR branch

If `$WORKTREE_DIR` is already set (e.g. by an orchestrator), use that directory directly and skip creation and cleanup.

```bash
_WORKTREE_OWNER=false
if [ -z "${WORKTREE_DIR:-}" ]; then
  git fetch "https://github.com/$HEAD_REPO.git" $HEAD_BRANCH
  WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
  mkdir -p /tmp/sdlc/$REPO
  git worktree add $WORKTREE_DIR FETCH_HEAD
  _WORKTREE_OWNER=true
fi
```

If worktree creation fails, stop.

### 3. Collect the diff and classify the changed files

Resolve the diff inside the worktree against the PR's merge base:

```bash
BASE_BRANCH=$(gh pr view $PR_NUMBER --repo "$REPO" --json baseRefName --jq .baseRefName)
git -C "$WORKTREE_DIR" fetch origin "$BASE_BRANCH"
DIFF_REF="origin/${BASE_BRANCH}...HEAD"
git -C "$WORKTREE_DIR" diff --name-only "$DIFF_REF"
git -C "$WORKTREE_DIR" diff "$DIFF_REF"
```

Split the changed files into two groups:

- **Behavior-bearing**: source logic; API routes, handlers, and response shapes; database schemas and migrations; configuration defaults and feature flags; CLI flags, arguments, and output; permissions and auth rules; serialization/wire formats; error messages and status/exit codes; retry, timeout, and scheduling logic; dependency upgrades that change runtime behavior.
- **Behavior-preserving**: comments, docstrings, formatting and whitespace; pure renames with no semantic change; test-only files; documentation; lockfiles; dependency pins with no runtime effect.

Only the behavior-bearing group feeds the summary.
The behavior-preserving group is listed briefly so the reader knows what was excluded and why (see step 6).

### 4. Enumerate the behavior changes

For each behavior-bearing change in the diff, read the hunk and the surrounding code (and its callers where the change is a public surface) and record:

1. **Area / entry point**: the user-facing or programmatic surface that changes, named as a consumer would see it (`POST /payments`, `--timeout` flag, `pricing.calculate`), with its `path:line`.
2. **Before**: the behavior prior to this PR. For genuinely new behavior, write "did not exist".
3. **After**: the behavior after this PR.
4. **Change type**: `added`, `changed`, `removed`, `fixed`, `performance`, or `dependency`.
5. **Breaking?**: `Yes` / `No` / `Conditional`, with the reason (see step 5).
6. **Consumer affected**: who or what observes the difference (end users, API clients, downstream services, operators, other modules).

Prefer observable behavior over implementation detail: "requests now time out after 30s instead of hanging" beats "added a timeout parameter to the client constructor", unless the parameter itself is the public surface that callers use.

### 5. Call out breaking changes and removals

Identify the changes that can break an existing consumer:

- Removed or renamed public functions, endpoints, flags, config keys, or fields
- Changed function/endpoint signatures or response shapes
- Changed defaults (for example a new default timeout, pagination size, or permission)
- Stricter validation that rejects input previously accepted
- Changed error types, messages, status codes, or exit codes
- Removed or renamed environment variables, headers, or metrics

List each one with what breaks and what a consumer must do to adapt.
A change is `Conditional` breaking when it only breaks a specific usage (for example a caller that relied on an undocumented behavior).

### 6. State what is not a behavior change

Summarize the behavior-preserving changes in one short list so the reader knows the summary is complete and what was deliberately excluded:

```
Renames, formatting, docs, and tests only, no observable behavior change in:
- src/util/format.py (whitespace, comment)
- tests/test_format.py (new assertions, no production code)
```

If the entire diff is behavior-preserving, say so plainly; that is a useful result (a pure refactor).

### 7. Surface undeclared behavior changes (findings)

The summary is not a review, but it should make two things visible when it sees them, at severity proportional to impact:

- 🔴 MUST: a **breaking change** with no migration note, deprecation path, or mention in the PR description/issue
- 🟡 SHOULD: a **behavior change the linked issue and PR description do not mention** (unstated scope)
- 🟢 MAY: a behavior change that is declared but hard to find (for example only in a commit message)

Frame these as surfacing, not verdicts: "this changes X, and nothing in the issue or PR description mentions it", so the human can decide whether it was intended.
Do not score risk (that is `/assess-pr-risk`) or judge craft (that is `/review-pr`).

### 8. Write the report and post it

Write the report to `$PR_REVIEW_DIR/summarize-behavior-changes.$SHORT_SHA.md` and point the stable symlink at it:

```bash
PR_REVIEW_DIR="$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER"
mkdir -p "$PR_REVIEW_DIR"
ln -sf "summarize-behavior-changes.$SHORT_SHA.md" "$PR_REVIEW_DIR/summarize-behavior-changes.report.md"
```

Start the file with the marker so the orchestrator can detect which commit was summarized:

```markdown
<!-- {"step":"summarize-behavior-changes","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"informational"} -->
```

The verdict is always `informational`; this step never gates anything.
Below the marker, add the traffic-light header from `sdlc/references/shared.md` (Report header (traffic light)): the title, one overall go/no-go line, then one line each for Behavior changes, Breaking changes, and Declaration with their own lights.
The lights report what the diff shows; they gate nothing.

Posting as a PR comment is decided by `should-post-to-github`.
Run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`; if it exits 1, skip posting (the report is saved locally).
If it exits 0, set `REPORT` to the report file's contents and `FOOTER` to the attribution footer per `../github-post-attribution/SKILL.md`, then post with the **Posting a review report** recipe in `skills/sdlc/references/shared.md` (`STEP="summarize-behavior-changes"`).
The recipe updates this step's existing comment on the PR (append or replace per `PR_REVIEW_POST_MODE`, default `replace`) instead of adding a new comment on every run; in `replace` mode the body also ends with the reviewed-commits index.

### 9. Clean up

```bash
~/.agents/scripts/review-progress stop --step summarize-behavior-changes --repo "$REPO" --pr "$PR_NUMBER"
if [ "$_WORKTREE_OWNER" = true ]; then
  git worktree remove $WORKTREE_DIR
fi
```

## Orchestrated runs (review-pr-full)

When dispatched by `review-pr-full`, this step runs **in parallel** with `assess-pr-risk` and the first chain step (`analyze-test-coverage`).
The worktree already exists at `$WORKTREE_DIR`; use it and do not create or remove one.
Resolve the PR context and diff as in steps 1 and 3, produce the summary, and write the report per step 8.

It is self-contained, so its report is written before the later chain steps run and is never read by them; it never gates the chain and is never dropped by a chain failure.

## Output Format

```markdown
<!-- {"step":"summarize-behavior-changes","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"informational"} -->
# Behavior Changes: #<PR_NUMBER> <title>

**🟢 / 🟡 / 🔴 <Clear / Caution / No-go>** — <one sentence: what a consumer or release-note author must know before merge>

- 🟢 / 🟡 / 🔴 Behavior changes — <N changes across <k> areas>
- 🟢 / 🟡 / 🔴 Breaking changes — <none, or the list, and whether each has a migration note>
- 🟢 / 🟡 / 🔴 Declaration — <every change named in the issue or PR description, or N unstated>

Reviewed commit: `SHORT_SHA`

## Summary

<One paragraph: the overall nature of the change (for example "adds a payment
endpoint and changes the default request timeout") and the headline behavior
difference a consumer will see.>

## Behavior changes

| Area / entry point | Before | After | Change type | Breaking? | Consumer affected |
|---|---|---|---|---|---|
| `POST /payments` (`src/payments/routes.py:12`) | did not exist | accepts a charge and returns a payment id | added | No | API clients |
| default request timeout (`src/http/client.py:30`) | 10s | 30s | changed | Conditional | callers relying on a fast failure |

## Breaking changes

<For each breaking or conditional change: what breaks, and what a consumer must
do to adapt. Omit the section when there are none.>

## Removed behavior

<Functions, endpoints, flags, config keys, or fields that no longer exist, with
their replacement if any. Omit when there are none.>

## Undeclared behavior changes

<Findings per step 7: breaking changes with no migration path, and behavior
changes the issue/PR description does not mention. Omit when there are none.>

## Not behavior changes

<The behavior-preserving files that were excluded, so the reader knows the
summary is complete. If the whole diff is behavior-preserving, say so here and
keep the sections above empty.>

---
<Attribution footer per github-post-attribution>
```

## Failure Modes

| Mode | Response |
|---|---|
| **Worktree creation fails** | Stop |
| **PR is CLOSED or MERGED** | Note it and stop |
| **Diff is very large (>1000 lines)** | Summarize the entry points and public surfaces exhaustively, sample internal changes, and say which areas were sampled rather than read |
| **`ghx` unavailable** | Fall back to `gh pr view` for PR context |
| **Base branch unavailable** | Diff against `HEAD` and the merge base with the repository default branch, and note the fallback |

## Example Usage

**Scenario 1: New endpoint plus a default change**
```
/summarize-behavior-changes 42 acme/api
```
The diff adds `POST /payments` and changes the client's default timeout from 10s to 30s, with the timeout change unmentioned in the issue.
The report lists both under Behavior changes, flags the timeout as `Conditional` breaking (a caller relying on fast failure), and raises one 🟡 finding for the unstated timeout change.

**Scenario 2: Pure refactor**
```
/summarize-behavior-changes 55 acme/api
```
The diff is renames, extraction, and formatting, with no observable behavior change.
The report says so plainly under Not behavior changes and keeps the Behavior changes table empty.

**Scenario 3: Removal with a migration note**
```
/summarize-behavior-changes 61 acme/api
```
The diff removes the deprecated `--legacy-mode` flag and documents the replacement in the PR description.
The report lists the removal under Removed behavior with the replacement, and raises no finding because the change is declared.

**Scenario 4: Called by review-pr-full**
```
review-pr-full dispatches this skill in parallel with assess-pr-risk and analyze-test-coverage, passing WORKTREE_DIR.
```
The skill reuses the worktree, writes its report with the `informational` marker, and never gates the chain.

## Related Skills

| Skill | Relationship |
|---|---|
| `review-pr-full` | Dispatches this skill in parallel with assess-pr-risk and the analyze-test-coverage -> validate -> verify -> review chain; its report carries the commit marker the staleness script tracks |
| `analyze-test-coverage` | Sibling parallel/early step: asks whether the behavior changes are covered by tests; this skill asks what the behavior changes are |
| `assess-pr-risk` | Sibling parallel step: judges how risky the changes are; this skill describes what the changes do |
| `review-pr` | Code-craft review: answers whether the change is well built, not what behavior it changes |
| `review-requested-prs` | Orchestrates this skill (via review-pr-full) across all review-requested PRs |
