---
name: end-of-day-review
description: Reflective end-of-day review that forces alignment between your work, your goals, and your team's goals.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=`date +%Y-%m-%d`
YEAR=`date +%Y`
MONTH=`date +%m`
DAY=`date +%d`

# End-of-Day Review

Guides a structured reflection on how the day's work aligned with personal and team goals, where attention went, and what needs to shift tomorrow.

## Prerequisites

- `NOTES_DIR` environment variable set (resolved via `scripts/get-env NOTES_DIR`)
- `scripts/get-env` utility available
- Optional: `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.overall.md` from end-of-day-summary
- Optional: `{BASE_DIR}/goals.md` with current personal goals
- Optional: `{BASE_DIR}/team-goals.md` with current team goals

## Steps

### 1. Gather Context

Read the following files if they exist:
- `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.overall.md` (today's activity summary)
- `{BASE_DIR}/{YEAR}/{MONTH}/{TODAY}.standup.md` (what you planned to do today)
- `{BASE_DIR}/goals.md` (your current goals and priorities)
- `{BASE_DIR}/team-goals.md` (your team's current goals and priorities)

If the overall summary does not exist, note that and proceed with the available context.

### 2. Assess Goal Alignment

Using the gathered context, identify:
- Which of today's activities directly advanced a personal goal
- Which advanced a team goal
- Which were reactive (requests, interruptions, unplanned) vs. proactive
- Which activities were neither goal-aligned nor clearly necessary

### 3. Ask Reflective Questions

Ask the user the following questions. Ask all questions in a single message, numbered, so they can answer all at once:

1. What were your top 3 priorities for today? Did you accomplish them?
2. On a scale of 1-5, how reactive was today (1 = fully focused, 5 = entirely reactive/interrupted)?
3. What single activity moved your most important goal forward today?
4. Did any team member need your attention or unblock that you may have missed or deprioritized?
5. What is the one thing you must do tomorrow that you did not do today?

### 4. Write the Review

Write the review to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.review.md`:

```markdown
---
date: {TODAY}
---

# End-of-Day Review

## Goals Snapshot

A brief reminder of the 1-3 most important current goals (personal and team).

## Today's Alignment

### Moved the needle on goals
- <activity> → <goal it served>

### Necessary but not goal-driven
- <activity>

### Reactive / unplanned
- <activity>

### Should have skipped or delegated
- <activity>

## Reflection

**Top priorities vs. reality:** <how stated priorities matched actual work>

**Reactivity score:** <1-5> — <one sentence on what drove it>

**Highest-leverage thing done today:** <activity>

**Team check:** <notes on whether team members were unblocked and supported>

## Tomorrow

**Must do:** <single most important item>

**Should protect time for:** <goal-aligned deep work>

**Can deprioritize:** <item to drop or defer>
```

## Example Usage

**Scenario 1: Focused, goal-aligned day**
Activity summary shows deep work on a key project. User rates reactivity as 2. Review captures the progress and sets a clear #1 priority for tomorrow.

**Scenario 2: Highly reactive day**
Most time was in meetings and responding to requests. User rates reactivity as 5. Review surfaces the drift and the review prompts a decision: what to protect tomorrow.

**Scenario 3: No summary file available**
`{DAY}.overall.md` does not exist. Questions are asked without pre-populated context. Review is written based entirely on user responses.

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `date +%Y-%m-%d` | Get today's date in ISO format |
