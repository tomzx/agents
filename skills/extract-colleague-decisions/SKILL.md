---
name: extract-colleague-decisions
description: >-
  Search Slack for messages a set of colleagues authored on a given day, read the
  full threads behind them, and extract the decisions each of them made plus who
  supported them, filtering out the chatter and citing permalinks. Use this to
  catch up on what changed across a team without reading every thread, or when
  asked "what decisions were made today", "what did <people> decide", "what did
  my colleagues decide yesterday", or to build a daily decisions digest. Reads the
  colleague list from the COLLEAGUES env var and searches with the slackx CLI.
argument-hint: "[YYYY-MM-DD | yesterday (default: today)]"
---

# Colleague Decisions

Answers a recurring question: *"What did my colleagues actually decide today?"*
A day of Slack produces a sea of messages, most of them chatter, acknowledgements,
and questions, with a handful of real decisions buried inside. This skill searches
Slack for each colleague's authored messages in a day, then reads them and pulls
out the decisions, so you can catch up on what changed without reading every thread.

The judgement is the point: telling a decision from chatter is a reading task, not
a keyword match. `slackx search` only gets the messages in front of you; you decide
what counts.

## Prerequisites

- `SLACK_TOKEN` (and `SLACK_COOKIE` for xoxc/web tokens) in `.env`, found by
  searching up from the working directory. Source it before invoking `slackx`.
- `COLLEAGUES` in `.env`: a comma-separated list of Slack usernames (e.g.
  `alice.smith,bob.jones`). Resolve it with
  `~/.agents/scripts/get-env COLLEAGUES`.
- `slackx` on PATH; install if missing:
  ```bash
  if ! command -v slackx &>/dev/null; then
    git clone https://github.com/TomzxCode/slackx /tmp/slackx
    uv tool install /tmp/slackx
  fi
  ```
- `jq` for filtering the search JSON.

## Workflow

### 1. Resolve inputs

Determine the target day: the argument if given (`YYYY-MM-DD` or `yesterday`),
otherwise today. Compute the window (see the slackx skill for why Slack's day
operators are bracketed this way):

```bash
TARGET=2026-09-18                       # or: date +%Y-%m-%d
PREV=$(date -d "$TARGET - 1 day" +%Y-%m-%d)
NEXT=$(date -d "$TARGET + 1 day" +%Y-%m-%d)
```

Resolve the colleagues and source credentials:

```bash
set -a; source .env; set +a
COLLEAGUES=$(~/.agents/scripts/get-env COLLEAGUES)
```

If `COLLEAGUES` is empty, stop and tell the user to set it. Do not guess handles.

### 2. Resolve handles to real names (recommended)

Slack usernames do not always match the email prefix (e.g. `alice.smith`'s handle
is `alice`). If a search comes back empty, confirm the handle exists before
concluding the person was silent:

```bash
slackx show-users --json --no-fetch \
  | jq -r '.users[] | select(.name=="<handle>") | "\(.name) | \(.real_name) | \(.payload.profile.email)"'
```

`--no-fetch` reads the cache; drop it (or run `slackx fetch-users` once) to refresh.
If a handle does not resolve, say so and ask the user for the correct one.

While you are here, build a handle-to-real-name map and use the **real name**
everywhere in the report (section headings, `Supported by` lists, headlines).
Mixing handles and real names splits one person into two entries in the
aggregated web page (e.g. `Tom Rochette` and `tom.rochette`):

```bash
slackx fetch-users   # refresh once so the cache is complete
slackx show-users --json --no-fetch \
  | jq -r '.users[] | "\(.name)\t\(.real_name // .payload.profile.real_name // .name)"'
```

Name each person by the second column. If a real name is empty, fall back to the
handle. For a name you cannot resolve, at least normalize it the same way every
time rather than writing a handle in one place and a real name in another.

### 3. Search each colleague's messages for the day

`slackx search` is the only tool used to find messages. Search is a live API call.
Run one search per colleague and save the JSON, using `--fields` to keep only the
fields this skill needs. The available fields are `channel`, `channel_name`,
`ts`, `thread_ts`, `user`, `user_name`, `text`, `permalink`, and `payload`; the
default omits only `payload`, so selecting explicitly drops the rest. We keep
`ts` (ordering), `channel`/`channel_name`, `text`, and `permalink`; we drop
`user`/`user_name` (we already know whose messages these are) and `payload`
(the large raw Slack object).

Pass `--full-threads` so that every thread a matched message belongs to is cached
with all of its replies. A colleague's top-level message is often just the start
of the story: the decision, the pushback, and the endorsements all live in the
replies, and without them the extraction misses support. `--full-threads` makes
that content available to `slackx show` in the next step:

```bash
mkdir -p /tmp/extract-colleague-decisions
echo "$COLLEAGUES" | tr ',' '\n' | while read -r c; do
  slackx search "from:@${c} after:${PREV} before:${NEXT}" \
    --count 200 --full-threads \
    --fields ts,channel,channel_name,text,permalink --json 2>/dev/null \
    > "/tmp/extract-colleague-decisions/${c}.json"
done
```

