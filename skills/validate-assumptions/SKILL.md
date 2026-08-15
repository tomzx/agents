---
name: validate-assumptions
description: Collect technical assumptions accumulated during design, design and run minimal code experiments to verify the risky ones, and record results before implementation begins.
argument-hint: "[feature-id or feature-directory]"
---

# Validate Assumptions

Before implementation begins, systematically collects all technical assumptions accumulated during the design phases (codebase analysis, feasibility, specification, plan, tasks), designs minimal code experiments (spikes, tests, proofs of concept, probes) to verify the risky ones, runs them, and records results. Acts as a gate: if a critical assumption is invalidated, backtrack to the affected design phase.

This is the phase where unverified beliefs meet reality. Every assumption that carries meaningful risk gets tested with the cheapest decisive experiment before implementation commits to it.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/plan.md` (must have passed review with findings verdict `approved`)
- `.sdlc/features/N-<slug>/specification.md` (reviewed and approved)
- `.sdlc/features/N-<slug>/codebase-analysis.md` and `feasibility.md` when available (these are the primary sources of technical assumptions)
- Read `.sdlc/knowledge/assumptions/` for formally recorded assumptions relevant to this feature
- Read any files present under `.sdlc/context/` (`architecture.md`, `conventions.md`, `infrastructure.md`) for project-level context

## Steps

1. Read all design artifacts in the feature directory: `codebase-analysis.md`, `feasibility.md`, `specification.md`, `plan.md`, and task files under `tasks/`.
2. Read all assumption records in `.sdlc/knowledge/assumptions/` and filter to those relevant to this feature (by cross-references in their content, or by the feature ID in their frontmatter).
3. Scan the design artifacts for **implicit assumptions** not yet formally recorded: behavior claims about existing code, performance expectations, integration compatibility beliefs, third-party API behavior assumptions, and any "we assume" or "should" or "probably" language. For each implicit assumption that carries meaningful risk, promote it via `/create-assumption`.
4. Build the **assumption inventory**: a table of all Active assumptions (status `Active`, not yet `Validated` / `Invalidated` / `Deferred`) relevant to this feature, with their risk level (High / Medium / Low) and validation method.
5. Filter to assumptions that need validation before implementation:
   - Risk is High or Medium (Low-risk assumptions can be deferred to post-implementation monitoring)
   - Verifiable through a code experiment (assumptions about organizational processes, user behavior, or future events are out of scope here)
   - Not already validated (status is `Active`, not `Validated` or `Invalidated`)
6. If no assumptions meet these criteria, write a short note stating that no assumptions require pre-implementation validation and skip to step 12. This is a valid, complete output.
7. For each assumption needing validation, design a **minimal decisive experiment**:
   - **Spike**: write a small proof of concept to verify a technical capability (e.g., "can our ORM handle this query pattern?", "does this library support streaming responses?")
   - **Existing code test**: write a test against current code to verify a behavior assumption (e.g., "does the auth middleware already support custom claims?")
   - **Load/performance test**: verify performance or scalability claims (e.g., "can the database handle 10k concurrent connections with this schema?")
   - **Integration test**: verify compatibility assumptions (e.g., "does this library work with our framework version?")
   - **API probe**: verify third-party API behavior (e.g., "does the vendor API return results within 500ms at p99?", "does it support pagination the way the docs claim?")
   - The experiment must be the cheapest test that can decisively confirm or refute the assumption. If a test cannot be decisive, note why and defer the assumption.
   - Set a pass/fail threshold before running, not after.
8. Run each experiment. Use a worktree or the feature branch. Keep experiments small and disposable: the goal is to learn, not to produce production code. Discard spike code after recording results, or keep it only if it evolves into a real test.
9. For each experiment, record the result:
   - **Validated**: the assumption is confirmed. Update the assumption status to `Validated` via `/review-assumption`.
   - **Invalidated**: the assumption is disproved. Update the assumption status to `Invalidated` via `/review-assumption`. Identify which downstream artifacts (specification, plan, tasks) depend on this assumption and are now affected.
   - **Inconclusive**: the experiment could not decisively confirm or refute. Defer the assumption (`Deferred` via `/review-assumption`) with the risk acknowledged and a plan for when validation will be possible.
10. For each **Invalidated** assumption:
    - Assess blast radius: which specification decisions, plan phases, or tasks depend on this assumption?
    - If the assumption was critical (High risk): backtrack to the affected design phase (specification or plan), revise, and re-derive downstream artifacts. Record the backtrack via `/create-decision`.
    - If the assumption was Medium risk and the impact is contained: note the finding, adjust the affected artifacts in place, and proceed with the revised understanding.
11. Write the validation report to `.sdlc/features/N-<slug>/assumption-validation.md`.
12. Proceed to `/review-assumption-validation` only when all High-risk assumptions are `Validated` or `Deferred` with acknowledged risk. Medium-risk assumptions may be `Validated`, `Invalidated` with adjustments made, or `Deferred`.

## Handling No Assumptions

If the feature has no Active assumptions with Medium or High risk:
- Write a one-paragraph note in `assumption-validation.md` stating that no assumptions require pre-implementation validation, list any Low-risk or Deferred assumptions for reference, and mark the phase as done.
- This is a valid, complete output. Not every feature has risky assumptions.

## Output Format

Use the template at `skills/sdlc/templates/features/assumption-validation.md` (copied to `.sdlc/templates/features/assumption-validation.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | All High-risk assumptions Validated or Deferred with acknowledged risk; no critical invalidation |
| `changes-requested` | Some experiments were inconclusive or poorly designed; redo before proceeding |
| `rejected` | A critical assumption was invalidated and the feature must backtrack or stop |

