---
name: slack-vision-monitor
description: Monitor configured Slack channels and tracked colleagues for messages that conflict with the team's stated vision. Builds a knowledge base of facts from conversations and flags misalignment with a draft response ready to post.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
NOW=`date +%Y-%m-%dT%H:%M:%S`

# Slack Vision Monitor

Processes recent Slack messages from monitored channels and tracked colleagues, accumulates a knowledge base of facts, and immediately flags any conversation that conflicts with the stated team vision. Designed to run every 5 minutes via `/loop 5m /slack-vision-monitor`.

## Prerequisites

- Slack MCP server connected and authenticated
- `NOTES_DIR` environment variable set (resolved via `scripts/get-env NOTES_DIR`)
- Config file at `{BASE_DIR}/slack-vision-monitor/config.md` (see Config Format below)
- Vision file at the path specified in config

## State Files

| File | Purpose |
|------|---------|
| `{BASE_DIR}/slack-vision-monitor/last-run.txt` | ISO timestamp of the previous successful run |
| `{BASE_DIR}/slack-vision-monitor/knowledge-base.md` | Accumulated facts extracted from messages |
| `{BASE_DIR}/slack-vision-monitor/flags.md` | Flagged conversations with draft responses |
| `{BASE_DIR}/slack-vision-monitor/colleagues/{username}.md` | Per-colleague misalignment history |

## Config Format

`{BASE_DIR}/slack-vision-monitor/config.md`:

```markdown
# Slack Vision Monitor Config

## Vision File

/path/to/vision.md

## Monitored Channels

- channel-name-1
- channel-name-2
- channel-name-3

## Tracked Colleagues

- slack-username-1
- slack-username-2

## Watch Phrases

- exact phrase or keyword
- another term
```

**Monitored channels**: channels the agent fetches messages from directly.

**Tracked colleagues**: people whose messages are fetched from any channel they post in (catches conversations happening in channels you are not monitoring). Use this for key stakeholders whose alignment matters most.

**Watch phrases**: terms searched workspace-wide regardless of channel or author. Use these to catch specific topics, technology names, competitor names, or buzzwords that warrant attention anywhere they appear. Each match pulls the full thread into the vision alignment check. Phrase matches are also surfaced directly in the report even when no vision conflict is found, so you stay aware of where those topics are being discussed.

## Steps

### 1. Load Config and State

Read `{BASE_DIR}/slack-vision-monitor/config.md`. Extract:
- `VISION_FILE`: path on the first non-blank line under `## Vision File`
- `CHANNELS`: list of channel names under `## Monitored Channels`
- `COLLEAGUES`: list of Slack usernames under `## Tracked Colleagues`
- `WATCH_PHRASES`: list of terms under `## Watch Phrases` (empty list if section absent)

Read `{BASE_DIR}/slack-vision-monitor/last-run.txt` if it exists. Store as `LAST_RUN`. If the file does not exist, default `LAST_RUN` to 5 minutes ago (`{NOW}` minus 5 minutes).

Read the vision file at `VISION_FILE`. If it does not exist, abort with a clear error message telling the user to create it.

Read `{BASE_DIR}/slack-vision-monitor/knowledge-base.md` if it exists.

Read `{BASE_DIR}/slack-vision-monitor/flags.md` if it exists.

For each colleague in `COLLEAGUES`, read `{BASE_DIR}/slack-vision-monitor/colleagues/{username}.md` if it exists.

### 2. Fetch Messages

Use the Slack MCP server to fetch messages posted after `LAST_RUN`.

**Per monitored channel**: fetch all messages in that channel since `LAST_RUN`. Include thread replies. Collect sender, timestamp, channel, text, thread URL.

**Per tracked colleague**: search for messages by that user across all channels since `LAST_RUN`. Include thread replies they authored. Collect the same fields. Skip any messages already collected from monitored channels to avoid duplicates.

**Per watch phrase**: for each phrase in `WATCH_PHRASES`, run a workspace-wide Slack search restricted to messages since `LAST_RUN`. Fetch the full thread for each matching message. Tag each result with the phrase(s) that triggered it. Skip any messages already collected from channels or colleague searches to avoid duplicates. A single message may match multiple phrases; record all matching phrases against it.

If a channel does not exist or you lack access, log a warning and continue with the remaining channels.

### 3. Extract Facts

For each collected message, extract any factual claims, decisions, plans, or opinions that are worth remembering. Focus on:
- Technical decisions or architectural choices
- Process changes or proposals
- Team or project direction statements
- Commitments, deadlines, or agreements
- Strong opinions that others might reference later

Discard messages with no extractable facts (e.g. emoji reactions described in text, "thanks", "lgtm", pure small talk).

Format each fact as:

```
- [{ISO_TIMESTAMP}] @{sender} in #{channel}: {concise fact statement}
```

### 4. Update Knowledge Base

Append new facts to `{BASE_DIR}/slack-vision-monitor/knowledge-base.md` under a `## {TODAY}` heading (create the heading if it does not exist for today). Do not re-extract facts already present in the knowledge base.

Knowledge base format:

```markdown
# Knowledge Base

## {YYYY-MM-DD}

- [{ISO_TIMESTAMP}] @{sender} in #{channel}: {fact}

## {YYYY-MM-DD}

- ...
```

### 5. Check Vision Alignment

Read the vision file. For each collected message (not just the extracted facts, but the full conversation thread), determine whether the message or thread:

