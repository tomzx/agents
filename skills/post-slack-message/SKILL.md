---
name: post-slack-message
description: Post a message to a Slack channel or as a thread reply. By default writes the message to a temp file and asks the user to confirm before sending; pass --yes to send immediately without prompting. Use when the user says /post-slack-message, "post to Slack", "send a Slack message", "reply in a Slack thread", or another skill delegates its Slack posting here.
argument-hint: "[--yes] [--channel <id|url|name>] [--thread-ts <ts>] <message>"
---

# Post Slack Message

Posts a message to a Slack channel or as a thread reply using `post_slack_message.py` (Slack Web API `chat.postMessage`). The compose-and-confirm flow lives in this skill so it can use the question tool; the script is the send primitive.

## Behavior modes

- **Review mode (default):** write the message to a temp file, then use the **question** tool to ask the user to confirm sending the content of that file. Nothing is posted until the user approves.
- **Immediate mode (`--yes`):** skip the confirmation and post right away. Use this for fully unattended flows (scheduled jobs, automation, or a caller that has already shown the message to the user).

`--yes` (also `-y`, `--send`, `--auto`) is accepted in any position of the arguments.

## Prerequisites

- `SLACK_TOKEN` set. A bot token (`xoxb-`) only needs the token; a web/browser token (`xoxc-`) also needs `SLACK_COOKIE` (the `xoxd-` value), the same credentials used by `slack-kb-individual` and `slack-cached`. Place them in `.env` at the repo root or export them in the environment.
- The target channel: a channel id, a Slack archive URL, or a channel name.

## Inputs

- **channel:** one of `--channel <id>`, `--channel-url <url>`, or `--channel-name <name>` (the name is resolved to an id via `conversations.list`). Exactly one is required.
- **thread_ts:** optional `--thread-ts <ts>` to post as a thread reply; auto-detected when `--channel-url` points at a thread message.
- **message:** the message body in Slack mrkdwn (`*bold*`, `<@USERID>` mentions, `<https://url|label>` links). Provided as a trailing argument, via `--file <path>`, or via `--stdin`. Exactly one source.
- **mode:** `--yes` for immediate send; otherwise review mode.
- **dry-run:** `--dry-run` resolves the channel and shows what would be posted without sending. Use it to pre-validate credentials and targeting.

## Steps

### 1. Resolve inputs

Determine the channel (id/url/name) and the final message text. If the caller passed an explicit message string, use it verbatim. Otherwise compose the message from context, keeping it short and using Slack mrkdwn. Decide whether this is a thread reply (`--thread-ts`).

### 2. Write the message to a temp file

Always materialize the exact bytes that will be sent into a temp file so the user reviews the precise content:

```bash
MSG_FILE="/tmp/opencode/post-slack-message-$(date +%Y%m%d-%H%M%S).md"
# write the message text to $MSG_FILE (use the Write tool, or a heredoc via bash)
```

This file is the single source of truth for both review and send. (To sanity-check targeting first, you may run a `--dry-run`.)

### 3. Branch on mode

#### Review mode (default)

Use the **question** tool to ask the user to confirm sending the content of the temp file. Do not summarize the message from memory; point the user at the file so they review the real content. For example:

> I've prepared the Slack message in `/tmp/opencode/post-slack-message-<ts>.md`. Please review it. Send it to `<channel>`?

Options:

- **Send it** - post the file's content as-is.
- **Edit, then I'll re-confirm** - the user edits the file (or tells you changes); you rewrite the temp file and ask again.
- **Cancel** - stop without sending.

- On **Send it**: continue to step 4.
- On **Edit**: apply the edits, rewrite the temp file, and re-ask. Loop until the user sends or cancels.
- On **Cancel**: stop and tell the user nothing was posted.

#### Immediate mode (`--yes`)

Skip the question and go straight to step 4. Only use this when the caller explicitly opted in.

### 4. Send the message

Send the temp file's content through the sender script so the reviewed bytes are exactly what is posted:

```bash
uv run post_slack_message.py --channel <channel-id> --file "$MSG_FILE"
```

For a thread reply or a URL/name target:

```bash
uv run post_slack_message.py --channel-url <url> --thread-ts <ts> --file "$MSG_FILE"
uv run post_slack_message.py --channel-name tom-rochette-updates --file "$MSG_FILE"
```

The script prints the posted message's permalink to stdout (and a short status line to stderr). Other skills that delegate here (e.g. start-day, end-day) may call the script directly with a positional message when they have already opted into immediate send.

If the send fails (missing token, `chat.postMessage` error, rate limit exhausted), surface the error from stderr and stop. Do not silently retry; let the user decide.

### 5. Report back

Report the permalink (and the channel, and the thread if applicable) to the user, and confirm whether review or immediate mode was used.

## Example usage

**Review a drafted update (default):**
```
/post-slack-message --channel C0BE3BM97B7 "*Start of day*\n\n*Top 3 outcomes:* ..."
```

**Send without prompting (automation):**
```
/post-slack-message --yes --channel C0BE3BM97B7 "Deploy started for v1.4.2"
```

**Post a file's contents:**
```
/post-slack-message --yes --channel C0BE3BM97B7 "$(cat /tmp/opencode/msg.md)"
```

**Reply in a thread (URL carries the thread_ts):**
```
/post-slack-message --yes --channel-url https://acme.slack.com/archives/C0BE3BM97B7/p1700000000123456 "Reply text"
```

**Post by channel name:**
```
/post-slack-message --yes --channel-name tom-rochette-updates "Hello world"
```

**Mentions and links (Slack mrkdwn):**
```
/post-slack-message --channel C0BE3BM97B7 "Hey <@U07G5TUFSJF>, the deploy is done. See <https://example.com|details>."
```

**Validate without posting:**
```
/post-slack-message --channel C0BE3BM97B7 --dry-run "Test message"
```

## Notes for calling skills

Skills like **start-day** and **end-day** post automated daily updates and are already gated behind the `SEND_DAILY_SLACK` opt-in. They may call `post_slack_message.py` directly (immediate send) because the user has pre-approved that flow. Any interactive or one-off post should go through this skill's review mode instead.

## Useful commands reference

| Command | Description |
|---|---|
| `uv run post_slack_message.py --channel <id> --file <path>` | Post a file's contents to a channel (used by the review flow). |
| `uv run post_slack_message.py --channel <id> "<text>"` | Post a positional message immediately. |
| `uv run post_slack_message.py --channel-url <url> "<text>"` | Post to a channel parsed from a Slack archive URL (thread_ts auto-detected). |
| `uv run post_slack_message.py --channel-name <name> "<text>"` | Post to a channel resolved by name. |
| `uv run post_slack_message.py ... --thread-ts <ts> "<text>"` | Post as a thread reply. |
| `uv run post_slack_message.py ... --dry-run "<text>"` | Resolve channel and preview without sending. |
| `echo "<text>" \| uv run post_slack_message.py --channel <id> --stdin` | Post a message read from stdin. |
| `slack-cached show-channels` | Look up a channel name/id. |
