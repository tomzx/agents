---
name: create-plan
description: Create an implementation plan with phases, milestones, dependencies, and risks from a specification or requirements document.
argument-hint: "[specification or requirements doc]"
---

# Create Plan

Produces a structured implementation plan from a specification or requirements document, organized into phases with milestones, dependencies, effort estimates, and a risk register.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/specification.md` (must have passed review with findings verdict `approved`), or a specification/requirements document provided in context or as a file path (`$1`)
- `.sdlc/features/N-<slug>/telemetry.md` (optional, if a telemetry plan was produced): include analytics instrumentation as deliverables in the plan
- `.sdlc/features/N-<slug>/observability.md` (optional, if an observability plan was produced): include logging, metrics, tracing, and alerting as deliverables in the plan
- Team size and velocity context (if available)

## Steps

1. Read the specification or requirements, and the telemetry and observability plans if present.
2. Identify all units of work and group them into logical phases.
3. Define phase goals (milestones) and their success criteria.
4. Map dependencies between phases and external factors.
5. Estimate effort for each phase (person-days or story points).
6. Identify risks and mitigations.
7. Propose a timeline if team capacity is known.
8. Write the output to `.sdlc/features/N-<slug>/plan.md`.

## Output Format

Use the template at `skills/sdlc/templates/features/plan.md` (copied to `.sdlc/templates/features/plan.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md` once the draft `plan/` PR is opened. If no PR was opened, omit the file.

## Example Usage

**Scenario 1: End-to-end feature**
Spec describes a payment flow.
Plan: Phase 1 (DB schema + migrations), Phase 2 (API endpoints), Phase 3 (frontend integration), Phase 4 (testing + hardening), Phase 5 (rollout).

**Scenario 2: High-risk external dependency**
Plan includes a spike in Phase 1 to validate a third-party payment provider integration before committing to Phase 2 scope.

## Next Step

Run `/review-plan` to audit for completeness, feasibility, and risk coverage before moving on.
Once approved, run `/publish-plan` to commit the plan and share it with the issue author, then continue with `/create-tasks-decomposition`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
