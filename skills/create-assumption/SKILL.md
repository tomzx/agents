---
name: create-assumption
description: Record an assumption made during implementation with its basis, risk, and validation plan.
argument-hint: "[assumption topic or context]"
---

# Create Assumption

Records an assumption made during implementation: what is being assumed, why, how confident the team is, what breaks if the assumption is wrong, and how to validate it.

Assumptions differ from decisions: a decision is a deliberate choice between known options; an assumption is something believed to be true that has not been fully verified.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- An assumption that was made (implicitly or explicitly) during design or implementation
- Enough context to assess its basis and risk

## Steps

1. State the assumption clearly and specifically.
2. Describe the basis: what evidence or reasoning supports it.
3. Assess confidence level and risk if the assumption is wrong.
4. Describe the impact on the implementation if the assumption turns out to be false.
5. Define a validation plan: how and when to confirm or refute the assumption.
6. Save the document to `.sdlc/knowledge/assumptions/` using the filename pattern `N-<slug>.md` where `N` is the next available number (counting existing files in that directory).

## Output Format

Use the template at `skills/sdlc/templates/knowledge/assumption.md` (copied to `.sdlc/templates/knowledge/assumption.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Example Usage

**Scenario 1: Load assumption**
Assuming the service will handle at most 1,000 concurrent users based on the current contract.
Basis: product manager's statement in the kick-off meeting.
Confidence: Medium (verbal, not written).
Risk if wrong: connection pool and caching strategy are sized for this load; exceeding it causes timeouts.
Validation: confirm in writing with PM before go-live.

**Scenario 2: Third-party API behavior**
Assuming a vendor API returns results within 500ms at p99.
Basis: vendor's marketing docs; no SLA contract yet.
Confidence: Low.
Risk if wrong: timeout budgets in the gateway are set to 600ms; slow responses cascade.
Validation: run a latency spike against the staging endpoint in Phase 1.

**Scenario 3: User behaviour**
Assuming users will complete onboarding in a single session.
Basis: UX research from a similar product two years ago.
Confidence: Medium.
Risk if wrong: multi-session onboarding requires persisting partial state, which is not currently designed.
Validation: monitor drop-off in the first two weeks after launch.

## Useful Commands Reference

No CLI commands required. This skill operates on information provided in context and writes a Markdown file.