## Example Usage

**Scenario 1: Spike to verify ORM capability**
The specification assumes the ORM can handle a complex polymorphic join. Confidence is Low because this query pattern was never used in the codebase.
Experiment: write a minimal spike that constructs the query against a test database and checks the result shape. If the ORM produces correct results within acceptable latency, the assumption is Validated. If it errors or produces wrong results, the assumption is Invalidated and the specification must use a different data access strategy.

**Scenario 2: Existing code test to verify auth behavior**
The codebase analysis assumes the auth middleware already supports custom JWT claims because the code references a `claims` map. No test covers this path.
Experiment: write a unit test that passes a JWT with custom claims through the middleware and asserts the claims are available downstream. If the test passes, the assumption is Validated. If it fails, the assumption is Invalidated and the specification must include extending the middleware.

**Scenario 3: API probe to verify vendor behavior**
The plan assumes a third-party API returns paginated results with cursor-based pagination. The vendor docs say so but there is no SLA.
Experiment: write a small script that calls the API with a known query and inspects the response structure and pagination headers. If the response matches expectations, the assumption is Validated. If the API uses offset pagination instead, the assumption is Invalidated and the plan's integration phase must be revised.

**Scenario 4: No risky assumptions**
A straightforward feature adds a CSV export endpoint to an existing API. The codebase analysis found no risky assumptions, feasibility was Go, and the specification makes no unverified claims.
Output: one-paragraph note stating no assumptions require validation. Phase is done.

## Completion Checklist

Before handing off to review, confirm:

- [ ] All Active assumptions with High or Medium risk were considered
- [ ] Each experiment had a pass/fail threshold set before running
- [ ] Each assumption's status was updated (Validated / Invalidated / Deferred) via `/review-assumption`
- [ ] Invalidated assumptions have affected artifacts identified
- [ ] Critical invalidations triggered backtracking with `/create-decision` recording the reason

Self-check the report against the [`review-assumption-validation` checklist](../review-assumption-validation/SKILL.md) and fix what you can, so review finds less to flag.

## Next Step

Run `/review-assumption-validation` to audit whether the validation was rigorous and complete.
If approved, continue with `/create-tasks-decomposition`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `grep` / codebase search | Verify behavior claims about existing code |
| `read` | Read source to design targeted experiments |
| `/create-assumption` | Promote implicit assumptions found during scanning |
| `/review-assumption` | Update assumption status to Validated / Invalidated / Deferred |
| `/create-decision` | Record a backtrack decision when an assumption is invalidated |
