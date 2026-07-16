---
name: sessions-memory
description: "Turn AI agent sessions archived by agentsview into durable memory. Reads the local agentsview SQLite archive directly (Claude Code, Codex, OpenCode, Gemini, Copilot, and every other harness agentsview syncs), incrementally tracks what has already been processed, and writes two memory layers: per-day timeline notes and PARA entity facts. Use when the user says /sessions-memory, 'remember my sessions', 'build memory from sessions', 'what did I work on', 'sync sessions to memory', or wants coding-session history turned into long-term knowledge. Feeds the para-memory-files system."
---

# Sessions Memory

Reads every AI coding session agentsview has synced from disk (Claude Code, Codex, OpenCode, Gemini, Copilot, and the dozens of other harnesses in its registry) out of the local SQLite archive, and turns them into the two memory layers defined by `para-memory-files`: daily timeline notes (Layer 2, the "when") and PARA entity facts (Layer 1, the durable knowledge graph).

The script owns every deterministic decision: where the archive lives, which sessions are noise (automated runs, subagents, deleted), how incremental processing works, and how transcripts are grouped. The skill owns the judgment part: deciding what is actually worth remembering from each session.

## Prerequisites

- **agentsview archive**: a `sessions.db` produced by the agentsview daemon.
  Resolved in this order: explicit `--db` flag, `$AGENTSVIEW_DATA_DIR` (legacy
  `$AGENT_VIEWER_DATA_DIR`), then `~/.agentsview/sessions.db`.
  If none exists, tell the user to install and run agentsview first.

```bash
uv run <skill_dir>/scripts/fetch_sessions.py status
```

- **Memory root**: `$AGENT_HOME` (default `$HOME`). Daily notes land in
  `$AGENT_HOME/memory/YYYY-MM-DD.md` and PARA facts in `$AGENT_HOME/life/`.
  This is the same root `para-memory-files` uses.

- Read `para-memory-files` before extracting facts so the PARA structure and
  the atomic-fact `items.yaml` schema are applied consistently.

## How it works

An incremental watermark at `$AGENT_HOME/memory/.sessions-memory.json` records
each processed session with a timestamp. `fetch` returns sessions absent from
the watermark, plus sessions whose `local_modified_at`/`ended_at` moved past
their processed timestamp (catches appended or re-synced sessions). `commit`
moves the just-presented sessions into the watermark only after the agent has
written memory, so a crash mid-run re-presents the same work idempotently.

By default the script excludes deleted sessions, automated runs
(`is_automated = 1`), and pure subagent sessions (`relationship_type =
'subagent'`). Override with `--include-automated` / `--include-subagents`.

## Steps

### 1. See what is pending

```bash
uv run <skill_dir>/scripts/fetch_sessions.py status
```

Reports total, processed, unprocessed, and last run. If unprocessed is 0,
there is nothing to do.

### 2. Fetch unprocessed sessions

```bash
uv run <skill_dir>/scripts/fetch_sessions.py fetch --limit 20
```

Emits JSON to stdout, grouped by day, each session carrying its metadata, full
message transcript (user and assistant text), and a deduplicated tool-call
summary (files touched, skills used). Message content is capped at 2000 chars
by default; raise with `--max-content 0` for unlimited, or add
`--include-thinking` when reasoning traces matter for fact extraction.

Narrow the window with `--since 2026-07-01`, `--until 2026-07-15`,
`--agent claude`, or `--project agentsview`. The script writes the presented
session ids to a pending file; do not edit it by hand.

### 3. Write daily timeline notes (Layer 2)

For each day in the fetch output, append a timeline section to
`$AGENT_HOME/memory/YYYY-MM-DD.md`. Two equivalent ways:

- Use the pre-formatted markdown from the script (ignores the watermark, so it
  works for any window, not just unprocessed sessions):

```bash
uv run <skill_dir>/scripts/fetch_sessions.py timeline --since 2026-07-15 --until 2026-07-15
```