Each `matches[]` entry is top-level (not nested under `payload`). A readable dump
is:

```bash
jq -r '.matches | sort_by(.ts)[]
  | "[\(.ts)] #\(.channel_name // .channel)\n\(.text)\n\(.permalink)\n---"' \
  "/tmp/extract-colleague-decisions/${c}.json"
```

For many colleagues, fan out one subagent per person so the searches and reads run
in parallel, then merge the per-person findings yourself.

### 4. Read the threads behind each message

A message rarely stands alone. The decision is often stated in a reply, the
support ("endorse", "+1", "go ahead") is posted by someone else further down the
thread, and the reasoning is in between. Before classifying anything, pull the
full thread for every message that has one so the whole conversation is in front
of you.

`--full-threads` on the search already cached every reply, so `slackx show`
serves them from the cache. Run `slackx fetch-users` once first so `show` renders
each author as a name and handle (e.g. `Alice Smith (alice)`) rather than a raw
user id, which is what the **Supported by** list needs:

```bash
# Optional but recommended: resolve author names for the thread renders.
slackx fetch-users

# Read the whole thread behind one message (auto-fetches if not cached).
slackx show "<permalink>"
```

Use `show --json` instead when you want to process many threads programmatically;
it returns a `messages` array but authors appear as raw `user` ids, so resolve
them with `slackx show-users --json`. To batch the human-readable reads, collect
the permalinks and loop:

```bash
jq -r '.matches[].permalink' "/tmp/extract-colleague-decisions/${c}.json" \
  | sort -u \
  | while read -r url; do
      slackx show "$url" >> "/tmp/extract-colleague-decisions/${c}.threads.md"
    done
```

A thread comes back as the root message followed by its replies in order, each
with its own author and text (in `--json`, that is `messages[0]` and the rest of
the `messages` array). Treat the thread as one unit of evidence: read the root
plus every reply in order before deciding what it says.

If a colleague's message has no thread, `show` returns just that one message,
which is fine. Keep the thread JSON alongside the search JSON in
`/tmp/extract-colleague-decisions/` so a later question can be answered without
re-fetching.

### 5. Extract the decisions

Read each colleague's messages in chronological order and classify every message.
Include the thread replies: a decision or endorsement may have been posted as a
reply rather than a top-level message.

A message is decision-bearing when it does any of the following:

