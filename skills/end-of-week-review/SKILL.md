---
name: end-of-week-review
description: Reflective end-of-week review covering goal progress, time and attention patterns, team health, and what to change next week. Runs the audit-attention skill to classify the week's activities as compounding or depreciating.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=!`date +%Y-%m-%d`
YEAR=!`date +%Y`
WEEK=!`date +%V`
NEXT_WEEK=!`date -d "next Monday" +%V`

# End-of-Week Review

Guides a structured weekly reflection connecting your week's work to goals, surfacing patterns in how you spent your time and attention, checking on team health, and deciding what to change next week.

## Prerequisites

- `NOTES_DIR` environment variable set (resolved via `scripts/get-env NOTES_DIR`)
- `scripts/get-env` utility available
- Optional: daily `.review.md` files from the week in `{BASE_DIR}/{YEAR}/{MONTH}/`
- Optional: daily `.overall.md` files from the week in `{BASE_DIR}/{YEAR}/{MONTH}/`
- Optional: `{BASE_DIR}/goals.md` with current personal goals
- Optional: `{BASE_DIR}/team-goals.md` with current team goals
- Optional: `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.colleagues.md` from end-of-week-summary
- The **audit-attention** skill available (invoked in step 3)

## Steps

### 1. Gather Context

Read the following files if they exist:
- All `*.review.md` files from this week in `{BASE_DIR}/{YEAR}/{MONTH}/`
- All `*.overall.md` files from this week in `{BASE_DIR}/{YEAR}/{MONTH}/`
- `{BASE_DIR}/goals.md`
- `{BASE_DIR}/team-goals.md`
- `{BASE_DIR}/{YEAR}/weekly/{WEEK}/action-items.md`
- `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.colleagues.md`

### 2. Synthesize Patterns

Before asking questions, analyze the gathered data to identify:

**Time allocation:** Estimate what percentage of the week went to (a) goal-driven deep work, (b) collaboration and team support, (c) reactive/unplanned work, (d) administrative overhead.

**Goal progress:** For each goal in `goals.md` and `team-goals.md`, assess: not started / some progress / significant progress / completed.

**Reactivity trend:** Using the daily reactivity scores (if available), is the week trending better or worse than the previous pattern?

**Team signals:** From colleague summaries and notes, flag any team members who seem blocked, overloaded, disengaged, or who did something notable worth recognizing.

**Recurring friction:** Look for activities, meetings, or requests that consumed time multiple days running without clear goal alignment.

### 3. Run Attention Audit

Invoke the **audit-attention** skill against this week's activities, using the gathered context and synthesized patterns as the activity list. Apply the two-year test to classify each significant activity as compounding or depreciating, estimate the fraction of the week that landed on compounding work, and note any boundary moves since the last audit.

If the gathered context does not yield a clear activity list, ask the user to enumerate the significant activities of the week before proceeding.

Capture the audit output; it becomes the `## Attention Allocation` section of the review written in step 5.

### 4. Ask Reflective Questions

Present a summary of the synthesized patterns and the attention audit results, then ask the user the following questions in a single message:

1. What were your top 3 goals for the week? Rate progress on each (0%, 25%, 50%, 75%, 100%).
2. What was the highest-leverage thing you did this week? What made it possible?
3. What consumed time that, in hindsight, you should have declined, delegated, or deferred?
4. Which team member needs more from you next week? Which is set up to do their best work?
5. What one behavior or habit would make next week meaningfully better?
6. Is there a decision you have been avoiding that this week made more urgent?

### 5. Write the Review

Write the review to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/review.md`:

```markdown
---
week: {WEEK}
year: {YEAR}
date: {TODAY}
---

# End-of-Week Review

## Goals Snapshot

### Personal goals
| Goal | Status | Notes |
|------|--------|-------|
| <goal> | <0-100%> | <one line> |

### Team goals
| Goal | Status | Notes |
|------|--------|-------|
| <goal> | <0-100%> | <one line> |

## Time and Attention

**Estimated allocation:**
- Goal-driven deep work: <X>%
- Collaboration and team support: <X>%
- Reactive / unplanned: <X>%
- Administrative: <X>%

**Verdict:** <one sentence on whether time was well spent>

## Attention Allocation

**Fraction of week on compounding work:** <X>% (direction cycle over cycle: up / flat / down / first audit)

**Two-year test results:**

| Activity | Compounding / Depreciating | Keep / Delegate next week |
|----------|---------------------------|---------------------------|
| <activity> | <C/D> | <keep/delegate> |

**Boundary moves since last audit:** <activities that shifted category, and which direction; or "none / first audit">

**Time to ring-fence next week:** <specific compounding activity and the block that protects it>

**To delegate next week:** <specific depreciating activities and the delegation path>

## Highest Leverage

**Best use of time:** <activity and why it mattered>

**Biggest time sink:** <activity that should have been declined/delegated/deferred>

## Team Health

| Person | Status | Action needed |
|--------|--------|---------------|
| <name> | <blocked/on-track/thriving> | <none / specific action> |

## Decisions

**Decision avoided:** <the call being deferred, and why it matters>

**Decisions made:** <list>

## What Changes Next Week

**Behavior to change:** <specific, actionable>

**Time to protect:** <what and why>

**To decline or delegate:** <specific items>

## Carry-Forward Actions

- <action item not completed this week>
```

## Example Usage

**Scenario 1: Goal-aligned week**
Daily reviews show mostly proactive work. Goal table shows 75-100% on priorities. Review confirms the pattern and surfaces one area (a recurring meeting) to cut.

**Scenario 2: Reactive week**
Most days scored 4-5 on reactivity. Goal progress is low. Review surfaces the drift clearly, names the source of interruptions, and proposes one structural change (e.g., block focus time each morning).

**Scenario 3: Team concern surfaced**
Colleague summary shows a team member is absent from key discussions. Review flags it, user notes they should check in, action carries forward to next week.

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `date +%V` | Get the ISO week number |
| `date +%Y-%m-%d` | Get today's date in ISO format |
| `date -d "next Monday" +%V` | Get next week's ISO week number |
