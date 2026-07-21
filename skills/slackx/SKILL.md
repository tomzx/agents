---
name: slackx
description: >
  Use the `slack-cached` CLI to cache and read Slack threads, channel history,
  users, and channels from a local SQLite database. It fetches threads via
  `conversations.replies`, channel history via `conversations.history`, and
  workspace users/channels, storing everything locally so subsequent reads are
  instant and incremental. Trigger when the user wants to read, cache, refresh,
  or poll a Slack thread or channel, render a thread with human-readable author
  names, search the workspace and cache matches, or says "slack-cached" or
  "slackx" explicitly. Other Slack skills (slack-resolve-threads,
  slack-kb-channel, slack-kb-individual) build on top of this tool.
---

# slackx Skill

`slack-cached` is a small Python CLI that caches Slack threads, channel
messages, users, and channels to a local SQLite database. Given a Slack thread
URL (or an explicit channel id and root timestamp), it fetches the thread via
`conversations.replies` and stores every message. On subsequent runs it only
fetches new replies (and detects edits) by passing `oldest` to the API based on
the highest cached `ts`.

It is the single source of Slack thread content for every other Slack skill:
`slack-resolve-threads` reads threads through `slack-cached show`, and the
knowledge-base skills use it to cache and render conversations.

---

## Prerequisites

### Binary

Check whether the binary is on PATH; install from the source repo if not:

```bash
if ! command -v slack-cached &>/dev/null; then
  git clone https://github.com/TomzxCode/slackx /tmp/slackx
  uv tool install /tmp/slackx
fi
```

If `uv tool install` isn't desired, run it in place with
`uv run --project /tmp/slackx slack-cached ...`. Confirm it works:
`slack-cached --help`.

### Authentication

Credentials are loaded in this order:

1. Environment variables: `SLACK_TOKEN` (and optional `SLACK_COOKIE` for
   xoxc/web-client tokens).
2. A config file at `$XDG_CONFIG_HOME/slack-cached/config`
   (defaults to `~/.config/slack-cached/config`).
   It uses a simple `KEY=VALUE` format:
   ```
   SLACK_TOKEN=xoxb-...
   SLACK_COOKIE=...
   SLACK_API_BASE_URL=https://slack.com/api
   ```

An `xoxc-` browser token also requires its matching `xoxd-` d cookie
(`SLACK_COOKIE`); both values must come from the same browser session. Bot
tokens (`xoxb-`) only need `SLACK_TOKEN`.

### Cache location

The default cache database lives at
`$XDG_CACHE_HOME/slack-cached/threads.db` (or `~/.cache/slack-cached/threads.db`).
Override with `--db /path/to/file.db`.

All commands accept `-v/--verbose` for debug logging on stderr, `--db` to
override the cache location, and `--api-base-url` to override the Slack API
base URL (defaults to `https://slack.com/api`; also settable via
`SLACK_API_BASE_URL`).

---

## Threads

### Cache or refresh a thread

`fetch` always reaches out to Slack. It prints only a summary on stderr; no
thread output goes to stdout.

```bash
slack-cached fetch https://acme.slack.com/archives/C0123ABCDEF/p1700000000123456
```

Or with explicit channel/ts:

```bash
slack-cached fetch --channel C0123ABCDEF --ts 1700000000.123456
```

### Show a cached thread

`show` prints a cached thread to stdout (human-readable by default). It
auto-fetches if the thread is missing; pass `--no-fetch` to disable that.

```bash
slack-cached show https://acme.slack.com/archives/C0123ABCDEF/p1700000000123456
slack-cached show --json https://acme.slack.com/archives/C0123ABCDEF/p1700000000123456
slack-cached show --jsonl --channel C0123ABCDEF --ts 1700000000.123456 >> threads.jsonl
```

Output formats:

- **human** (default): one block per message with timestamp, author, and text.
- **`--json`**: pretty-printed JSON with `channel`, `thread_ts`,
  `message_count`, and a `messages` array (each message carries its full Slack
  `payload`, including `reactions`).
- **`--jsonl`**: the whole payload as a single compact JSON line, easy to
  append to a file.

When the thread's authors are present in the cached users, `show` renders their
real name and handle (e.g. `Alice Smith (alice)`) instead of raw user ids. Run
`fetch-users` once to populate names.

---

## Channel messages

A channel URL (no message timestamp) or `--channel` alone fetches the channel's
recent history via `conversations.history`:

```bash
slack-cached fetch https://acme.slack.com/archives/C0B6CQN0G6B
slack-cached fetch --channel C0B6CQN0G6B
slack-cached show https://acme.slack.com/archives/C0B6CQN0G6B
slack-cached show --json https://acme.slack.com/archives/C0B6CQN0G6B
```

Control the lookback window with `--last` (e.g. `24h`, `2d5h30m`, `90m`;
default `1d`; use `all` for full history):

```bash
slack-cached fetch --channel C0B6CQN0G6B --last 7d
slack-cached show  --channel C0B6CQN0G6B --last 7d
```

Add `--full-threads` to also fetch every reply for messages that have replies:

