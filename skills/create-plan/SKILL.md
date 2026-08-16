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
- `.sdlc/features/N-<slug>/lifecycle.md` (optional, if a lifecycle document was produced): include state machine implementation, invariant enforcement, and retention policy work as deliverables in the plan
- `.sdlc/features/N-<slug>/telemetry.md` (optional, if a telemetry plan was produced): include analytics instrumentation as deliverables in the plan
- `.sdlc/features/N-<slug>/observability.md` (optional, if an observability plan was produced): include logging, metrics, tracing, and alerting as deliverables in the plan
- Team size and velocity context (if available)

## Steps

1. Read the specification or requirements, and the lifecycle, telemetry, and observability plans if present.
2. **Determine the plan structure** (see [Plan Structure](#plan-structure-unified-vs-split)):
   - Identify the distinct concerns the work spans from the spec (e.g., database/models, API, CLI, SDK, frontend).
   - Ask the user whether to produce a **unified** plan (`plan.md`) or a **split** plan set (`plan/` directory, one file per concern plus an `index.md`). Use the `question` tool when available; otherwise ask conversationally and wait for the answer.
   - When the user picks split, confirm the concern list and one-word slugs (lowercase, hyphenated) that will name each `plan/<concern>.md` file.
   - Under automation (`$OUTCOME_YAML` set, no interactive user), default to **unified** and note the choice in the plan. If the spec clearly names multiple independent components and a split is obviously warranted, you may still default to unified; the structure can be split later during review.
3. Identify all units of work and group them into logical phases. For a split plan, group phases *within each concern*; for a unified plan, group them globally.
4. Define phase goals (milestones) and their success criteria.
5. Map dependencies between phases and external factors as a Mermaid `flowchart TD` (Phase Dependencies), so parallel tracks and unintended serialization are visible at a glance. For a split plan, capture cross-concern dependencies in `plan/index.md` the same way.
6. Estimate effort for each phase (person-days or story points).
7. Identify risks and mitigations.
8. Record assumptions that the plan depends on but has not verified. Risks in the risk register often encode assumptions (e.g., "the third-party API will be available by Phase 2", "the team will have the required capacity", "the database migration will not require downtime"). For each assumption that carries meaningful risk, promote it via `/create-assumption` so it is tracked and can be validated before implementation.
9. Propose a timeline if team capacity is known: render it as a Mermaid `gantt` (one section per phase, or per concern for a split plan) when calendar dates are estimable; otherwise keep a duration-only table.
10. Validate best-effort: render each `mermaid` block with `mmdc` (or `npx -y @mermaid-js/mermaid-cli`) when available. A missing tool is skipped; a render failure is a defect to fix before handoff.
11. Write the output:
    - **Unified:** `.sdlc/features/N-<slug>/plan.md`.
    - **Split:** `.sdlc/features/N-<slug>/plan/index.md` plus one `.sdlc/features/N-<slug>/plan/<concern>.md` per concern.

## Plan Structure (Unified vs Split)

Two layouts are supported. They are interchangeable for downstream skills (`review-plan`, `publish-plan`, `create-tasks-decomposition`), which resolve the plan via `plan.md` first, then `plan/index.md`.

- **Unified** (default): a single `.sdlc/features/N-<slug>/plan.md` covering all phases, milestones, dependencies, risks, and timeline. Best when the work is one cohesive feature with tightly coupled phases.
- **Split**: a `.sdlc/features/N-<slug>/plan/` directory containing:
  - `index.md` — the cross-cutting entry point: goal, the list of concerns with links, shared milestones, the cross-concern dependency table, the aggregated risk register, and the consolidated timeline.
  - `<concern>.md` — one file per concern (e.g., `database.md`, `api.md`, `cli.md`, `sdk.md`), each with its own goal, phases, deliverables, effort estimates, and concern-local risks.

  Best when the work spans several independent components or teams that each warrant their own phased breakdown. Prefer split only when concerns are numerous or independently owned; otherwise unified is simpler.

## Output Format

- **Unified:** use the template at `skills/sdlc/templates/features/plan.md` (copied to `.sdlc/templates/features/plan.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to `.sdlc/features/N-<slug>/plan.md`.
- **Split:** use `skills/sdlc/templates/features/plan-index.md` for `plan/index.md` and `skills/sdlc/templates/features/plan-concern.md` for each `plan/<concern>.md`. Write them under `.sdlc/features/N-<slug>/plan/`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md` once the draft `plan/` PR is opened. If no PR was opened, omit the file.

## Example Usage

**Scenario 1: End-to-end feature**
Spec describes a payment flow.
Plan: Phase 1 (DB schema + migrations), Phase 2 (API endpoints), Phase 3 (frontend integration), Phase 4 (testing + hardening), Phase 5 (rollout).

**Scenario 2: High-risk external dependency**
Plan includes a spike in Phase 1 to validate a third-party payment provider integration before committing to Phase 2 scope.
Assumptions promoted: "the payment provider API supports tokenized recurring charges" (High risk, validate via API probe in Phase 1 spike), "the webhook retry policy handles at-least-once delivery" (Medium risk, validate via integration test in Phase 1 spike).

**Scenario 3: Split by concern**
Spec describes a feature spanning a new database schema, a public API, a CLI, and an SDK. The user picks split.
Output: `plan/index.md` (cross-concern milestones, deps, risks, timeline) plus `plan/database.md`, `plan/api.md`, `plan/cli.md`, `plan/sdk.md`, each with its own phases and deliverables.

## Completion Checklist

Before handing off to review, confirm:

- [ ] Telemetry and observability deliverables pulled into the plan as explicit work items
- [ ] Risky assumptions from the risk register promoted via `/create-assumption`
- [ ] Phase dependencies rendered as a Mermaid `flowchart TD` (cross-concern for a split plan)
- [ ] Timeline rendered as a Mermaid `gantt` when calendar dates are estimable, duration-only table otherwise
- [ ] If split: every concern has its own `plan/<concern>.md`, and `plan/index.md` lists them all plus the shared milestones, cross-concern dependencies, aggregated risks, and consolidated timeline

Self-check the draft against the [`review-plan` checklist](../review-plan/SKILL.md) and fix what you can, so review finds less to flag.

## Next Step

Run `/review-plan` to audit for completeness, feasibility, and risk coverage before moving on.
Once approved, run `/publish-plan` to commit the plan and share it with the issue author, then continue with `/create-tasks-decomposition`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `mmdc -i <diagram.mmd>` or `npx -y @mermaid-js/mermaid-cli` | Best-effort Mermaid render check for the dependency flowchart and gantt |
