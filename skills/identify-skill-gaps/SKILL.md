---
name: identify-skill-gaps
description: Identify workflows the user performs that are not yet encoded as skills in the dot-claude repository, and prompt to create or backlog them. Drives a self-reinforcing improvement loop.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`

# Identify Skill Gaps

Surfaces manual workflows that could be automated as skills, then prompts to scaffold or backlog them.

## Prerequisites

- dot-claude repository available at `~/dot-claude` (for reading the existing skill library)
- Optional: `{BASE_DIR}/skill-backlog.md` (created if it does not exist when the user chooses backlog)
- Optional: activity context from the current session (summaries, standup, review files) to infer today's workflows

## Steps

### 1. Inventory existing skills

List all directories under `~/dot-claude/skills/`. This is the current skill library.

### 2. Extract workflows from context

From any activity context available in the session (GitHub summary, Slack summary, overall summary, standup, review, or conversation), identify distinct **repeated or multi-step workflows** the user executed. Focus on:

- Things done more than once, or done the same way as on previous days.
- Multi-step tasks that follow a clear pattern (collect → process → write → send).
- Anything the user said "I always do X when Y" about, explicitly or implicitly.
- Manual steps that produced an artifact (a doc, a message, a PR, a report).

### 3. Compare against existing skills

For each workflow identified, check if a matching skill already exists in the library. A skill "covers" a workflow if its name or description clearly matches the intent.

### 4. Report gaps

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

If no gaps are found, say so briefly and skip steps 5-6.

### 5. Prompt for action

Ask the user: "Would you like to create any of these skills now, or add them to a backlog?"

### 6. Act on the response

- **Yes to one or more**: scaffold a `skills/<name>/SKILL.md` for each chosen skill using standard frontmatter and a brief instructions stub, then commit and push.
- **Backlog**: append the gaps as unchecked items to `{BASE_DIR}/skill-backlog.md` (create the file if it does not exist).
- **No**: skip and close.
