#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "requests",
# ]
# ///
"""
Post a message to a Slack channel or as a thread reply.

Uses the Slack Web API chat.postMessage endpoint directly. No external CLI
dependencies. Run via `uv run` so PEP 723 script deps are applied.

Credentials: reads SLACK_TOKEN and SLACK_COOKIE from .env (python-dotenv,
searches up from cwd). An xoxc- browser token requires its matching xoxd-
cookie; a bot token (xoxb-) only needs SLACK_TOKEN.

Usage:
  # Post to a channel by ID, URL, or name
  uv run post_slack_message.py --channel C0BE3BM97B7 "Hello world"
  uv run post_slack_message.py --channel-url https://shopify.enterprise.slack.com/archives/C0BE3BM97B7 "Hello world"
  uv run post_slack_message.py --channel-name tom-rochette-updates "Hello world"

  # Post as a thread reply
  uv run post_slack_message.py --channel C0BE3BM97B7 --thread-ts 1700000000.123456 "Reply text"

  # Post with mentions (use raw text, Slack will parse <@U123> mentions)
  uv run post_slack_message.py --channel C0BE3BM97B7 "Hey <@U07G5TUFSJF>, check this out"

  # Dry run (validate credentials and channel without posting)
  uv run post_slack_message.py --channel C0BE3BM97B7 --dry-run "Test message"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import requests as http_lib
from dotenv import dotenv_values

SLACK_API_BASE = "https://slack.com/api"
MAX_RETRIES = 3
CHANNEL_LIST_PAGE_SIZE = 500


def load_credentials() -> tuple[str, str | None]:
    """Load SLACK_TOKEN and SLACK_COOKIE from .env, searching up from cwd."""
    for d in [Path.cwd()] + list(Path.cwd().parents):
        env_file = d / ".env"
        if env_file.is_file():
            vals = dotenv_values(env_file)
            token = vals.get("SLACK_TOKEN", "")
            cookie = vals.get("SLACK_COOKIE", "")
            if token:
                return token, cookie or None
    raise SystemExit(
        "Could not find SLACK_TOKEN in any .env file. "
        "Create one with SLACK_TOKEN (and SLACK_COOKIE for xoxc- tokens)."
    )


def parse_channel_from_url(url: str) -> str:
    """Extract channel ID from a Slack archive URL.

    Accepts:
      https://workspace.slack.com/archives/C0BE3BM97B7
      https://workspace.enterprise.slack.com/archives/C0BE3BM97B7/p1700000000123456
    """
    m = re.search(r"/archives/([A-Z0-9]+)", url)
    if not m:
        raise SystemExit(f"Could not parse channel ID from URL: {url}")
    return m.group(1)


def parse_thread_ts_from_url(url: str) -> str | None:
    """Extract thread_ts from a Slack archive URL if present.

    Handles both the path-encoded timestamp and the thread_ts query parameter.
    """
    m = re.search(r"/archives/[A-Z0-9]+/p(\d+)(?:\?thread_ts=([\d.]+))?", url)
    if not m:
        return None
    query_thread_ts = m.group(2)
    if query_thread_ts:
        return query_thread_ts
    path_ts = m.group(1)
    return f"{path_ts[:-6]}.{path_ts[-6:]}"


def resolve_channel_name(token: str, cookie: str | None, name: str) -> str:
    """Resolve a channel name to its ID via conversations.list pagination."""
    import time

    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    if cookie:
        headers["Cookie"] = f"d={cookie}"

    cursor = ""
    while True:
        params: dict[str, str] = {
            "limit": str(CHANNEL_LIST_PAGE_SIZE),
            "types": "private_channel,public_channel",
        }
        if cursor:
            params["cursor"] = cursor

        for attempt in range(1, MAX_RETRIES + 1):
            resp = http_lib.get(
                f"{SLACK_API_BASE}/conversations.list",
                headers=headers,
                params=params,
                timeout=30,
            )
            if resp.status_code == 429 and attempt < MAX_RETRIES:
                retry_after = int(resp.headers.get("Retry-After", "2"))
                print(f"Rate limited, retrying in {retry_after}s (attempt {attempt}/{MAX_RETRIES})...", file=sys.stderr)
                time.sleep(retry_after)
                continue
            resp.raise_for_status()
            break

        body = resp.json()

        if not body.get("ok"):
            raise SystemExit(f"Slack API error resolving channel name: {body.get('error', 'unknown')}")

        for ch in body.get("channels", []):
            if ch.get("name") == name:
                return ch["id"]

        cursor = body.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break

    raise SystemExit(f"Could not find channel named '{name}'. Make sure it exists and the token has access.")


def post_message(
    token: str,
    cookie: str | None,
    channel: str,
    text: str,
    thread_ts: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Post a message to Slack via chat.postMessage."""
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    if cookie:
        headers["Cookie"] = f"d={cookie}"

    payload: dict[str, Any] = {
        "channel": channel,
        "text": text,
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts

    if dry_run:
        print(f"[dry-run] Would post to channel {channel}" + (f" (thread {thread_ts})" if thread_ts else ""))
        print(f"[dry-run] Message: {text}")
        return {"ok": True, "dry_run": True}

    for attempt in range(1, MAX_RETRIES + 1):
        resp = http_lib.post(
            f"{SLACK_API_BASE}/chat.postMessage",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()

        if body.get("ok"):
            return body

        error = body.get("error", "unknown")
        if error == "ratelimited" and attempt < MAX_RETRIES:
            retry_after = int(resp.headers.get("Retry-After", "2"))
            print(f"Rate limited, retrying in {retry_after}s (attempt {attempt}/{MAX_RETRIES})...", file=sys.stderr)
            import time
            time.sleep(retry_after)
            continue

        raise SystemExit(f"Slack API error: {error}\nResponse: {body}")

    raise SystemExit(f"Failed after {MAX_RETRIES} retries")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post a message to a Slack channel or thread.",
    )
    msg_group = parser.add_mutually_exclusive_group(required=True)
    msg_group.add_argument(
        "--channel",
        help="Channel ID (e.g. C0BE3BM97B7)",
    )
    msg_group.add_argument(
        "--channel-url",
        help="Slack archive URL (e.g. https://workspace.slack.com/archives/C0BE3BM97B7)",
    )
    msg_group.add_argument(
        "--channel-name",
        help="Channel name (e.g. tom-rochette-updates). Resolved to ID at runtime.",
    )
    parser.add_argument(
        "--thread-ts",
        help="Thread timestamp to reply in a thread (e.g. 1700000000.123456). "
             "If --channel-url points to a thread, this is extracted automatically.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate credentials and show what would be posted without sending.",
    )
    parser.add_argument(
        "message",
        help="Message text to post. Supports Slack mrkdwn formatting.",
    )

    args = parser.parse_args()

    token, cookie = load_credentials()

    if args.channel_url:
        channel = parse_channel_from_url(args.channel_url)
        thread_ts = args.thread_ts or parse_thread_ts_from_url(args.channel_url)
    elif args.channel_name:
        channel = resolve_channel_name(token, cookie, args.channel_name)
        thread_ts = args.thread_ts
    else:
        channel = args.channel
        thread_ts = args.thread_ts

    result = post_message(
        token=token,
        cookie=cookie,
        channel=channel,
        text=args.message,
        thread_ts=thread_ts,
        dry_run=args.dry_run,
    )

    if result.get("ok") and not result.get("dry_run"):
        ts = result.get("ts", "")
        posted_channel = result.get("channel", channel)
        print(f"Posted to {posted_channel}" + (f" (thread {thread_ts})" if thread_ts else ""))
        print(f"Message timestamp: {ts}")
        print(f"Permalink: https://shopify.slack.com/archives/{posted_channel}/p{ts.replace('.', '')}")


if __name__ == "__main__":
    main()
