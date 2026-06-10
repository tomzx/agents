---
name: review-telemetry
description: Review a telemetry plan for completeness, actionability, measurability, and consistency with the specification.
---

# Review Telemetry

Audits a telemetry plan for completeness, actionability, measurability, and consistency with the specification and requirements.

## Prerequisites

- `.sdlc/features/FEAT-NNNN-<slug>/telemetry.md`, or a telemetry document provided in context or as a file path
- `.sdlc/features/FEAT-NNNN-<slug>/specification.md` (for cross-referencing)
- `.sdlc/features/FEAT-NNNN-<slug>/requirements.md` (optional, for cross-referencing acceptance criteria)
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

## Steps

1. Read the telemetry document. If reading from `.sdlc/features/FEAT-NNNN-<slug>/telemetry.md`, update `status: draft` → `status: in-review` in the frontmatter before proceeding.
2. Cross-reference against the specification and requirements.
3. Identify issues in each of the five categories below.
4. Report findings. Omit any category that has no findings.
5. After all findings are resolved: update `status: in-review` → `status: approved` in the frontmatter. Append unresolved open questions to `.sdlc/features/FEAT-NNNN-<slug>/questions.md` (create the file if it does not exist).

## Review Checklist

### Completeness
- Does every key user flow from the specification have corresponding events?
- Does every functional requirement with user-facing behavior have at least one event or metric?
- Are funnel steps complete (no gaps between entry and desired outcome)?
- Are counter metrics defined for features that could cause harm or degrade experience?

### Measurability
- Is every success metric tied to a concrete number, ratio, or threshold (not subjective)?
- Is the measurement method specified (how the metric is computed)?
- Are timeframes specified for each success metric?
- Can each event be reliably emitted from the identified location in the codebase?

### Actionability
- If a metric moves in the wrong direction, is it clear what action to take?
- Are alert thresholds reasonable (not too noisy, not too silent)?
- Do counter metrics have clear investigation triggers?

### Consistency
- Do event names follow the naming convention (snake_case, entity_action_status)?
- Are event properties typed and required/optional status marked?
- Do events reference entities and actions that match the specification's terminology?

### Coverage Gaps
- Are error states instrumented (not just happy paths)?
- Are background processes and async operations tracked where relevant?
- Is the telemetry infrastructure sufficient to support the defined events?
- Are dashboards and alerts specified for metrics that matter?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Measurability

<Findings or "No issues found.">

## Actionability

<Findings or "No issues found.">

## Consistency

<Findings or "No issues found.">

## Coverage Gaps

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Missing error events**
Specification defines a file upload flow with validation, upload, and processing steps.
Telemetry plan only has events for `upload_started` and `upload_completed`.
Report under Coverage Gaps: no events for upload failure, validation rejection, or processing timeout.

**Scenario 2: Vague metric**
Success metric says "users should find the feature useful."
Report under Measurability: no concrete threshold, no measurement method, no timeframe.

**Scenario 3: Naming inconsistency**
Specification calls the entity "invoice" but events use "bill" prefix.
Report under Consistency: event names should use `invoice_` not `bill_` to match specification terminology.

## Next Step

Once all findings are resolved and `status` is set to `approved`, continue with `/create-plan`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
