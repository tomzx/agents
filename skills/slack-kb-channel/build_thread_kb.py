#!/usr/bin/env python3
"""
Batch-fetch Slack thread metadata for KB ingestion for any channel.

1. Pulls channel history from `--oldest` (month start) via `devx agent-tools slack`.
2. Keeps messages whose `ts` is in [month_start, month_end).
3. Fetches each thread (JSON) and records reply count + first-line preview.

Output: JSON lines (one object per thread with channel id), for maintainer ingestion (not for pasting a thread index into the monthly memory file).

Usage:
  python3 skills/slack-kb-channel/build_thread_kb.py --channel C01234567 --month 2026-02 \\
    --output memory/temporal/thread-fetch-2026-02-C01234567.jsonl --write-valid-list

  export SLACK_CHANNEL_ID=C01234567
  python3 skills/slack-kb-channel/build_thread_kb.py --month 2026-03 -o -   # stdout
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CHANNEL_FETCH_LIMIT = 1000
THREAD_REPLY_LIMIT = 200


def find_devx() -> str:
    """Locate devx binary or fail with a helpful message."""
    path = shutil.which("devx")
    if path:
        return path
    raise SystemExit(
        "Could not find `devx` on PATH. "
        "Install it or ensure it's available (e.g. via `tec`)."
    )


def parse_month(s: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d{4})-(\d{2})", s.strip())
    if not m:
        raise SystemExit(f"Invalid --month {s!r}; expected YYYY-MM")
    y, mo = int(m.group(1)), int(m.group(2))
    if not 1 <= mo <= 12:
        raise SystemExit(f"Invalid month in {s!r}")
    return y, mo


def resolve_channel(arg_channel: str | None) -> str:
    """Channel id from --channel or SLACK_CHANNEL_ID."""
    ch = (arg_channel or os.environ.get("SLACK_CHANNEL_ID") or "").strip()
    if not ch:
        raise SystemExit(
            "Set --channel <CHANNEL_ID> or export SLACK_CHANNEL_ID (Slack channel id, e.g. C01234567)."
        )
    return ch


def month_bounds_utc(year: int, month: int) -> tuple[float, float]:
    """Return (start_inclusive, end_exclusive) as Slack-compatible float timestamps."""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start.timestamp(), end.timestamp()


def devx_slack(*args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    devx = find_devx()
    return subprocess.run(
        [devx, "agent-tools", "slack", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def fetch_channel_messages(
    channel: str,
    oldest_ts: float,
    latest_ts: float,
    limit: int,
) -> list[dict[str, Any]]:
    """Fetch channel messages in the given time window, returning parsed JSON list."""
    r = devx_slack(
        "message", "list", channel,
        f"--oldest={oldest_ts:.6f}",
        f"--latest={latest_ts:.6f}",
        f"--limit={limit}",
        "--json", "ts,threadTs,replyCount,text",
    )
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0 or "Authentication" in out:
        print(out, file=sys.stderr)
        raise SystemExit("devx agent-tools slack failed (auth or error). Run `devx agent-tools slack auth setup`.")
    return json.loads(r.stdout)


def fetch_thread_json(
    channel: str,
    ts: str,
    limit: int,
) -> list[dict[str, Any]]:
    """Fetch thread replies as a JSON list."""
    r = devx_slack(
        "message", "thread", channel, ts,
        f"--limit={limit}",
        "--json", "ts,text,replyCount",
        timeout=180,
    )
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0 or "Authentication" in out:
        print(out[:500], file=sys.stderr)
        raise SystemExit("Slack auth failed mid-run.")
    return json.loads(r.stdout)


def extract_preview(messages: list[dict[str, Any]]) -> tuple[int, str]:
    """Extract reply count and first-message preview from thread JSON."""
    if not messages:
        return -1, ""
    first = messages[0]
    reply_count = first.get("replyCount", len(messages) - 1)
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


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Batch-fetch Slack thread metadata for a channel (by calendar month, UTC)."
    )
    ap.add_argument(
        "--month",
        metavar="YYYY-MM",
        required=True,
        help="Calendar month (UTC): fetch channel from month start and keep threads in [start, next_month).",
    )
    ap.add_argument(
        "--channel",
        metavar="CHANNEL_ID",
        default=None,
        help="Slack channel id (e.g. C01234567). If omitted, uses env SLACK_CHANNEL_ID.",
    )
    ap.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help=(
            "Write JSONL here, or '-' for stdout "
            "(default: memory/temporal/thread-fetch-YYYY-MM-<CHANNEL_ID>.jsonl under CWD)."
        ),
    )
    ap.add_argument(
        "--write-valid-list",
        action="store_true",
        help=(
            "Also write memory/temporal/extracted-thread-ts-YYYY-MM-<CHANNEL_ID>-valid.txt "
            "(one thread_ts per line)."
        ),
    )
    ap.add_argument(
        "--channel-limit",
        type=int,
        default=CHANNEL_FETCH_LIMIT,
        help=f"Max messages per channel request (default {CHANNEL_FETCH_LIMIT}).",
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
    args = ap.parse_args()

    channel = resolve_channel(args.channel)
    year, month = parse_month(args.month)
    start_ts, end_ts = month_bounds_utc(year, month)

    cwd = Path.cwd()
    out_path: Path | None
    if args.output == "-":
        out_f = sys.stdout
        out_path = None
    elif args.output:
        out_path = Path(args.output).expanduser()
        if not out_path.is_absolute():
            out_path = (cwd / out_path).resolve()
    else:
        out_path = cwd / "memory" / "temporal" / f"thread-fetch-{args.month}-{channel}.jsonl"

    messages = fetch_channel_messages(channel, start_ts, end_ts, args.channel_limit)
    if len(messages) >= args.channel_limit:
        print(
            f"warning: got {len(messages)} messages (>= --channel-limit); "
            "results may be truncated. Increase --channel-limit or extend this script to paginate.",
            file=sys.stderr,
        )

    messages.sort(key=lambda m: float(m["ts"]))
    ids = [m["ts"] for m in messages]

    if args.skip_threads:
        for ts in ids:
            print(ts)
        if args.write_valid_list:
            valid_path = cwd / "memory" / "temporal" / f"extracted-thread-ts-{args.month}-{channel}-valid.txt"
            valid_path.parent.mkdir(parents=True, exist_ok=True)
            valid_path.write_text("\n".join(ids) + "\n")
            print(f"Wrote {valid_path}", file=sys.stderr)
        return

    records: list[ThreadRecord] = []
    for i, ts in enumerate(ids):
        try:
            thread_msgs = fetch_thread_json(channel, ts, args.thread_limit)
        except (json.JSONDecodeError, SystemExit) as exc:
            records.append(ThreadRecord(channel=channel, ts=ts, replies=-1, preview="", error=str(exc)))
            print(f"[{i + 1}/{len(ids)}] {ts} ERR {exc}", file=sys.stderr)
            continue
        if not thread_msgs:
            records.append(
                ThreadRecord(channel=channel, ts=ts, replies=-1, preview="", error="thread_not_found")
            )
            print(f"[{i + 1}/{len(ids)}] {ts} ERR thread_not_found", file=sys.stderr)
            continue
        replies, preview = extract_preview(thread_msgs)
        records.append(ThreadRecord(channel=channel, ts=ts, replies=replies, preview=preview))
        print(f"[{i + 1}/{len(ids)}] {ts} replies={replies}", file=sys.stderr)

    lines = [json.dumps(r.to_json_obj(), ensure_ascii=False) for r in records]
    text = "\n".join(lines) + ("\n" if lines else "")

    if out_path is None:
        sys.stdout.write(text)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text)
        print(f"Wrote {out_path} ({len(records)} threads)", file=sys.stderr)

    if args.write_valid_list:
        valid_path = cwd / "memory" / "temporal" / f"extracted-thread-ts-{args.month}-{channel}-valid.txt"
        valid_path.parent.mkdir(parents=True, exist_ok=True)
        good = [r.ts for r in records if not r.error]
        valid_path.write_text("\n".join(good) + "\n")
        print(f"Wrote {valid_path} ({len(good)} lines)", file=sys.stderr)


if __name__ == "__main__":
    main()
