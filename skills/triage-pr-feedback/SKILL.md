---
name: triage-pr-feedback
description: Proactively scan your open PRs for unresolved reviewer feedback, fan out one analysis agent per PR to write an analysis file per comment, then present decisions and hand off execution to handle-pr-reviewer-feedback. Designed to run on a 10-15 minute schedule so you never have to run handle-pr-reviewer-feedback manually. An orchestrator only: the analysis artifact, vocabulary, and execution all belong to handle-pr-reviewer-feedback.
allowed-tools: Bash(uv run:*, gh:*, ghx:*, git:*, ~/.agents/scripts/triage_pr_feedback.py:*, ~/.agents/scripts/should-post-to-github:*, opencode run:*), Read, Write, Edit, Glob, Grep, Task
argument-hint: "[pr-url ... | owner/repo ...] [--reanalyze] [--prepare-only]"
---

# Triage PR Feedback

Scans the open pull requests you authored for reviewer feedback that is still awaiting a response, drives `handle-pr-reviewer-feedback` in analyze-only mode to write one analysis file per comment, presents the recommendations so you can decide, and hands execution back to `handle-pr-reviewer-feedback`.

This skill is the proactive counterpart of `handle-pr-reviewer-feedback`: instead of you running that skill by hand to find what reviewers said, a scheduled run does the discovery and the analysis in advance, so the only thing left is a decision.

This skill is an **orchestrator only**. The analysis file contract (location, ids, format, decision vocabulary) and the execution of decisions are owned by `handle-pr-reviewer-feedback`, which is also the skill that documents them. Do not restate the contract here; reference it.

Nothing here posts to GitHub, commits, or pushes. Those actions belong to `handle-pr-reviewer-feedback` and are gated by `should-post-to-github`.

## Prerequisites

- `uv` installed (for running the Python script)
- `gh` CLI authenticated (used by the script as a token fallback, and by analysis agents for the occasional PR metadata call)
- `git` available (analysis agents check out the PR head into a temporary worktree so they can read code and diff from disk)
- Sub-agent dispatch via the `Task` tool (`subagent_type: "general"`). If unavailable, use sequential mode instead.

### Related skills

For the reviewer-side flow (verifying that a PR author addressed your review comments), use `handle-pr-author-feedback` instead.

## How feedback is tracked

A feedback item moves through three file-based states: **analyzed** once its analysis file exists, **decided** once the file has a `decision:` key, and **executed** once it also has an `executed_at:` key. An item with a `decision:` but no `executed_at:` is **awaiting execution**: the user already chose the outcome (possibly in the PR feedback dashboard) but the executor has not run it yet. The canonical path, id scheme, frontmatter keys, and the `implement | decline | defer` vocabulary are defined in `handle-pr-reviewer-feedback` under "The reviewer-feedback contract"; this skill relies on them and does not redefine them.

Because the state is file-based and keyed on stable ids, re-running the script (for example on a 15-minute schedule) reports only genuinely new feedback, which is what makes the cadence safe and quiet. Pass `--reanalyze` to ignore existing files and treat everything as new.

A decision can be recorded either in this skill's prompt or in the standalone dashboard (`uv run ~/.agents/scripts/pr_feedback_dashboard.py`), which writes the same files. Either way, `handle-pr-reviewer-feedback` is what executes the decision; the dashboard only records it.

## Workflow

