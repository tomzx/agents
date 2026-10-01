---
name: slackx
description: >
  Use the `slackx` CLI to cache and read Slack threads, channel history, DMs,
  users, and channels from a local SQLite database. It fetches threads via
  `conversations.replies`, channel history via `conversations.history`, and
  workspace users/channels, storing everything locally so subsequent reads are
  instant and incremental. Trigger when the user wants to read, cache, refresh,
  or poll a Slack thread or channel, render a thread with human-readable author
  names, search the workspace and cache matches, or says "slackx" explicitly.
  Other Slack skills (slack-resolve-threads,
  slack-kb-channel, slack-kb-individual) build on top of this tool.
cli: slackx
---

# slackx Skill

`slackx` is a small Python CLI (package name `slack-cached`) that caches Slack
threads, channel messages, DMs, users, and channels to a local SQLite database.
Given a Slack permalink (or a channel and root timestamp), it fetches the thread
via `conversations.replies` and stores every message. On subsequent runs it only
fetches new replies (and detects edits) by passing `oldest` to the API based on
the highest cached `ts`.

It is the single source of Slack thread content for the other Slack skills:
`slack-resolve-threads` reads threads through `slackx conversations show`, and
the knowledge-base skills use it to cache and render conversations.

---

## Command tree

The CLI is grouped into subcommands. The old flat commands (`fetch`, `show`,
`search`, `poll`, `fetch-users`, `fetch-channels`, `show-users`,
`show-channels`, `show-channel`) no longer exist.

```
slackx
  conversations   fetch | show | search | poll
  channels        fetch | list
  users           fetch | list
  cache           status | clear
  serve
```

Every command takes `--help` (or `-h`) and shows its own options and
positional arguments.

### Options live on the leaf command

`--db`, `--workspace`, `--api-base-url`, and `--log-level` are options on each
leaf command, not on `slackx` itself. Put them after the command:

```bash
slackx cache status --db /tmp/x.db --log-level debug
slackx users list --json --workspace acme
```

The equivalent environment variables (for example `SLACK_API_BASE_URL`) still
apply process-wide and are the easiest way to point every command at an
alternate API. There is no top-level `-v/--verbose`; use `--log-level`
(`debug`, `info`, `warning`, `error`, `critical`, default `info`).

---

## Prerequisites

### Binary

Check whether the binary is on PATH; install from the source repo if not:

```bash
if ! command -v slackx &>/dev/null; then
  git clone https://github.com/TomzxCode/slackx /tmp/slackx
  uv tool install /tmp/slackx
fi
```

The install provides two binaries, `slackx` and `slack-fake-server`. If
`uv tool install` isn't desired, run it in place with
`uv run --project /tmp/slackx slackx ...`. Confirm it works: `slackx --help`.

### Authentication

Credentials are loaded in this order:

1. A `.env` file in the current working directory, if present. Source it before
   invoking `slackx` so the variables become real environment variables:
   ```bash
   if [[ -f .env ]]; then
     set -a
     source .env
     set +a
   fi
   ```
   The file uses `KEY=VALUE` lines (same keys as below). Existing environment
   variables always win over `.env` values, so explicit exports or CI secrets
   are never overridden.
2. Environment variables: `SLACK_TOKEN` (and optional `SLACK_COOKIE` for
   xoxc/web-client tokens).
3. A config file at `$XDG_CONFIG_HOME/slackx/config`
   (defaults to `~/.config/slackx/config`).
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

Each Slack workspace gets its own cache database at
`$XDG_CACHE_HOME/slackx/<workspace>/threads.db` (or
`~/.cache/slackx/<workspace>/threads.db`). The workspace is discovered
automatically via `auth.test`; select one explicitly with `--workspace <name>`,
or point at a specific file with `--db /path/to/file.db`.

---

## Targeting a conversation

`conversations fetch` and `conversations show` take a `TARGET` positional that
is one of:

- a Slack permalink (thread or channel),
- a channel id (`C...`, `G...`, `D...`), a channel name (e.g. `general`), or a
  `#`-prefixed name (e.g. `#general`),
- a DM, given a user id (e.g. `U001`) or an `@handle`.

Add `--ts <root_ts>` to read a specific thread from a channel or DM target.
Without `--ts`, the command operates on the channel's recent messages.

Run `slackx channels fetch` first if you want to resolve channels by name, and
`slackx users fetch` to resolve `@handle` DMs.

---

## Conversations

### Fetch (cache or refresh)

`conversations fetch` always reaches out to Slack. It prints a summary; the
summary and logs go to stderr, and no conversation output goes to stdout.

