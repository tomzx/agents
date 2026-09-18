---
name: triage-pr-feedback
description: Proactively scan your open PRs for unresolved reviewer feedback, fan out one analysis agent per PR to write a concrete recommendation file per comment, then present decisions and hand off execution to handle-pr-reviewer-feedback. Designed to run on a 10-15 minute schedule so you never have to run handle-pr-reviewer-feedback manually.
allowed-tools: Bash(uv run:*, gh:*, ghx:*, git:*, ~/.agents/scripts/triage_pr_feedback.py:*, ~/.agents/scripts/should-post-to-github:*, opencode run:*), Read, Write, Edit, Glob, Grep, Task
argument-hint: "[pr-url ... | owner/repo ...] [--reanalyze] [--prepare-only]"
---

# Triage PR Feedback

Scans the open pull requests you authored for reviewer feedback that is still awaiting a response, and for each new comment writes a recommendation file analyzing how to address it. It then presents the recommendations so you can decide what to do, and on approval hands execution off to `handle-pr-reviewer-feedback`.

This skill is the proactive counterpart of `handle-pr-reviewer-feedback`: instead of you running that skill by hand to discover what reviewers said, a scheduled run does the discovery and the analysis up front, so the only thing left is a decision.

Nothing here posts to GitHub, commits, or pushes. Those actions belong to `handle-pr-reviewer-feedback` and are gated by `should-post-to-github`.

## Prerequisites

- `uv` installed (for running the Python script)
- `gh` CLI authenticated (used by the script as a token fallback, and by analysis agents for the occasional PR metadata call)
- `git` available: each analysis agent creates a temporary worktree of the PR head so it can read the code and diff from disk instead of making repeated `gh api` calls
- Sub-agent dispatch via the `Task` tool (`subagent_type: "general"`). If unavailable, fall back to sequential mode.

### Related skills

For the reviewer-side flow (verifying that a PR author addressed your review comments), use `handle-pr-author-feedback` instead.

## How new feedback is tracked

A feedback item is considered **already handled** once an analysis file exists for it:

```
$HOME/.sdlc/{owner}/{repo}/pull-requests/{PR}/feedback/{feedback-id}.md
```

The id is derived from the GitHub node, so it is stable across runs (e.g. `comment-4021164710`, `review-4123`, `conversation-5689431256`). Re-running the script therefore reports only genuinely new feedback, which is what makes a 10-15 minute cadence safe and quiet. Pass `--reanalyze` to ignore existing files and treat everything as new.

A feedback item is **awaiting a decision** when its file exists but has no `decision:` frontmatter key. Recording a decision (`implement`, `decline`, `defer`) stops it from being re-surfaced.

## Workflow

```
Run ~/.agents/scripts/triage_pr_feedback.py $@ --json
                |
                v
   PRs with new_feedback[] (and analysis_path per item)
                |
                v
   Fan out: one analysis subagent per PR, concurrently
     |   checks out the PR head into a temp worktree, reads code from disk
     |   writes $HOME/.sdlc/<repo>/pull-requests/<n>/feedback/<id>.md
     |   (one file per feedback item, recommendation + draft reply)
                |
                v
   Collect recommendations -> decision table
                |
                v
   Prompt user: implement / decline / defer per item
                |
                v
   implement -> load + run handle-pr-reviewer-feedback per PR
   record decision in each analysis file
```

## Steps

### 1. Run the discovery script

Run the script with the skill's arguments and JSON output:

```bash
~/.agents/scripts/triage_pr_feedback.py $@ --json
```

The script accepts the same target arguments as `review-requested-prs`:
- No arguments: all open PRs you authored (drafts included), across all repos
- `owner/repo` or `owner` arguments: scope the search
- PR URL arguments: process only those specific PRs

Useful flags:
- `--limit N`: cap the number of PRs discovered (default 100)
- `--workers N`: number of PRs processed in parallel for feedback discovery (default 8)
- `--exclude-drafts`: skip draft PRs
- `--include-resolved`: also analyze resolved review threads (excluded by default)
- `--reanalyze`: ignore existing recommendation files and treat all feedback as new
- `--log-level debug`: see API call timings

It returns a JSON array of PR states. Each PR has `new_feedback` (items with no analysis file) and `pending_decision` (analyzed but undecided), plus `head_commit`, `head_repo`, `head_branch`, `base_ref`, `base_commit`, `title`, `url`, `draft`, and per-item `id`, `kind`, `author`, `body`, `url`, `path`, `line`, `thread_id`, and `analysis_path`.

If every PR has an empty `new_feedback`, report "no new feedback" and stop. If some PRs have a non-empty `pending_decision` while none have new feedback, list them as awaiting a decision but do not re-prompt (their decision is deliberately deferred).

### 2. Fan out one analysis subagent per PR

