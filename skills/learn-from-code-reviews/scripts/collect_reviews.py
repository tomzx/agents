#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Deterministic collector for the learn-from-code-reviews skill.

Reads the review feedback received on pull requests you authored, filters out
noise and low-signal items, and emits one JSON document the skill then distills
into reusable review rules.

All reads come from the local ghx cache (SQLite at
``$GHX_CACHE_DIR/cache.db``, default ``~/.cache/ghx/cache/cache.db``) plus
``ghx pr threads`` for inline review comments, which the cache does not store.
Run ``ghx cache`` for a repository first so its PRs and conversation comments
are present; nothing here calls the GitHub API directly.

Usage:
    collect_reviews.py [owner/repo ... | store] [--mine]
        [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--limit N]
        [--state merged|closed|all] [--include-bots] [--include-low-signal]
        [--include-conversation] [--exclude-author LOGIN ...]
        [--state-file PATH] [--update-state] [--max-body N]

Examples:
    # Everything authored by you in the ghx cache, merged and closed
    collect_reviews.py --mine

    # One repository, everything since a date
    collect_reviews.py acme/api --since 2026-01-01

    # A single PR URL (resolved to owner/repo + number)
    collect_reviews.py https://github.com/acme/api/pull/42
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

DEFAULT_STATE_FILE = Path.home() / ".sdlc" / "review-rules" / "state.json"
DEFAULT_WINDOW_DAYS = 30

# Bots whose output is process noise rather than review feedback.
NOISE_BOTS = {
    "dependabot",
    "dependabot-preview",
    "renovate",
    "github-actions",
    "codecov",
    "sonarcloud",
    "mergify",
    "stale",
    "kodiak",
    "snyk-bot",
    "allcontributors",
    "imgbot",
}

# Feedback with no design or implementation content.
LOW_SIGNAL = re.compile(
    r"^\s*(lgtm|looks good( to me)?|nice|thanks?!?|thank you|\+1|"
    r"ship it|good (catch|job)|ditto|agreed|sgtm|ok(ay)?)[.!\s]*$",
    re.IGNORECASE,
)
LOW_SIGNAL_MIN_CHARS = 20

_TAG = re.compile(r"<[^>]+>")
_BLOCK = re.compile(
    r"</?(?:p|div|li|ul|ol|tr|h[1-6]|br|details|summary)[^>]*>", re.IGNORECASE
)


def cache_db_path() -> Path:
    if os.environ.get("GHX_CACHE_DIR"):
        return Path(os.environ["GHX_CACHE_DIR"]).expanduser() / "cache.db"
    return Path.home() / ".cache" / "ghx" / "cache" / "cache.db"


def open_db() -> sqlite3.Connection:
    path = cache_db_path()
    if not path.exists():
        sys.exit(
            f"ghx cache not found at {path}. Run `ghx cache` for the target "
            "repository first (and set GHX_CACHE_DIR if you store it elsewhere)."
        )
    # Read-only so a concurrent ghx run is never blocked or corrupted.
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def viewer(conn: sqlite3.Connection) -> str:
    rows = conn.execute(
        "SELECT author_login, count(*) c FROM pull_requests "
        "WHERE author_login != '' GROUP BY author_login ORDER BY c DESC LIMIT 1"
    ).fetchall()
    return rows[0]["author_login"] if rows else ""


BOT_SUFFIX = "[bot]"
# Logins ending in one of these are AI reviewers / automation, even when GitHub
# does not render them with the `[bot]` suffix.
BOT_NAME_PATTERNS = ("-bot", "_bot", "bot-")
# Known code-review and CI bots whose login carries none of the patterns above.
KNOWN_REVIEW_BOTS = {
    "greptile-apps",
    "greptile",
    "codiumai-pr-agent",
    "codiumai-pr-agent-free",
    "qodo-merge-pro",
    "coderabbitai",
    "copilot-pull-request-reviewer",
    "graphite-app",
    "ellipsis-dev",
    "sweep-ai",
    "cursor",
    "opencode-agent",
}