```bash
# a thread by permalink
slackx conversations fetch https://acme.slack.com/archives/C0123ABCDEF/p1700000000123456

# a thread by channel and ts
slackx conversations fetch C0123ABCDEF --ts 1700000000.123456

# recent channel messages (lookback defaults to 1d)
slackx conversations fetch C0123ABCDEF
slackx conversations fetch C0123ABCDEF --last 7d

# every reply for every thread in the channel
slackx conversations fetch C0123ABCDEF --full-threads --last all
```

`--last` accepts `24h`, `2d5h30m`, `90m`, or `all` for full history.

### Show (read from cache)

`conversations show` prints a thread or channel to stdout (human-readable by
default). It auto-fetches when not already cached; pass `--no-fetch` to read
only the cache.

```bash
slackx conversations show https://acme.slack.com/archives/C0123ABCDEF/p1700000000123456
slackx conversations show --json https://acme.slack.com/archives/C0123ABCDEF/p1700000000123456
slackx conversations show C0123ABCDEF --ts 1700000000.123456 --jsonl >> threads.jsonl
slackx conversations show C0123ABCDEF --last all
slackx conversations show C0123ABCDEF --last all --with-thread-message
```

Options:

- `--fetch/--no-fetch`: auto-fetch on a cache miss (default on).
- `--json`: pretty-printed JSON.
- `--jsonl`: the whole payload as a single compact JSON line, easy to append to
  a file.
- `--with-thread-message`: when showing a channel, also include thread replies,
  rendered marked as belonging to their thread (default is top-level messages
  only).
- `--last`: channel lookback window (default `1d`).

Output shapes:

- **thread `--json`**: keys `channel`, `channel_name`, `thread_ts`,
  `message_count`, `messages`. Each message carries `ts`, `user`, `text`,
  `user_name`, and the full Slack `payload` (including `reactions`).
- **channel `--json`**: keys `channel`, `channel_name`, `message_count`,
  `messages`. Each message carries `ts`, `user`, `text`, `thread_ts`,
  `is_thread_reply`, `user_name` (no full `payload`).
- **human**: one block per message with timestamp, author, and text.

When the thread's authors are present in the cached users, `show` renders their
real name and handle (e.g. `Alice Smith (alice)`) instead of raw user ids. Run
`slackx users fetch` once to populate names.

### Search

Search the workspace with the same query syntax as the Slack search box. Every
matched message is cached under its `(channel, thread_ts)` so it can be
revisited later with `show`. Search is always a live API call.

```bash
slackx conversations search "deploy failed"
slackx conversations search "from:@alice after:2024-01-01" --json
slackx conversations search "incident" --jsonl
slackx conversations search "incident" --full-threads
```

Options:

- `--count`: maximum results per page (default 20).
- `--limit`: maximum total matches to fetch (default 200; `0` for no limit).
  Broad queries can span hundreds of pages, so the cap keeps them from taking a
  very long time under Slack's rate limits.
- `--sort` (`score` or `timestamp`, default `timestamp`) and `--sort-dir`
  (`asc` or `desc`, default `desc`).
- `--full-threads`: also fetch every reply for each matched thread.
- `--fields`: comma-separated fields to include, in order:
  `channel,channel_name,ts,thread_ts,user,user_name,text,permalink,payload`
  (default `channel,channel_name,ts,thread_ts,user,user_name,text,permalink`).
- `--json` / `--jsonl`.

`after:` and `before:` are exclusive date bounds. To search a single day
(e.g. `2026-09-18`), bracket it with the day before and the day after:
`after:<prev-day> before:<next-day>`, since `after:2026-09-18` would exclude
that day itself.

```bash
slackx conversations search "after:2026-09-17 before:2026-09-19" --json
```

The `--json` payload has keys `query`, `match_count`, `matches`, where each
match carries the configured fields.

### Poll

Poll multiple channels concurrently in a loop for new messages. Uses
`httpx.AsyncClient` with an `asyncio.Semaphore` for concurrent, non-blocking
HTTP requests. Reads `X-RateLimit-Remaining` headers to proactively throttle
before hitting 429s. Stops gracefully with `Ctrl+C`.

```bash
slackx conversations poll --channels C001,#general,random --interval 5m --last 5m --concurrency 3
```

`--channels` is required. Each entry may be a channel id, a bare name, or a
`#`-prefixed name. Names are resolved against cached channels, so run
`slackx channels fetch` first if resolving by name. Add `--full-threads` to
expand threads, and `--json` for per-cycle JSON summaries on stdout.