- States an intent or choice ("Let's do X", "I'll go with B", "we're dropping Y").
- Names a trade-off and picks a side ("A over B because…").
- Endorses or rejects a proposal ("Endorse", "I'm in favor of…", "recommend
  against…", "too broad", "should not").
- Grants an approval or authorization ("you can proceed", "I approve", "go ahead").
- Records a constraint or non-goal ("must not be managed by us", "we will not…").
- Commits someone to an action ("I'll take a look", "I'll send the PR", who does
  what by when).
- Reports a result that closes a loop ("confirmed the fix works", "merged", "no
  longer need X").
- Opens a concrete question that changes the plan (an open question, not idle
  curiosity).

Ignore: greetings, thanks, reactions-as-words, jokes, pure acknowledgements
("sounds good", "lol"), logistics ("cancel today's 1:1"), and questions that got
no substantive answer.

Cluster each person's decision-bearing messages into four buckets:

- **Decisions made**: the choice and the one-line reasoning.
- **Decisions deferred**: explicitly pushed to a follow-up, next sprint, or "later".
- **Open questions**: raised, affecting the work, not yet answered.
- **Commitments**: who said they would do what (even loosely).

Attribute every item to a person. When several people converge on one decision,
say so rather than listing it repeatedly.

Also track **support**: an endorsement, approval, or seconding of someone else's
decision ("endorse", "I'm in favor", "you can proceed", "go ahead", "+1 on this
one"). A message can both make a decision and support another. For each decision,
record the people who supported it, excluding the decision's author. Support from
a colleague outside `COLLEAGUES` counts too; use the name as it appears in the
message. This is what lets the aggregated web page answer *"who backed this?"*.

Most support lives in the thread replies, not in the messages you searched for,
so mine the threads from step 4 for it: a reply by someone other than the author
that endorses, approves, or seconds a decision attaches that person to the
decision's **Supported by** list. A reply can also carry its own decision or
commitment; attribute it to the reply's author and file it in that person's
section, even if they are outside `COLLEAGUES`.

### 6. Write the report

Write the report to a Markdown file, then summarize it to the user in chat. One
section per colleague, most decision-dense first (or in `COLLEAGUES` order if the
user prefers). Start with a one-line headline per person, then the buckets.
Always include the permalink for each decision so the user can jump to it. Skip
people with no decision-bearing messages, but list them once at the end so the
user knows they were checked.

Name every person by their Slack **real name** (resolved in step 2), both for
section headings and in `Supported by` lists. Do not write a handle in one place
and a real name in another: that is what makes the same person show up twice in
the web page's matrix and sidebar.

The output path follows the same layout as the other summary skills:

```
{BASE_DIR}/decisions/{YEAR}/{MONTH}/{DAY}.md
```

where `{BASE_DIR}` is `~/.agents/scripts/get-env NOTES_DIR`, and `{YEAR}`,
`{MONTH}`, `{DAY}` are derived from the target day. Create any missing
directories. Write the file at the end of the run, then report the path to the
user.

```markdown
# Colleague decisions — <TARGET>

Searched N colleagues over <TARGET> (window after:<PREV> before:<NEXT>).
<M> authored messages, <K> decision-bearing.

## <name>
**Headline:** <the single most important thing they decided, if any>
- **Decided:** <choice>. <reason>  <permalink>
  - **Supported by:** <name1>, <name2>
- **Deferred:** <what> (<why/when>).  <permalink>
- **Open:** <question>.  <permalink>
- **Committed:** <who> to <do what>.  <permalink>

## Not heard from (no decisions)
- <name1>, <name2>

## Cross-cutting
<Optional: the same decision reached by multiple people, or themes across people.>
```

The `**Supported by:**` line is optional and indented under the decision it backs;
omit it when nobody supported the item. Keep names comma-separated, without a
leading `@`. This layout is parsed by `scripts/colleague_decisions_page.py`, so
keep the `**Decided:**`/`**Deferred:**`/`**Open:**`/`**Committed:**` labels and the
indentation exactly as shown.

### 7. Render the aggregated web page (optional)

After writing today's report, you can refresh a single page that aggregates *every*
report, so the whole decision history is browsable in one place. This reads the
files on disk only (no Slack calls) and is safe to re-run anytime:

```bash
uv run ~/.agents/scripts/colleague_decisions_page.py
```

It scans `NOTES_DIR` for `decisions/YYYY/MM/DD.md` reports and writes
`{NOTES_DIR}/colleague-decisions.html`, a self-contained page (no server, no
network) showing each decision, who made it, and who supported it. It relies on
the report using consistent names (see step 2): a person written once as a handle
and once as a real name shows up twice. The page has views by author, by
supporter, and a support matrix (click a cell to list the decisions for that
author/supporter pair), plus in-page filters for date
range (from/to inputs and 7/30/90-day presets) and status (Decided/Deferred/Open/
Committed), and a sidebar to jump to a person. Pass `--open` to launch it, or
`--since`/`--until` to bake a narrower date range into the page. Report the HTML
path to the user.

## Example Usage

**Scenario 1: Today**
```
/extract-colleague-decisions
```
Searches all `COLLEAGUES` for today, extracts decisions, writes
`{NOTES_DIR}/decisions/2026/09/18.md`, and prints the path.

**Scenario 2: A specific day**
```
/extract-colleague-decisions 2026-09-18
```
Brackets the day with `after:2026-09-17 before:2026-09-19` and writes the report
to `{NOTES_DIR}/decisions/2026/09/18.md`.

**Scenario 3: Quiet day**
```
/extract-colleague-decisions yesterday
```
No decision-bearing messages. The file still gets written with "No decisions
found" and everyone listed under "Not heard from".

## Useful Commands Reference

| Command | Description |
|---|---|
| `~/.agents/scripts/get-env COLLEAGUES` | Resolve the comma-separated colleague list |
| `~/.agents/scripts/get-env NOTES_DIR` | Resolve the notes directory for optional persistence |
| `slackx search "from:@<handle> after:<PREV> before:<NEXT>" --count 200 --full-threads --fields ts,channel,channel_name,text,permalink --json` | Find a colleague's messages for the day and cache every thread they belong to |
| `slackx show "<permalink>"` | Read the full thread behind a message, with author names resolved (use `--json` for raw structure) |
| `slackx fetch "<permalink>"` | Force a live refresh of a thread when the cache may be stale |
| `slackx show-users --json --no-fetch` | Confirm a handle resolves to a user |
| `slackx fetch-users` | Refresh the cached user list so thread authors render as names |
| `date -d "$TARGET - 1 day" +%Y-%m-%d` | Compute the exclusive lower bound |
| `date -d "$TARGET + 1 day" +%Y-%m-%d` | Compute the exclusive upper bound |
| `uv run ~/.agents/scripts/colleague_decisions_page.py [--open] [--since D] [--until D]` | Aggregate every report into a static decisions web page |

## Notes on cost and safety

- Each colleague is one live search, and `--full-threads` expands every thread a
  match belongs to, so a busy day costs more API calls than the message count
  suggests. This is read-only; the skill never writes to Slack.
- `--count 200` is the practical per-query ceiling. If a person hits it, narrow the
  window (split the day) rather than assuming you saw everything.
- Keep the per-person search and thread JSON in
  `/tmp/extract-colleague-decisions/` during the run so a later question about a
  specific person or thread can be answered without re-searching.
- Threads are the source of support. If you skip step 4, the report's
  **Supported by** lists will be empty or incomplete.
