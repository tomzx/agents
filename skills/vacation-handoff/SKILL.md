---
name: vacation-handoff
description: Generate a pre-vacation (or pre-leave) handoff covering deadline-bound work to land, on-call coverage, in-flight PRs and issues, and items to delegate. Use when the user says vacation handoff, going on leave, OOO handoff, or wants to prepare for being out.
---

# Vacation Handoff

Produces a structured handoff document so work continues smoothly while the user is out.

## Prerequisites

- `gh` CLI authenticated (to list authored/reviewing PRs and assigned issues)
- `NOTES_DIR` resolvable via `scripts/get-env NOTES_DIR` (output location)
- Leave dates (start/end) and any known coverage arrangements from the user

## Steps

### 1. Gather the user's open work

- Open PRs authored by the user (especially any with a deadline before the leave start).
- PRs where the user is a requested reviewer.
- Open issues assigned to the user.
- Recent in-flight work from the last few days of summaries/standups if available.

### 2. Confirm leave details and coverage

Ask the user (if not provided):
- Leave start and end dates.
- On-call coverage during the absence (primary/secondary swaps).
- Any specific people who should pick up specific items.

### 3. Write the handoff

Write to `{NOTES_DIR}/{YEAR}/{MONTH}/{START}-vacation-handoff.md`:

```markdown
# Vacation Handoff ({START} - {END})

## Must land before I leave
- PR/issue + owner-to-chase + deadline

## In-flight (paused while I'm out)
- Work item + current state + where to pick up

## Delegated / coverage
- Item -> person

## On-call
- Coverage arrangement

## Watch-outs
- Known risks, conflicts, fragile areas

## Contacts
- Who to ask about what
```

### 4. Offer to notify

Ask whether to draft a Slack message announcing the handoff (delegate tone to `create-message`).

## Notes

- Prioritize deadline-bound items at the top; make ownership explicit (who chases what).
- Keep each item to one line; link PRs/issues.
