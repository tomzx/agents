#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Read AI agent sessions from the agentsview SQLite archive and expose them
for memory extraction.

agentsview syncs session transcripts from every supported coding agent
(Claude Code, Codex, OpenCode, Gemini, Copilot, etc.) into a single SQLite
archive. This script reads that archive read-only, tracks which sessions have
already been turned into memory, and emits structured JSON or ready-to-paste
timeline markdown grouped by day.

The script owns every deterministic decision (where the DB lives, how the
incremental watermark works, which sessions are noise) so the skill stays
focused on the judgment part: deciding what is worth remembering.

Subcommands:

  status              Show total / processed / pending / unprocessed counts.
  fetch               Emit unprocessed sessions as JSON, grouped by day, with
                      full message transcripts and tool-call summaries so the
                      agent can extract facts and write daily notes.
  timeline            Emit markdown grouped by day, ready to append to a daily
                      note. Ignores the watermark by default.
  show <session_id>   Full detail of a single session (all messages + tools).
  commit              Move pending session ids into the processed watermark.
  reset               Clear the watermark so every session re-processes.

Watermark:

  Processed state lives at <memory_root>/memory/.sessions-memory.json as a map
  of session_id -> processed_at ISO timestamp. A session is re-processed when it
  is absent from the map, or when its local_modified_at / ended_at moved past
  the recorded processed_at (catches appended or re-synced sessions).

Usage:

  uv run fetch_sessions.py status
  uv run fetch_sessions.py fetch --limit 10
  uv run fetch_sessions.py fetch --since 2026-07-01 --agent claude --max-content 1500
  uv run fetch_sessions.py timeline --since 2026-07-01 --until 2026-07-15
  uv run fetch_sessions.py show opencode:ses_abc123
  uv run fetch_sessions.py commit
  uv run fetch_sessions.py reset

Path resolution:

  DB:      $AGENTSVIEW_DATA_DIR/sessions.db (legacy $AGENT_VIEWER_DATA_DIR),
           default ~/.agentsview/sessions.db.
  Memory:  $AGENT_HOME, default $HOME. Watermark and notes live under here.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Columns selected for a session row. Kept in one place so every caller and
# the row->dict mapper stay in lockstep.
SESSION_COLUMNS = [
    "id",
    "project",
    "machine",
    "agent",
    "first_message",
    "session_name",
    "display_name",
    "started_at",
    "ended_at",
    "local_modified_at",
    "message_count",
    "user_message_count",
    "total_output_tokens",
    "has_total_output_tokens",
    "is_automated",
    "outcome",
    "outcome_confidence",
    "termination_status",
    "cwd",
    "git_branch",
    "parent_session_id",
    "relationship_type",
]


@dataclass
class FetchOptions:
    """Toggles controlling how much of each session is emitted."""

    max_content: int = 2000
    include_thinking: bool = False
    include_system: bool = False
    include_tool_input: bool = False
    include_automated: bool = False
    include_subagents: bool = False


@dataclass
class Filters:
    """Optional narrowing applied on top of the incremental watermark."""

    since: str | None = None
    until: str | None = None
    agent: str | None = None
    project: str | None = None
    limit: int | None = None


def resolve_db_path(override: str | None = None) -> Path:
    """Return the agentsview sessions.db path.

    Precedence: explicit override, $AGENTSVIEW_DATA_DIR, legacy
    $AGENT_VIEWER_DATA_DIR, then ~/.agentsview.
    """
    if override:
        return Path(override).expanduser()
    for env in ("AGENTSVIEW_DATA_DIR", "AGENT_VIEWER_DATA_DIR"):
        val = os.environ.get(env)
        if val:
            return Path(val) / "sessions.db"
    return Path.home() / ".agentsview" / "sessions.db"


def resolve_memory_root(override: str | None = None) -> Path:
    """Return the memory root ($AGENT_HOME, default $HOME)."""
    if override:
        return Path(override).expanduser()
    return Path(os.environ.get("AGENT_HOME") or Path.home())


