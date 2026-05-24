---
name: recent-work-and-needs
description: Write a personal status article covering what you have been working on recently and what you currently need. Draws from notes, goals, and action items, then uses write-article to produce a polished piece.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=!`date +%Y-%m-%d`
YEAR=!`date +%Y`
MONTH=!`date +%m`
DAY=!`date +%d`
WEEK=!`date +%V`

# Recent Work and Needs

Produces a personal status article with two sections: what you have been working on recently, and what you see as your current needs. Useful for standup context, manager syncs, personal reflection, or sharing with collaborators.

## Prerequisites

- `NOTES_DIR` environment variable set (resolved via `scripts/get-env NOTES_DIR`)
- `scripts/get-env` utility available
- Optional: `{BASE_DIR}/goals.md` with current personal goals
- Optional: `{BASE_DIR}/team-goals.md` with current team goals
- Optional: daily note files from the past two weeks in `{BASE_DIR}/{YEAR}/{MONTH}/`
- Optional: `{BASE_DIR}/{YEAR}/weekly/{WEEK}/action-items.md`

## Steps

### 1. Gather Recent Work

Read daily note files from the past two weeks in `{BASE_DIR}/{YEAR}/{MONTH}/` (and the prior month's folder if the two-week window crosses a month boundary). Look for:

- Features completed or shipped
- Problems investigated or resolved
- Significant decisions made
- Code or systems changed
- Collaborations and meetings with material outcomes

Discard routine administrative activity (recurring standups, calendar management) unless it produced a notable outcome.

### 2. Gather Current Needs

Read if they exist:
- `{BASE_DIR}/goals.md`
- `{BASE_DIR}/team-goals.md`
- `{BASE_DIR}/{YEAR}/weekly/{WEEK}/action-items.md`

From this context, identify:

- Blockers: things that cannot move forward without external input, a decision, or a dependency resolving
- Resources: tools, access, people, or time that would meaningfully accelerate current work
- Clarity gaps: areas where the goal, scope, or approach is still ambiguous
- Support: collaboration or review that is needed from specific people

Ask the user: "Are there any current needs I should include that aren't in your notes?"

### 3. Produce the Article

Use the `write-article` skill with the following inputs:

- **Target audience**: The user's intended reader (ask if not obvious from context; default to "a direct collaborator or manager")
- **Topic**: Personal work status covering recent activity and current needs
- **Sources**: The synthesized notes from steps 1 and 2, plus any additional input from the user

Apply `write-article`'s quality criteria. In particular:

- Open with the most significant or interesting recent work, not a chronological list
- Under current needs, be specific: name the blocker, the person whose input is needed, or the resource required
- Avoid vague language ("working on various things", "need more support") -- name the thing

### 4. Write Output

Write the finished article to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.recent-work-and-needs.md`.

## Article Structure

```markdown
# [Title: personal, specific, not generic -- e.g. "Where I am: week of 2026-05-24"]

[Lead: 1-2 sentences framing the period and its defining theme. Skip if nothing stands out.]

## What I Have Been Working On

[Narrative or short list of recent work. Group related items. Lead with what is most significant.
Prefer concrete outputs over activities: "shipped X", "resolved Y", "decided Z".]

## What I Currently Need

[Specific needs, each with enough context to act on:
- Blocker from <person or system>: <what is needed and why>
- Clarity on <topic>: <what is ambiguous>
- Access to <resource>: <what it unlocks>
Omit this section entirely if there are no real needs right now.]
```

## Quality Criteria

Apply `write-article` quality criteria plus:

- Every need should be specific enough that someone reading it knows what to do
- Recent work should show outputs and decisions, not just effort
- The article should be useful to someone who has not spoken to you in two weeks

## Example Usage

**Scenario 1: Manager sync**
Two weeks of notes, goals file present, one open blocker. Output: a three-paragraph article naming the shipped feature, the investigation underway, and a specific request for a decision on scope.

**Scenario 2: Quiet period**
Light notes, no blockers. Output: honest brief summary of maintenance work done, no needs section.

**Scenario 3: Many open threads**
Five parallel workstreams. Output: groups related items into two or three themes rather than listing all five separately, with needs section calling out the one critical blocker.

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `date +%Y-%m-%d` | Get today's date |
| `date +%V` | Get the ISO week number |
| `date +%m` | Get current month |
