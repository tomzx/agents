---
name: end-of-week-summary
description: Summarize weekly Slack activity, colleague activity, action items, and thanks for the week.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=`date +%Y-%m-%d`
YEAR=`date +%Y`
WEEK=`date +%V`
WEEK_START=`date -d "$(date +%Y-%m-%d) -$(( $(date +%u) - 1 )) days" +%Y-%m-%d`
WEEK_START_MINUS_ONE=`date -d "$WEEK_START - 1 day" +%Y-%m-%d`
TOMORROW=`date -d "tomorrow" +%Y-%m-%d`

# Generate End-of-Week Summary

Produces a weekly digest covering personal Slack activity, a monitored Slack channel, each colleague's contributions, outstanding action items, and thanks from the week.

## Prerequisites

- `SLACK_TOKEN`, `SLACK_COOKIE`, and `SLACK_USER` in `.env` (same credentials used by `collect_individual_threads.py`)
- `NOTES_DIR` environment variable set, containing daily `.slack.md` note files
- `COLLEAGUES` environment variable set (resolved via `scripts/get-env COLLEAGUES`)
- `SLACK_USER` environment variable set (resolved via `scripts/get-env SLACK_USER`; Slack username, e.g. `tom.rochette`)
- `HELP_ML_CHANNEL_ID` environment variable set (resolved via `scripts/get-env HELP_ML_CHANNEL_ID`; Slack channel id for `#help-ml-infrastructure`)
- `scripts/get-env` utility available

## Pipeline

```
Personal Slack  --> {BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.md
#help-ml-infra  --> {BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.help-ml-infrastructure.md
Colleagues      --> {BASE_DIR}/{YEAR}/weekly/{WEEK}/slack/{COLLEAGUE}.md (parallel)
                    {BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.colleagues.md
Action Items    --> {BASE_DIR}/{YEAR}/weekly/{WEEK}/action-items.md
Thanks          --> {BASE_DIR}/{YEAR}/weekly/{WEEK}/thanks.md
```

## Steps

### 1. Summarize Personal Slack Activity

Summarize `.slack.md` files in `{BASE_DIR}` from the week ending {TODAY}. Write to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.md`.

### 2. Summarize #help-ml-infrastructure Channel

Fetch messages from the #help-ml-infrastructure Slack channel during the week ending {TODAY} using `build_thread_kb.py`. `WEEK_START` is Monday of the current week; `TOMORROW` is used as the exclusive upper bound.

```bash
HELP_ML_CHANNEL_ID=`scripts/get-env HELP_ML_CHANNEL_ID`

uv run skills/slack-kb-channel/build_thread_kb.py \
  --channel $HELP_ML_CHANNEL_ID \
  --after {WEEK_START} --before {TOMORROW} \
  --output {BASE_DIR}/{YEAR}/weekly/{WEEK}/thread-fetch-help-ml.jsonl
```

Read the resulting JSONL and summarize into `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.help-ml-infrastructure.md`:

```markdown
# <Issue title> (one entry per issue)

## Link
## Participants
## Issue
## Key events
## Outcome

# Overall

## Response Quality
## Common Issues
## Action Items
```

### 3. Summarize Colleague Activity (parallel)

Resolve the colleagues list:
```
scripts/get-env COLLEAGUES
```

For each person in the list, run as a subagent in parallel using `collect_individual_threads.py`. Slack's `after:` is exclusive, so pass the day before `WEEK_START` as `--after` and `TOMORROW` as `--before`:

```bash
uv run skills/slack-kb-individual/collect_individual_threads.py \
  --user <COLLEAGUE> \
  --after {WEEK_START_MINUS_ONE} --before {TOMORROW} \
  -o {BASE_DIR}/{YEAR}/weekly/{WEEK}/slack/{COLLEAGUE}.jsonl
```

Read each JSONL and summarize into `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack/{COLLEAGUE}.md`, listing all channels they contributed to.

Aggregate into `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.colleagues.md`.

### 4. Summarize Action Items

Review all notes from the week in `{BASE_DIR}` and extract pending action items. Write to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/action-items.md`.

### 5. Summarize Thanks

Compile thanks from the week's notes. Write to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/thanks.md`.

## Example Usage

**Scenario 1: Standard week-end run**
```
/end-of-week-summary
```
Processes week 15 of 2026. Creates `{NOTES_DIR}/2026/weekly/15/` with all output files.

**Scenario 2: Multiple colleagues**
With 4 colleagues in `COLLEAGUES`, 4 subagents run in parallel to fetch their Slack activity, then results are merged into `slack.colleagues.md`.

**Scenario 3: Quiet week**
Few Slack messages and no action items. Summaries are brief; `action-items.md` notes "No outstanding action items."

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env COLLEAGUES` | Resolve the list of colleagues to summarize |
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `date +%V` | Get the ISO week number |
| `date +%Y-%m-%d` | Get today's date in ISO format |