def watermark_path(memory_root: Path) -> Path:
    return memory_root / "memory" / ".sessions-memory.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_watermark(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"processed": {}, "last_run": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"processed": {}, "last_run": None}
    data.setdefault("processed", {})
    data.setdefault("last_run", None)
    if not isinstance(data["processed"], dict):
        data["processed"] = {}
    return data


def save_watermark(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def open_db(db_path: Path) -> sqlite3.Connection:
    """Open the archive read-only with a reasonable busy timeout."""
    if not db_path.is_file():
        raise FileNotFoundError(f"agentsview database not found: {db_path}")
    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def session_mtime(row: sqlite3.Row) -> str | None:
    """Most recent known change time for incremental reprocessing checks."""
    for col in ("local_modified_at", "ended_at"):
        val = row[col]
        if val:
            return val
    return None


def _base_session_query(where: str = "") -> str:
    cols = ", ".join(SESSION_COLUMNS)
    clause = f"WHERE {where}" if where else ""
    return f"SELECT {cols} FROM sessions {clause} ORDER BY started_at ASC, id ASC"


def list_sessions(
    conn: sqlite3.Connection,
    filters: Filters | None = None,
    *,
    include_automated: bool = False,
    include_subagents: bool = False,
) -> list[sqlite3.Row]:
    """Return session rows matching filters, ordered oldest first."""
    filters = filters or Filters()
    clauses: list[str] = ["deleted_at IS NULL"]
    params: list[Any] = []
    if not include_automated:
        clauses.append("is_automated = 0")
    if not include_subagents:
        clauses.append("(relationship_type IS NULL OR relationship_type != 'subagent')")
    if filters.since:
        clauses.append("started_at >= ?")
        params.append(filters.since)
    if filters.until:
        clauses.append("started_at <= ?")
        params.append(filters.until)
    if filters.agent:
        clauses.append("agent = ?")
        params.append(filters.agent)
    if filters.project:
        clauses.append("project = ?")
        params.append(filters.project)
    query = _base_session_query(" AND ".join(clauses))
    if filters.limit is not None:
        query += f" LIMIT {int(filters.limit)}"
    return list(conn.execute(query, params))


def fetch_messages(conn: sqlite3.Connection, session_id: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT ordinal, role, content, thinking_text, timestamp, model, "
            "is_system, has_thinking, has_tool_use, content_length "
            "FROM messages WHERE session_id = ? ORDER BY ordinal",
            (session_id,),
        )
    )


def fetch_tool_calls(conn: sqlite3.Connection, session_id: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT category, tool_name, file_path, skill_name, call_index "
            "FROM tool_calls WHERE session_id = ? ORDER BY call_index, id",
            (session_id,),
        )
    )


def _truncate(text: str | None, limit: int) -> tuple[str, bool]:
    """Return (text, truncated_flag). None becomes empty string."""
    if not text:
        return "", False
    if limit > 0 and len(text) > limit:
        return text[:limit], True
    return text, False


def session_row_to_meta(row: sqlite3.Row) -> dict[str, Any]:
    """Map a session row to a metadata dict (no messages/tools)."""
    meta = {col: row[col] for col in SESSION_COLUMNS}
    # Normalize presence flags to booleans for cleaner downstream logic.
    for flag in ("has_total_output_tokens", "is_automated"):
        meta[flag] = bool(meta[flag])
    return meta