```
Run ~/.agents/scripts/triage_pr_feedback.py $@ --json
                |
                v
   PRs with new_feedback[] (and analysis_path per item)
                |
                v
   Fan out: one subagent per PR, concurrently,
   each running handle-pr-reviewer-feedback --analyze-only
     |   enumerates via the script, checks out the PR head,
     |   writes $HOME/.sdlc/<repo>/pull-requests/<n>/feedback/<id>.md
                |
                v
   Re-read state -> decision table
                |
                v
   Prompt user: implement / decline / defer per item
   (items already decided elsewhere, e.g. in the dashboard,
    are listed as awaiting execution, not re-prompted)
                |
                v
   Hand off to handle-pr-reviewer-feedback (default mode)
   per PR with the approved/declined lists; it executes,
   commits, pushes, replies, and records decisions +
   executed_at (and picks up pending_execution items too)
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
- `--reanalyze`: ignore existing analysis files and treat all feedback as new
- `--log-level debug`: see API call timings

It returns a JSON array of PR states. Each PR has `new_feedback` (items with no analysis file), `pending_decision` (analyzed but undecided), and `pending_execution` (decided but not yet run), plus `head_commit`, `head_repo`, `head_branch`, `base_ref`, `base_commit`, `title`, `url`, `draft`, and per-item `id`, `kind`, `author`, `body`, `url`, `path`, `line`, `thread_id`, and `analysis_path`.

If every PR has an empty `new_feedback`, report "no new feedback". If some PRs still have non-empty `pending_decision` or `pending_execution`, list them as awaiting a decision or awaiting execution. In an unattended run (`--prepare-only` or `$OUTCOME_YAML` set), stop there and leave them for the next interactive session. In an interactive run, skip the fan-out (step 2) and continue at step 3 so that `pending_execution` items (decisions recorded elsewhere, for example in the dashboard) are handed to `handle-pr-reviewer-feedback` and `pending_decision` items are prompted.

### 2. Fan out analysis, delegated to handle-pr-reviewer-feedback

For each PR with a non-empty `new_feedback`, launch one subagent with the `Task` tool, `subagent_type: "general"`. Put **multiple Task calls in a single message** so they run concurrently; if there are many PRs, launch in batches (for example 5 at a time) and wait for each batch.

Each subagent runs the analyze-only mode of `handle-pr-reviewer-feedback`, which owns the analysis procedure and the file format. The prompt only needs to name the PR and request the summary lines:

```
Prepare reviewer-feedback recommendations for a GitHub pull request by
running the handle-pr-reviewer-feedback skill in analyze-only mode. Do not
change code, commit, push, or post anything to GitHub.

Load the skill `handle-pr-reviewer-feedback` (skill tool) and run it for
<PR_URL> with --analyze-only, following its own analyze workflow: it will
enumerate feedback via ~/.agents/scripts/triage_pr_feedback.py <PR_URL>
--json, check out the PR head, and write one analysis file per new item at
its analysis_path with the session_link from shared.md.

When finished, return exactly one line per feedback item and nothing else:
FEEDBACK <id> | <recommendation> | <confidence> | <one-line summary>
```

The subagent inherits the analysis instructions from the skill, so this prompt stays short and the artifact format lives in exactly one place.

#### Fallback: no Task tool

If the `Task` tool is unavailable, run each PR's analysis sequentially by loading `handle-pr-reviewer-feedback` and running it with `--analyze-only`, or with the agent CLI:

```bash
opencode run --auto "/handle-pr-reviewer-feedback <PR_URL> --analyze-only"
```

Record in the summary that sequential mode was used.

### 3. Collect and present recommendations

Re-run the discovery script (or re-read the PR states) so the just-written analysis files are reflected, and for each PR take its `pending_decision` items. Read each item's `analysis_path` for its `recommendation` and `confidence` per the contract in `handle-pr-reviewer-feedback`. Also list each PR's `pending_execution` items (already decided, for example in the dashboard) so the user sees them, but do not prompt for them. Build a decision table grouped by repository:

| Repository | PR | Feedback | Author | Ask | Recommendation | Confidence | Analysis |
|---|---|---|---|---|---|---|---|
| owner/repo | #42 | comment-123 | alice | Add null guard for `user` | implement | high | [file](file:///...) |
| owner/repo | #42 | comment-124 | alice | Rename `processBatch` | reject | medium | [file](file:///...) |

Link each row to its `analysis_path` (a `file://` link) so the user can open the full analysis.

