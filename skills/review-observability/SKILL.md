---
name: review-observability
description: Review an observability plan for completeness, actionability, consistency, and alignment with the specification.
---

# Review Observability

Audits an observability plan for completeness, actionability, consistency, and alignment with the specification and requirements.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/features/FEAT-NNNN-<slug>/observability.md`, or an observability document provided in context or as a file path
- `.sdlc/features/FEAT-NNNN-<slug>/specification.md` (for cross-referencing)
- `.sdlc/features/FEAT-NNNN-<slug>/telemetry.md` (optional, to avoid overlap with business metrics)
- `.sdlc/features/FEAT-NNNN-<slug>/requirements.md` (optional, for cross-referencing NFRs)

## Steps

1. Read the observability document. If reading from `.sdlc/features/FEAT-NNNN-<slug>/observability.md`, update `status: draft` → `status: in-review` in the frontmatter before proceeding.
2. Cross-reference against the specification, telemetry plan, and requirements.
3. Identify issues in each of the five categories below.
4. Report findings. Omit any category that has no findings.
5. After all findings are resolved: update `status: in-review` → `status: approved` in the frontmatter. Append unresolved open questions to `.sdlc/features/FEAT-NNNN-<slug>/questions.md` (create the file if it does not exist).

## Review Checklist

### Completeness
- Does every critical path from the specification have corresponding logs, metrics, or traces?
- Does every new endpoint or service have health checks defined?
- Does every failure mode identified in the specification have an alert or log entry?
- Are SLOs defined for features with availability or latency requirements?

### Actionability
- Does every alert have a runbook with concrete diagnostic and resolution steps?
- Is every alert tied to a human response (no "alert and forget")?
- Are log entries structured and queryable (not free-form text)?
- Do metrics include labels that allow narrowing down the issue (service, endpoint, error type)?

### Consistency
- Are metric names consistent with existing naming conventions in the codebase?
- Do log levels follow a consistent standard (INFO for normal, WARN for degraded, ERROR for failure)?
- Is there overlap or conflict with metrics already defined in the telemetry plan?
- Do trace spans align with the service boundaries described in the specification?

### Coverage Gaps
- Are error states and degraded modes observed (not just happy paths)?
- Are background processes and async operations covered?
- Are dependencies (databases, external APIs, queues) monitored for health and latency?
- Are saturation metrics (connection pools, queue depth, resource limits) included where applicable?

### Overlap with Telemetry
- Are system health metrics (observability) clearly separated from business/usage metrics (telemetry)?
- If the same event is tracked in both, is it clear which system owns it?
- Are there duplicated metrics that could cause confusion in dashboards?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Actionability

<Findings or "No issues found.">

## Consistency

<Findings or "No issues found.">

## Coverage Gaps

<Findings or "No issues found.">

## Overlap with Telemetry

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

**Scenario 1: Missing error alerts**
Specification defines a payment processing flow with external API calls.
Observability plan has latency metrics but no alert for API call failures.
Report under Completeness: no alert for upstream payment provider errors.

**Scenario 2: Unstructured logs**
Log entries are described as "log a message when the job fails."
Report under Actionability: logs should be structured with job_id, error_type, and timestamp for queryability.

**Scenario 3: Metric overlap**
Telemetry plan defines `orders_created_total` for business reporting.
Observability plan also defines `orders_created_total` for system health.
Report under Overlap with Telemetry: use `orders_request_total` (observability, includes errors) vs. `orders_created_total` (telemetry, business events only).

## Next Step

Once all findings are resolved and `status` is set to `approved`, continue with `/create-plan`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
