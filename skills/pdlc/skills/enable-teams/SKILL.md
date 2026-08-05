---
name: enable-teams
description: Produce the sales playbook, support runbook, and internal training needed so teams can sell, support, and explain the launch. Part of the PDLC Launch phase.
argument-hint: "[initiative-id]"
---

# Enable Teams

A launch fails in the field when sales, support, and customer success cannot explain or defend the product. This skill produces the enablement kit: the artifacts each front-line team needs to do their job without escalating to the PM.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `prd.md`, `messaging.md`, and `launch-plan.md`.

## Steps

1. Identify the teams to enable: sales, support, customer success, and any internal users.
2. For each team, produce the artifacts they need:
   - **Sales:** target customer profile, discovery questions, objection-handling, pricing/packaging summary, competitive talking points.
   - **Support:** what it does, known limitations, how to troubleshoot common issues, escalation path.
   - **Customer success:** migration/transition guidance for existing customers.
3. Run a dry-run or review with a representative from each team; capture what they could not answer.
4. Fill the gaps until a front-line team member can handle the common cases unaided.
5. Write `enablement-kit.md` to the initiative directory (it can reference separate asset files).

## Output Format

Use the template at `skills/pdlc/templates/initiatives/enablement-kit.md`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Each front-line team has role-specific artifacts
- [ ] Objection-handling and troubleshooting cover the common cases
- [ ] A representative from each team reviewed it (or a gap is flagged)
- [ ] Escalation path defined

## Next Step

Load `set-pricing` if not done, then run the **Launch gate** via `make-decision`.