def messages_to_payload(
    rows: Iterable[sqlite3.Row], opts: FetchOptions
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rows:
        if r["is_system"] and not opts.include_system:
            continue
        content, truncated = _truncate(r["content"], opts.max_content)
        msg: dict[str, Any] = {
            "ordinal": r["ordinal"],
            "role": r["role"],
            "content": content,
            "truncated": truncated,
            "full_length": r["content_length"],
            "timestamp": r["timestamp"],
            "model": r["model"],
        }
        if opts.include_thinking and r["thinking_text"]:
            thinking, t_trunc = _truncate(r["thinking_text"], opts.max_content)
            msg["thinking"] = thinking
            msg["thinking_truncated"] = t_trunc
        out.append(msg)
    return out


def tools_to_payload(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for r in rows:
        key = (r["category"] or r["tool_name"] or "", r["file_path"] or "")
        # Deduplicate identical edit/write targets to keep summaries compact;
        # reads of the same file stay since order matters less here.
        if r["category"] in ("Edit", "Write") and key in seen:
            continue
        seen.add(key)
        entry: dict[str, Any] = {
            "category": r["category"],
            "tool": r["tool_name"],
            "file_path": r["file_path"],
        }
        if r["skill_name"]:
            entry["skill"] = r["skill_name"]
        out.append(entry)
    return out


def build_session_payload(
    conn: sqlite3.Connection, row: sqlite3.Row, opts: FetchOptions
) -> dict[str, Any]:
    payload = session_row_to_meta(row)
    payload["messages"] = messages_to_payload(fetch_messages(conn, row["id"]), opts)
    payload["tool_calls"] = tools_to_payload(fetch_tool_calls(conn, row["id"]))
    return payload


def date_key(iso_ts: str | None) -> str:
    """Return YYYY-MM-DD for an ISO timestamp, or 'unknown'."""
    if not iso_ts:
        return "unknown"
    # agentsview stores UTC ISO8601 like 2026-07-15T03:09:42.781Z.
    return iso_ts[:10]


def group_sessions_by_day(rows: Iterable[sqlite3.Row]) -> dict[str, list[sqlite3.Row]]:
    days: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        days[date_key(row["started_at"])].append(row)
    return dict(days)


def select_unprocessed(
    rows: list[sqlite3.Row], processed: dict[str, str]
) -> list[sqlite3.Row]:
    """Keep rows absent from the watermark or whose mtime moved past processed_at."""
    out: list[sqlite3.Row] = []
    for row in rows:
        sid = row["id"]
        seen_at = processed.get(sid)
        if seen_at is None:
            out.append(row)
            continue
        mtime = session_mtime(row)
        if mtime and mtime > seen_at:
            out.append(row)
    return out


# --------------------------------------------------------------------------- #
# Output formatters
# --------------------------------------------------------------------------- #


def build_fetch_output(
    conn: sqlite3.Connection,
    rows: list[sqlite3.Row],
    opts: FetchOptions,
    db_path: Path,
) -> dict[str, Any]:
    days = group_sessions_by_day(rows)
    day_payload: list[dict[str, Any]] = []
    for day in sorted(days):
        day_payload.append(
            {
                "date": day,
                "sessions": [build_session_payload(conn, r, opts) for r in days[day]],
            }
        )
    return {
        "generated_at": now_iso(),
        "db_path": str(db_path),
        "count": len(rows),
        "pending_ids": [r["id"] for r in rows],
        "days": day_payload,
    }


def format_timeline(
    conn: sqlite3.Connection, rows: list[sqlite3.Row], opts: FetchOptions
) -> str:
    """Render markdown grouped by day, ready to append to a daily note."""
    if not rows:
        return "<!-- no sessions matched -->\n"
    days = group_sessions_by_day(rows)
    lines: list[str] = []
    for day in sorted(days, reverse=True):
        day_rows = days[day]
        lines.append(f"### {day}")
        lines.append("")
        for row in day_rows:
            title = (
                row["session_name"]
                or row["display_name"]
                or row["first_message"]
                or row["id"]
            )
            title = title.strip().splitlines()[0][:120] if title else row["id"]
            agent = row["agent"]
            branch = f", {row['git_branch']}" if row["git_branch"] else ""
            outcome = row["outcome"] or "unknown"
            ended = _clock_time(row["ended_at"])
            turns = row["user_message_count"]
            tools = tools_to_payload(fetch_tool_calls(conn, row["id"]))
            touched = _summarize_touched(tools)
            lines.append(
                f"- **{row['project']}** ({agent}{branch}) - {title} - {outcome}"
            )
            details = [f"{turns} user turns", f"ended {ended}"]
            if touched:
                details.append(f"touched: {touched}")
            lines.append(f"  - {'; '.join(details)}")
        lines.append("")
    return "\n".join(lines)


def _clock_time(iso_ts: str | None) -> str:
    if not iso_ts or len(iso_ts) < 16:
        return "?"
    # HH:MM from a UTC ISO timestamp.
    return iso_ts[11:16] + "Z"


def _summarize_touched(tools: list[dict[str, Any]]) -> str:
    paths: list[str] = []
    for t in tools:
        fp = t.get("file_path")
        if fp:
            paths.append(os.path.basename(fp))
    # Preserve order, dedupe consecutive duplicates.
    uniq: list[str] = []
    for p in paths:
        if not uniq or uniq[-1] != p:
            uniq.append(p)
    return ", ".join(uniq[:8])


# --------------------------------------------------------------------------- #
# Subcommands
# --------------------------------------------------------------------------- #


def cmd_status(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.db)
    wm = load_watermark(watermark_path(resolve_memory_root(args.memory_root)))
    processed: dict[str, str] = wm.get("processed", {})
    try:
        conn = open_db(db_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    with conn:
        rows = list_sessions(
            conn,
            include_automated=args.include_automated,
            include_subagents=args.include_subagents,
        )
    total = len(rows)
    unproc = select_unprocessed(rows, processed)
    print(f"db:         {db_path}")
    print(f"watermark:  {watermark_path(resolve_memory_root(args.memory_root))}")
    print(f"total:      {total}")
    print(f"processed:  {len(processed)}")
    print(f"unprocessed:{len(unproc)}")
    print(f"last_run:   {wm.get('last_run') or 'never'}")
    if unproc:
        sample = ", ".join(r["id"][:20] for r in unproc[:5])
        print(f"next ids:   {sample}{' ...' if len(unproc) > 5 else ''}")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.db)
    wm = load_watermark(watermark_path(resolve_memory_root(args.memory_root)))
    opts = FetchOptions(
        max_content=args.max_content,
        include_thinking=args.include_thinking,
        include_system=args.include_system,
        include_tool_input=args.include_tool_input,
        include_automated=args.include_automated,
        include_subagents=args.include_subagents,
    )
    filters = Filters(
        since=args.since,
        until=args.until,
        agent=args.agent,
        project=args.project,
        limit=args.limit,
    )
    try:
        conn = open_db(db_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    with conn:
        rows = list_sessions(
            conn,
            filters,
            include_automated=opts.include_automated,
            include_subagents=opts.include_subagents,
        )
        unproc = select_unprocessed(rows, wm.get("processed", {}))
        output = build_fetch_output(conn, unproc, opts, db_path)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    # Record the presented ids as pending so commit can advance the watermark
    # only after the agent has actually written memory.
    pending_path = watermark_path(resolve_memory_root(args.memory_root)).with_name(
        ".sessions-memory-pending.json"
    )
    save_watermark(pending_path, {"pending": output["pending_ids"]})
    return 0


def cmd_timeline(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.db)
    opts = FetchOptions(
        max_content=args.max_content,
        include_automated=args.include_automated,
        include_subagents=args.include_subagents,
    )
    filters = Filters(
        since=args.since,
        until=args.until,
        agent=args.agent,
        project=args.project,
        limit=args.limit,
    )
    try:
        conn = open_db(db_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    with conn:
        rows = list_sessions(
            conn,
            filters,
            include_automated=opts.include_automated,
            include_subagents=opts.include_subagents,
        )
        md = format_timeline(conn, rows, opts)
    print(md)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.db)
    opts = FetchOptions(
        max_content=args.max_content,
        include_thinking=True,
        include_system=True,
        include_tool_input=True,
    )
    try:
        conn = open_db(db_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    with conn:
        row = conn.execute(_base_session_query("id = ?"), (args.session_id,)).fetchone()
        if row is None:
            print(f"error: session not found: {args.session_id}", file=sys.stderr)
            return 3
        payload = build_session_payload(conn, row, opts)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_commit(args: argparse.Namespace) -> int:
    root = resolve_memory_root(args.memory_root)
    wm_path = watermark_path(root)
    pending_path = wm_path.with_name(".sessions-memory-pending.json")
    wm = load_watermark(wm_path)
    processed: dict[str, str] = wm.get("processed", {})
    if not pending_path.is_file():
        print("nothing pending to commit", file=sys.stderr)
        return 1
    pending = load_watermark(pending_path).get("pending", [])
    if not pending:
        print("nothing pending to commit", file=sys.stderr)
        return 1
    stamp = now_iso()
    for sid in pending:
        processed[sid] = stamp
    wm["processed"] = processed
    wm["last_run"] = stamp
    save_watermark(wm_path, wm)
    pending_path.unlink(missing_ok=True)
    print(f"committed {len(pending)} session(s) to watermark")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    wm_path = watermark_path(resolve_memory_root(args.memory_root))
    save_watermark(wm_path, {"processed": {}, "last_run": None})
    wm_path.with_name(".sessions-memory-pending.json").unlink(missing_ok=True)
    print(f"cleared watermark at {wm_path}")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fetch_sessions.py",
        description="Read agentsview sessions into memory files.",
    )
    parser.add_argument(
        "--db", help="override agentsview sessions.db path", default=None
    )
    parser.add_argument(
        "--memory-root", help="override memory root ($AGENT_HOME)", default=None
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="show processing counts")
    p_status.add_argument("--include-automated", action="store_true")
    p_status.add_argument("--include-subagents", action="store_true")
    p_status.set_defaults(func=cmd_status)

    def add_session_filters(p: argparse.ArgumentParser) -> None:
        p.add_argument("--since", help="started_at >= (ISO date or datetime)")
        p.add_argument("--until", help="started_at <= (ISO date or datetime)")
        p.add_argument("--agent", help="filter by agent type (e.g. claude)")
        p.add_argument("--project", help="filter by project name")
        p.add_argument("--limit", type=int, help="cap number of sessions")

    def add_content_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--max-content",
            type=int,
            default=2000,
            help="max chars per message (0 = unlimited)",
        )
        p.add_argument("--include-thinking", action="store_true")
        p.add_argument("--include-system", action="store_true")
        p.add_argument("--include-tool-input", action="store_true")
        p.add_argument("--include-automated", action="store_true")
        p.add_argument("--include-subagents", action="store_true")

    p_fetch = sub.add_parser(
        "fetch", help="emit unprocessed sessions as JSON (grouped by day)"
    )
    add_session_filters(p_fetch)
    add_content_flags(p_fetch)
    p_fetch.set_defaults(func=cmd_fetch)

    p_tl = sub.add_parser(
        "timeline", help="emit markdown grouped by day for daily notes"
    )
    add_session_filters(p_tl)
    p_tl.add_argument("--max-content", type=int, default=2000)
    p_tl.add_argument("--include-automated", action="store_true")
    p_tl.add_argument("--include-subagents", action="store_true")
    p_tl.set_defaults(func=cmd_timeline)

    p_show = sub.add_parser("show", help="full detail of one session")
    p_show.add_argument("session_id")
    p_show.add_argument("--max-content", type=int, default=4000)
    p_show.set_defaults(func=cmd_show)

    p_commit = sub.add_parser("commit", help="mark pending sessions processed")
    p_commit.set_defaults(func=cmd_commit)

    p_reset = sub.add_parser("reset", help="clear the watermark")
    p_reset.set_defaults(func=cmd_reset)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
