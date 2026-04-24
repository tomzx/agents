#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "requests",
# ]
# ///
"""
Batch-fetch Slack thread metadata for KB ingestion for any channel.

Uses the Slack API directly (conversations.history + conversations.replies)
without any CLI dependencies. Credentials are read from .env.

1. Pulls channel history for the given time range via conversations.history.
2. For each root message, fetches thread replies via conversations.replies.
3. Outputs JSONL (one object per thread: channel, ts, replies, preview).

Usage:
  uv run build_thread_kb.py --channel C01234567 --month 2026-02 \\
    --output memory/temporal/thread-fetch-2026-02-C01234567.jsonl --write-valid-list

  uv run build_thread_kb.py --channel C01234567 --after 2026-04-07 --before 2026-04-14 \\
    --output /tmp/channel-week.jsonl

  export SLACK_CHANNEL_ID=C01234567
  uv run build_thread_kb.py --month 2026-03 -o -   # stdout
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import requests as http_lib
from dotenv import dotenv_values

CHANNEL_FETCH_LIMIT = 1000
THREAD_REPLY_LIMIT = 200
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


def conversations_history_all(
    token: str,
    cookie: str,
    channel: str,
    oldest_ts: float,
    latest_ts: float,
    limit: int = CHANNEL_FETCH_LIMIT,
) -> list[dict[str, Any]]:
    """Fetch all messages in a channel time window, handling cursor pagination."""
    all_messages: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        params: dict[str, Any] = {
            "channel": channel,
            "oldest": f"{oldest_ts:.6f}",
            "latest": f"{latest_ts:.6f}",
            "limit": limit,
            "inclusive": "true",
        }
        if cursor:
            params["cursor"] = cursor

        r = _slack_request(
            "GET",
            "https://slack.com/api/conversations.history",
            token, cookie,
            params=params,
        )
        data = r.json()
        if not data.get("ok"):
            error = data.get("error", "unknown")
            raise SystemExit(f"conversations.history failed: {error}")

        all_messages.extend(data.get("messages", []))

        if not data.get("has_more"):
            break
        meta = data.get("response_metadata", {})
        cursor = meta.get("next_cursor")
        if not cursor:
            break

        print(
            f"  channel history: {len(all_messages)} messages so far, fetching more...",
            file=sys.stderr,
        )
        time.sleep(0.2)

    return all_messages


def conversations_replies_all(
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


def extract_preview(messages: list[dict[str, Any]]) -> tuple[int, str]:
    """Extract reply count and first-message preview from thread."""
    if not messages:
        return -1, ""
    first = messages[0]
    reply_count = first.get("reply_count", len(messages) - 1)
    if reply_count is None:
        reply_count = len(messages) - 1
    preview = (first.get("text") or "").split("\n")[0].strip()
    if len(preview) > 400:
        preview = preview[:397] + "..."
    return reply_count, preview


@dataclass
class ThreadRecord:
    channel: str
    ts: str
    replies: int
    preview: str
    error: str | None = None

    def to_json_obj(self) -> dict[str, Any]:
        o: dict[str, Any] = {
            "channel": self.channel,
            "ts": self.ts,
            "replies": self.replies,
            "preview": self.preview,
        }
        if self.error:
            o["error"] = self.error
        return o


# ---------------------------------------------------------------------------
# Arg helpers
# ---------------------------------------------------------------------------

def parse_month(s: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d{4})-(\d{2})", s.strip())
    if not m:
        raise SystemExit(f"Invalid --month {s!r}; expected YYYY-MM")
    y, mo = int(m.group(1)), int(m.group(2))
    if not 1 <= mo <= 12:
        raise SystemExit(f"Invalid month in {s!r}")
    return y, mo


def parse_date(s: str) -> date:
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s.strip())
    if not m:
        raise SystemExit(f"Invalid date {s!r}; expected YYYY-MM-DD")
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def month_bounds_utc(year: int, month: int) -> tuple[float, float]:
    """Return (start_inclusive, end_exclusive) as Slack timestamps."""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start.timestamp(), end.timestamp()


def date_bounds_utc(after: date, before: date) -> tuple[float, float]:
    """Convert --after/--before dates to UTC midnight timestamps (both inclusive ends)."""
    start = datetime(after.year, after.month, after.day, tzinfo=timezone.utc)
    end = datetime(before.year, before.month, before.day, tzinfo=timezone.utc)
    return start.timestamp(), end.timestamp()


def resolve_channel(arg_channel: str | None) -> str:
    ch = (arg_channel or os.environ.get("SLACK_CHANNEL_ID") or "").strip()
    if not ch:
        raise SystemExit(
            "Set --channel <CHANNEL_ID> or export SLACK_CHANNEL_ID (e.g. C01234567)."
        )
    return ch


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Batch-fetch Slack thread metadata for a channel (KB ingestion)."
    )
    ap.add_argument(
        "--channel",
        metavar="CHANNEL_ID",
        default=None,
        help="Slack channel id (e.g. C01234567). Falls back to SLACK_CHANNEL_ID env var.",
    )
    ap.add_argument(
        "-o", "--output",
        metavar="PATH",
        help=(
            "Write JSONL here, or '-' for stdout "
            "(default: memory/temporal/thread-fetch-<date>-<CHANNEL_ID>.jsonl)."
        ),
    )
    ap.add_argument(
        "--write-valid-list",
        action="store_true",
        help="Also write memory/temporal/extracted-thread-ts-<date>-<CHANNEL_ID>-valid.txt.",
    )
    ap.add_argument(
        "--channel-limit",
        type=int,
        default=CHANNEL_FETCH_LIMIT,
        help=f"Max messages per history page (default {CHANNEL_FETCH_LIMIT}).",
    )
    ap.add_argument(
        "--thread-limit",
        type=int,
        default=THREAD_REPLY_LIMIT,
        help=f"Max thread replies (default {THREAD_REPLY_LIMIT}).",
    )
    ap.add_argument(
        "--skip-threads",
        action="store_true",
        help="Only list thread roots from channel history (no per-thread fetch).",
    )

    range_group = ap.add_mutually_exclusive_group(required=True)
    range_group.add_argument(
        "--month",
        metavar="YYYY-MM",
        help="Calendar month (UTC): fetch from month start to next month start.",
    )
    range_group.add_argument(
        "--after",
        metavar="YYYY-MM-DD",
        help="Start date (inclusive, UTC midnight). Requires --before.",
    )

    ap.add_argument(
        "--before",
        metavar="YYYY-MM-DD",
        help="End date (exclusive, UTC midnight). Required when --after is used.",
    )

    args = ap.parse_args()

    if args.after and not args.before:
        ap.error("--before is required when --after is used.")

    channel = resolve_channel(args.channel)

    if args.month:
        year, month = parse_month(args.month)
        start_ts, end_ts = month_bounds_utc(year, month)
        date_label = args.month
    else:
        after_date = parse_date(args.after)
        before_date = parse_date(args.before)
        if after_date >= before_date:
            ap.error("--after must be before --before.")
        start_ts, end_ts = date_bounds_utc(after_date, before_date)
        date_label = f"{args.after}_{args.before}"

    cwd = Path.cwd()
    out_path: Path | None
    if args.output == "-":
        out_path = None
    elif args.output:
        out_path = Path(args.output).expanduser()
        if not out_path.is_absolute():
            out_path = (cwd / out_path).resolve()
    else:
        out_path = cwd / "memory" / "temporal" / f"thread-fetch-{date_label}-{channel}.jsonl"

    token, cookie = load_credentials()

    print(f"Fetching channel {channel} history ({date_label})...", file=sys.stderr)
    messages = conversations_history_all(token, cookie, channel, start_ts, end_ts, args.channel_limit)
    print(f"Got {len(messages)} messages from channel history.", file=sys.stderr)

    messages.sort(key=lambda m: float(m["ts"]))
    ids = [m["ts"] for m in messages]

    if args.skip_threads:
        for ts in ids:
            print(ts)
        if args.write_valid_list:
            valid_path = (
                cwd / "memory" / "temporal"
                / f"extracted-thread-ts-{date_label}-{channel}-valid.txt"
            )
            valid_path.parent.mkdir(parents=True, exist_ok=True)
            valid_path.write_text("\n".join(ids) + "\n")
            print(f"Wrote {valid_path}", file=sys.stderr)
        return

    records: list[ThreadRecord] = []
    for i, ts in enumerate(ids):
        try:
            thread_msgs = conversations_replies_all(token, cookie, channel, ts, args.thread_limit)
        except Exception as exc:
            records.append(ThreadRecord(channel=channel, ts=ts, replies=-1, preview="", error=str(exc)))
            print(f"[{i + 1}/{len(ids)}] {ts} ERR {exc}", file=sys.stderr)
            continue
        if not thread_msgs:
            records.append(
                ThreadRecord(channel=channel, ts=ts, replies=-1, preview="", error="thread_not_found")
            )
            print(f"[{i + 1}/{len(ids)}] {ts} ERR thread_not_found", file=sys.stderr)
            continue
        reply_count, preview = extract_preview(thread_msgs)
        records.append(ThreadRecord(channel=channel, ts=ts, replies=reply_count, preview=preview))
        print(f"[{i + 1}/{len(ids)}] {ts} replies={reply_count}", file=sys.stderr)

    lines = [json.dumps(r.to_json_obj(), ensure_ascii=False) for r in records]
    text = "\n".join(lines) + ("\n" if lines else "")

    if out_path is None:
        sys.stdout.write(text)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text)
        print(f"Wrote {out_path} ({len(records)} threads)", file=sys.stderr)

    if args.write_valid_list:
        valid_path = (
            cwd / "memory" / "temporal"
            / f"extracted-thread-ts-{date_label}-{channel}-valid.txt"
        )
        valid_path.parent.mkdir(parents=True, exist_ok=True)
        good = [r.ts for r in records if not r.error]
        valid_path.write_text("\n".join(good) + "\n")
        print(f"Wrote {valid_path} ({len(good)} lines)", file=sys.stderr)


if __name__ == "__main__":
    main()