For each PR with a non-empty `new_feedback`, launch one subagent with the `Task` tool, `subagent_type: "general"`. Put **multiple Task calls in a single message** so they run concurrently; if there are many PRs, launch in batches (for example 5 at a time) and wait for each batch.

Each subagent starts with a fresh context, so its prompt must be self-contained and embed the feedback items verbatim. Use this template, substituting the bracketed values and repeating the per-item block for every item in `new_feedback`:

```
You are analyzing reviewer feedback on a GitHub pull request to prepare a
recommendation for its author. Do not change code, commit, push, or post
anything to GitHub. Your only output is one recommendation file per feedback
item.

Repository: <REPO>
Pull request: #<N>
URL: <URL>
Head: <HEAD_REPO>@<HEAD_BRANCH> (<HEAD_COMMIT>)
Base: <BASE_REF> (<BASE_COMMIT>)

Check the PR out once into a scratch repo and read everything from disk
instead of calling `gh api` per file:

SCRATCH=/tmp/sdlc/<REPO>
WORKTREE=$SCRATCH/pr-<N>
mkdir -p "$SCRATCH"
[ -d "$SCRATCH/repo/.git" ] || git -C "$SCRATCH" init -q repo
git -C "$SCRATCH/repo" fetch https://github.com/<HEAD_REPO>.git \
  <HEAD_BRANCH>:refs/triage-pr-feedback/<N>/head
git -C "$SCRATCH/repo" fetch https://github.com/<REPO>.git \
  <BASE_REF>:refs/triage-pr-feedback/<N>/base
git -C "$SCRATCH/repo" worktree add --detach "$WORKTREE" \
  refs/triage-pr-feedback/<N>/head
BASE_SHA=$(git -C "$SCRATCH/repo" rev-parse refs/triage-pr-feedback/<N>/base)

If the worktree already exists, reuse it and skip recreation. Then read from
the checkout:
- Diff:    git -C "$WORKTREE" diff "$BASE_SHA"...HEAD
- Files:   read "$WORKTREE/<path>" directly (no gh api)
- History: git -C "$WORKTREE" log --oneline "$BASE_SHA"..HEAD
- PR description: gh pr view <N> --repo <REPO> (one call, only if needed)

When finished with all files, clean up the checkout:
git -C "$SCRATCH/repo" worktree remove "$WORKTREE" --force
git -C "$SCRATCH/repo" update-ref -d refs/triage-pr-feedback/<N>/head
git -C "$SCRATCH/repo" update-ref -d refs/triage-pr-feedback/<N>/base

For EACH feedback item below, write exactly one file at its ANALYSIS_PATH.

FEEDBACK_ID: <id>
KIND: <kind>
AUTHOR: <author>
URL: <url>
LOCATION: <path>:<line>
ANALYSIS_PATH: <analysis_path>
COMMENT:
<body>
```

(repeat the block above for each item)

```
Each file must use exactly this structure:

---
feedback_id: <id>
kind: <kind>
repo: <REPO>
pr: <N>
author: <author>
created_at: <created_at>
head_commit: <HEAD_COMMIT>
analyzed_at: <ISO-8601 UTC>
recommendation: implement | reject | clarify | no-action
confidence: high | medium | low
session_link: http://localhost:10000/?session=<session-id>
---

# <one-line title>

## Comment

> <verbatim comment body>

Location: `<path>:<line>` ([thread](<url>))

## Analysis

<What is being asked; whether it is correct, grounded in file:line evidence;
its impact, scope, and any risks or trade-offs.>

## Recommended action

<Concrete steps naming the files and lines to change and how, or why the
feedback should be rejected, or what to ask if it is ambiguous.>

## Suggested reply

<A concise reply in the author's voice, ready to post on the thread.>

## Suggested change

<Optional diff sketch or ordered steps. Omit if not applicable.>

Guidance:
- Recommend `implement` when the feedback is correct and in scope.
- Recommend `reject` when it is wrong, already addressed, or out of scope,
  with the reasoning spelled out.
- Recommend `clarify` when the reviewer's intent is genuinely ambiguous.
- Recommend `no-action` when the comment is not actionable (for example a bot
  status card or a resolved-by-other-means note).
- Ground every claim in the code at the PR head (the worktree checkout), citing
  file:line. Do not trust the comment's description of the code without
  checking it.

When finished, return exactly one line per feedback item and nothing else:
FEEDBACK <id> | <recommendation> | <confidence> | <one-line summary>
```

#### Fallback: no Task tool

If the `Task` tool is unavailable, run each PR's analysis sequentially with `opencode run`:

```bash
opencode run --auto "<THE SUBAGENT PROMPT ABOVE>"
```

Record in the summary that sequential mode was used.

### 3. Collect and present recommendations

Parse each subagent's `FEEDBACK ...` lines and read the recommendation files it wrote. Build a decision table grouped by repository:

