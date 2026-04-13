---
name: end-of-month-summary
description: Summarize monthly GitHub activity, Slack activity, colleague activity, and generate a monthly highlights report.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=`date +%Y-%m-%d`
YEAR=`date +%Y`
MONTH=`date +%m`
MONTH_NAME=`date +%B`
MONTH_START=`date -d "$(date +%Y-%m-01)" +%Y-%m-%d`

# Generate End-of-Month Summary

Produces a monthly digest covering personal GitHub activity, personal Slack activity, a monitored Slack channel, each colleague's contributions, outstanding action items, and thanks from the month.

## Prerequisites

- Slack MCP server connected and authenticated with access to relevant channels
- `gh` CLI authenticated
- `summarize-github-activity` script at `$HOME/repos/git/personal-automation/others/summarize-github-activity`
- `NOTES_DIR` environment variable set (resolved via `scripts/get-env NOTES_DIR`)
- `COLLEAGUES` environment variable set (resolved via `scripts/get-env COLLEAGUES`)
- `scripts/get-env` utility available

## Pipeline

```
GitHub Activity --> {BASE_DIR}/{YEAR}/{MONTH}/github.md
Slack Activity  --> {BASE_DIR}/{YEAR}/{MONTH}/slack.md
#help-ml-infra  --> {BASE_DIR}/{YEAR}/{MONTH}/slack.help-ml-infrastructure.md
Colleagues      --> {BASE_DIR}/{YEAR}/{MONTH}/slack/{COLLEAGUE}.md (parallel)
                    {BASE_DIR}/{YEAR}/{MONTH}/slack.colleagues.md
Action Items    --> {BASE_DIR}/{YEAR}/{MONTH}/action-items.md
Thanks          --> {BASE_DIR}/{YEAR}/{MONTH}/thanks.md
```

## Steps

### 1. Summarize GitHub Activity

```
$HOME/repos/git/personal-automation/others/summarize-github-activity tomzx {MONTH_START} {TODAY} Shopify,shop
```

Write output to `{BASE_DIR}/{YEAR}/{MONTH}/github.md`.

### 2. Summarize Personal Slack Activity

Summarize `.slack.md` files in `{BASE_DIR}/{YEAR}/{MONTH}/` from the month ending {TODAY}. Write to `{BASE_DIR}/{YEAR}/{MONTH}/slack.md`:

```markdown
# Summary

A summary of the key conversations for the month.

# Key Conversations

A list of the key conversations (including a link to each conversation).

# Action Items Generated

A list of the action items generated.
```

### 3. Summarize #help-ml-infrastructure Channel

Fetch messages from the #help-ml-infrastructure Slack channel during the month ending {TODAY}. Write to `{BASE_DIR}/{YEAR}/{MONTH}/slack.help-ml-infrastructure.md`:

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

### 4. Summarize Colleague Activity (parallel)

Resolve the colleagues list:
```
scripts/get-env COLLEAGUES
```

For each person in the list, run as a subagent in parallel: fetch their Slack messages and thread replies during the month, list all channels they contributed to. Write each to `{BASE_DIR}/{YEAR}/{MONTH}/slack/{COLLEAGUE}.md`.

Aggregate into `{BASE_DIR}/{YEAR}/{MONTH}/slack.colleagues.md`.

### 5. Summarize Action Items

Review all notes from the month in `{BASE_DIR}/{YEAR}/{MONTH}/` and extract pending action items. Write to `{BASE_DIR}/{YEAR}/{MONTH}/action-items.md`.

### 6. Summarize Thanks

Compile thanks from the month's notes and Slack activity. Write to `{BASE_DIR}/{YEAR}/{MONTH}/thanks.md`.

## Example Usage

**Scenario 1: Standard month-end run**
```
/end-of-month-summary
```
Processes {MONTH_NAME} {YEAR}. Creates `{NOTES_DIR}/{YEAR}/{MONTH}/` with all output files.

**Scenario 2: Multiple colleagues**
With 4 colleagues in `COLLEAGUES`, 4 subagents run in parallel to fetch their Slack activity, then results are merged into `slack.colleagues.md`.

**Scenario 3: Quiet month**
Few GitHub events and minimal Slack. Summaries are brief; `action-items.md` notes "No outstanding action items."

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env COLLEAGUES` | Resolve the list of colleagues to summarize |
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `date +%Y-%m-%d` | Get today's date in ISO format |
| `date +%m` | Get the current month number |
| `date +%B` | Get the current month name |
| `date +%Y` | Get the current year |
| `date -d "$(date +%Y-%m-01)" +%Y-%m-%d` | Get the first day of the current month |
| `$HOME/repos/git/personal-automation/others/summarize-github-activity <user> <from> <to> <exclude>` | Summarize GitHub activity for a user |
