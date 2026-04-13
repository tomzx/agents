---
name: start-month
description: Opens the calendar month with a theme, monthly outcomes, and carryover from the prior month review. Use when the user says /start-month, start of month, monthly planning, or new month kickoff.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=`date +%Y-%m-%d`
YEAR=`date +%Y`
MONTH=`date +%m`
MONTH_NAME=`date +%B`
PREV_MONTH=`date -d "last month" +%m`
PREV_YEAR=`date -d "last month" +%Y`

# Start Month

Sets intent for the calendar month: theme, a small set of outcomes, carryover from last month’s review, and what to protect or drop.

## Prerequisites

- `NOTES_DIR` set (via `scripts/get-env NOTES_DIR`)
- Optional: `{BASE_DIR}/goals.md`, `{BASE_DIR}/team-goals.md`
- Optional: `{BASE_DIR}/{PREV_YEAR}/{PREV_MONTH}/month-review.md` (from **end-of-month-review**)
- Optional: latest weekly `plan.md` or `review.md` under `{BASE_DIR}/{YEAR}/weekly/` for continuity

## Steps

### 1. Resolve month context

Use calendar month `{MONTH}` and `{YEAR}`. For “last month,” use `{PREV_YEAR}` and `{PREV_MONTH}` (handles January rolling to December of the prior year when using the same `date` patterns as **end-of-month-review**).

### 2. Gather context

Read if they exist:

- `{BASE_DIR}/{PREV_YEAR}/{PREV_MONTH}/month-review.md` (especially the **Next Month** section)
- `{BASE_DIR}/goals.md` and `{BASE_DIR}/team-goals.md`
- This month’s `{BASE_DIR}/{YEAR}/{MONTH}/month-plan.md` if you already started the month

### 3. Synthesize (in chat unless the user asks for a file)

Deliver:

- **Theme** (one line for the month)
- **Top 3 to 5 outcomes** (measurable or clearly done or not done)
- **Carryover** from last month’s review (scheduled, delegated, or explicitly dropped)
- **Strategic focus** (single most important thread, aligned with goals or OKRs)
- **Risks** (capacity, dependencies, recurring commitments to trim)

If last month’s `month-review.md` is missing, note the gap and plan from goals plus what the user states.

### 4. Optional file output

If the user wants it persisted, write `{BASE_DIR}/{YEAR}/{MONTH}/month-plan.md`:

```markdown
---
month: {MONTH_NAME} {YEAR}
date: {TODAY}
---

# Month plan

## Theme
## Top outcomes (3 to 5)
## Carryover from last month
## Strategic focus
## Risks and constraints
```

## Relationship to other skills

- **end-of-month-review** writes `{BASE_DIR}/{YEAR}/{MONTH}/month-review.md` at month end; start-month should read the **previous** month’s file when present.
- Do not run the full **end-of-month-review** workflow here unless the user explicitly asks for a retrospective.
