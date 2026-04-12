---
name: end-of-month-review
description: Reflective end-of-month review covering OKR/goal progress, time allocation trends, team trajectory, and strategic focus adjustments for the next month.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=`date +%Y-%m-%d`
YEAR=`date +%Y`
MONTH=`date +%m`
MONTH_NAME=`date +%B`
PREV_MONTH=`date -d "last month" +%m`
PREV_MONTH_NAME=`date -d "last month" +%B`

# End-of-Month Review

Guides a structured monthly retrospective that connects work patterns to goals and OKRs, surfaces trends in time and attention allocation, assesses team trajectory, and produces concrete focus adjustments for the next month.

## Prerequisites

- `NOTES_DIR` environment variable set (resolved via `scripts/get-env NOTES_DIR`)
- `scripts/get-env` utility available
- Optional: weekly `review.md` files from the month in `{BASE_DIR}/{YEAR}/weekly/`
- Optional: `{BASE_DIR}/goals.md` with current goals and OKRs
- Optional: `{BASE_DIR}/team-goals.md` with current team goals and OKRs
- Optional: `{BASE_DIR}/{YEAR}/weekly/*/action-items.md` files from the month

## Steps

### 1. Gather Context

Read the following files if they exist:
- All `review.md` files from this month's weekly folders in `{BASE_DIR}/{YEAR}/weekly/`
- All `action-items.md` files from this month's weekly folders
- `{BASE_DIR}/goals.md`
- `{BASE_DIR}/team-goals.md`
- `{BASE_DIR}/{YEAR}/{PREV_MONTH}/month-review.md` (last month's review, for continuity)

### 2. Synthesize Monthly Patterns

Aggregate data across the month's weekly reviews to identify:

**Time allocation trend:** Average and trend (improving/declining) across the four weeks for (a) goal-driven deep work, (b) collaboration, (c) reactive work, (d) overhead. Flag any week that was a significant outlier.

**Goal trajectory:** For each goal in `goals.md` and `team-goals.md`, reconstruct weekly progress to show the trajectory across the month. Identify goals with no movement (stalled), linear progress, or accelerating progress.

**Carried-forward actions:** List any action items that appeared in multiple weekly reviews without resolution. These are the items that keep getting deferred.

**Decisions avoided:** Aggregate any decisions flagged as avoided across the month's reviews.

**Team trajectory:** Across the weekly team health tables, identify: anyone who has been blocked for more than one week, consistent high performers, anyone who has dropped off.

### 3. Ask Reflective Questions

Present the synthesized patterns, then ask the user the following questions in a single message:

1. For each goal, rate your satisfaction with the month's progress (1-5) and name the single biggest reason it went the way it did.
2. Looking at your time allocation trends: what pattern bothers you most? What enabled the best weeks?
3. Which team members grew this month? Who needs a direct conversation about trajectory or support?
4. What was the most important decision you made this month? What was the most important one you avoided?
5. If you could give advice to yourself at the start of this month, what would it be?
6. What should be your single most important focus next month? What needs to be deprioritized to make room for it?

### 4. Write the Review

Write the review to `{BASE_DIR}/{YEAR}/{MONTH}/month-review.md`:

```markdown
---
month: {MONTH_NAME} {YEAR}
date: {TODAY}
---

# End-of-Month Review: {MONTH_NAME} {YEAR}

## Goals and OKRs

### Personal goals
| Goal | Month progress | Satisfaction (1-5) | Primary driver |
|------|---------------|---------------------|----------------|
| <goal> | <trajectory summary> | <1-5> | <key reason> |

### Team goals
| Goal | Month progress | Satisfaction (1-5) | Primary driver |
|------|---------------|---------------------|----------------|
| <goal> | <trajectory summary> | <1-5> | <key reason> |

## Time and Attention Trends

| Week | Deep work | Collaboration | Reactive | Overhead |
|------|-----------|---------------|----------|----------|
| W<N> | <X>% | <X>% | <X>% | <X>% |
| W<N> | ... | | | |
| **Avg** | **<X>%** | **<X>%** | **<X>%** | **<X>%** |

**Best week:** Week <N> — <one sentence on what made it work>

**Worst week:** Week <N> — <one sentence on the cause>

**Pattern to change:** <the most important structural change>

## Carried-Forward Items

These items appeared in multiple weekly reviews without resolution:
- <item> (carried <N> weeks) — <decision: resolve, delegate, or kill>

## Team Trajectory

| Person | Trend | Notes | Next action |
|--------|-------|-------|-------------|
| <name> | <growing/steady/at-risk> | <observation> | <action or none> |

## Decisions

**Most important decision made:** <decision and outcome>

**Most important decision avoided:** <the call still being deferred, and the cost of deferring>

## Retrospective

**Advice to past self at start of month:** <honest, specific>

**What went better than expected:** <item>

**What went worse than expected:** <item>

## Next Month

**Single most important focus:** <one thing>

**What gets deprioritized to make room:** <specific>

**One behavior to change:** <specific, measurable>

**Goals to set or revise:** <new or updated goals for next month>
```

## Example Usage

**Scenario 1: OKR-driven month**
User has formal OKRs. Review maps each OKR to a trajectory curve, surfaces two that stalled despite intent, and produces a focused plan for next month with one OKR explicitly deprioritized.

**Scenario 2: Pattern of reactive work**
Across four weekly reviews, reactive work averaged 60%. Review surfaces it clearly, names the source (a recurring escalation pattern), and produces one structural change to trial next month.

**Scenario 3: Team member at risk**
Three consecutive weekly team health tables show a team member as "blocked" or absent. Monthly review makes the pattern undeniable. User commits to a direct 1:1 conversation as the primary action.

**Scenario 4: No weekly reviews available**
Weekly `review.md` files don't exist. Proceed with goals files and user responses only. Note the gap and recommend running end-of-week-review going forward.

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `date +%B` | Get the current month name |
| `date +%m` | Get the current month number |
| `date +%Y` | Get the current year |
| `date -d "last month" +%B` | Get last month's name |
