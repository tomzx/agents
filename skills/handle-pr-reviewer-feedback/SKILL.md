---
name: handle-pr-reviewer-feedback
description: Address reviewer comments on your own GitHub pull request, implementing valid feedback or explaining rejections, then push changes. Owns the reviewer-feedback contract (one analysis file per comment at a canonical path, the implement|decline|defer decision vocabulary, and both the analyze-only and execute modes that triage-pr-feedback orchestrates). The author-side counterpart of handle-pr-author-feedback.
allowed-tools: Bash(gh:*, ghx:*, git:*, uv:*, ~/.agents/scripts/triage_pr_feedback.py:*, ~/.agents/scripts/should-post-to-github:*), Read, Write, Edit, Glob, Grep
argument-hint: "[<pr-number>] [--analyze-only] [--reanalyze]"
---

# Handle PR Reviewer Feedback

Reviews and responds to all reviewer comments on a GitHub pull request you authored, implementing valid feedback or explaining rejections with clear justification.
On user approval it commits and pushes changes; whether replies are posted to GitHub is decided by `should-post-to-github` (based on `~/.sdlc/config.yaml`), otherwise replies are drafted without posting.

This skill owns the reviewer-feedback contract: the canonical analysis file per feedback item, the outcome vocabulary, and the two modes that `triage-pr-feedback` orchestrates.
`triage-pr-feedback` references this contract; it does not restate it.

Two modes:

- **Analyze mode** (`--analyze-only`): enumerate unresolved feedback, analyze each item against the PR head, and write one analysis file per item.
  No code changes, no commits, no pushes, no GitHub writes.
  Idempotent: items whose analysis file already exists are skipped unless `--reanalyze` is passed.
  This is the read-only mode a scheduled `triage-pr-feedback` run drives.
- **Execute mode** (default): analyze any items still missing a file, present the recommendations for the undecided ones, then apply `implement` / `decline` / `defer`, commit and push approved changes, reply (gated by `should-post-to-github`), and record the decision in each file.
  It also picks up items that already carry a `decision` but no `executed_at` (for example decisions recorded by the PR feedback dashboard) and runs them without re-prompting.

For the reviewer-side flow (verifying that a PR author addressed your review comments), use `handle-pr-author-feedback` instead.

## The reviewer-feedback contract

This section is the single source of truth for the analysis artifact.
`triage-pr-feedback` and the discovery script depend on it and must not restate it.

### Location and ids

One file per feedback item:

```
$HOME/.sdlc/{owner}/{repository}/pull-requests/{PR_NUMBER}/feedback/{feedback-id}.md
```

`{feedback-id}` is derived from the GitHub node and is stable across runs: `comment-<databaseId>` (review-thread comment), `review-<databaseId>` (change-request review body), `conversation-<databaseId>` (top-level conversation comment).

### File format

Markdown with YAML frontmatter.
Keys:

- Provenance: `feedback_id`, `kind`, `repo`, `pr`, `author`, `created_at`, `head_commit`, `analyzed_at`.
- `recommendation` — advisory: one of `implement`, `reject`, `clarify`, `no-action`.
- `confidence` — `high`, `medium`, or `low`.
- `decision` — set only after the user decides: `implement`, `decline`, or `defer`.
  Its **absence** marks the item as awaiting a decision; its presence (including `defer`) stops it being re-surfaced.
- `decided_at` — set alongside `decision`.
- `executed_at` — set once the decision has actually been carried out (code changed/committed/pushed and reply posted for `implement`; reply posted for `decline`; the intentional no-op for `defer`).
  Its **absence** alongside a present `decision` marks the item as decided but not yet run, which is the state a decision recorded outside this skill (for example by the PR feedback dashboard) leaves behind.
- `session_link` — the standard session link from `shared.md`.

