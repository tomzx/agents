---
name: end-of-week-summary
description: Summarize weekly Slack activity, colleague activity, action items, and thanks for the week.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=`date +%Y-%m-%d`
YEAR=`date +%Y`
WEEK=`date +%V`

# Generate End-of-Week Summary

Produces a weekly digest covering personal Slack activity, a monitored Slack channel, each colleague's contributions, outstanding action items, and thanks from the week.

## Prerequisites

- Slack MCP server connected and authenticated with access to relevant channels
- `NOTES_DIR` environment variable set, containing daily `.slack.md` note files
- `COLLEAGUES` environment variable set (resolved via `scripts/get-env COLLEAGUES`)
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

Fetch messages from the #help-ml-infrastructure Slack channel during the week ending {TODAY}. Write to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.help-ml-infrastructure.md`:

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

For each person in the list, run as a subagent in parallel: fetch their Slack messages and thread replies during the week, list all channels they contributed to. Write each to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack/{COLLEAGUE}.md`.

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
