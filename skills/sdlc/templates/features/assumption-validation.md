---
title: "<Feature Name>"
status: draft
---

# Assumption Validation: <Feature Name>

## Summary

<One paragraph summarizing the validation outcome: how many assumptions were considered, how many validated, invalidated, or deferred, and the overall proceed/backtrack/stop verdict.>

## Assumption Inventory

All Active assumptions relevant to this feature, with their risk level and whether they require pre-implementation validation.

| Assumption | Risk | Verifiable by Code | Requires Validation | Status |
|---|---|---|---|---|
| <N-<slug> or title> | High / Medium / Low | Yes / No | Yes / No (deferred) | Active / Validated / Invalidated / Deferred |

## Experiments

### Experiment 1: <Assumption title or reference>

**Assumption:** <N-<slug> — state the assumption being tested>

**Method:** Spike / Existing code test / Load test / Integration test / API probe

**Design:** <What the experiment does, what code it touches, what it measures. Keep it minimal.>

**Pass/Fail Threshold:** <Set BEFORE running. What result confirms the assumption? What result refutes it?>

**Result:** Validated / Invalidated / Inconclusive

**Evidence:** <Concrete output: test result, measurement, API response, error message. Not "seems to work".>

**Impact if Invalidated:** <Which downstream artifacts (specification, plan, tasks) depend on this assumption and are affected.>

### Experiment 2: <Assumption title or reference>

<Repeat the structure above for each experiment.>

## Deferred Assumptions

Assumptions that cannot be validated before implementation, with the reason and a follow-up plan.

| Assumption | Risk | Reason for Deferral | Follow-up Plan |
|---|---|---|---|
| <N-<slug> or title> | High / Medium / Low | <why it cannot be tested now> | <when and how it will be validated> |

## Invalidated Assumptions and Artifact Impact

For each invalidated assumption, the affected artifacts and the action taken. Omit this section if no assumptions were invalidated.

### <Assumption title or reference>

**What was assumed:** <the assumption statement>

**What was found:** <what the experiment revealed>

**Affected artifacts:**
- `specification.md` — <what needs to change>
- `plan.md` — <what needs to change>
- `tasks/` — <which tasks are affected>

**Action taken:** Backtracked to `<phase>` and revised / Adjusted in place / Accepted risk with decision record `<N>`

## Overall Verdict

**Proceed / Backtrack / Stop**

**Rationale:** <Why this verdict follows from the individual results. Confirm all High-risk assumptions are Validated or Deferred with acknowledged risk.>

## Low-Risk Assumptions (for reference)

Assumptions with Low risk that were not validated pre-implementation. These should be monitored post-implementation.

| Assumption | Risk | Monitoring Plan |
|---|---|---|
| <N-<slug> or title> | Low | <how to watch for this being wrong in production> |
