"""Green-path tests for fetch_sessions.py.

Run with:

    uv run --with pytest pytest tests/

The script reads the agentsview SQLite schema, so these tests build a minimal
matching schema in a temp DB and assert observable behavior: which sessions are
selected, how they are grouped and formatted, and that the incremental
watermark advances on commit. They do not introspect the script's internals
beyond the public functions exercised by the skill.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import fetch_sessions as fs  # noqa: E402


def _utc(hour: int) -> str:
    return f"2026-07-15T{hour:02d}:00:00.000Z"


def make_db(tmp_path: Path) -> sqlite3.Connection:
    """Create a minimal agentsview-shaped schema and return a connection."""
    conn = sqlite3.connect(tmp_path / "sessions.db")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            project TEXT NOT NULL,
            machine TEXT NOT NULL DEFAULT 'local',
            agent TEXT NOT NULL DEFAULT 'claude',
            first_message TEXT,
            session_name TEXT,
            display_name TEXT,
            started_at TEXT,
            ended_at TEXT,
            local_modified_at TEXT,
            message_count INTEGER NOT NULL DEFAULT 0,
            user_message_count INTEGER NOT NULL DEFAULT 0,
            total_output_tokens INTEGER NOT NULL DEFAULT 0,
            has_total_output_tokens INTEGER NOT NULL DEFAULT 0,
            is_automated INTEGER NOT NULL DEFAULT 0,
            outcome TEXT NOT NULL DEFAULT 'unknown',
            outcome_confidence TEXT NOT NULL DEFAULT 'low',
            termination_status TEXT,
            cwd TEXT NOT NULL DEFAULT '',
            git_branch TEXT NOT NULL DEFAULT '',
            parent_session_id TEXT,
            relationship_type TEXT NOT NULL DEFAULT '',
            deleted_at TEXT
        );
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            thinking_text TEXT NOT NULL DEFAULT '',
            timestamp TEXT,
            model TEXT NOT NULL DEFAULT '',
            is_system INTEGER NOT NULL DEFAULT 0,
            has_thinking INTEGER NOT NULL DEFAULT 0,
            has_tool_use INTEGER NOT NULL DEFAULT 0,
            content_length INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE tool_calls (
            id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL,
            category TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            file_path TEXT,
            skill_name TEXT,
            call_index INTEGER
        );
        """
    )
    conn.commit()
    return conn


def insert_session(
    conn: sqlite3.Connection,
    sid: str,
    *,
    project: str = "demo",
    agent: str = "claude",
    started_at: str = "2026-07-15T10:00:00.000Z",
    ended_at: str | None = "2026-07-15T11:00:00.000Z",
    local_modified_at: str | None = None,
    first_message: str = "do the thing",
    is_automated: int = 0,
    relationship_type: str = "",
    deleted_at: str | None = None,
    outcome: str = "completed",
    git_branch: str = "main",
    user_message_count: int = 3,
) -> None:
    conn.execute(
        """
        INSERT INTO sessions (id, project, agent, started_at, ended_at,
            local_modified_at, first_message, is_automated, relationship_type,
            deleted_at, outcome, git_branch, user_message_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sid,
            project,
            agent,
            started_at,
            ended_at,
            local_modified_at,
            first_message,
            is_automated,
            relationship_type,
            deleted_at,
            outcome,
            git_branch,
            user_message_count,
        ),
    )
    conn.commit()


def insert_message(
    conn: sqlite3.Connection,
    sid: str,
    ordinal: int,
    role: str,
    content: str,
    *,
    is_system: int = 0,
    thinking: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO messages (session_id, ordinal, role, content, is_system,
            thinking_text, content_length, timestamp, model)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'glm-5.2')
        """,
        (
            sid,
            ordinal,
            role,
            content,
            is_system,
            thinking,
            len(content),
            "2026-07-15T10:05:00.000Z",
        ),
    )
    conn.commit()


