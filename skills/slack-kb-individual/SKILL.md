---
name: slack-kb-individual
description: >-
  Collect all Slack conversations a specific person participated in during a
  date range. Useful for performance reviews, 1:1 prep, or building a picture
  of someone's contributions. Outputs JSONL via the Slack API.
---

# Individual Slack activity collector

Use when collecting all Slack conversations a specific person participated in during a date range — useful for performance reviews, 1:1 prep, or building a picture of someone's contributions.

## What it does

[`collect_individual_threads.py`](collect_individual_threads.py) searches Slack for messages **from** a given user, deduplicates by thread, then fetches each thread root for reply count and preview. It outputs **JSONL** (one object per thread: `thread_ts`, `channel`, `channelName`, `replies`, `preview`, `permalink`).

Uses the Slack API directly (`search.messages` + `conversations.replies`) — no CLI dependencies. Thread fetching is concurrent (8 workers by default). Run via `uv run` for automatic dependency management (`requests`, `python-dotenv`).

Credentials: reads `SLACK_TOKEN` and `SLACK_COOKIE` from `.env` (searches up from cwd).

## Two modes

### Full scan

Searches the entire `--after`/`--before` date range newest-first and fetches every discovered thread. Pagination uses `sort=timestamp&sort_dir=desc` with sliding date windows to work around Slack's 100-page cap. Stops automatically at the retention boundary (older messages return empty).

```bash
uv run collect_individual_threads.py \
  --user tom.rochette --after 2024-10-06 --before 2026-04-08 \
  -o tom-threads.jsonl
```

### Incremental update

Loads the existing output JSONL as a cache, then searches only a recent window (default: last 7 days). Threads found in the window are fetched (or re-fetched if they were already cached — they had recent activity). Cached threads outside the window are kept as-is.

```bash
# Daily — searches last 7 days, merges with existing cache
uv run collect_individual_threads.py \
  --user tom.rochette --incremental -o tom-threads.jsonl

# Custom window — last 14 days
uv run collect_individual_threads.py \
  --user tom.rochette --incremental --recent-days 14 -o tom-threads.jsonl
```

## All options

| Flag | Description |
|------|-------------|
| `--user` (required) | Slack username (e.g. `tom.rochette`) |
| `--after` / `--before` | Full scan date range (`YYYY-MM-DD`). Slack's `after:` is exclusive. |
| `--incremental` | Incremental mode: search recent window, merge with cache. Requires `-o`. |
| `--recent-days N` | Days to search in incremental mode (default 7). |
| `--channel` | Restrict search to a specific channel name. |
| `--skip-threads` | List unique threads without fetching them (search only). |
| `--workers N` | Concurrent thread fetch workers (default 8). |
| `-o` / `--output` | Output path, or `-` for stdout. Default: `<user>-threads.jsonl`. |

## Output format

Each JSONL line:

```json
{
  "thread_ts": "1775582398.721149",
  "channel": "C0ABY4NCBD3",
  "channelName": "example-channel",
  "replies": 12,
  "preview": "First line of the thread root message...",
  "permalink": "https://example.slack.com/archives/C0ABY4NCBD3/p1775582398721149"
}
```

## Workflow

1. **First pull**: full scan with `--after`/`--before` covering the period you care about.
2. **Daily/periodic**: `--incremental` to pick up recent activity cheaply.
3. **Occasional refresh**: re-run full scan to catch threads where others replied but you didn't (not visible to incremental search).
4. Summarize findings into review notes or 1:1 prep docs.
