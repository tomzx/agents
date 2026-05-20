---
name: end-of-day-summary
description: Summarize GitHub activity, Slack activity, and overall activity for the day, then generate a standup for the next day.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=!`date +%Y-%m-%d`
YESTERDAY=!`date -d "yesterday" +%Y-%m-%d`
TOMORROW=!`date -d "tomorrow" +%Y-%m-%d`
YEAR=!`date +%Y`
MONTH=!`date +%m`
DAY=!`date +%d`
NEXT_WORKDAY=!`date -d "$([ $(date +%u) -ge 5 ] && echo "next Monday" || echo "tomorrow")" +%Y-%m-%d`

# Generate End-of-Day Summary

Produces structured summaries of GitHub and Slack activity for the current day, an overall accomplishments/blockers report, a timeline, and a standup draft for the next workday.

## Prerequisites

- `SLACK_TOKEN`, `SLACK_COOKIE`, and `SLACK_USER` in `.env` (same credentials used by `collect_individual_threads.py`)
- `gh` CLI authenticated
- `summarize-github-activity` script at `$HOME/repos/git/personal-automation/others/summarize-github-activity`
- `NOTES_DIR` environment variable set (resolved via `scripts/get-env NOTES_DIR`)
- `SLACK_USER` environment variable set (resolved via `scripts/get-env SLACK_USER`; Slack username, e.g. `tom.rochette`)
- `scripts/get-env` utility available

## Pipeline

```
GitHub Activity --> {BASE_DIR}/{YEAR}/{MONTH}/{DAY}.github.md
Slack Activity  --> {BASE_DIR}/{YEAR}/{MONTH}/{DAY}.slack.md
Overall Summary --> {BASE_DIR}/{YEAR}/{MONTH}/{DAY}.overall.md
Timeline        --> {BASE_DIR}/{YEAR}/{MONTH}/{DAY}.timeline.md
Standup         --> {BASE_DIR}/{YEAR}/{MONTH}/{NEXT_WORKDAY}.standup.md
```

## Steps

### 1. Summarize GitHub Activity

```
$HOME/repos/git/personal-automation/others/summarize-github-activity tomzx {TODAY} {TODAY} Shopify,shop
```

Write output to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.github.md`.

### 2. Summarize Slack Activity

Collect Slack threads for {TODAY} using `collect_individual_threads.py`. Slack's `after:`/`before:` search operators are exclusive, so use the day before and the day after {TODAY} as bounds:

```bash
SLACK_USER=`scripts/get-env SLACK_USER`

uv run skills/slack-kb-individual/collect_individual_threads.py \
  --user $SLACK_USER \
  --after {YESTERDAY} --before {TOMORROW} \
  -o {BASE_DIR}/{YEAR}/{MONTH}/{DAY}.slack.jsonl
```

Read the resulting JSONL and summarize into `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.slack.md`:

```markdown
# Summary

A summary of the key conversations.

# Key Conversations

A list of the key conversations (including a link to the conversation).

# Action Items Generated

A list of the action items generated.
```

Use Slack activity to identify collaborators to thank.

### 3. Summarize Overall Activity

Combine GitHub and Slack data. Write to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.overall.md`:

```markdown
# Accomplishments
# Decisions
# Blockers/Waiting for
# For Your Information
# Need to Discuss
# Thanks
# Next Steps
```

Avoid repeating the same information differently within the same section.

### 4. Build Timeline

Write a chronological view to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.timeline.md`:

```markdown
# Timeline

* HH:MM - Activity
```

### 5. Generate Standup

Write to `{BASE_DIR}/{YEAR}/{MONTH}/{NEXT_WORKDAY}.standup.md` (max 5 bullet points per section):

```markdown
# What I did yesterday
# What I will do today
# Blockers/Waiting for
# For Your Information
# Thanks
```

## Example Usage

**Scenario 1: Regular weekday**
Run at end of Thursday. Generates 5 files; standup targets Friday's date.

**Scenario 2: End of Friday**
`NEXT_WORKDAY` resolves to the following Monday. Standup file is created for Monday.

**Scenario 3: Light activity day**
Few GitHub events and minimal Slack. Summaries are brief; Overall may have mostly empty sections except Accomplishments.

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `date +%Y-%m-%d` | Get today's date in ISO format |
| `date -d "next Monday" +%Y-%m-%d` | Get next Monday's date |
| `$HOME/repos/git/personal-automation/others/summarize-github-activity <user> <from> <to> <exclude>` | Summarize GitHub activity for a user |
