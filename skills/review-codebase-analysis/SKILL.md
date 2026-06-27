---
name: review-codebase-analysis
description: Review a codebase analysis for coverage of relevant components, accuracy of behavior claims, rigor of changeability assessments, and completeness of migration and impact analysis.
---

# Review Codebase Analysis

Audits a codebase analysis and reports findings across five categories: coverage, accuracy, changeability rigor, and impact and migration completeness.
The review verifies that the analysis describes the real code (not assumptions) and that every change disposition is justified and de-risked.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/features/FEAT-NNNN-<slug>/codebase-analysis.md`, or an analysis document provided in context or as a file path
- `.sdlc/features/FEAT-NNNN-<slug>/requirements.md` (optional, improves coverage analysis)

## Steps

1. Read the analysis. If reading from `.sdlc/features/FEAT-NNNN-<slug>/codebase-analysis.md`, update `status: draft` → `status: in-review` in the frontmatter before proceeding.
2. Cross-reference against the requirements document if available: every requirement that implies a code change should map to an analyzed component.
3. Spot-check the analysis against the actual codebase to confirm behavior claims and paths.
4. Identify issues in each of the categories below.
5. Report findings. Omit any category that has no findings.
6. After all findings are resolved: update `status: in-review` → `status: approved` in the frontmatter. Append unresolved open questions to `.sdlc/features/FEAT-NNNN-<slug>/questions.md` (create the file if it does not exist). For any question that carries meaningful risk, also invoke `/create-assumption` to record it formally. For a chosen change disposition with lasting consequences (e.g. replace vs. extend), invoke `/create-decision`.

## Review Checklist

### Coverage
- Does the analysis address every requirement that implies a change to existing code, or are touched components missing?
- Are the search entry points recorded (queries, paths) so the scope is auditable?
- For a greenfield verdict, is the integration boundary (where it attaches to existing systems) actually empty, or was existing code overlooked?

### Accuracy
- Are component responsibilities and paths correct and current (verify against the codebase, not the prose)?
- Are behavior claims (ordering guarantees, error handling, side effects) backed by the source rather than assumed?
- Is any stale or recently changed code treated as current?

### Changeability Rigor
- Is each component assigned exactly one disposition (reuse, extend, refactor, replace)?
- Is every disposition justified by a rationale tied to the requirements and the coupling map, not by preference?
- Is the risk of each disposition stated, and is the risk driver concrete?
- Are the "must not change" constraints (public API, data formats, behavior contracts) explicit for extend/refactor/replace?

### Impact and Migration
- For every refactor or replace disposition, is the blast radius mapped (what else depends on the changed part)?
- Is there a migration path from current to target behavior, with backward compatibility and rollout strategy?
- Are de-risking measures considered (feature flag, dual-run, shadow comparison) for high-risk changes?
- If the section is omitted, is that justified (i.e. only reuse/extend dispositions, or greenfield)?

### Coupling Awareness
- Are dependencies between relevant components and external systems mapped, including shared state and synchronous vs. asynchronous boundaries?
- Does the changeability assessment account for the coupling, or does it ignore downstream effects?

## Output Format

```markdown
## Coverage

<Findings or "No issues found.">

## Accuracy

<Findings or "No issues found.">

## Changeability Rigor

<Findings or "No issues found.">

## Impact and Migration

<Findings or "No issues found.">

## Coupling Awareness

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

## Example Usage

**Scenario 1: A touched component was missed**
The requirements imply changes to a shared cache layer, but the analysis only covers the reconciliation loop.
Report under Coverage.

**Scenario 2: Behavior claim contradicts the code**
The analysis claims a consumer reads asynchronously, but the source shows a synchronous call, which changes the blast radius.
Report under Accuracy.

**Scenario 3: Replace disposition without a migration path**
The analysis recommends replacing the polling loop with an event-driven consumer but gives no rollout, backward-compatibility, or de-risking plan.
Report under Impact and Migration.

**Scenario 4: Risk stated without a driver**
A component is marked "Replace, High risk" with no explanation of what drives the risk.
Report under Changeability Rigor.

## Next Step

Once all findings are resolved and `status` is set to `approved`, continue with `/create-feasibility`, which consumes this analysis to judge viability and cost.

## Useful Commands Reference

| Command | Description |
|---|---|
| `read` / `grep` | Verify component paths and behavior claims against the actual source |
| `/create-assumption` | Formalize an unresolved open question that carries risk |
| `/create-decision` | Record a change disposition with lasting consequences |
