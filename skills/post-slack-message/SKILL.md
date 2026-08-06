---
name: post-slack-message
description: >-
  Post a message to a Slack channel or as a thread reply. Use when the user
  asks to send, post, or write a message to Slack, reply in a Slack thread,
  notify a Slack channel, or share something in a specific Slack channel,
  even if they don't say "post" explicitly. Also use when the user provides
  a Slack channel URL and wants to communicate something there.
---

# Post Slack Message

Posts a message to a Slack channel or as a thread reply using the Slack Web API
`chat.postMessage` endpoint. Supports both top-level messages and thread
replies, with Slack mrkdwn formatting (mentions, links, bold, etc.).

## Prerequisites

- `SLACK_TOKEN` and `SLACK_COOKIE` in `.env` (same credentials used by
  `slack-kb-individual` and `slack-cached`). A bot token (`xoxb-`) only needs
  `SLACK_TOKEN`; a browser token (`xoxc-`) also needs `SLACK_COOKIE`.
- The channel ID, name, or Slack archive URL to post to.
- The message text to send.

## What it does

[`post_slack_message.py`](post_slack_message.py) sends a single message to a
Slack channel via `chat.postMessage`. It handles credentials, URL parsing,
channel name resolution, thread replies, rate-limit retries, and dry-run
validation.

Run via `uv run` for automatic dependency management (`python-dotenv`,
`requests`).

## Usage

### Post to a channel by ID

```bash
uv run post_slack_message.py --channel C0BE3BM97B7 "Hello world"
```

### Post to a channel by URL

```bash
uv run post_slack_message.py \
  --channel-url https://shopify.enterprise.slack.com/archives/C0BE3BM97B7 \
  "Hello world"
```

### Post to a channel by name

```bash
uv run post_slack_message.py --channel-name tom-rochette-updates "Hello world"
```

### Post as a thread reply

```bash
uv run post_slack_message.py \
  --channel C0BE3BM97B7 --thread-ts 1700000000.123456 \
  "Reply text"
```

If `--channel-url` points at a specific thread message (has a `p<timestamp>`
path or `thread_ts` query parameter), the thread timestamp is extracted
automatically:

```bash
uv run post_slack_message.py \
  --channel-url https://shopify.slack.com/archives/C0BE3BM97B7/p1700000000123456 \
  "Reply text"
```

### Post with mentions and formatting

Slack mrkdwn is supported in the message text. Use `<@UUSERID>` for mentions:

```bash
uv run post_slack_message.py \
  --channel C0BE3BM97B7 \
  "Hey <@U07G5TUFSJF>, the deploy is done. See <https://example.com|details>."
```

### Dry run (validate without posting)

```bash
uv run post_slack_message.py --channel C0BE3BM97B7 --dry-run "Test message"
```

## All options

| Flag | Description |
|------|-------------|
| `--channel ID` | Channel ID (e.g. `C0BE3BM97B7`). Mutually exclusive with `--channel-url` and `--channel-name`. |
| `--channel-url URL` | Slack archive URL. Channel ID and thread_ts parsed from the URL. |
| `--channel-name NAME` | Channel name (e.g. `tom-rochette-updates`). Resolved to ID via `conversations.list`. |
| `--thread-ts TS` | Thread timestamp to reply in a thread. Optional; auto-detected from `--channel-url` if present. |
| `--dry-run` | Show what would be posted without sending. |
| `message` (positional) | Message text. Supports Slack mrkdwn formatting. |

## Workflow

1. Confirm the target channel and message content with the user before posting.
2. Run the script with `uv run post_slack_message.py`.
3. On success, the script prints the channel, message timestamp, and a permalink.
4. If the user wants to verify first, use `--dry-run`.
5. Report the result back to the user, including the permalink.