def insert_tool(
    conn: sqlite3.Connection,
    sid: str,
    category: str,
    *,
    file_path: str | None = None,
    tool_name: str = "t",
    skill: str | None = None,
    call_index: int = 0,
) -> None:
    conn.execute(
        """
        INSERT INTO tool_calls (session_id, category, tool_name, file_path,
            skill_name, call_index)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (sid, category, tool_name, file_path, skill, call_index),
    )
    conn.commit()


# --- watermark + selection --------------------------------------------------


def test_watermark_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "memory" / ".sessions-memory.json"
    data = {"processed": {"s1": "2026-01-01T00:00:00+00:00"}, "last_run": None}
    fs.save_watermark(path, data)
    loaded = fs.load_watermark(path)
    assert loaded["processed"]["s1"] == "2026-01-01T00:00:00+00:00"


def test_load_watermark_missing_file_returns_empty(tmp_path: Path) -> None:
    wm = fs.load_watermark(tmp_path / "absent.json")
    assert wm == {"processed": {}, "last_run": None}


def test_select_unprocessed_includes_new_and_updated(make_db_rows):
    conn, rows = make_db_rows
    processed = {"old": "2026-07-15T11:00:00.000Z"}
    # 'old' has ended_at == processed_at -> skipped; 'upd' moved past it.
    unproc = fs.select_unprocessed(rows, processed)
    ids = {r["id"] for r in unproc}
    assert ids == {"new", "upd"}


def test_select_unprocessed_all_processed(make_db_rows):
    conn, rows = make_db_rows
    stamp = "2026-12-31T00:00:00+00:00"
    processed = {r["id"]: stamp for r in rows}
    assert fs.select_unprocessed(rows, processed) == []


# --- list_sessions filters --------------------------------------------------


def test_list_sessions_excludes_deleted_automated_subagents(tmp_path: Path) -> None:
    conn = make_db(tmp_path)
    insert_session(conn, "alive", is_automated=0)
    insert_session(conn, "auto", is_automated=1)
    insert_session(conn, "sub", relationship_type="subagent")
    insert_session(conn, "gone", deleted_at="2026-07-15T00:00:00.000Z")
    rows = fs.list_sessions(conn)
    assert {r["id"] for r in rows} == {"alive"}


def test_list_sessions_filters_by_agent_and_date(tmp_path: Path) -> None:
    conn = make_db(tmp_path)
    insert_session(conn, "c1", agent="claude", started_at="2026-07-01T00:00:00.000Z")
    insert_session(conn, "c2", agent="claude", started_at="2026-08-01T00:00:00.000Z")
    insert_session(conn, "o1", agent="opencode", started_at="2026-07-15T00:00:00.000Z")
    rows = fs.list_sessions(
        conn, fs.Filters(since="2026-07-01", until="2026-07-31", agent="claude")
    )
    assert {r["id"] for r in rows} == {"c1"}


# --- payload building -------------------------------------------------------


def test_messages_payload_truncates_and_skips_system(tmp_path: Path) -> None:
    conn = make_db(tmp_path)
    insert_session(conn, "s1")
    insert_message(conn, "s1", 0, "user", "hello world")
    insert_message(conn, "s1", 1, "system", "system note", is_system=1)
    insert_message(conn, "s1", 2, "assistant", "x" * 500)
    payload = fs.messages_to_payload(
        fs.fetch_messages(conn, "s1"),
        fs.FetchOptions(max_content=10, include_system=False),
    )
    assert [m["role"] for m in payload] == ["user", "assistant"]
    assert payload[1]["truncated"] is True
    assert len(payload[1]["content"]) == 10


def test_tools_payload_dedupes_edit_targets(tmp_path: Path) -> None:
    conn = make_db(tmp_path)
    insert_session(conn, "s1")
    insert_tool(conn, "s1", "Edit", file_path="/a/foo.go", call_index=0)
    insert_tool(conn, "s1", "Edit", file_path="/a/foo.go", call_index=1)
    insert_tool(conn, "s1", "Read", file_path="/b/bar.go", call_index=2)
    insert_tool(conn, "s1", "Read", file_path="/b/bar.go", call_index=3)
    payload = fs.tools_to_payload(fs.fetch_tool_calls(conn, "s1"))
    edits = [t for t in payload if t["category"] == "Edit"]
    reads = [t for t in payload if t["category"] == "Read"]
    assert len(edits) == 1  # deduped
    assert len(reads) == 2  # reads keep duplicates


# --- fetch output + timeline formatting -------------------------------------


def test_fetch_output_groups_by_day(tmp_path: Path) -> None:
    conn = make_db(tmp_path)
    insert_session(conn, "s1", started_at="2026-07-15T10:00:00.000Z")
    insert_session(conn, "s2", started_at="2026-07-16T10:00:00.000Z")
    insert_message(conn, "s1", 0, "user", "hi")
    insert_tool(conn, "s1", "Edit", file_path="/x/y.go")
    out = fs.build_fetch_output(
        conn, fs.list_sessions(conn), fs.FetchOptions(max_content=100), tmp_path / "db"
    )
    assert out["count"] == 2
    assert [d["date"] for d in out["days"]] == ["2026-07-15", "2026-07-16"]
    day0 = out["days"][0]["sessions"][0]
    assert day0["id"] == "s1"
    assert day0["messages"][0]["content"] == "hi"
    assert day0["tool_calls"][0]["file_path"] == "/x/y.go"


def test_timeline_markdown_contains_project_and_outcome(tmp_path: Path) -> None:
    conn = make_db(tmp_path)
    insert_session(
        conn,
        "s1",
        project="agentsview",
        first_message="fix search",
        outcome="completed",
        started_at="2026-07-15T10:00:00.000Z",
    )
    insert_tool(conn, "s1", "Edit", file_path="/repo/search.go")
    md = fs.format_timeline(conn, fs.list_sessions(conn), fs.FetchOptions())
    assert "### 2026-07-15" in md
    assert "agentsview" in md
    assert "completed" in md
    assert "search.go" in md


# --- CLI end-to-end: fetch -> commit -> status ------------------------------


def test_cli_fetch_commit_status_cycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "sessions.db"
    mem_root = tmp_path / "memroot"

    monkeypatch.setattr(fs, "resolve_db_path", lambda override=None: db)
    monkeypatch.setattr(fs, "resolve_memory_root", lambda override=None: mem_root)

    # Seed a single session using the shared full-schema helper, then close it
    # so the CLI opens the same file read-only.
    conn = make_db(tmp_path)
    insert_session(conn, "cli-1", started_at="2026-07-15T10:00:00.000Z")
    conn.close()

    # fetch emits the unprocessed session and records pending ids
    assert fs.main(["fetch", "--max-content", "50"]) == 0
    pending = json.loads(
        (mem_root / "memory" / ".sessions-memory-pending.json").read_text()
    )
    assert pending["pending"] == ["cli-1"]

    # commit advances the watermark from pending into processed
    assert fs.main(["commit"]) == 0
    wm = json.loads((mem_root / "memory" / ".sessions-memory.json").read_text())
    assert "cli-1" in wm["processed"]
    # pending file is cleared after commit
    assert not (mem_root / "memory" / ".sessions-memory-pending.json").exists()


def test_resolve_db_path_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTSVIEW_DATA_DIR", "/custom/data")
    assert fs.resolve_db_path() == Path("/custom/data/sessions.db")
    assert fs.resolve_db_path("/explicit/x.db") == Path("/explicit/x.db")


# --- shared fixture ---------------------------------------------------------


@pytest.fixture
def make_db_rows(tmp_path: Path):
    conn = make_db(tmp_path)
    # 'old' ended before its processed stamp; 'upd' was modified after.
    insert_session(
        conn,
        "old",
        started_at=_utc(9),
        ended_at="2026-07-15T11:00:00.000Z",
    )
    insert_session(
        conn,
        "upd",
        started_at=_utc(10),
        ended_at="2026-07-15T11:00:00.000Z",
        local_modified_at="2026-08-01T00:00:00.000Z",
    )
    insert_session(conn, "new", started_at=_utc(12))
    rows = fs.list_sessions(conn)
    return conn, rows