If the run is unattended (`--prepare-only` argument, or `$OUTCOME_YAML` is set), stop here: report the table and the file paths, and do not prompt. The recommendations are ready for the next interactive session.

### 4. Prompt the user for decisions

Ask the user, per `pending_decision` feedback item, whether to `implement`, `decline`, or `defer`. Use the `question` tool when available; otherwise present the table and ask in prose. Do not prompt for `pending_execution` items: their decision is already recorded and the executor will run it.

Recommendations are advisory: the user may override any of them.

### 5. Hand off to handle-pr-reviewer-feedback

Load the successor skill before running it, per the shared SDLC conventions:

1. For each PR with at least one decided item or at least one `pending_execution` item, load `handle-pr-reviewer-feedback` with the skill tool and run it in default mode, naming the approved and declined items by feedback id and analysis file path:

   ```
   /handle-pr-reviewer-feedback <N>
   ```
   Tell it, in the prompt, which feedback items the user approved (`implement`) and which the user declined (`decline`); items left undecided are `defer`. It also picks up the PR's `pending_execution` items on its own. That skill owns the vocabulary and the recording: it executes the changes, commits, pushes, replies on the threads (gated by `should-post-to-github`), and writes `decision` + `decided_at` (when absent) and `executed_at` into each analysis file. Do not record decisions here.

2. Report what was implemented, declined, and deferred, and which PRs were handed off.

## Example Usage

**Scenario 1: New reviewer comments on two PRs**
```
/triage-pr-feedback
```
The script reports 3 new feedback items on PR #42 and 1 on PR #88. Two subagents run concurrently, each invoking `handle-pr-reviewer-feedback --analyze-only`, writing 4 analysis files under `~/.sdlc/<repo>/pull-requests/<n>/feedback/`. The user approves 2 fixes and declines 1; `handle-pr-reviewer-feedback` is loaded and run for PR #42 to implement, record the decisions, and reply.

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
- Analysis runs as `handle-pr-reviewer-feedback --analyze-only`, which is read-only apart from writing analysis files (no code changes, no commits, no GitHub writes).
- The decision prompt is skipped when `--prepare-only` is passed or `$OUTCOME_YAML` is set.

Scheduling options, in order of preference:

- **OpenChamber scheduled task:** create a task that runs `/triage-pr-feedback --prepare-only` every 15 minutes. Recommendations accumulate under `~/.sdlc/.../feedback/` for the next interactive session.
- **launchd / cron:** a `*/15 * * * *` entry invoking the agent CLI with `/triage-pr-feedback --prepare-only`.
- **GitHub Actions:** a `schedule:` workflow on a self-hosted runner, if you prefer not to depend on a local agent.

Prefer a launchd/cron/OpenChamber task over GitHub Actions when the PRs are in third-party repositories you do not control, since the analysis store lives under `$HOME`.

## Script Reference

| Script | Description |
|---|---|
| `~/.agents/scripts/triage_pr_feedback.py` | Discovers your open PRs, extracts unresolved non-author feedback (review threads, change-request reviews, conversation comments), checks each item's analysis file and its decision/execution state, and outputs the remaining work as JSON (`--json`), dispatch lines (`--dispatch`), or a Rich table. |

## Related Skills

| Skill | Relationship |
|---|---|
| `handle-pr-reviewer-feedback` | Owns the feedback contract and execution: its analyze-only mode produces the analysis files this skill fans out; its default mode executes the decisions this skill collects. |
| `handle-pr-author-feedback` | Reviewer-side counterpart: verifies an author's fixes against your review comments. |
| `handle-pr-comment` | Reply to a single PR comment without a full triage pass. |
| `review-requested-prs` | The reviewer-side orchestrator this skill's discovery/fan-out model is based on. |
| `should-post-to-github` | The single gate deciding whether replies may be posted to GitHub. |
