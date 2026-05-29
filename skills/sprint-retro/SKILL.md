---
name: sprint-retro
description: Generate a sprint retrospective covering kudos, what went well, what could have gone better, blockers to speed, and action items. Use when the user asks for a sprint retro, retrospective, or sprint review.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=!`date +%Y-%m-%d`
YEAR=!`date +%Y`
MONTH=!`date +%m`
DAY=!`date +%d`

# Generate Sprint Retrospective

Produces a structured sprint retrospective by reviewing the past two weeks of daily notes, GitHub activity, and Slack activity.

## Prerequisites

- Slack MCP server connected and authenticated
- `gh` CLI authenticated
- `NOTES_DIR` environment variable set (resolved via `scripts/get-env NOTES_DIR`)
- `scripts/get-env` utility available
- At least one week of daily notes present in `{BASE_DIR}`

## Steps

### 1. Gather Data

1. Resolve the notes directory:
   ```
   scripts/get-env NOTES_DIR
   ```
2. Read all daily note files from the past two weeks within `{BASE_DIR}` (`.github.md`, `.slack.md`, `.overall.md`, `.timeline.md`, weekly summaries).
3. Fetch recent GitHub activity (PRs opened, reviewed, merged; issues closed) for the past two weeks using `gh`.
4. Fetch recent Slack activity via the Slack MCP server for context on collaboration, blockers, and thanks.
5. Run churn analysis to surface technical debt accumulated during the sprint:
   ```
   /git-churn-analysis month
   ```
   Note the top 3 high-churn files and the highest-priority suggestions from the report.

### 2. Analyze and Categorize

Review all gathered data and categorize findings into the five retrospective sections below.

### 3. Write Retrospective

Write the output to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.sprint-retro.md` using this template:

```markdown
# Sprint Retrospective ({TODAY})

## Kudos
People who helped, collaborated well, or went above and beyond.
- **[Person]**: [What they did and why it mattered]

## Went Well
Things that worked effectively this sprint.
- [Item with brief supporting evidence]

## Could Have Gone Better
Things that did not go as smoothly as hoped.
- [Item with brief explanation of what happened]

## What Would I Have Needed to Move Faster This Sprint?
Blockers, missing context, tooling gaps, or process friction that slowed progress.
- [Item with specific suggestion if possible]

## Technical Debt Hotspots
Files with the highest churn this sprint and the top improvement suggestion for each.
- **[file]**: [suggestion — e.g., add tests, extract helper, replace library]

## Action Items
Concrete next steps to improve the next sprint, derived from the sections above.
Include at least one item from Technical Debt Hotspots if any 🔴 High-priority suggestions exist.
- [ ] [Actionable item with owner if applicable]
```

### Guidelines for Each Section

**Kudos**: Look for thanks in Slack messages, helpful PR reviews, unblocking conversations, and collaborative problem-solving. Attribute specific contributions to specific people.

**Went Well**: Identify PRs merged smoothly, features shipped on time, effective processes, good test coverage, smooth deployments, and productive collaborations.

**Could Have Gone Better**: Surface slow PR review cycles, context-switching overhead, unclear requirements, flaky tests, repeated blockers, or communication gaps. Be constructive, not blaming.

**What Would I Have Needed to Move Faster**: Identify tooling friction, missing documentation, slow CI, waiting on dependencies, unclear ownership, or gaps in knowledge that caused delays.

**Action Items**: Derive 3-5 concrete, actionable improvements from the "Could Have Gone Better" and "Move Faster" sections. Each item should be specific enough to act on in the next sprint.

## Example Usage

**Scenario 1: Standard sprint retro**
```
/sprint-retro
```
Reviews 10 days of notes and activity. Produces a retrospective with 3 kudos, 4 went-well items, 2 improvement areas, 2 speed blockers, and 4 action items.

**Scenario 2: Quiet sprint**
Few notes and low activity. Retrospective is brief; action items focus on whether the quiet sprint was intentional or a sign of blockers.

**Scenario 3: Rough sprint**
Many blockers and slow reviews surface in the data. "Could Have Gone Better" and "Move Faster" sections are detailed; action items are prioritized by impact.

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `date +%Y-%m-%d` | Get today's date for output filename |
| `gh pr list --author @me --state merged --search "merged:>={TWO_WEEKS_AGO}"` | List merged PRs from the sprint |
| `gh pr list --reviewed-by @me --search "updated:>={TWO_WEEKS_AGO}"` | List PRs reviewed during the sprint |
| `/git-churn-analysis month` | Identify high-churn files and improvement suggestions for the sprint period |