---

## Channels

Cache or refresh every visible channel, or a single channel by id or name:

```bash
slackx channels fetch
slackx channels fetch C001
```

Print cached channels (human-readable by default, `--json` for pretty JSON,
`--jsonl` for a single compact JSON line). Pass a channel id, name, or URL to
show only that channel; it is fetched from Slack via `conversations.info` when
not cached, unless `--no-fetch` is given.

```bash
slackx channels list
slackx channels list C001 --json
slackx channels list general --jsonl
slackx channels list https://acme.slack.com/archives/C001
```

Options: `--fetch/--no-fetch`, `--limit` (0 for all), and `--fields`
(`id,name,is_private,display_name,fetched_at,payload`, default
`id,name,is_private`). The `--json` payload has keys `channel_count` and
`channels`.

Unknown or inaccessible channels surface a clean `channel_not_found` error
(exit code 1) rather than a traceback.

---

## Users

Cache or refresh every workspace user, or a single user by id:

```bash
slackx users fetch
slackx users fetch U001
```

Print cached users (human-readable by default). Pass a user id to show only
that user; it is fetched from Slack via `users.info` when not cached, unless
`--no-fetch` is given.

```bash
slackx users list
slackx users list --json
slackx users list --jsonl
slackx users list U001 --json
```

Options: `--fetch/--no-fetch`, `--limit` (0 for all), and `--fields`
(`id,name,real_name,fetched_at,payload`, default `id,name,real_name`). The
`--json` payload has keys `user_count` and `users`.

---

## Cache management

Inspect and clear the local cache without calling Slack.

```bash
slackx cache status
slackx cache status --json
slackx cache status --jsonl
```

`cache status` prints counts and last update per entity (channels, users,
threads, messages).

```bash
slackx cache clear                 # asks for confirmation on a TTY
slackx cache clear messages
slackx cache clear channels --yes
slackx cache clear users -y
slackx cache clear all --yes
```

`cache clear` takes an optional `TARGET` of `all` (default), `messages`,
`channels`, or `users`, and `--yes/-y` to skip the confirmation prompt.
Clearing messages also clears their thread metadata, so the threads are
refetched on next use.

---

## Web UI

Browse the cached database through a local Slack-like web UI (Ctrl+P jumps
between channels and conversations; refresh buttons trigger live fetches when
credentials are configured):

```bash
slackx serve --port 8280
slackx serve --host 0.0.0.0 --port 8280
```

---

## URL parsing

`slackx` accepts Slack archives URLs in these forms:

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

For explicit channel ids without a URL, pass the channel id as the target
(optionally with `--ts <TS>` for a single thread).

---

## Refresh behavior

`conversations fetch` always reaches out to Slack. If the thread is already
cached, it requests `conversations.replies` with `oldest=<latest_cached_ts>` so
the API returns only new replies (and any recent edits at that boundary).
Messages are upserted by `ts`, so edits replace the older version in place.

For a channel target, `fetch` requests `conversations.history` with
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
`conversations.replies`, `conversations.history`, `conversations.info`,
`users.list`) and can simulate Slack-tier rate limiting with `--rate-limits`.
Other options include `--host`, `--seed`, `--num-users`, `--num-channels`,
`--num-ims`, `--messages-per-thread`, `--activity-ratio`, and `--epoch-base`.

Point `slackx` at it with the API base URL option on the leaf command (or the
environment variable):

```bash
slackx conversations fetch C001 --api-base-url http://localhost:8199/api
```

---

## Tips

- Run `slackx users fetch` once at the start of a session so every later `show`
  renders author names instead of raw user ids.
- Use `conversations show --json` on a thread when a consuming skill needs the
  full Slack `payload` (e.g. `reactions` on the root message for
  `slack-resolve-threads`).
- Use `--jsonl` when appending many threads to a single file for batch
  processing.
- `show` auto-fetches on a cache miss, but an existing cached thread only
  refreshes on its reply boundary. Run an explicit `conversations fetch` first
  when you need the current live state.
- Run `slackx channels fetch` before `conversations poll` if you want to
  reference channels by name instead of id.
- For inline review comments or PR operations, use `ghx`, not this tool; this
  tool is Slack-only and read-only (no write/reaction path).

---

## Wrap up

After completing the user's request, summarise:

1. Which thread(s) or channel(s) were fetched or shown, and whether the cache
   was used or the API was called.
2. The output format used (human, `--json`, `--jsonl`).
3. Whether users/channels were cached (so author names render), if relevant.
