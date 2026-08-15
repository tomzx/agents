---
name: review-assumption-validation
description: Review an assumption validation report for completeness, experiment quality, result rigor, and soundness of the proceed or backtrack decision.
argument-hint: "[validation-report or feature-directory]"
---

# Review Assumption Validation

Audits an assumption validation report and reports findings across five categories: completeness, experiment quality, result rigor, impact assessment, and verdict soundness.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/assumption-validation.md`, or a validation report provided in context or as a file path
- Access to `.sdlc/knowledge/assumptions/` to cross-check assumption statuses

## Steps

1. Read the assumption validation report from `.sdlc/features/N-<slug>/assumption-validation.md` if present, otherwise from context or as a file path.
2. Read the assumption records in `.sdlc/knowledge/assumptions/` to cross-check that statuses were updated consistently with the report's claims.
3. Read the design artifacts (`specification.md`, `plan.md`, `tasks/`) to verify that invalidated assumptions were followed by artifact revisions where needed.
4. Evaluate the report against the checklist below.
5. Report findings by category. Omit categories with no findings.
6. Write the findings to `.sdlc/features/N-<slug>/review-assumption-validation.md` with frontmatter `artifact: assumption-validation`, `verdict` (`approved` / `changes-requested` / `rejected`), and `reviewed_at: <ISO date>`, and the findings as the body, per `skills/sdlc/references/shared.md`.

## Review Checklist

### Completeness
- Were all Active assumptions with High or Medium risk considered for validation?
- Were implicit assumptions in the design artifacts scanned for, not just formally recorded ones?
- Were Low-risk assumptions listed for reference even if not validated?
- If the report claims no assumptions needed validation, is that claim justified by the artifacts?

### Experiment Quality
- Was each experiment the cheapest decisive test available for the assumption?
- Was a pass/fail threshold set before running each experiment, not after?
- Did each experiment actually test the stated assumption, or did it test something adjacent?
- Were spike experiments kept minimal and disposable, not creeping toward implementation?

### Result Rigor
- Are results backed by concrete evidence (test output, measurements, API responses) rather than "seems to work"?
- For Validated assumptions, is the evidence sufficient to justify the confidence level?
- For Invalidated assumptions, is the disproval clear and unambiguous?
- For Inconclusive results, is the reason for inconclusiveness explained and a follow-up plan stated?

### Impact Assessment
- For each Invalidated assumption, are the affected downstream artifacts (specification, plan, tasks) identified?
- Was backtracking performed for critical (High-risk) invalidations?
- Were backtrack decisions recorded via `/create-decision`?
- Were affected artifacts actually revised, or just noted as "affected" without changes?

### Verdict Soundness
- Does the overall proceed/backtrack/stop decision logically follow from the individual results?
- Are all High-risk assumptions either Validated or Deferred with acknowledged risk before proceeding?
- If Medium-risk assumptions were Deferred, is the deferral justified and the risk accepted explicitly?
- Is there a plan for validating Deferred assumptions post-implementation (e.g., monitoring, follow-up spike)?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Experiment Quality

<Findings or "No issues found.">

## Result Rigor

<Findings or "No issues found.">

## Impact Assessment

<Findings or "No issues found.">

## Verdict Soundness

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; all High-risk assumptions are Validated or Deferred with acknowledged risk |
| `changes-requested` | Some experiments were inconclusive or poorly designed; redo before proceeding |
| `rejected` | A critical assumption was invalidated and backtracking was not performed, or the proceed decision is unsound |

## Example Usage

**Scenario 1: Missing assumption**
The report validates three assumptions but the feasibility document mentions a fourth (third-party API rate limits) that was never formally recorded or tested. Flag under Completeness: promote via `/create-assumption` and design an experiment.

**Scenario 2: Experiment tested the wrong thing**
An assumption says "the ORM handles polymorphic joins" but the experiment tested a simple join, not a polymorphic one. Flag under Experiment Quality: the experiment does not test the stated assumption.

**Scenario 3: Invalidated assumption without backtracking**
An assumption was Invalidated (the auth middleware does not support custom claims) but the specification was not revised to include extending the middleware. Flag under Impact Assessment: revise the specification to account for the finding.

**Scenario 4: Proceeding with invalidated High-risk assumption**
A High-risk assumption was Invalidated but the report says "proceed anyway." Flag under Verdict Soundness: either backtrack to revise the affected artifacts or explicitly accept the risk with a decision record.

## Next Step

Once the findings verdict is `approved`, continue with `/create-tasks-decomposition`.
If the findings verdict is `changes-requested`, address the findings and re-run `/validate-assumptions` for the affected experiments.
If the findings verdict is `rejected`, backtrack to the affected design phase and revise.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context and cross-checks against assumption records and design artifacts.