The body carries the verbatim comment, an analysis based on `file:line` read from the PR head (not from the comment's own description of the code), a recommended action, a draft reply, and an optional suggested change.

### Decision vocabulary

The outcome vocabulary is exactly `implement | decline | defer`:

- `implement` — valid and in scope: change code, commit, push, reply naming the commit.
- `decline` — wrong, already addressed, or out of scope: reply with the reasoning, no code change.
- `defer` — intentionally silent: no reply and no code change until the reviewer comments again (which yields a new feedback id).

The analysis `recommendation` is advisory; the user's `decision` is authoritative.
A `reject` or `no-action` recommendation normally becomes a `decline` decision.

A decision is not the same as a done outcome.
The `decision` key records what the user chose; the `executed_at` key records that the choice was carried out.
The executor writes `executed_at` for every item it runs, including `defer` (whose "execution" is the intentional no-op), so that a decided item is attempted exactly once.

### State semantics

There is no separate state file.
Three keys in each analysis file drive the whole state machine:

- file present -> **analyzed**
- `decision` present -> **decided**
- `executed_at` present -> **executed**

The gap between a present `decision` and an absent `executed_at` is the **decided but not run** state.
This is what lets a decision be recorded in one place (the dashboard, or a prior session) and executed later by this skill without re-prompting.
It is also what makes scheduled analysis idempotent and quiet.
The store is user-global (outside any repo), not governed by `SDLC_DIR`, and never committed.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `gh` CLI authenticated with write access to the target repository.
- `ghx` CLI authenticated for cached PR reads and thread replies.
- `uv` available (the enumeration script runs via its `uv run --script` shebang).
- A PR number or URL.
  If no argument is provided, resolve the number with `ghx pr list --head $(git branch --show-current) --json | jq -r '.[0].number'` and the repo with `gh repo view --json nameWithOwner --jq .nameWithOwner` (or use `$PR_NUMBER` / `$REPO` when present).

### Skill attribution (GitHub)

Before posting any PR comment with `gh`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Posted with** footer for `SKILL_DIR` = `handle-pr-reviewer-feedback`.

### Communication guidelines (outbound text)

Before composing any text posted or drafted on the user's behalf, apply [`communication-guidelines/SKILL.md`](../communication-guidelines/SKILL.md).

## Workflow

```
Resolve target PR ($1)
        |
        v
Enumerate unresolved feedback
  (triage_pr_feedback.py <pr-url> --json)
   -> new_feedback[]      (no file yet)
   -> pending_decision[]  (file, no decision)
   -> pending_execution[] (decision, no executed_at)
        |
        v
Analyze mode: for each item in new_feedback
  write $HOME/.sdlc/.../feedback/<id>.md
        |
        v
--analyze-only? ---- yes ----> report paths, stop
        |                       (no decisions, no writes)
        no
        v
Present recommendation table -> user decides
  implement | decline | defer per item
  (pending_execution items skip the prompt:
   their decision is already recorded)
        |
        v
Execute (no-ops for decline/defer)
        |
        v
Commit + push if any implement
        |
        v
Reply per thread (ghx), only if
should-post-to-github allows:
  implement -> done + commit link
  decline   -> rejection explanation
  defer     -> no reply
        |
        v
Record decision + decided_at (if absent)
and executed_at in each file
```

## Steps

### 1. Resolve the target PR

Use `$1` when given.
Otherwise resolve the number and repo as in the prerequisites.
Work with a canonical URL, `https://github.com/<owner>/<repo>/pull/<n>`, in the steps below.

### 2. Enumerate unresolved feedback

The discovery script is the shared enumerator; it computes the stable feedback ids and the canonical `analysis_path` for each item, and reports which are analyzed and decided:

```
~/.agents/scripts/triage_pr_feedback.py https://github.com/<owner>/<repo>/pull/<n> --json [--reanalyze]
```

Take the single PR object from the array.
Per item it returns `id`, `kind`, `author`, `created_at`, `body`, `url`, `path`, `line`, `thread_id`, `analysis_path`, `analyzed`, `decision`, and `executed_at`; per PR it returns `head_commit`, `head_repo`, `head_branch`, `base_ref`, and `base_commit`.

- `new_feedback[]` — items with no analysis file yet; these need analysis.
- `pending_decision[]` — analyzed but undecided; these need a decision.
- `pending_execution[]` — decided (`decision` present) but not run (`executed_at` absent); these already carry a decision and only need execution.
  A decision recorded by the PR feedback dashboard lands here.
- `feedback[]` — the full set, including already-decided and already-executed items.
- `skipped_reason` — `no_new_feedback` or `draft`; not an error.

If `new_feedback`, `pending_decision`, and `pending_execution` are all empty, report "nothing awaiting response" and stop.

### 3. Analyze items (mode: analyze, or the first phase of execute)

Skip this step entirely when `new_feedback` is empty.

Read the code from the PR head rather than trusting the comments.
Prefer the current checkout when it is the PR head; otherwise create a scratch worktree:

```
SCRATCH=/tmp/sdlc/<owner>/<repo>
WORKTREE=$SCRATCH/pr-<n>
mkdir -p "$SCRATCH"
[ -d "$SCRATCH/repo/.git" ] || git -C "$SCRATCH" init -q repo
git -C "$SCRATCH/repo" fetch https://github.com/<head_repo>.git \
  <head_branch>:refs/handle-pr-reviewer-feedback/<n>/head
git -C "$SCRATCH/repo" fetch https://github.com/<owner>/<repo>.git \
  <base_ref>:refs/handle-pr-reviewer-feedback/<n>/base
git -C "$SCRATCH/repo" worktree add --detach "$WORKTREE" \
  refs/handle-pr-reviewer-feedback/<n>/head
BASE_SHA=$(git -C "$SCRATCH/repo" rev-parse refs/handle-pr-reviewer-feedback/<n>/base)
```

If the worktree already exists, reuse it.
Read the diff (`git -C "$WORKTREE" diff "$BASE_SHA"...HEAD`), files (`"$WORKTREE/<path>"`), and history directly from disk.

For each item in `new_feedback`, write exactly one file at its `analysis_path`, following the file format above, with `analyzed_at` set to the current UTC time and `session_link` per `shared.md`.
Do not modify the file for an item that already has one.

### 4. Present recommendations and collect decisions

If `--analyze-only` is set, or the run is unattended (`$OUTCOME_YAML` set), stop here: report the recommendation table and the analysis file paths, and do not prompt.
(`--analyze-only` never executes, so `pending_execution` items are reported but left for a later execute run.)

Otherwise present the table for the `pending_decision` items, grouped by repository:

| Repository | PR | Feedback | Author | Ask | Recommendation | Confidence | Analysis |
|---|---|---|---|---|---|---|---|
| owner/repo | #42 | comment-123 | alice | Add null guard for `user` | implement | high | [file](file:///...) |

Ask the user, per item, whether to `implement`, `decline`, or `defer` (use the `question` tool when available).
Recommendations are advisory; the user may override any of them.

`pending_execution` items are **not** prompted for: their `decision` is already recorded.
Read it from the file and add them to the work list directly.

When invoked by `triage-pr-feedback`, the caller passes the approved and declined item lists keyed by feedback id and analysis path: use them directly instead of prompting for those items, and merge them with any `pending_execution` items.

### 5. Execute the decisions

The work list is every `pending_decision` item the user just decided plus every `pending_execution` item, each with its effective decision.
For each item:

- `implement` — apply the change named in the analysis.
  Edit the current checkout when it is the PR branch; when working from a scratch worktree, make the edits there and land them in step 6.
- `decline` — no code change; the reasoning goes in the reply.
- `defer` — no code change and no reply.

### 6. Commit and push (only if at least one `implement`)

From the user's checkout:

```
git add -A && git commit -m "<message>"
git push
```

From a scratch worktree, commit there and push to the PR head branch:

```
git -C "$WORKTREE" add -A
git -C "$WORKTREE" commit -m "<message>"
git -C "$WORKTREE" push https://github.com/<head_repo>.git HEAD:refs/heads/<head_branch>
```

Then remove the scratch worktree and its refs:

```
git -C "$SCRATCH/repo" worktree remove "$WORKTREE" --force
git -C "$SCRATCH/repo" update-ref -d refs/handle-pr-reviewer-feedback/<n>/head
git -C "$SCRATCH/repo" update-ref -d refs/handle-pr-reviewer-feedback/<n>/base
```

### 7. Reply to the threads (execute mode only)

Decide whether replies may be posted: get the PR author (`ghx pr view <n> --repo <owner>/<repo> --json | jq -r .author.login`), then run `~/.agents/scripts/should-post-to-github --repo "<owner>/<repo>" --author "<PR_AUTHOR>"`.
If it exits 1, present the drafted replies to the user without posting.

If it exits 0, reply using the `thread_id` from step 2:

- `implement` items: a brief summary and the commit, e.g. "Done: added null guard for `user` in abc1234."
  Never wrap a commit SHA in backticks (GitHub does not autolink a backticked SHA), so write it plain.
- `decline` items: the rejection explanation.
- `defer` items: never reply.

```
ghx pr comment <n> --reply-thread <thread-id> --body "<outcome summary>"
```

Append the **Skill attribution** footer to each reply.

### 8. Record the decisions and their execution

For every item in the work list, regardless of the decision, write the outcome into its analysis file frontmatter so the next run does not re-surface or re-run it:

```yaml
decision: implement | decline | defer
decided_at: <ISO-8601 UTC>
executed_at: <ISO-8601 UTC>
```

Write `decision` and `decided_at` only when they are absent: a `pending_execution` item already has them (recorded by the dashboard or a prior session), so leave them untouched and add only `executed_at`.
Always set `executed_at`, including for `defer`, whose execution is the intentional no-op.

A `defer` decision intentionally stays silent until the reviewer comments again, which produces a new feedback id.

## Example Usage

**Scenario 1: Analyze only (scheduled, no writes)**
```
/handle-pr-reviewer-feedback 42 --analyze-only
```
Enumerates unresolved feedback, writes one analysis file per item under `~/.sdlc/<repo>/pull-requests/42/feedback/`, and reports the paths.
No decisions, commits, pushes, or GitHub writes.

**Scenario 2: Bug fix requested**
```
/handle-pr-reviewer-feedback 42
```
Comment on line 37: "This function doesn't handle `user` being null."
Recommendation: `implement`.
Decision: implement.
Add a null guard, commit, push, reply "Done: ... in abc1234."

**Scenario 3: Stylistic disagreement**
```
/handle-pr-reviewer-feedback 100
```
Comment: "Rename `processBatch` to `run`."
Recommendation: `reject`.
Decision: decline.
Reply: "Keeping `processBatch` as it communicates intent better than `run`."

**Scenario 4: Multiple mixed comments**
```
/handle-pr-reviewer-feedback 77
```
Three comments: a missing test (`implement`), a type annotation (`implement`), an out-of-scope design change (`decline`).
Address each independently, record each decision, then push.

**Scenario 5: Driven by triage-pr-feedback** `triage-pr-feedback` runs this skill with `--analyze-only` per PR on a schedule, then in an interactive session passes the approved/declined lists to a default run, which executes them without re-analyzing.

**Scenario 6: Decisions recorded in the dashboard** The user reviews the analysis files in the PR feedback dashboard and clicks Implement / Decline / Defer, which writes `decision` + `decided_at` but not `executed_at`.
Running `/handle-pr-reviewer-feedback 42` finds those items in `pending_execution`, runs them (no prompt, the decision is already made), and stamps `executed_at`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `~/.agents/scripts/triage_pr_feedback.py <pr-url> --json` | Enumerate unresolved feedback with stable ids and analysis paths |
| `ghx pr comment <n> --reply-thread <thread-id> --body "..."` | Reply to a specific review thread |
| `ghx pr comment <n> --body "..."` | Post a top-level comment on the PR |
| `~/.agents/scripts/should-post-to-github --repo <owner>/<repo> --author <login>` | Gate deciding whether replies may be posted |
| `git push` | Push committed changes from the checkout |