| Repository | PR | Feedback | Author | Ask | Recommendation | Confidence | Analysis |
|---|---|---|---|---|---|---|---|
| owner/repo | #42 | comment-123 | alice | Add null guard for `user` | implement | high | [file](file:///...) |
| owner/repo | #42 | comment-124 | alice | Rename `processBatch` | reject | medium | [file](file:///...) |

Link each row to its `analysis_path` (a `file://` link) so the user can open the full analysis.

If the run is unattended (`--prepare-only` argument, or `$OUTCOME_YAML` is set), stop here: report the table and the file paths, and do not prompt. The recommendations are ready for the next interactive session.

### 4. Prompt the user for decisions

Ask the user, per feedback item, whether to `implement`, `decline`, or `defer`. Use the `question` tool when available; otherwise present the table and ask in prose.

Recommendations are advisory: the user may override any of them.

### 5. Execute the decisions

Load the successor skill before running it, per the shared SDLC conventions:

1. For each PR with at least one `implement` decision, load `handle-pr-reviewer-feedback` with the skill tool, then run it for that PR with a prompt that names the approved items and their analysis files:

   ```
   /handle-pr-reviewer-feedback <N>
   ```
   Tell it, in the prompt, which feedback items the user approved (by feedback id and analysis file path) and which the user declined. That skill owns implementing, committing, pushing, and replying, and it consults `should-post-to-github` before posting.

2. For every item, regardless of the decision, write the outcome into its analysis file's frontmatter so the next run does not re-surface it:

   ```yaml
   decision: implement | decline | defer
   decided_at: <ISO-8601 UTC>
   ```

   A `defer` decision intentionally stays silent until the reviewer comments again (which produces a new feedback id).

3. Report what was implemented, declined, and deferred, and which PRs were handed off.

## Example Usage

**Scenario 1: New reviewer comments on two PRs**
```
/triage-pr-feedback
```
The script reports 3 new feedback items on PR #42 and 1 on PR #88. Two subagents run concurrently, writing 4 analysis files under `~/.sdlc/<repo>/pull-requests/<n>/feedback/`. The user approves 2 fixes and declines 1; `handle-pr-reviewer-feedback` is loaded and run for PR #42 to implement and reply.

**Scenario 2: Scheduled run, nothing new**
```
/triage-pr-feedback --prepare-only
```
Every open PR's feedback already has an analysis file. The script reports no new feedback, the skill exits with a one-line summary, and no subagents are launched.

**Scenario 3: Re-analyze after a force-push**
```
/triage-pr-feedback --reanalyze
```
All feedback items are treated as new; analysis files are rewritten against the current head, and the decision table is presented again.

**Scenario 4: Scope to one PR**
```
/triage-pr-feedback https://github.com/acme/api/pull/42
```
Only PR #42 is scanned, regardless of your other open PRs.

## Scheduling (10-15 minute cadence)

This skill is designed to run unattended. Properties that make it safe:

- Discovery and state are file-based and idempotent: only genuinely new feedback produces work.
- Analysis is read-only (no code changes, no GitHub writes).
- The decision prompt is skipped when `--prepare-only` is passed or `$OUTCOME_YAML` is set.

Scheduling options, in order of preference:

- **OpenChamber scheduled task:** create a task that runs `/triage-pr-feedback --prepare-only` every 15 minutes. Recommendations accumulate under `~/.sdlc/.../feedback/` for the next interactive session.
- **launchd / cron:** a `*/15 * * * *` entry invoking the agent CLI with `/triage-pr-feedback --prepare-only`.
- **GitHub Actions:** a `schedule:` workflow on a self-hosted runner, if you prefer not to rely on a local agent.

Prefer a launchd/cron/OpenChamber task over GitHub Actions when the PRs are in third-party repositories you do not control, since the analysis store lives under `$HOME`.

## Script Reference

| Script | Description |
|---|---|
| `~/.agents/scripts/triage_pr_feedback.py` | Discovers your open PRs, extracts unresolved non-author feedback (review threads, change-request reviews, conversation comments), checks each item's analysis file, and outputs the remaining work as JSON (`--json`), dispatch lines (`--dispatch`), or a Rich table. |

## Related Skills

| Skill | Relationship |
|---|---|
| `handle-pr-reviewer-feedback` | Executor for approved decisions: implements, commits, pushes, and replies. This skill prepares the recommendations it acts on. |
| `handle-pr-author-feedback` | Reviewer-side mirror: verifies an author's fixes against your review comments. |
| `handle-pr-comment` | Reply to a single PR comment without a full triage pass. |
| `review-requested-prs` | The reviewer-side orchestrator this skill's discovery/fan-out model is based on. |
| `should-post-to-github` | The single gate deciding whether replies may be posted to GitHub. |