- Or write the section yourself from the fetch JSON when you want a curated
  summary rather than the raw list.

Merge into the existing daily note rather than overwriting it. Keep entries
terse: project, agent, what was attempted, outcome, notable files.

### 4. Extract PARA entity facts (Layer 1)

This is the judgment step the script cannot do. For each fetched session, read
the transcript and extract durable facts worth remembering long term:

- **Decisions**: a choice was made and why (write to the relevant
  `projects/<name>/items.yaml`).
- **Project facts**: architecture, conventions, gotchas discovered
  (`resources/<topic>/items.yaml` or `projects/<name>/items.yaml`).
- **Learnings**: a mistake or lesson that should not be repeated
  (`resources/<topic>/items.yaml`).
- **Tooling discoveries**: a useful command, library, or workflow.

Follow the atomic-fact schema from `para-memory-files/references/schemas.md`:
`id`, `fact`, `category`, `timestamp`, `source`, `status`. Link related entities.
Never delete a fact; supersede it. Not every session yields a fact; when in
doubt, the daily note is enough.

For a deep dive on a single high-value session, pull its full detail:

```bash
uv run <skill_dir>/scripts/fetch_sessions.py show opencode:ses_abc123 --max-content 0
```

### 5. Commit the watermark

After the daily notes are written and facts are saved, advance the watermark so
those sessions are not re-presented:

```bash
uv run <skill_dir>/scripts/fetch_sessions.py commit
```

If you skip this step, the same sessions reappear on the next `fetch`, which is
safe (memory writes are append/supersede, not destructive) but wasteful.

## Command reference

| Command | Purpose |
|---------|---------|
| `status` | Total / processed / pending counts and last run. |
| `fetch` | Unprocessed sessions as JSON, grouped by day, with transcripts. |
| `timeline` | Markdown grouped by day, ready to paste into a daily note. |
| `show <id>` | Full detail of one session (all messages, thinking, tools). |
| `commit` | Move presented sessions into the processed watermark. |
| `reset` | Clear the watermark so every session re-processes. |

Common flags on `fetch`/`timeline`: `--since`, `--until`, `--agent`,
`--project`, `--limit`. Content flags on `fetch`/`show`: `--max-content`,
`--include-thinking`, `--include-system`, `--include-tool-input`.

## Output format

`fetch` emits one JSON object:

```json
{
  "generated_at": "2026-07-16T...",
  "db_path": "/home/user/.agentsview/sessions.db",
  "count": 2,
  "pending_ids": ["claude:abc", "opencode:def"],
  "days": [
    {
      "date": "2026-07-15",
      "sessions": [
        {
          "id": "claude:abc", "project": "agentsview", "agent": "claude",
          "started_at": "...", "ended_at": "...", "outcome": "completed",
          "cwd": "/home/user/src/agentsview", "git_branch": "main",
          "user_message_count": 8, "first_message": "fix the search bug",
          "messages": [{"role": "user", "content": "...", "truncated": false}],
          "tool_calls": [{"category": "Edit", "file_path": ".../search.go"}]
        }
      ]
    }
  ]
}
```

## Example usage

**Scenario 1: first run, catch up on the whole archive**

```bash
uv run <skill_dir>/scripts/fetch_sessions.py fetch --limit 50
```

Process 50 sessions at a time, writing daily notes and extracting facts, then
`commit` and repeat until `status` shows 0 unprocessed.

**Scenario 2: weekly review of recent work**

```bash
uv run <skill_dir>/scripts/fetch_sessions.py timeline --since 2026-07-08 --until 2026-07-15
```

Paste the markdown into the week's notes, then `fetch` over the same window to
extract facts for anything noteworthy.

**Scenario 3: remember one specific session**

```bash
uv run <skill_dir>/scripts/fetch_sessions.py show opencode:ses_3c4091d
```

Read the transcript and record the durable facts. `commit` is not needed for
ad-hoc `show` lookups since `show` does not touch the watermark.
