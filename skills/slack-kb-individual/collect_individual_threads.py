#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "requests",
# ]
# ///
"""
Collect all Slack threads a specific user participated in.

Uses the Slack API directly (search.messages + conversations.replies) with
timestamp-sorted pagination. No external CLI dependencies.

Two modes:

  Full scan (--after/--before):
    Paginates through all messages newest-first, deduplicates by thread,
    fetches each thread root for reply count and preview.

  Incremental (--incremental):
    Loads existing JSONL as cache, searches only the last N days
    (--recent-days, default 7). Threads with recent activity are re-fetched;
    cached threads outside the window are kept as-is.

Credentials: reads SLACK_TOKEN and SLACK_COOKIE from .env (python-dotenv).

Usage (run via uv run so PEP 723 script deps are applied):
  uv run collect_individual_threads.py \\
    --user tom.rochette --after 2024-10-06 --before 2026-04-08 \\
    -o tom-threads.jsonl

  uv run collect_individual_threads.py \\
    --user tom.rochette --incremental -o tom-threads.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests as http_lib
from dotenv import dotenv_values

SEARCH_PAGE_SIZE = 100
MAX_PAGES = 100  # Slack hard limit
THREAD_REPLY_LIMIT = 200
DEFAULT_RECENT_DAYS = 7
THREAD_FETCH_WORKERS = 8
MAX_RETRIES = 5


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

def load_credentials() -> tuple[str, str]:
    """Load SLACK_TOKEN and SLACK_COOKIE from .env, searching up from cwd."""
    for d in [Path.cwd()] + list(Path.cwd().parents):
        env_file = d / ".env"
        if env_file.is_file():
            vals = dotenv_values(env_file)
            token = vals.get("SLACK_TOKEN", "")
            cookie = vals.get("SLACK_COOKIE", "")
            if token and cookie:
                return token, cookie
    raise SystemExit(
        "Could not find SLACK_TOKEN and SLACK_COOKIE in any .env file. "
        "Create one with both values set."
    )


# ---------------------------------------------------------------------------
# Slack API helpers
# ---------------------------------------------------------------------------

def _slack_headers(token: str, cookie: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"d={cookie}",
    }


def _slack_request(
    method: str,
    url: str,
    token: str,
    cookie: str,
    **kwargs: Any,
) -> http_lib.Response:
    """Make a Slack API request with automatic retry on rate limiting."""
    headers = kwargs.pop("headers", {})
    headers["Cookie"] = f"d={cookie}"
    if "data" not in kwargs:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(MAX_RETRIES):
        r = http_lib.request(method, url, headers=headers, timeout=30, **kwargs)
        if r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", 5))
            print(
                f"  rate limited, waiting {retry_after}s (attempt {attempt + 1}/{MAX_RETRIES})",
                file=sys.stderr,
            )
            time.sleep(retry_after)
            continue
        r.raise_for_status()
        data = r.json()
        if data.get("error") == "ratelimited":
            retry_after = int(r.headers.get("Retry-After", 5))
            print(
                f"  rate limited, waiting {retry_after}s (attempt {attempt + 1}/{MAX_RETRIES})",
                file=sys.stderr,
            )
            time.sleep(retry_after)
            continue
        return r

    raise SystemExit(f"Rate limited {MAX_RETRIES} times in a row, giving up.")


def slack_search(
    token: str,
    cookie: str,
    query: str,
    sort: str = "timestamp",
    sort_dir: str = "desc",
    count: int = SEARCH_PAGE_SIZE,
    page: int = 1,
) -> dict[str, Any]:
    r = _slack_request(
        "POST",
        "https://slack.com/api/search.messages",
        token, cookie,
        data={
            "token": token,
            "query": query,
            "sort": sort,
            "sort_dir": sort_dir,
            "count": count,
            "page": page,
        },
    )
    data = r.json()
    if not data.get("ok"):
        raise SystemExit(f"Slack API error: {data.get('error', data)}")
    return data


def slack_conversations_replies_all(
    token: str,
    cookie: str,
    channel: str,
    ts: str,
    limit: int = THREAD_REPLY_LIMIT,
) -> list[dict[str, Any]]:
    """Fetch all thread replies, handling cursor pagination."""
    all_messages: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        params: dict[str, Any] = {"channel": channel, "ts": ts, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        r = _slack_request(
            "GET",
            "https://slack.com/api/conversations.replies",
            token, cookie,
            params=params,
        )
        data = r.json()
        if not data.get("ok"):
            error = data.get("error", "unknown")
            raise RuntimeError(f"conversations.replies failed: {error}")

        all_messages.extend(data.get("messages", []))

        if not data.get("has_more"):
            break
        meta = data.get("response_metadata", {})
        cursor = meta.get("next_cursor")
        if not cursor:
            break

    return all_messages


# ---------------------------------------------------------------------------
# Search pagination
# ---------------------------------------------------------------------------

def search_all_messages(
    token: str,
    cookie: str,
    user: str,
    after: date | None = None,
    before: date | None = None,
    channel: str | None = None,
) -> list[dict[str, Any]]:
    """
    Paginate through all search results newest-first (sort=timestamp, desc).

    Uses sliding date windows to work around Slack's 100-page cap. Stops
    when a page returns empty matches (retention boundary).
    """
    all_matches: list[dict[str, Any]] = []
    seen_ts: set[str] = set()
    t0 = time.monotonic()

    query_parts = [f"from:{user}"]
    if channel:
        query_parts.append(f"in:{channel}")

    current_before = before
    total_pages = 0

    while True:
        q = " ".join(query_parts)
        if after:
            q += f" after:{after.isoformat()}"
        if current_before:
            q += f" before:{current_before.isoformat()}"

        batch_start = len(all_matches)
        hit_retention_wall = False

        for page in range(1, MAX_PAGES + 1):
            data = slack_search(token, cookie, q, page=page)
            messages = data.get("messages", {})
            matches = messages.get("matches", [])
            total = messages.get("total", 0)
            total_pages += 1

            for m in matches:
                ts = m.get("ts", "")
                if ts and ts not in seen_ts:
                    seen_ts.add(ts)
                    all_matches.append(m)

            elapsed = time.monotonic() - t0
            print(
                f"  search: {len(all_matches)} messages found | "
                f"page {total_pages} | {elapsed:.0f}s elapsed | "
                f"API reports {total} total",
                file=sys.stderr,
            )

            if not matches:
                print(
                    f"  retention boundary reached (API reports {total} but page is empty)",
                    file=sys.stderr,
                )
                hit_retention_wall = True
                break

            if len(matches) < SEARCH_PAGE_SIZE:
                break

            time.sleep(0.3)

        if hit_retention_wall:
            break

        batch_count = len(all_matches) - batch_start

        if page < MAX_PAGES:
            break

        if batch_count == 0:
            break

        oldest_ts = min(
            (float(m["ts"]) for m in all_matches[batch_start:] if m.get("ts")),
            default=None,
        )
        if oldest_ts is None:
            break
        oldest_date = datetime.fromtimestamp(oldest_ts, tz=timezone.utc).date()
        if current_before and oldest_date >= current_before:
            oldest_date = current_before - timedelta(days=1)
        if after and oldest_date <= after:
            break
        current_before = oldest_date + timedelta(days=1)
        print(
            f"  hit page cap, shifting window: before={current_before} "
            f"({len(all_matches)} messages so far)",
            file=sys.stderr,
        )

    return all_matches


# ---------------------------------------------------------------------------
# Thread deduplication
# ---------------------------------------------------------------------------

def permalink_to_thread_ts(permalink: str) -> str | None:
    m = re.search(r"thread_ts=([0-9.]+)", permalink)
    return m.group(1) if m else None


@dataclass
class ThreadInfo:
    """Lightweight struct from search deduplication (before thread fetch)."""
    thread_ts: str
    channel_id: str
    channel_name: str
    permalink: str
    search_text: str


def dedupe_messages_to_threads(
    matches: list[dict[str, Any]],
) -> dict[tuple[str, str], ThreadInfo]:
    threads: dict[tuple[str, str], ThreadInfo] = {}
    for m in matches:
        ts = m.get("ts", "")
        permalink = m.get("permalink", "")
        thread_ts = permalink_to_thread_ts(permalink) or ts
        ch = m.get("channel", {})
        channel_id = ch.get("id", "") if isinstance(ch, dict) else str(ch)
        channel_name = ch.get("name", "") if isinstance(ch, dict) else ""
        key = (channel_id, thread_ts)
        if key not in threads:
            threads[key] = ThreadInfo(
                thread_ts=thread_ts,
                channel_id=channel_id,
                channel_name=channel_name,
                permalink=permalink,
                search_text=m.get("text", ""),
            )
    return threads


# ---------------------------------------------------------------------------
# Thread fetching (conversations.replies, concurrent)
# ---------------------------------------------------------------------------

@dataclass
class ThreadMessage:
    ts: str
    user: str
    text: str

    def to_json_obj(self) -> dict[str, Any]:
        return {"ts": self.ts, "user": self.user, "text": self.text}

    @staticmethod
    def from_json_obj(o: dict[str, Any]) -> ThreadMessage:
        return ThreadMessage(ts=o.get("ts", ""), user=o.get("user", ""), text=o.get("text", ""))


@dataclass
class ThreadRecord:
    thread_ts: str
    channel: str
    channel_name: str
    replies: int
    preview: str
    permalink: str
    messages: list[ThreadMessage] | None = None
    error: str | None = None

    def to_json_obj(self) -> dict[str, Any]:
        o: dict[str, Any] = {
            "thread_ts": self.thread_ts,
            "channel": self.channel,
            "channelName": self.channel_name,
            "replies": self.replies,
            "preview": self.preview,
            "permalink": self.permalink,
        }
        if self.messages is not None:
            o["messages"] = [m.to_json_obj() for m in self.messages]
        if self.error:
            o["error"] = self.error
        return o

    @staticmethod
    def from_json_obj(o: dict[str, Any]) -> ThreadRecord:
        msgs = o.get("messages")
        return ThreadRecord(
            thread_ts=o["thread_ts"],
            channel=o["channel"],
            channel_name=o.get("channelName", ""),
            replies=o.get("replies", -1),
            preview=o.get("preview", ""),
            permalink=o.get("permalink", ""),
            messages=[ThreadMessage.from_json_obj(m) for m in msgs] if msgs is not None else None,
            error=o.get("error"),
        )


def fetch_one_thread(
    token: str,
    cookie: str,
    info: ThreadInfo,
    thread_limit: int = THREAD_REPLY_LIMIT,
) -> ThreadRecord:
    """Fetch full thread via conversations.replies."""
    try:
        raw_msgs = slack_conversations_replies_all(
            token, cookie, info.channel_id, info.thread_ts, limit=thread_limit,
        )
    except Exception as exc:
        return ThreadRecord(
            thread_ts=info.thread_ts, channel=info.channel_id,
            channel_name=info.channel_name, replies=-1, preview="",
            permalink=info.permalink, error=str(exc),
        )
    if not raw_msgs:
        return ThreadRecord(
            thread_ts=info.thread_ts, channel=info.channel_id,
            channel_name=info.channel_name, replies=-1, preview="",
            permalink=info.permalink, error="thread_not_found",
        )
    root = raw_msgs[0]
    reply_count = root.get("reply_count", 0)
    text = root.get("text", "")
    preview = text.split("\n")[0].strip()
    if len(preview) > 400:
        preview = preview[:397] + "..."
    thread_messages = [
        ThreadMessage(ts=m.get("ts", ""), user=m.get("user", ""), text=m.get("text", ""))
        for m in raw_msgs
    ]
    return ThreadRecord(
        thread_ts=info.thread_ts, channel=info.channel_id,
        channel_name=info.channel_name, replies=reply_count,
        preview=preview, permalink=info.permalink,
        messages=thread_messages,
    )


def fetch_threads_concurrent(
    token: str,
    cookie: str,
    thread_infos: list[ThreadInfo],
    thread_limit: int = THREAD_REPLY_LIMIT,
    workers: int = THREAD_FETCH_WORKERS,
) -> list[ThreadRecord]:
    """Fetch full threads concurrently, printing progress."""
    total = len(thread_infos)
    results: dict[int, ThreadRecord] = {}
    completed = 0
    errors = 0
    t0 = time.monotonic()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(fetch_one_thread, token, cookie, info, thread_limit): idx
            for idx, info in enumerate(thread_infos)
        }
        for future in as_completed(futures):
            idx = futures[future]
            rec = future.result()
            results[idx] = rec
            completed += 1
            if rec.error:
                errors += 1
            elapsed = time.monotonic() - t0
            rate = completed / elapsed if elapsed > 0 else 0
            eta = (total - completed) / rate if rate > 0 else 0
            pct = completed * 100 // total
            print(
                f"  [{completed}/{total}] {pct}% | "
                f"{rate:.1f} threads/s | ETA {eta:.0f}s | "
                f"{errors} errors",
                file=sys.stderr,
            )

    return [results[i] for i in range(total)]


# ---------------------------------------------------------------------------
# Cache I/O
# ---------------------------------------------------------------------------

def load_cache(path: Path) -> dict[tuple[str, str], ThreadRecord]:
    cache: dict[tuple[str, str], ThreadRecord] = {}
    if not path.is_file():
        return cache
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        rec = ThreadRecord.from_json_obj(obj)
        cache[(rec.channel, rec.thread_ts)] = rec
    return cache


def write_output(records: list[ThreadRecord], out_path: Path | None) -> None:
    lines = [json.dumps(r.to_json_obj(), ensure_ascii=False) for r in records]
    text = "\n".join(lines) + ("\n" if lines else "")
    if out_path is None:
        sys.stdout.write(text)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text)
        print(f"Wrote {out_path} ({len(records)} threads)", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_date(s: str) -> date:
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s.strip())
    if not m:
        raise SystemExit(f"Invalid date {s!r}; expected YYYY-MM-DD")
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Collect Slack threads a user participated in. "
        "Uses Slack API directly with timestamp-sorted pagination."
    )
    ap.add_argument("--user", required=True, help="Slack username (e.g. tom.rochette).")
    ap.add_argument("-o", "--output", metavar="PATH",
                    help="Write JSONL here, or '-' for stdout. Default: <user>-threads.jsonl.")
    ap.add_argument("--thread-limit", type=int, default=THREAD_REPLY_LIMIT,
                    help=f"Max thread replies (default {THREAD_REPLY_LIMIT}).")
    ap.add_argument("--channel", help="Restrict to a specific channel name.")
    ap.add_argument("--workers", type=int, default=THREAD_FETCH_WORKERS,
                    help=f"Concurrent thread fetch workers (default {THREAD_FETCH_WORKERS}).")

    mode = ap.add_argument_group("mode")
    mode.add_argument("--after", help="Full scan: start date (YYYY-MM-DD).")
    mode.add_argument("--before", help="Full scan: end date (YYYY-MM-DD).")
    mode.add_argument("--incremental", action="store_true",
                      help="Incremental: search last --recent-days, merge with cache.")
    mode.add_argument("--recent-days", type=int, default=DEFAULT_RECENT_DAYS,
                      help=f"Days to search in incremental mode (default {DEFAULT_RECENT_DAYS}).")

    ap.add_argument("--skip-threads", action="store_true",
                    help="List unique threads without fetching them.")
    args = ap.parse_args()

    cwd = Path.cwd()
    out_path: Path | None
    if args.output == "-":
        out_path = None
    elif args.output:
        out_path = Path(args.output).expanduser()
        if not out_path.is_absolute():
            out_path = (cwd / out_path).resolve()
    else:
        out_path = cwd / f"{args.user}-threads.jsonl"

    token, cookie = load_credentials()

    if args.incremental:
        run_incremental(args, out_path, token, cookie)
    else:
        if not args.after or not args.before:
            raise SystemExit("Full scan mode requires both --after and --before.")
        run_full_scan(args, out_path, token, cookie)


def _threads_to_skip_records(threads: dict[tuple[str, str], ThreadInfo]) -> list[ThreadRecord]:
    return [
        ThreadRecord(
            thread_ts=info.thread_ts, channel=info.channel_id,
            channel_name=info.channel_name, replies=-1,
            preview=info.search_text.split("\n")[0].strip()[:400],
            permalink=info.permalink,
        )
        for info in threads.values()
    ]


def run_full_scan(args: argparse.Namespace, out_path: Path | None, token: str, cookie: str) -> None:
    after = parse_date(args.after)
    before = parse_date(args.before)
    if after >= before:
        raise SystemExit("--after must be before --before")

    print(f"Full scan: messages from {args.user} between {after} and {before}...", file=sys.stderr)
    matches = search_all_messages(token, cookie, args.user, after=after, before=before, channel=args.channel)
    print(f"Search complete: {len(matches)} messages", file=sys.stderr)

    threads = dedupe_messages_to_threads(matches)
    sorted_infos = sorted(threads.values(), key=lambda t: float(t.thread_ts))
    print(f"Unique threads: {len(sorted_infos)}", file=sys.stderr)

    if args.skip_threads:
        records = sorted(
            _threads_to_skip_records(threads),
            key=lambda r: float(r.thread_ts),
        )
        write_output(records, out_path)
        return

    print(f"Fetching {len(sorted_infos)} threads ({args.workers} workers)...", file=sys.stderr)
    records = fetch_threads_concurrent(token, cookie, sorted_infos, thread_limit=args.thread_limit, workers=args.workers)
    print(f"\nDone: {len(records)} threads fetched", file=sys.stderr)
    write_output(records, out_path)


def run_incremental(args: argparse.Namespace, out_path: Path | None, token: str, cookie: str) -> None:
    if out_path is None:
        raise SystemExit("Incremental mode requires an output file (not stdout). Use -o <path>.")

    cache = load_cache(out_path)
    if cache:
        print(f"Loaded {len(cache)} cached threads from {out_path}", file=sys.stderr)

    today = date.today()
    window_after = today - timedelta(days=args.recent_days)
    window_before = today + timedelta(days=1)

    print(
        f"Incremental: messages from {args.user} in last {args.recent_days} days "
        f"({window_after} to {window_before})...",
        file=sys.stderr,
    )
    matches = search_all_messages(
        token, cookie, args.user,
        after=window_after, before=window_before, channel=args.channel,
    )
    print(f"Search complete: {len(matches)} messages in window", file=sys.stderr)

    threads = dedupe_messages_to_threads(matches)
    print(f"Unique threads in window: {len(threads)}", file=sys.stderr)

    if args.skip_threads:
        merged: dict[tuple[str, str], ThreadRecord] = dict(cache)
        for key, info in threads.items():
            merged[key] = ThreadRecord(
                thread_ts=info.thread_ts, channel=info.channel_id,
                channel_name=info.channel_name, replies=-1,
                preview=info.search_text.split("\n")[0].strip()[:400],
                permalink=info.permalink,
            )
        records = sorted(merged.values(), key=lambda r: float(r.thread_ts))
        write_output(records, out_path)
        return

    to_fetch = sorted(threads.values(), key=lambda t: float(t.thread_ts))
    cached_keys = set(cache.keys())
    new_count = sum(1 for t in to_fetch if (t.channel_id, t.thread_ts) not in cached_keys)
    refreshed_count = len(to_fetch) - new_count

    print(
        f"Fetching {len(to_fetch)} threads ({new_count} new, {refreshed_count} refreshed, "
        f"{args.workers} workers)...",
        file=sys.stderr,
    )
    fetched = fetch_threads_concurrent(token, cookie, to_fetch, thread_limit=args.thread_limit, workers=args.workers)

    updated_cache = dict(cache)
    for rec in fetched:
        updated_cache[(rec.channel, rec.thread_ts)] = rec

    records = sorted(updated_cache.values(), key=lambda r: float(r.thread_ts))
    cached_kept = len(records) - len(to_fetch)
    print(
        f"\nDone: {len(records)} threads total — "
        f"{cached_kept} kept from cache, {refreshed_count} refreshed, {new_count} new",
        file=sys.stderr,
    )
    write_output(records, out_path)


if __name__ == "__main__":
    main()
