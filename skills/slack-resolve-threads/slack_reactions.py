#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "requests",
# ]
# ///
"""
Check for and add a reaction on the root message of a Slack thread.

This is the small piece slackx does not do: slackx can read a thread
but has no write command and its cached reaction payloads can be stale. This
helper talks to the Slack API directly so the "is it already marked?" check and
the "mark it" action always reflect the live state.

Two subcommands:

  check   Report whether the configured emoji is already on the thread root.
          Prints a JSON object to stdout and exits 0 when reachable.

  add     Add the configured emoji to the thread root (idempotent: an
          "already_reacted" response from Slack is treated as success).

A target is either a thread permalink or an explicit --channel/--ts pair, the
same forms slackx accepts.

Credentials: reads SLACK_TOKEN and SLACK_COOKIE from .env (searching up from the
current directory), matching the other Slack skills in this repo.

Usage (run via uv so the PEP 723 deps are installed automatically):

  uv run slack_reactions.py check \
    https://acme.slack.com/archives/C0123ABCDEF/p1700000000123456

  uv run slack_reactions.py add --channel C0123ABCDEF --ts 1700000000.123456

  uv run slack_reactions.py check --emoji white_check_mark <url>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests as http_lib
from dotenv import dotenv_values

DEFAULT_EMOJI = "white_check_mark"
MAX_RETRIES = 5


def load_credentials() -> tuple[str, str]:
    """Load SLACK_TOKEN and SLACK_COOKIE from .env, searching up from cwd."""
    for d in [Path.cwd()] + list(Path.cwd().parents):
        env_file = d / ".env"
        if env_file.is_file():
            vals = dotenv_values(env_file)
            token = vals.get("SLACK_TOKEN", "")
            cookie = vals.get("SLACK_COOKIE", "")
            if token:
                # Cookie is only required for xoxc/web-client tokens; allow
                # bot/user tokens (xoxb/xoxp) to work without one.
                return token, cookie
    raise SystemExit(
        "Could not find SLACK_TOKEN in any .env file. "
        "Create one with SLACK_TOKEN (and SLACK_COOKIE for xoxc tokens) set."
    )


def _headers(token: str, cookie: str) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if cookie:
        headers["Cookie"] = f"d={cookie}"
    return headers


def parse_target(url: str | None, channel: str | None, ts: str | None) -> tuple[str, str]:
    """Resolve a (channel, thread_ts) pair from a permalink or explicit args.

    Permalinks look like
    https://workspace.slack.com/archives/C0123ABCDEF/p1700000000123456
    where the trailing pNNNNNNNNNNNNNNNN encodes the ts with the dot removed.
    """
    if channel and ts:
        return channel, ts
    if not url:
        raise SystemExit("Provide either a permalink or both --channel and --ts.")
    m = re.search(r"/archives/([A-Z0-9]+)/p(\d{10})(\d{6})", url)
    if not m:
        raise SystemExit(f"Could not parse channel/ts from URL: {url}")
    chan, seconds, micros = m.group(1), m.group(2), m.group(3)
    return chan, f"{seconds}.{micros}"


def _call(
    method: str,
    token: str,
    cookie: str,
    params: dict[str, str],
    *,
    http_method: str = "GET",
) -> dict:
    """Call a Slack Web API method with basic rate-limit retry handling."""
    url = f"https://slack.com/api/{method}"
    for attempt in range(MAX_RETRIES):
        if http_method == "POST":
            resp = http_lib.post(url, headers=_headers(token, cookie), data=params, timeout=30)
        else:
            resp = http_lib.get(url, headers=_headers(token, cookie), params=params, timeout=30)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "1"))
            time.sleep(max(wait, 1))
            continue
        resp.raise_for_status()
        return resp.json()
    raise SystemExit(f"Slack API {method} kept rate-limiting after {MAX_RETRIES} attempts.")


def has_reaction(token: str, cookie: str, channel: str, ts: str, emoji: str) -> bool:
    """Return True when `emoji` is already present on the thread root message."""
    data = _call(
        "reactions.get",
        token,
        cookie,
        {"channel": channel, "timestamp": ts, "full": "true"},
    )
    if not data.get("ok"):
        raise SystemExit(f"reactions.get failed: {data.get('error', 'unknown error')}")
    message = data.get("message") or {}
    for reaction in message.get("reactions", []):
        if reaction.get("name") == emoji:
            return True
    return False


def add_reaction(token: str, cookie: str, channel: str, ts: str, emoji: str) -> str:
    """Add `emoji` to the thread root. Returns a short status string.

    Treats Slack's `already_reacted` error as success so repeated runs are safe.
    """
    data = _call(
        "reactions.add",
        token,
        cookie,
        {"channel": channel, "timestamp": ts, "name": emoji},
        http_method="POST",
    )
    if data.get("ok"):
        return "added"
    error = data.get("error", "unknown error")
    if error == "already_reacted":
        return "already_reacted"
    raise SystemExit(f"reactions.add failed: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or add a Slack reaction on a thread root.")
    parser.add_argument("action", choices=["check", "add"], help="What to do.")
    parser.add_argument("url", nargs="?", help="Slack thread permalink.")
    parser.add_argument("--channel", help="Slack channel id (used with --ts).")
    parser.add_argument("--ts", help="Thread root ts, e.g. 1700000000.123456 (used with --channel).")
    parser.add_argument(
        "--emoji",
        default=DEFAULT_EMOJI,
        help=f"Reaction emoji name without colons (default: {DEFAULT_EMOJI}).",
    )
    args = parser.parse_args(argv)

    token, cookie = load_credentials()
    channel, ts = parse_target(args.url, args.channel, args.ts)

    if args.action == "check":
        present = has_reaction(token, cookie, channel, ts, args.emoji)
        json.dump(
            {"channel": channel, "ts": ts, "emoji": args.emoji, "present": present},
            sys.stdout,
        )
        sys.stdout.write("\n")
        return 0

    status = add_reaction(token, cookie, channel, ts, args.emoji)
    json.dump(
        {"channel": channel, "ts": ts, "emoji": args.emoji, "status": status},
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
