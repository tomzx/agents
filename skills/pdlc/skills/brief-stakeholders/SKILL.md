---
name: brief-stakeholders
description: Produce an exec summary, status update, or stakeholder map for a product initiative or the whole portfolio. The communication layer of the PDLC.
argument-hint: "[initiative-id]"
---

# Brief Stakeholders

Turns PDLC artifacts into communication that decision-makers and stakeholders can act on. Three modes: a single-initiative status update, an exec summary, or a stakeholder map.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- An initiative (`$1`) or the portfolio (no argument).

## Steps

1. Determine the mode from the request:
   - **Status update** — one initiative, current phase and gate history.
   - **Exec summary** — the portfolio or a major initiative, outcomes and asks.
   - **Stakeholder map** — who cares, what they need, and their current stance.
2. Read the relevant artifacts: `progress.md`, the latest decision records, `prd.md`, `health-report.md`, `feedback-loop.md`, and `.pdlc/context/goals.md` for alignment.
3. Produce the brief. Lead with the decision or ask, then the one-paragraph rationale, then evidence. Executives read top-down; put the ask first.
4. For a stakeholder map, capture each stakeholder's interest, influence, current stance (supporter / neutral / blocker), and what would move them.
5. Do not post or send anything. Present the draft. Sending requires explicit user confirmation (commit/push/PR gate).

## Output Format

```
## Status: INIT-N — <title> (<phase>, last gate: <verdict>)

Ask / decision needed: <one line>
Why it matters: <one paragraph, tied to a goal in goals.md>
Evidence: <strongest 1-2 points from artifacts>
Risks: <top risk and mitigation>
Next checkpoint: <date and what will be decided>

### Stakeholder map (if requested)
| Stakeholder | Interest | Influence | Stance | What moves them |
|---|---|---|---|---|
```

## Useful Commands Reference

No CLI commands required. Posting to Slack, email, or GitHub is out of scope for this skill and must be triggered explicitly by the user.

## Next Step

If the brief surfaces a needed decision, run `make-decision`. If it surfaces a kill, run `kill-initiative`.

## Completion Checklist

- [ ] The ask or decision is stated in the first line
- [ ] Rationale tied to a goal in `goals.md`
- [ ] No artifacts quoted verbatim; synthesized for the audience
- [ ] Sending deferred until explicit confirmation
