---
name: review-service-levels
description: Review SLOs, SLIs, SLAs, and error budgets for measurability, coverage, and policy soundness.
---

# Review Service Levels

Audits a service-level objective set for measurability, coverage, policy soundness, and alignment with the architecture and goals.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/context/service-levels.md`, or an SLO document provided in context or as a file path.
- `.sdlc/context/architecture.md` (to verify service and journey coverage).
- `.sdlc/context/goals.md` (optional, to verify strategic alignment).

## Steps

1. Read the SLO document from `.sdlc/context/service-levels.md` if present, otherwise from context or as a file path.
2. Cross-reference against the architecture (services, journeys) and goals.
3. Identify issues in each category below.
4. Report findings. Omit any category that has no findings.
5. Write the findings to `.sdlc/context/review-service-levels.md` with frontmatter `artifact: service-levels`, `verdict` (`approved` if no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, with the findings as the body, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body.

## Review Checklist

### Measurability
- Is every SLI expressed as an explicit good/total ratio with both numerator and denominator defined?
- Is the signal source for each SLI specified (metric, log, query), and does it actually exist in the measurement infrastructure?
- Is a single rolling window used consistently across all SLOs?
- Are targets concrete percentages or counts (not "high" or "good")?

### Coverage
- Does every critical user journey from the architecture have at least one SLO?
- Are both availability and latency covered where users experience them?
- Are dependencies (databases, external APIs, queues) reflected in at least one SLI where they can break a journey?
- Are SLOs omitted for components that genuinely have no user-facing reliability, and documented as out of scope?

### Error Budget and Policy
- Is the error budget computed for each SLO (100% minus target)?
- Is there a stated policy for what happens when the budget is depleted (freeze features, escalate, prioritize reliability)?
- Are burn-rate or threshold alerts defined that surface depletion before the window ends?

### Agreements
- Where SLAs exist, are they looser than the corresponding SLO, so internal headroom protects the agreement?
- Is the consequence of an SLA breach stated (credit, penalty, escalation)?

### Alignment
- Do the SLO targets reflect the priorities in `.sdlc/context/goals.md` (a reliability-first objective implies tighter targets)?
- Is each SLO owned by a named team or person?

## Output Format

```markdown
## Measurability

<Findings or "No issues found.">

## Coverage

<Findings or "No issues found.">

## Error Budget and Policy

<Findings or "No issues found.">

## Agreements

<Findings or "No issues found.">

## Alignment

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

**Scenario 1: SLI without a clear denominator**
SLI says "low error rate" with no definition of total events.
Report under Measurability: define good and total events explicitly; an SLI must be a ratio.

**Scenario 2: No error budget policy**
SLO target is 99.9% but nothing states what happens when the budget runs out.
Report under Error Budget and Policy: an SLO without a depletion policy cannot govern prioritization.

**Scenario 3: SLA tighter than SLO**
SLA promises 99.95% but the SLO target is only 99.9%.
Report under Agreements: the SLA must be looser than the SLO or the agreement has no headroom.

## Next Step

Once the findings verdict is `approved`, the objectives are ready to govern reliability.
`observe-production` and `audit-observability` consume `.sdlc/context/service-levels.md` directly.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