- **Directly contradicts** a stated vision principle (highest priority, always flag)
- **Proposes a direction** that conflicts with the vision (flag)
- **Makes a decision** that diverges from the vision without acknowledging the divergence (flag)

Do NOT flag:
- Messages that question the vision constructively (healthy debate)
- Messages that are unrelated to the vision topics
- Messages that express uncertainty or ask for clarification
- Automated messages, bots, or CI/CD notifications

For each flagged item, record:
- Channel and thread URL
- Sender(s) involved
- The specific vision principle being contradicted
- A brief explanation of the conflict (1-2 sentences)
- A draft reply message suitable for posting in that thread

### 6. Write Flags and Update Colleague Histories

If new flags were found, append them to `{BASE_DIR}/slack-vision-monitor/flags.md`:

```markdown
# Vision Alignment Flags

## {ISO_TIMESTAMP} — #{channel}

**Thread**: {thread URL}
**Participants**: @{sender1}, @{sender2}
**Vision principle**: {the principle from the vision file, quoted briefly}
**Conflict**: {1-2 sentence explanation of what contradicts the vision}

**Draft reply**:
> {ready-to-post message that cites the vision and invites alignment, written in a collaborative, non-confrontational tone}

---
```

For each flag that involves a tracked colleague, append a row to that colleague's history file at `{BASE_DIR}/slack-vision-monitor/colleagues/{username}.md`. Create the file with a header if it does not exist.

Colleague history format:

```markdown
# Misalignment History: @{username}

| Timestamp | Channel | Summary |
|-----------|---------|---------|
| {ISO_TIMESTAMP} | #{channel} | {one-line summary of the conflict} |
```

Append new rows in chronological order. Do not modify existing rows. Each row captures when and where the misalignment occurred and a brief description specific enough to be useful without re-reading the full flags file.

### 7. Report to User

After processing, output a concise summary:

```
Slack Vision Monitor — {NOW}
Checked since: {LAST_RUN}

Messages scanned: {total count}
Facts added to knowledge base: {count}
Vision conflicts flagged: {count}
Phrase matches: {count} across {N} phrase(s)
```

If any conflicts were flagged, list each one with its channel, a one-line description of the conflict, and remind the user that draft replies are in `{BASE_DIR}/slack-vision-monitor/flags.md`.

If any flagged conflicts involved tracked colleagues, list each affected colleague and their total misalignment count (from their history file), e.g. `@alice — 3 total misalignments (colleagues/alice.md)`.

If any watch phrase produced matches (even without a vision conflict), list each phrase alongside the channel(s) and sender(s) where it appeared so the user is aware of where those topics surfaced.

If no conflicts and no phrase matches were found, say so clearly.

### 8. Update Last-Run Timestamp

Write `{NOW}` to `{BASE_DIR}/slack-vision-monitor/last-run.txt`, overwriting the previous value.

## Vision File Format

The vision file can be in any format the user prefers. Recommended structure:

```markdown
# Team Vision

## Core Principles

- {principle 1}
- {principle 2}

## Technical Direction

- {decision or direction}

## Ways of Working

- {process or culture norm}

## Anti-Patterns

Things we explicitly want to avoid:
- {anti-pattern 1}
- {anti-pattern 2}
```

The more explicit the vision file, especially the **Anti-Patterns** section, the more precisely the agent can detect conflicts.

## Example Usage

**Scenario 1: Regular 5-minute run, no conflicts**
Run via `/loop 5m /slack-vision-monitor`. 12 messages scanned across 3 channels and 2 colleagues. 3 facts added to the knowledge base. No conflicts. Last-run timestamp updated.

**Scenario 2: Conflict detected**
A colleague posts in #architecture proposing a new service that contradicts the stated "monolith-first" principle. The agent flags it, records the conflict, and drafts a reply citing the vision and asking the team to revisit the decision together.

**Scenario 3: Colleague tracked across channels**
A tracked colleague posts in #sales-engineering (a channel not in the monitored list) advocating for a vendor tool the vision explicitly rules out. Because the colleague is tracked, the message is caught and flagged even though the channel is not monitored directly.

**Scenario 4: Colleague with repeat misalignments**
A tracked colleague @bob has been flagged twice before. On this run he posts again in #infrastructure contradicting the "no new cloud vendors without an RFC" principle. The agent appends a third row to `colleagues/bob.md` and the summary reports `@bob — 3 total misalignments`. The history file gives a quick audit trail without having to scan all flags.

**Scenario 5: Watch phrase match, no vision conflict**
The phrase "big rewrite" appears in #backend-guild. The thread is a casual discussion and does not contradict any vision principle. No flag is raised, but the report lists `"big rewrite" — #backend-guild (@carol, @dave)` so the user knows the topic is circulating and can decide whether to engage.

**Scenario 6: Watch phrase match triggers a flag**
The phrase "switch to Kubernetes" appears in a DM group channel not otherwise monitored. The vision explicitly says "no new infrastructure complexity without an architecture review." The thread is flagged, a draft reply is written, and the match is credited to both the phrase trigger and the vision conflict in the report.

**Scenario 7: First run (no last-run file)**
No `last-run.txt` exists. The agent defaults to the last 5 minutes and processes whatever messages fall in that window. This is intentionally conservative to avoid processing a flood of historical messages on first run.

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `date +%Y-%m-%dT%H:%M:%S` | Current timestamp in ISO format |
| `date -d "5 minutes ago" +%Y-%m-%dT%H:%M:%S` | Timestamp 5 minutes ago |
| `/loop 5m /slack-vision-monitor` | Run this skill every 5 minutes |