def is_bot(login: str, known_bots: set[str] | None = None) -> bool:
    if login.endswith(BOT_SUFFIX) or login in NOISE_BOTS:
        return True
    if login in KNOWN_REVIEW_BOTS:
        return True
    if known_bots and login in known_bots:
        return True
    lowered = login.lower()
    return any(pat in lowered for pat in BOT_NAME_PATTERNS)


def is_noise(login: str) -> bool:
    return login in NOISE_BOTS


def strip_html(body: str) -> str:
    """Turn review-bot HTML into readable text."""
    if "<" not in (body or ""):
        return body or ""
    text = _BLOCK.sub("\n", body)
    text = _TAG.sub("", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_low_signal(body: str) -> bool:
    stripped = strip_html(body).strip()
    if len(stripped) < LOW_SIGNAL_MIN_CHARS:
        return True
    return bool(LOW_SIGNAL.match(stripped))


def iso(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_since(value: str | None, state: dict) -> dt.datetime:
    if value:
        return dt.datetime.fromisoformat(value).replace(tzinfo=dt.timezone.utc)
    last_run = state.get("last_run")
    if last_run:
        parsed = dt.datetime.fromisoformat(last_run).replace(tzinfo=dt.timezone.utc)
        return parsed - dt.timedelta(days=1)
    return dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DEFAULT_WINDOW_DAYS)


def parse_target(target: str) -> tuple[str | None, int | None]:
    """Return (owner/repo or None, pr_number or None) for a repo or PR URL."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", target)
    if m:
        return f"{m.group(1)}/{m.group(2)}", int(m.group(3))
    if re.match(r"^[^/\s]+/[^/\s]+$", target) or re.match(r"^[^/\s]+$", target):
        return target, None
    return None, None


def select_prs(
    conn: sqlite3.Connection,
    repo: str | None,
    number: int | None,
    author: str | None,
    state: str,
    since: dt.datetime,
    until: dt.datetime | None,
    limit: int,
) -> list[sqlite3.Row]:
    where = ["1=1"]
    params: list[object] = []
    if repo:
        owner, _, name = repo.partition("/")
        where.append("owner = ? AND repo = ?")
        params += [owner, name]
    if number is not None:
        where.append("number = ?")
        params.append(number)
    if author:
        where.append("author_login = ?")
        params.append(author)
    if state == "merged":
        where.append("state = 'MERGED'")
    elif state == "closed":
        where.append("state = 'CLOSED'")
    where.append("updated_at >= ?")
    params.append(since.date().isoformat())
    if until:
        where.append("updated_at <= ?")
        params.append(until.date().isoformat() + "T23:59:59")
    sql = (
        "SELECT host,owner,repo,number,title,state,author_login,updated_at,"
        "merged_at,closed_at,url,comment_count,comments FROM pull_requests "
        f"WHERE {' AND '.join(where)} ORDER BY updated_at DESC LIMIT ?"
    )
    params.append(limit)
    return conn.execute(sql, params).fetchall()


def inline_threads(repo: str, number: int) -> list[dict]:
    """Inline review threads (path:line + comment bodies) via `ghx pr threads`.

    Output format: a column-0 header ``<path>:<start>[-<end>]  [<state>]``
    followed by an indented block whose first line is ``<author>  <body>`` and
    whose continuation lines are indented to the same column.
    """
    proc = subprocess.run(
        ["ghx", "pr", "threads", str(number), "-R", repo, "--state", "all"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    threads: list[dict] = []
    current: dict | None = None
    indent = 0
    for raw in proc.stdout.splitlines():
        header = re.match(r"^(\S.*?):(\d+)(?:-\d+)?\s+\[(\w+)\]\s*$", raw)
        if header:
            current = {
                "path": header.group(1),
                "line": int(header.group(2)),
                "state": header.group(3),
                "author": None,
                "body": [],
            }
            threads.append(current)
            continue
        if current is None:
            continue
        # Body lines share one indentation level; the first carries the author.
        m = re.match(r"^(\s+)(.*)$", raw)
        if m:
            indent = indent or len(m.group(1))
            text = m.group(2).strip()
        else:
            text = raw.strip()
        if current["author"] is None and text:
            who, _, rest = text.partition("  ")
            current["author"] = who.strip()
            current["body"].append(rest.strip())
        else:
            current["body"].append(text)
    for thread in threads:
        thread["body"] = strip_html("\n".join(thread["body"]).strip())
    return threads


def cached_bots(conn: sqlite3.Connection) -> set[str]:
    """Logins seen as ``<name>[bot]`` in cached comments, without the suffix.

    `ghx pr threads` drops the suffix, so this lets the collector re-attach it.
    """
    bots: set[str] = set()
    for (comments,) in conn.execute(
        "SELECT comments FROM pull_requests WHERE comments LIKE '%[bot]%'"
    ):
        if not comments:
            continue
        try:
            data = json.loads(comments)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, list):
            continue
        for comment in data:
            login = (comment.get("author") or {}).get("login") or ""
            if login.endswith("[bot]"):
                bots.add(login[: -len("[bot]")])
    return bots


def conversation_comments(row: sqlite3.Row) -> list[dict]:
    if not row["comments"]:
        return []
    try:
        data = json.loads(row["comments"])
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return data


def collect(args: argparse.Namespace) -> dict:
    conn = open_db()
    who = viewer(conn)
    state = (
        json.loads(Path(args.state_file).expanduser().read_text())
        if Path(args.state_file).expanduser().exists()
        else {}
    )
    since = parse_since(args.since, state)
    until = (
        dt.datetime.fromisoformat(args.until).replace(tzinfo=dt.timezone.utc)
        if args.until
        else None
    )

    targets = args.targets or [None]
    default_author = None if args.include_all_authors else who

    known_bots = cached_bots(conn) | {b.strip() for b in args.bot_author if b.strip()}

    prs: list[sqlite3.Row] = []
    seen: set[tuple[str, str, int]] = set()
    for raw in targets:
        repo, number = parse_target(raw) if raw else (None, None)
        if raw and repo is None:
            print(f"warning: ignoring unparseable target {raw!r}", file=sys.stderr)
            continue
        # An explicit PR URL is collected regardless of who authored it; repo and
        # "mine" scopes stay restricted to your own PRs.
        target_author = None if number is not None else default_author
        for row in select_prs(
            conn, repo, number, target_author, args.state, since, until, args.limit
        ):
            key = (row["owner"], row["repo"], row["number"])
            if key in seen:
                continue
            seen.add(key)
            prs.append(row)

    feedback: list[dict] = []
    prs_meta: list[dict] = []

    def keep(author_login: str, body: str) -> bool:
        if author_login == who:
            return False
        if author_login in args.exclude_author:
            return False
        if is_noise(author_login):
            return False
        if is_bot(author_login, known_bots) and not args.include_bots:
            return False
        if not args.include_low_signal and is_low_signal(body):
            return False
        return bool(strip_html(body).strip())

    def truncate(body: str) -> str:
        body = strip_html(body)
        if args.max_body and len(body) > args.max_body:
            return body[: args.max_body] + "\n[... truncated]"
        return body

    for row in prs:
        repo = f"{row['owner']}/{row['repo']}"
        number = row["number"]
        prs_meta.append(
            {
                "repo": repo,
                "number": number,
                "title": row["title"],
                "url": row["url"],
                "merged_at": row["merged_at"],
                "closed_at": row["closed_at"],
                "updated_at": row["updated_at"],
            }
        )
        for comment in conversation_comments(row):
            login = (comment.get("author") or {}).get("login", "") or ""
            body = comment.get("body") or ""
            if not keep(login, body):
                continue
            feedback.append(
                {
                    "repo": repo,
                    "pr": number,
                    "pr_title": row["title"],
                    "pr_url": row["url"],
                    "kind": "conversation",
                    "id": f"conversation-{comment.get('id', '')}",
                    "author": login,
                    "is_bot": is_bot(login, known_bots),
                    "state": None,
                    "path": None,
                    "line": None,
                    "body": truncate(body),
                    "created_at": comment.get("createdAt"),
                    "url": comment.get("url"),
                }
            )
        if not args.include_conversation:
            for thread in inline_threads(repo, number):
                login = thread["author"] or ""
                # `ghx pr threads` prints bot logins without the "[bot]" suffix,
                # so re-attach it when the login is a known bot.
                if login and not login.endswith("[bot]") and login in known_bots:
                    login = f"{login}[bot]"
                if not keep(login, thread["body"]):
                    continue
                feedback.append(
                    {
                        "repo": repo,
                        "pr": number,
                        "pr_title": row["title"],
                        "pr_url": row["url"],
                        "kind": "review_comment",
                        "id": f"comment-{login}-{thread['path']}-{thread['line']}",
                        "author": login,
                        "is_bot": is_bot(login, known_bots),
                        "state": thread["state"],
                        "path": thread["path"],
                        "line": thread["line"],
                        "body": truncate(thread["body"]),
                        "created_at": row["updated_at"],
                        "url": f"{row['url']}#discussion",
                    }
                )

    now = dt.datetime.now(dt.timezone.utc)
    return {
        "generated_at": now.isoformat(),
        "viewer": who,
        "since": since.isoformat(),
        "until": until.isoformat() if until else None,
        "cache_db": str(cache_db_path()),
        "filters": {
            "include_bots": args.include_bots,
            "include_low_signal": args.include_low_signal,
            "include_conversation": args.include_conversation,
            "include_all_authors": args.include_all_authors,
            "exclude_authors": args.exclude_author,
        },
        "pull_requests": prs_meta,
        "feedback": feedback,
        "stats": {
            "pull_requests": len(prs_meta),
            "feedback_items": len(feedback),
            "by_kind": _count_by(feedback, "kind"),
            "by_repo": _count_by(feedback, "repo"),
            "by_author": _count_by(feedback, "author"),
        },
    }


def _count_by(items: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = item.get(key)
        if value is None:
            continue
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def update_state(args: argparse.Namespace, result: dict) -> None:
    path = Path(args.state_file).expanduser()
    state = json.loads(path.read_text()) if path.exists() else {}
    state["viewer"] = result["viewer"]
    state["last_run"] = result["generated_at"]
    repos = state.setdefault("repos", {})
    for item in result["feedback"]:
        cursor = repos.setdefault(item["repo"], {})
        newest = cursor.get("last_created_at")
        created = item.get("created_at")
        if created and (newest is None or created > newest):
            cursor["last_created_at"] = created
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", help="owner/repo (or OWNER) or PR URLs")
    parser.add_argument(
        "--mine", action="store_true", help="your PRs across all cached repos"
    )
    parser.add_argument("--since", help="only PRs updated on or after this date")
    parser.add_argument("--until", help="only PRs updated on or before this date")
    parser.add_argument("--limit", type=int, default=200, help="max PRs")
    parser.add_argument(
        "--state",
        choices=["merged", "closed", "all"],
        default="all",
        help="PR state to include (default: all closed)",
    )
    parser.add_argument("--include-bots", action="store_true")
    parser.add_argument("--include-low-signal", action="store_true")
    parser.add_argument(
        "--include-conversation",
        action="store_true",
        help="include top-level PR conversation comments (default: inline review only)",
    )
    parser.add_argument(
        "--include-all-authors",
        action="store_true",
        help="do not restrict to PRs you authored",
    )
    parser.add_argument(
        "--bot-author",
        action="append",
        default=[],
        help="login to treat as a bot (repeatable); needed because "
        "`ghx pr threads` strips the [bot] suffix",
    )
    parser.add_argument("--exclude-author", action="append", default=[])
    parser.add_argument(
        "--max-body", type=int, default=4000, help="0 keeps full bodies"
    )
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE))
    parser.add_argument("--update-state", action="store_true")
    args = parser.parse_args()

    result = collect(args)
    if args.update_state:
        update_state(args, result)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
