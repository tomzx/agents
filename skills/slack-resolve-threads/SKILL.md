---
name: slack-resolve-threads
description: >-
  Go through the Slack threads you participated in, read each one with
  slackx, judge whether the discussion reached a satisfactory conclusion,
  and mark resolved threads with a checkmark reaction so future runs skip them.
  Use this whenever the user wants to triage, review, clean up, or "close out"
  their open Slack conversations, check which of their threads still need a
  reply or follow-up, or asks "have all my Slack threads been resolved?" — even
  if they don't mention slackx by name.
---

# Resolve my Slack threads

This skill answers a recurring question: *"Of all the Slack conversations I'm
part of, which ones are actually done, and which still need me?"* It reads each
thread, decides whether it reached a satisfactory conclusion, and marks the done
ones with a checkmark (`:white_check_mark:`) reaction. The checkmark is both the
human-visible signal in Slack and the marker that lets future runs skip threads
they've already judged, so the work is incremental and cheap to repeat.

The judgement is the heart of this skill, and it needs a model reading the
actual conversation — not a keyword match. The tooling exists only to get the
thread text in front of you and to record the verdict.

## The pieces

**`slackx` is the only tool used to read threads.** Every conversation is
read through `slackx conversations show` (nothing else fetches or parses thread
content). The two small helpers below exist *only* to cover the two things
`slackx` deliberately cannot do, because it is a read-only, single-thread
cache: it has no command to list the threads you participated in, and no command
to write a reaction.

| Job | Tool | Why not slackx |
|-----|------|----------------------|
| Read a thread's full text | **`slackx conversations show --json`** | This is the whole point of slackx. Always use it. |
| Discover the threads I'm in | `slack-kb-individual`'s `collect_individual_threads.py` | slackx can search messages, but has no command to list the threads you participated in. |
| Set the checkmark | this skill's [`slack_reactions.py`](slack_reactions.py) | slackx is read-only; it has no write/reaction path. |

If the user supplies the thread URLs themselves, you don't need the discovery
helper at all — go straight to reading each one with `slackx`.

All three read `SLACK_TOKEN` (and `SLACK_COOKIE` for xoxc tokens) from a `.env`
file, found by searching up from the working directory. Marking threads needs a
token with `reactions:write`; if reactions fail with `not_allowed_token_type` or
a missing-scope error, tell the user their token can't react and stop — don't
silently fall back to a local-only marker, since the user asked for the
checkmark to appear in Slack.

## Prerequisites

`slackx` is a separate Python CLI (https://github.com/TomzxCode/slackx).
Check for it and install if missing:

```bash
if ! command -v slackx &>/dev/null; then
  git clone https://github.com/TomzxCode/slackx /tmp/slackx
  uv tool install /tmp/slackx        # or: cd /tmp/slackx && uv sync
fi
```

If `uv tool install` isn't desired, you can run it in place with
`uv run --project /tmp/slackx slackx ...`. Confirm it works:
`slackx --help`.

## Workflow

### 1. Discover the threads I'm in

Reuse the individual collector. Incremental mode is the right default for a
recurring triage — it only looks at recent activity and merges with the cached
list:

```bash
uv run ~/.agents/skills/slack-kb-individual/collect_individual_threads.py \
  --user <my-slack-username> --incremental -o my-threads.jsonl
```

For the very first run (or a periodic deep refresh), do a full scan over the
window the user cares about with `--after`/`--before`. Each line of the output
JSONL has `thread_ts`, `channel`, `permalink`, `replies`, and `preview`.

Ask the user for their Slack username and the time window if you don't already
know them. Don't guess the username.

### 2. Cache user names once (optional but recommended)

`slackx` renders raw user ids unless it knows the workspace users. One
call makes every later `show` readable:

```bash
slackx users fetch
```

### 3. For each thread: read, skip-if-done, judge, mark

Loop over the threads from step 1 (or the URLs the user gave you). For each one:

**a. Read the full thread with slackx.** This is the single source of
thread content:

```bash
slackx conversations fetch <permalink>   # refresh the cache to the live state
slackx conversations show --json <permalink>   # read it
```

The explicit `fetch` first guarantees you're reading the current state
(including any checkmark a previous run added); `show` alone would also
auto-fetch on a cache miss, but an existing cached thread would only refresh on
its reply boundary. Read every message in the returned `messages` array, not
just the preview.

**b. Skip if already resolved.** Each message in the `show --json` output
carries its full Slack `payload`, including a `reactions` array on the root
message. If the root already has the `white_check_mark` reaction, a previous run
closed this thread — skip it: no judgement, no write. Because step (a) just
re-fetched, this reaction state is current.

(If you ever need to confirm the reaction independently of the cache, the
helper's `check` action queries the live reaction directly:
`uv run ~/.agents/skills/slack-resolve-threads/slack_reactions.py check <permalink>`.)

**c. Judge whether it reached a satisfactory conclusion.** This is your call as
a reader, not a keyword search. A thread is **resolved** when the original ask
got a clear answer, fix, decision, or acknowledgement, and no open follow-up
question is left dangling. Lean on the shape of the conversation:

- A question that received a direct, accepted answer (often with a "thanks",
  a reaction, or the asker confirming) — resolved.
- A bug/issue report that ended in a fix, a workaround, a "shipped", or a clear
  decision/next-step owner — resolved.
- A discussion that converged on a decision everyone moved on from — resolved.

Leave it **unresolved** when:

- The last message is an unanswered question directed at me or the group.
- Someone is waiting on a reply, a fix, or a decision that never came.
- The thread just trails off mid-discussion with the core ask still open.

When it's genuinely ambiguous, prefer leaving it unresolved — a stray checkmark
hides a thread that may still need attention, which is worse than re-reading a
done thread next time. Briefly note *why* for each verdict; the reasoning is
what the user actually wants to see.

**d. Mark the resolved ones.** Only for threads you judged resolved:

```bash
uv run ~/.agents/skills/slack-resolve-threads/slack_reactions.py \
  add <permalink>
```

This is idempotent — Slack's `already_reacted` is treated as success.

## Report

After the loop, give the user a concise summary so they know exactly what needs
them. Use this structure:

```
# Slack thread triage — <date>

Scanned N threads (S already resolved and skipped).

## Resolved this run (M) — checkmark added
- <#channel> "<short topic>": <one-line reason it's done>

## Still needs you (K)
- <#channel> "<short topic>": <what's outstanding / who's waiting>  <permalink>

## Unsure — left unmarked (J)
- <#channel> "<short topic>": <why it's ambiguous>  <permalink>
```

Put the "Still needs you" section first in spirit — that's the actionable part.
Always include permalinks for anything not resolved so the user can jump
straight to it.

## Notes on cost and safety

- The whole loop is incremental: discovery merges with its JSONL cache,
  `slackx` only fetches new replies, and resolved threads are skipped via
  their checkmark. Running this daily stays cheap.
- Never add the checkmark to a thread you didn't actually read and judge in this
  run. The reaction is a claim that you reviewed it.
- Process threads in batches and keep going on errors (a single unreachable
  thread shouldn't abort the run); collect failures and list them at the end.
