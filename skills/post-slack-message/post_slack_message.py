#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "requests",
# ]
# ///
"""Post a message to a Slack channel or as a thread reply (chat.postMessage).

This is the send primitive behind the post-slack-message skill. It only sends;
the review/confirm step lives in the skill (agent-side) so it can use the
question tool.

The target channel can be given as an id (--channel), a Slack archive URL
(--channel-url), or a name (--channel-name, resolved at runtime). A thread
reply is posted with --thread-ts, auto-detected when --channel-url points at a
thread. The message comes from a positional argument, --file, or --stdin.

Credentials are read from the environment first, then from a .env file searched
up from the current directory. A bot token (xoxb-) only needs SLACK_TOKEN; a
web token (xoxc-) also needs its matching SLACK_COOKIE (the xoxd- value).

On success the message permalink is printed to stdout (status notes go to
stderr) so callers can capture it with command substitution.

Usage:
  uv run post_slack_message.py --channel C0BE3BM97B7 "Hello world"
  uv run post_slack_message.py --channel-name tom-rochette-updates "Hello"
  uv run post_slack_message.py --channel-url https://acme.slack.com/archives/C0BE3BM97B7/p1700000000123456 "Reply"
  uv run post_slack_message.py --channel C0BE3BM97B7 --file /tmp/opencode/msg.md
  echo "body" | uv run post_slack_message.py --channel C0BE3BM97B7 --stdin
  uv run post_slack_message.py --channel C0BE3BM97B7 --dry-run "Test"
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests as http_lib
from dotenv import dotenv_values

DEFAULT_API_BASE_URL = "https://slack.com/api"
MAX_RETRIES = 5
CHANNEL_LIST_PAGE_SIZE = 500


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


def load_credentials() -> tuple[str, str]:
    """Return (SLACK_TOKEN, SLACK_COOKIE) from env or a nearby .env file.

    Environment variables win over .env. SLACK_COOKIE may be empty for bot
    tokens.
    """
    token = os.environ.get("SLACK_TOKEN", "")
    cookie = os.environ.get("SLACK_COOKIE", "")

    if not token:
        for d in (Path.cwd(), *Path.cwd().parents):
            env_file = d / ".env"
            if env_file.is_file():
                vals = dotenv_values(env_file)
                token = vals.get("SLACK_TOKEN", "") or token
                cookie = vals.get("SLACK_COOKIE", "") or cookie
                if token:
                    break

    if not token:
        raise SystemExit(
            "Could not find SLACK_TOKEN. Set it in the environment or in a "
            ".env file (searched up from the current directory)."
        )

    if token.startswith("xoxc-") and not cookie:
        raise SystemExit(
            "An xoxc- web token also requires SLACK_COOKIE (the xoxd- value) "
            "from the same browser session."
        )

    return token, cookie


# ---------------------------------------------------------------------------
# Slack API helpers
# ---------------------------------------------------------------------------


def _request(
    method: str,
    url: str,
    token: str,
    cookie: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Perform a Slack API call with automatic retry on rate limiting."""
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    if cookie:
        headers["Cookie"] = f"d={cookie}"

    for attempt in range(MAX_RETRIES):
        r = http_lib.request(method, url, headers=headers, timeout=30, **kwargs)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", "5"))
            print(
                f"  rate limited, waiting {wait}s "
                f"(attempt {attempt + 1}/{MAX_RETRIES})",
                file=sys.stderr,
            )
            time.sleep(wait)
            continue
        r.raise_for_status()
        data = r.json()
        if data.get("error") == "ratelimited":
            wait = int(r.headers.get("Retry-After", "5"))
            print(
                f"  rate limited, waiting {wait}s "
                f"(attempt {attempt + 1}/{MAX_RETRIES})",
                file=sys.stderr,
            )
            time.sleep(wait)
            continue
        return data

    raise SystemExit(f"Rate limited {MAX_RETRIES} times in a row; giving up.")


def resolve_channel_name(
    token: str,
    cookie: str,
    name: str,
    api_base_url: str = DEFAULT_API_BASE_URL,
) -> str:
    """Resolve a channel name to its id via conversations.list pagination."""
    cursor: str | None = None
    while True:
        params: dict[str, Any] = {
            "limit": CHANNEL_LIST_PAGE_SIZE,
            "types": "private_channel,public_channel",
        }
        if cursor:
            params["cursor"] = cursor

        data = _request(
            "GET",
            f"{api_base_url}/conversations.list",
            token,
            cookie,
            params=params,
        )
        if not data.get("ok"):
            raise SystemExit(
                f"conversations.list failed: {data.get('error', 'unknown')}"
            )

        for ch in data.get("channels", []):
            if ch.get("name") == name:
                return ch["id"]

        cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break

    raise SystemExit(
        f"Could not find channel named '{name}'. Make sure it exists and the "
        "token can see it."
    )


def parse_channel_from_url(url: str) -> str:
    """Extract the channel id from a Slack archive URL."""
    m = re.search(r"/archives/([A-Z0-9]+)", url)
    if not m:
        raise SystemExit(f"Could not parse channel id from URL: {url}")
    return m.group(1)


