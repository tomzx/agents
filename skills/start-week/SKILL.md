---
name: start-week
description: Opens the calendar week with themes, outcomes, and carryover from last week. Use when the user says /start-week, start of week, weekly planning, or Monday kickoff.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=!`date +%Y-%m-%d`
YEAR=!`date +%Y`
WEEK=!`date +%V`

# Start Week

Sets intent for the ISO week: a small number of outcomes, how collaboration fits, and what to finish or drop from last week.

## Prerequisites

- `NOTES_DIR` set (via `scripts/get-env NOTES_DIR`)
- Optional: `{BASE_DIR}/goals.md`, `{BASE_DIR}/team-goals.md`
- Optional: `{BASE_DIR}/{YEAR}/weekly/{WEEK}/action-items.md` (if end-of-week-summary already ran this week)
- Optional: previous week's `{BASE_DIR}/{YEAR}/weekly/<prev>/review.md` or `action-items.md` for carryover

## Steps

### 1. Resolve week context

Use ISO week `{WEEK}` and year `{YEAR}`. If today is early in the week, treat "last week" as the previous ISO week (handle year boundary by checking weekly folders under `{BASE_DIR}/{YEAR}/weekly/`).

### 2. Gather context

Read if they exist:

- Prior week `review.md` or `action-items.md` under `{BASE_DIR}/{YEAR}/weekly/`
- `{BASE_DIR}/goals.md` and `{BASE_DIR}/team-goals.md`
- This week's `action-items.md` if it already exists

### 3. Identify code hotspots (optional)

If the project has a git repository in the working directory, run:

```
/git-churn-analysis week
```

Include a brief **Code Hotspots** note in the synthesis if any files show 3+ commits in the past week.
This surfaces technical debt to factor into the week's priorities before committing to outcomes.

### 4. Synthesize (in chat unless the user asks for a file)

Deliver:

- **Theme** (one line for the week)
- **Top 3 outcomes** (measurable or clearly done or not done)
- **Carryover** (explicitly scheduled or explicitly dropped)
- **Collaboration** (who to sync with, what decisions are waiting)
- **Risks** (capacity, dependencies, recurring meetings to trim)

### 5. Optional file output

If the user wants it persisted, write `{BASE_DIR}/{YEAR}/weekly/{WEEK}/plan.md`:

```markdown
---
week: {WEEK}
year: {YEAR}
date: {TODAY}
---

# Week plan

## Theme
## Top 3 outcomes
## Carryover from last week
## Collaboration and decisions
## Risks and constraints
```

## Relationship to other skills

- **end-of-week-summary** and **end-of-week-review** populate reflection and action items; start-week should reference them when present.
- Do not run the Slack or colleague pipelines from end-of-week-summary here unless the user explicitly asks for a weekly digest.
