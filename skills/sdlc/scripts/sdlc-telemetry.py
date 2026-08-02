#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "structlog",
# ]
# ///
"""Record SDLC pipeline events to a local SQLite database for self-analysis.

Each `record` invocation writes one event capturing when an SDLC step was
triggered, which step it was, which repository it ran in, and the associated
GitHub issue number when available. Events accumulate in a single
cross-repository database so you can later analyze frequency, timing, and
bottlenecks across all your SDLC work.

Storage location (first match wins):
  --db PATH argument
  $SDLC_TELEMETRY_DB environment variable
  $XDG_DATA_HOME/sdlc/telemetry.db   (default: ~/.local/share/sdlc/telemetry.db)

Repository resolution (first match wins):
  --repo owner/repo argument
  $REPO environment variable (set by the automation runner)
  `git remote get-url origin` parsed to owner/repo

Issue resolution (first match wins):
  --issue NUMBER argument
  $ISSUE_NUMBER environment variable (set by the automation runner)
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import structlog

SCHEMA = """
CREATE TABLE IF NOT EXISTS sdlc_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    step TEXT NOT NULL,
    repo TEXT,
    issue INTEGER,
    session_id TEXT,
    cwd TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON sdlc_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_step ON sdlc_events(step);
CREATE INDEX IF NOT EXISTS idx_events_repo ON sdlc_events(repo);
"""


def default_db_path() -> Path:
    override = os.environ.get("SDLC_TELEMETRY_DB")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "sdlc" / "telemetry.db"


def connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.executescript(SCHEMA)
    return conn


def parse_github_url(url: str) -> str:
    m = re.match(
        r"(?:git@github\.com:|https?://github\.com/)([^/]+)/([^/]+?)(?:\.git)?$",
        url.strip(),
    )
    return f"{m.group(1)}/{m.group(2)}" if m else ""


def resolve_repo(explicit: str | None) -> str:
    if explicit:
        return explicit
    repo = os.environ.get("REPO", "").strip()
    if repo:
        return repo
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return ""
    return parse_github_url(result.stdout)


def clean_issue(value: str) -> int | None:
    digits = re.sub(r"\D", "", value)
    return int(digits) if digits else None


def resolve_issue(explicit: str | None) -> int | None:
    if explicit:
        return clean_issue(explicit)
    env = os.environ.get("ISSUE_NUMBER", "").strip()
    return clean_issue(env) if env else None


def cmd_record(args: argparse.Namespace, log: structlog.stdlib.BoundLogger) -> int:
    step = args.step.strip()
    if not step:
        log.error("record_requires_step")
        return 2
    db = Path(args.db).expanduser() if args.db else default_db_path()
    repo = resolve_repo(args.repo)
    issue = resolve_issue(args.issue)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with connect(db) as conn:
            conn.execute(
                "INSERT INTO sdlc_events (timestamp, step, repo, issue, session_id, cwd) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    now,
                    step,
                    repo or None,
                    issue,
                    os.environ.get("SDLC_SESSION_ID") or None,
                    os.getcwd() or None,
                ),
            )
    except sqlite3.Error as exc:
        log.error("telemetry_write_failed", db=str(db), error=str(exc))
        return 1
    log.info(
        "telemetry_recorded", step=step, repo=repo or None, issue=issue, db=str(db)
    )
    return 0


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return str(value)


def _print_table(headers: list[str], rows: list[tuple]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    print("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def cmd_summary(args: argparse.Namespace, log: structlog.stdlib.BoundLogger) -> int:
    db = Path(args.db).expanduser() if args.db else default_db_path()
    if not db.exists():
        print(f"No telemetry database at {db}", file=sys.stderr)
        return 1
    where: list[str] = []
    params: list[object] = []
    if args.repo:
        where.append("repo = ?")
        params.append(args.repo)
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    with connect(db) as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS n FROM sdlc_events{clause}", params
        ).fetchone()["n"]
        print(f"# SDLC telemetry ({db})")
        print(f"Total events: {total}\n")

        print("## Events by step")
        rows = conn.execute(
            f"SELECT step, COUNT(*) AS n FROM sdlc_events{clause} "
            "GROUP BY step ORDER BY n DESC",
            params,
        ).fetchall()
        _print_table(["step", "count"], [(r["step"], r["n"]) for r in rows])

        print("\n## Events by repository")
        rows = conn.execute(
            f"SELECT COALESCE(repo, '(unknown)') AS repo, COUNT(*) AS n "
            f"FROM sdlc_events{clause} GROUP BY repo ORDER BY n DESC",
            params,
        ).fetchall()
        _print_table(["repo", "count"], [(r["repo"], r["n"]) for r in rows])

        print(
            "\n## Average time to first reach each step "
            "(hours from the issue's first event)"
        )
        rows = conn.execute(
            """
            WITH starts AS (
                SELECT issue, MIN(timestamp) AS first_ts
                FROM sdlc_events
                WHERE issue IS NOT NULL
                GROUP BY issue
            ),
            reached AS (
                SELECT e.step, e.issue, e.timestamp, s.first_ts
                FROM sdlc_events e
                JOIN starts s ON s.issue = e.issue
            ),
            first_reach AS (
                SELECT step, issue, MIN(timestamp) AS reached_at, first_ts
                FROM reached
                GROUP BY step, issue
            )
            SELECT step,
                   AVG((julianday(reached_at) - julianday(first_ts)) * 24) AS avg_hours,
                   COUNT(*) AS issues
            FROM first_reach
            GROUP BY step
            ORDER BY avg_hours DESC
            """
        ).fetchall()
        _print_table(
            ["step", "avg_hours_from_start", "issues"],
            [(r["step"], _fmt(r["avg_hours"]), r["issues"]) for r in rows],
        )
    log.info("summary_rendered", db=str(db), total=total)
    return 0


def cmd_recent(args: argparse.Namespace, log: structlog.stdlib.BoundLogger) -> int:
    db = Path(args.db).expanduser() if args.db else default_db_path()
    if not db.exists():
        print(f"No telemetry database at {db}", file=sys.stderr)
        return 1
    with connect(db) as conn:
        rows = conn.execute(
            "SELECT timestamp, step, repo, issue FROM sdlc_events "
            "ORDER BY id DESC LIMIT ?",
            (args.limit,),
        ).fetchall()
    _print_table(
        ["timestamp", "step", "repo", "issue"],
        [
            (r["timestamp"], r["step"], r["repo"] or "-", r["issue"] or "-")
            for r in rows
        ],
    )
    log.info("recent_rendered", db=str(db), count=len(rows))
    return 0


def main() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=logging.INFO, stream=sys.stderr)

    parser = argparse.ArgumentParser(
        description="Record and analyze SDLC pipeline events in a local SQLite database.",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-q", "--quiet", action="store_true", help="Suppress logging")
    common.add_argument(
        "--db", help="Path to telemetry database (overrides $SDLC_TELEMETRY_DB)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser(
        "record", parents=[common], help="Record one SDLC step event"
    )
    p_record.add_argument(
        "--step",
        required=True,
        help="The SDLC step/phase name (e.g. create-implementation)",
    )
    p_record.add_argument(
        "--repo", help="Repository as owner/repo (auto-detected from git if omitted)"
    )
    p_record.add_argument("--issue", help="Associated GitHub issue number")

    p_summary = sub.add_parser(
        "summary", parents=[common], help="Print counts and bottleneck analysis"
    )
    p_summary.add_argument("--repo", help="Filter to a repository (owner/repo)")

    p_recent = sub.add_parser(
        "recent", parents=[common], help="Show the most recent events"
    )
    p_recent.add_argument(
        "--limit", type=int, default=20, help="Number of events to show (default 20)"
    )

    args = parser.parse_args()
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    log = structlog.get_logger()
    handlers = {
        "record": cmd_record,
        "summary": cmd_summary,
        "recent": cmd_recent,
    }
    sys.exit(handlers[args.command](args, log))


if __name__ == "__main__":
    main()
