---
name: end-day
description: Closes the workday with GitHub and Slack summaries, overall notes, timeline, and next-day standup. Use when the user says /end-day, end of day, EOD, or daily wrap-up.
---

# End Day

This skill is an alias for the **end-of-day-summary** workflow, with an additional skill-gap identification step to drive a self-reinforcing improvement loop.

## Instructions

1. Read and follow **end-of-day-summary** in full (same outputs, same pipeline, same prerequisites).
2. If the user asks for reflection, goal alignment, or a review (not just a summary), also follow **end-of-day-review** after the summary files exist or when summary data is unavailable.
3. Run the **skill gap identification** step below every time, after the summary (and review, if run).

Do not invent a separate EOD format; stay consistent with end-of-day-summary templates.

---

## Skill Gap Identification

The goal is to surface workflows the user performed today that are not yet encoded as skills, so they can be written down and automated over time.

### Step 1 — Inventory existing skills

List all directories under `skills/` in the dot-claude repository (e.g., `ls ~/dot-claude/skills/`). This is the current skill library.

### Step 2 — Extract today's workflows

From the context already gathered (GitHub summary, Slack summary, overall summary, standup), identify distinct **repeated or multi-step workflows** the user executed today. Focus on:

- Things done more than once, or done the same way as previous days.
- Multi-step tasks that follow a clear pattern (collect → process → write → send).
- Anything the user said "I always do X when Y" about, explicitly or implicitly.
- Manual steps that produced an artifact (a doc, a message, a PR, a report).

### Step 3 — Compare against existing skills

For each workflow identified, check if a matching skill already exists in the library. A skill "covers" a workflow if its name or description clearly matches the intent.

### Step 4 — Report gaps

Present a short bulleted list of workflows that have **no matching skill**, grouped by rough category (e.g., communication, code review, reporting, planning). For each gap include:

- A one-sentence description of the workflow.
- A suggested skill name (kebab-case).
- Estimated frequency (daily / weekly / ad-hoc).

Example output format:

```
## Skill Gaps Identified

- **post-incident-summary** — Write and send a structured summary after a production incident. (weekly)
- **changelog-entry** — Draft a changelog entry from a merged PR description. (daily)
- **meeting-prep** — Pull agenda, related PRs, and open issues before a meeting. (ad-hoc)
```

### Step 5 — Prompt for action

Ask the user: "Would you like to create any of these skills now, or add them to a backlog?"

- If the user says **yes to one or more**, immediately scaffold a `skills/<name>/SKILL.md` for each chosen skill using the standard frontmatter and a brief instructions stub, then commit and push.
- If the user says **backlog**, append the gaps as unchecked items to `{BASE_DIR}/skill-backlog.md` (create the file if it does not exist).
- If the user says **no**, skip and close.
