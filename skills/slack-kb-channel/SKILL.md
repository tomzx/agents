# Slack channel knowledge base

Use when building or updating a **Slack channel** knowledge base for a given month. Works for any channel you have access to; you need its **Slack channel id** (starts with `C` for public channels).

## Memory (canonical — ship this)

**Temporal memory** (time-sliced, one file per calendar month) lives under **`memory/temporal/`**. That directory name signals content keyed by **when** it was observed, not by long-lived theme.

| Path | Purpose |
|------|---------|
| `memory/temporal/<channel-slug>-YYYY-MM.md` | Channel themes, incidents, pointers, and **thread-derived findings** (thematic digest keyed by `thread_ts`; no exhaustive thread list in the file) |

Use a **stable short slug** for the channel in the filename (e.g. `help-ml-infrastructure`, `team-foo-oncall`), so the same channel always maps to the same prefix. You may include the channel id in prose or front matter if that helps disambiguation.

Do **not** add a separate `-threads.md` or other companion KB files for the same month.

**Rules for memory**

- **Dates in prose:** Prefer **`YYYY/MM/DD`** for a specific day and **`YYYY/MM`** for a month (e.g. incident windows, “seen in” notes). Avoid English month names or abbreviations (`Feb`, `March 2026`) in running text unless quoting Slack verbatim.
- Do **not** include a **thread index** (full table of every `thread_ts` + topic) in the monthly markdown. Use **thread-derived findings** only, with `thread_ts` inline where it helps.
- Do **not** link to, name, or point readers at **raw thread capture files** (e.g. per-thread markdown exports, “dump” directories, or filenames derived from timestamps). Those are ingestion artifacts, not the KB.
- Thread identity in memory is **`thread_ts`** (and **channel id** when the slug alone is ambiguous). People re-open discussions in Slack using those ids.
- When merging new facts from Slack, update the single monthly file under `memory/temporal/` only; do not add “see file X in folder Y” for raw captures.

**Theme-organized views** (merged across months, grouped by topic) are maintained separately — see the [`kb-organized-memory`](../slack-kb-organized-memory/SKILL.md) skill.

---

## Ingestion (maintainers only — not part of memory)

Use `devx agent-tools slack` (or Slack MCP) to pull history and threads. Raw outputs may be stored outside `memory/temporal/` or in tooling-only paths; **keep them out of the canonical temporal memory docs.**

### Batch thread metadata (recommended)

[`build_thread_kb.py`](build_thread_kb.py) walks **any channel** (by Slack channel id) for a **calendar month (UTC)**, lists root messages in that window, then fetches each thread via `devx agent-tools slack`. It writes **JSONL** (one object per thread: `channel`, `ts`, `replies`, `preview`) — a **maintainer artifact** for ingestion and validation; it is not the published KB and is not pasted into memory as a thread table.

Pass **`--channel <CHANNEL_ID>`** or set **`SLACK_CHANNEL_ID`**. Default output files include the channel id so different channels for the same month do not overwrite each other.

```bash
# Requires `devx agent-tools slack auth setup` for Slack auth
python3 skills/slack-kb-channel/build_thread_kb.py --channel <CHANNEL_ID> --month 2026-03 \
  --output memory/temporal/thread-fetch-2026-03-<CHANNEL_ID>.jsonl \
  --write-valid-list
```

- **`--skip-threads`**: only print / list root `thread_ts` values in the month (no per-thread API calls).
- **`--write-valid-list`**: also writes `memory/temporal/extracted-thread-ts-YYYY-MM-<CHANNEL_ID>-valid.txt` (excludes rows where the thread fetch failed).

### Single thread (manual)

```bash
devx agent-tools slack message thread <CHANNEL_ID> '<thread_ts>' \
  --limit=200 --output json
```

**Workflow**

1. Note the channel id and a **stable `<channel-slug>`** for filenames. Run **`build_thread_kb.py`** for `YYYY-MM` (or ingest via Slack MCP / export).
2. Treat reply permalinks as **non-parent** timestamps when scraping; the script uses channel roots only.
3. Optional: commit or ignore `memory/temporal/thread-fetch-*.jsonl` and `memory/temporal/extracted-thread-ts-*-valid.txt` per your hygiene.
4. Refresh **`memory/temporal/<channel-slug>-YYYY-MM.md`**: themes and **Thread-derived findings** (with `thread_ts` where useful). Do **not** add a full thread index table to the memory file.
5. When themes should span months, refresh the organized output per [`kb-organized-memory`](../slack-kb-organized-memory/SKILL.md).
