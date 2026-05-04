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

Do not invent a separate EOD format; stay consistent with end-of-day-summary templates.