def parse_thread_ts_from_url(url: str) -> str | None:
    """Extract thread_ts from a Slack archive URL, if present.

    Handles both the path-encoded timestamp and a thread_ts query parameter.
    """
    m = re.search(r"/archives/[A-Z0-9]+/p(\d+)(?:\?thread_ts=([\d.]+))?", url)
    if not m:
        return None
    query_ts = m.group(2)
    if query_ts:
        return query_ts
    path_ts = m.group(1)
    return f"{path_ts[:-6]}.{path_ts[-6:]}"


def get_permalink(
    token: str,
    cookie: str,
    channel: str,
    ts: str,
    api_base_url: str = DEFAULT_API_BASE_URL,
) -> str:
    """Resolve a permalink for a posted message; empty string if unavailable."""
    data = _request(
        "GET",
        f"{api_base_url}/chat.getPermalink",
        token,
        cookie,
        params={"channel": channel, "message_ts": ts},
    )
    if not data.get("ok"):
        return ""
    return data.get("permalink", "")


def post_message(
    token: str,
    cookie: str,
    channel: str,
    text: str,
    thread_ts: str | None = None,
    dry_run: bool = False,
    api_base_url: str = DEFAULT_API_BASE_URL,
) -> tuple[str | None, str | None]:
    """Post text to channel (or as a thread reply). Returns (permalink, ts).

    In dry-run mode nothing is posted and (None, None) is returned after the
    intended post is printed to stderr.
    """
    where = f"channel {channel}" + (f" (thread {thread_ts})" if thread_ts else "")
    if dry_run:
        print(f"[dry-run] Would post to {where}", file=sys.stderr)
        print(f"[dry-run] Message:\n{text}", file=sys.stderr)
        return None, None

    payload: dict[str, Any] = {"channel": channel, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts

    data = _request(
        "POST",
        f"{api_base_url}/chat.postMessage",
        token,
        cookie,
        data=payload,
    )
    if not data.get("ok"):
        raise SystemExit(f"chat.postMessage failed: {data.get('error', 'unknown')}")

    ts = data["ts"]
    posted_channel = data.get("channel", channel)
    permalink = get_permalink(token, cookie, posted_channel, ts, api_base_url)
    return permalink, ts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def read_message(args: argparse.Namespace) -> str:
    """Resolve the message body from exactly one of: positional, --file, --stdin."""
    sources = [args.message is not None, args.file is not None, args.stdin]
    if sum(sources) != 1:
        raise SystemExit(
            "Provide the message exactly once: as a positional argument, "
            "--file PATH, or --stdin."
        )
    if args.file is not None:
        return Path(args.file).read_text(encoding="utf-8")
    if args.stdin:
        return sys.stdin.read()
    return args.message or ""


def resolve_target(
    args: argparse.Namespace,
    token: str,
    cookie: str,
) -> tuple[str, str | None]:
    """Return (channel_id, thread_ts) from the selected channel option."""
    if args.channel_url:
        channel = parse_channel_from_url(args.channel_url)
        thread_ts = args.thread_ts or parse_thread_ts_from_url(args.channel_url)
    elif args.channel_name:
        channel = resolve_channel_name(
            token, cookie, args.channel_name, args.api_base_url
        )
        thread_ts = args.thread_ts
    else:
        channel = args.channel or ""
        thread_ts = args.thread_ts
    return channel, thread_ts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post a message to a Slack channel or thread (chat.postMessage).",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--channel", help="Channel id (e.g. C0BE3BM97B7).")
    target.add_argument(
        "--channel-url",
        help="Slack archive URL; channel id and thread_ts are parsed from it.",
    )
    target.add_argument(
        "--channel-name",
        help="Channel name (e.g. tom-rochette-updates), resolved to an id at runtime.",
    )
    parser.add_argument(
        "--thread-ts",
        help="Thread timestamp to reply in a thread. Auto-detected from --channel-url.",
    )
    parser.add_argument("message", nargs="?", help="Message text (Slack mrkdwn).")
    parser.add_argument("--file", help="Read message text from this file.")
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read message text from standard input.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve the channel and show what would be posted, without sending.",
    )
    parser.add_argument(
        "--api-base-url",
        default=DEFAULT_API_BASE_URL,
        help=f"Slack API base URL (default: {DEFAULT_API_BASE_URL}).",
    )
    args = parser.parse_args()

    text = read_message(args)
    if not text:
        raise SystemExit("Refusing to send an empty message.")

    token, cookie = load_credentials()
    channel, thread_ts = resolve_target(args, token, cookie)

    permalink, ts = post_message(
        token,
        cookie,
        channel,
        text,
        thread_ts=thread_ts,
        dry_run=args.dry_run,
        api_base_url=args.api_base_url,
    )

    if args.dry_run:
        return

    where = f"Posted to {channel}" + (f" (thread {thread_ts})" if thread_ts else "")
    print(where, file=sys.stderr)
    if ts:
        print(f"Message timestamp: {ts}", file=sys.stderr)
    if permalink:
        print(permalink)
    elif ts:
        print(f"ts:{ts}")


if __name__ == "__main__":
    main()
