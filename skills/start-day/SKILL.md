---
name: start-day
description: Opens the workday by grounding priorities in yesterday's plan and goals, and optionally writes a short start-of-day note. Use when the user says /start-day, start of day, morning planning, or daily kickoff.
---

BASE_DIR=!`~/.agents/scripts/get-env NOTES_DIR`
TODAY=!`date +%Y-%m-%d`
YEAR=!`date +%Y`
MONTH=!`date +%m`
DAY=!`date +%d`

# Start Day

Frames the day before deep work: confirm priorities, first focus block, and blockers to surface early.

## Prerequisites

- `NOTES_DIR` set (via `~/.agents/scripts/get-env NOTES_DIR`)
- Optional: `{BASE_DIR}/goals.md`, `{BASE_DIR}/team-goals.md`
- Optional: `{BASE_DIR}/{YEAR}/{MONTH}/{TODAY}.standup.md` (from end-of-day-summary, written as "next workday" standup)
- Optional: `SEND_DAILY_SLACK` set (via `~/.agents/scripts/get-env SEND_DAILY_SLACK`; truthy values `1`, `true`, `yes` enable Slack posting)

## Steps

### 1. Gather context

Read if they exist:

- `{BASE_DIR}/{YEAR}/{MONTH}/{TODAY}.standup.md` (today's planned bullets from yesterday's EOD)
- `{BASE_DIR}/goals.md` and `{BASE_DIR}/team-goals.md`
- `{BASE_DIR}/{YEAR}/{MONTH}/` for yesterday's `*.overall.md` (same month folder; use calendar yesterday date) when you need continuity

### 2. Synthesize (in chat unless the user asks for a file)

Produce a short brief:

- **Top 3 outcomes** for today (from standup + goals; resolve conflicts explicitly)
- **First 60 to 90 minutes** (single concrete focus, no meeting multitasking)
- **Blockers or asks** to send before others go heads-down
- **One thing to protect or decline** if the day looks overloaded

If standup is missing, derive top 3 from goals and anything the user says is urgent.

### 3. Optional file output

If the user wants it persisted, write `{BASE_DIR}/{YEAR}/{MONTH}/{TODAY}.start.md`:

```markdown
---
date: {TODAY}
---

# Start of day

## Top 3 outcomes
## First focus (60 to 90 min)
## Blockers or asks (early)
## Notes
```

## Relationship to other skills

- **end-of-day-summary** writes `{TODAY}.standup.md` the prior evening (as the next workday file). Start-day consumes that file when present.
- Do not duplicate the GitHub or Slack pipelines from end-of-day-summary here.

## Post update to Slack

As the final step, check whether `SEND_DAILY_SLACK` is set (via `~/.agents/scripts/get-env SEND_DAILY_SLACK`). Only post when it resolves to a truthy value (`1`, `true`, `yes`). If unset or empty, skip this step and inform the user that the Slack update was skipped.

When enabled, post a brief summary to the `tom-rochette-updates` channel using the **post-slack-message** skill:

```bash
uv run post_slack_message.py --channel C0BE3BM97B7 "<summary>"
```

Format the message as a short brief of the top 3 outcomes and first focus block. Use Slack mrkdwn formatting (e.g. `*bold*`, line breaks with `\n`). Example:

```
*Start of day - {TODAY}*

*Top 3 outcomes:*
1. <outcome 1>
2. <outcome 2>
3. <outcome 3>

*First focus:* <first 60-90 min task>
```

Report the posted permalink back to the user.
