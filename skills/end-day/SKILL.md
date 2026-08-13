---
name: end-day
description: Closes the workday with GitHub and Slack summaries, overall notes, timeline, and next-day standup. Use when the user says /end-day, end of day, EOD, or daily wrap-up.
---

# End Day

This skill orchestrates the end-of-day pipeline.

## Instructions

1. Read and follow **end-of-day-summary** in full (same outputs, same pipeline, same prerequisites).
2. If the user asks for reflection, goal alignment, or a review (not just a summary), also follow **end-of-day-review** after the summary files exist or when summary data is unavailable.
3. Run **identify-skill-gaps** every time, after the summary (and review, if run).
4. Check whether `SEND_DAILY_SLACK` is set (via `~/.agents/scripts/get-env SEND_DAILY_SLACK`). Only post when it resolves to a truthy value (`1`, `true`, `yes`). If unset or empty, skip this step and inform the user that the Slack update was skipped.

When enabled, post a brief end-of-day summary to the `tom-rochette-updates` channel using the **post-slack-message** skill:

```bash
uv run post_slack_message.py --channel C0BE3BM97B7 "<summary>"
```

Format the message as a short wrap-up of what was accomplished today and the next-day standup bullets. Use Slack mrkdwn formatting. Example:

```
*End of day - {TODAY}*

*Done today:*
- <accomplishment 1>
- <accomplishment 2>

*Tomorrow:*
- <next-day bullet 1>
- <next-day bullet 2>
```

Report the posted permalink back to the user.

Do not invent a separate EOD format; stay consistent with end-of-day-summary templates.