```bash
slack-cached fetch --channel C0B6CQN0G6B --full-threads
slack-cached fetch --channel C0B6CQN0G6B --full-threads --last all
```

This works for enterprise grid workspaces too (e.g.
`https://acme.enterprise.slack.com/archives/C0B6CQN0G6B`).

---

## Search

Search the workspace with the same query syntax as the Slack search box. Every
matched message is cached under its `(channel, thread_ts)` so it can be
revisited later with `show`. Search is always a live API call.

```bash
slack-cached search "deploy failed"
slack-cached search "from:@alice after:2024-01-01" --json
slack-cached search "incident" --jsonl
```

Add `--full-threads` to also fetch every reply for each thread a match belongs
to:

```bash
slack-cached search "incident" --full-threads
```

Tune result paging and ordering with `--count`, `--sort` (`score` or
`timestamp`, default `timestamp`), and `--sort-dir` (`asc` or `desc`, default
`desc`):

```bash
slack-cached search "RFC" --count 5 --sort score --sort-dir asc
```

---

## Polling channels

Poll multiple channels concurrently for new messages. Uses `httpx.AsyncClient`
with an `asyncio.Semaphore` for concurrent, non-blocking HTTP requests. Reads
`X-RateLimit-Remaining` headers to proactively throttle before hitting 429s.
Stops gracefully with `Ctrl+C`.

```bash
slack-cached poll --channels C001,#general,random --interval 5m --last 5m --concurrency 3
```

Each `--channels` entry may be a channel id (e.g. `C001`), a bare name (e.g.
`general`), or a `#`-prefixed name (e.g. `#general`). Names are resolved
against the cached channels, so run `fetch-channels` first if resolving by
name.

Add `--full-threads` to expand threads, and `--json` to get per-cycle JSON
summaries on stdout.

---

## Users and channels

Cache or refresh every workspace user or visible channel:

```bash
slack-cached fetch-users
slack-cached fetch-channels
```

Show cached users or channels (human-readable by default, `--json` for pretty
JSON, `--jsonl` for a single compact JSON line; both auto-fetch when empty
unless `--no-fetch` is given):

```bash
slack-cached show-users
slack-cached show-channels --json
slack-cached show-channels --jsonl
```

---

## URL parsing

`slack-cached` accepts Slack archives URLs in these forms:

- `https://<workspace>.slack.com/archives/<CHANNEL_ID>` (channel, fetches
  history)
- `https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<PTS>` (thread, where
  `p<PTS>` is the timestamp with the dot removed)
- `https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<PTS>?thread_ts=<TS>`
  (a reply permalink; the thread root `ts` is taken from `thread_ts` so the
  whole thread is fetched)

When the URL points at a reply, the message timestamp in the path is the
reply's `ts`, and the actual thread root `ts` is in the `thread_ts` query
parameter. The tool returns the thread root so `conversations.replies` fetches
the entire thread.

For explicit channel ids without a URL, use `--channel <ID>` (optionally with
`--ts <TS>` for a single thread).

---

## Refresh behavior

`fetch` always reaches out to Slack. If the thread is already cached, it
requests `conversations.replies` with `oldest=<latest_cached_ts>` so the API
returns only new replies (and any recent edits at that boundary). Messages are
upserted by `ts`, so edits replace the older version in place.

For a channel URL, `fetch` requests `conversations.history` with
`oldest=<now - lookback>`, so only recent top-level messages are fetched. Each
top-level message is stored as its own thread root; messages with replies are
expanded via `conversations.replies` when `--full-threads` is given.

HTTP 429 / `ratelimited` responses are retried automatically with exponential
backoff (up to 5 attempts), respecting the `Retry-After` header.

---

## Fake Slack server (testing)

A built-in fake Slack API server for testing and development:

```bash
uv run slack-fake-server --port 8199 --num-threads 50
```

It serves deterministic workspace data (`conversations.list`,
`conversations.replies`, `conversations.history`, `users.list`) and can
simulate Slack-tier rate limiting with `--rate-limits`.

Point `slack-cached` at it with:

```bash
slack-cached --api-base-url http://localhost:8199/api fetch ...
```

---

## Tips

- Run `fetch-users` once at the start of a session so every later `show`
  renders author names instead of raw user ids.
- Use `show --json` when a consuming skill needs the full Slack payload (e.g.
  `reactions` on the root message for `slack-resolve-threads`).
- Use `show --jsonl` when appending many threads to a single file for batch
  processing.
- `show` auto-fetches on a cache miss, but an existing cached thread only
  refreshes on its reply boundary. Run an explicit `fetch` first when you need
  the current live state.
- Run `fetch-channels` before `poll` if you want to reference channels by name
  instead of id.
- For inline review comments or PR operations, use `ghx`, not this tool; this
  tool is Slack-only and read-only (no write/reaction path).

---

## Wrap up

After completing the user's request, summarise:

1. Which thread(s) or channel(s) were fetched or shown, and whether the cache
   was used or the API was called.
2. The output format used (human, `--json`, `--jsonl`).
3. Whether users/channels were cached (so author names render), if relevant.
