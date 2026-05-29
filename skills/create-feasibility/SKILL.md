---
name: create-feasibility
description: Assess technical, financial, and operational viability of a feature before committing to requirements.
argument-hint: "[issue-url or feature-name]"
---

# Create Feasibility Assessment

Produces a structured feasibility assessment for a proposed feature, evaluating technical, financial, and operational viability before the project invests in full requirements gathering. Acts as a go/no-go gate.

## Prerequisites

- A reviewed, prioritized GitHub issue or feature description provided as `$1`
- Read any files present under `.sdlc/context/` (`project-overview.md`, `architecture.md`, `conventions.md`) for project-level context
- Apply any artifact style rules found in `conventions.md` to the produced document

## Steps

1. Read the issue or feature description. Fetch from GitHub if a URL is provided.
2. Read `.sdlc/context/architecture.md` to understand the current system and technology stack.
3. Read `.sdlc/context/project-overview.md` to understand project scope and constraints.
4. Assess **technical feasibility**: can the feature be built with the current stack and integrations? Are there unknowns that require a spike?
5. Assess **financial feasibility**: what is the estimated effort (S/M/L/XL)? Are there infrastructure, licensing, or third-party costs?
6. Assess **operational feasibility**: does the team have the skills and availability? Does it fit the roadmap? What is the maintenance burden?
7. For each dimension, assign a verdict: Feasible / Feasible with conditions / Not feasible.
8. Derive the overall go/no-go decision. If any dimension is "Not feasible", the overall verdict is "No-go". If any dimension is "Feasible with conditions", list the conditions.
9. Derive the feature directory name: `FEAT-NNNN-<slug>` where `NNNN` is the next available four-digit sequence number within `.sdlc/features/` (count existing subdirectories, zero-pad). Slug is lowercase, hyphens for spaces. Record the related issue number in the frontmatter `issue` field, not in the directory name.
10. Write the output to `.sdlc/features/FEAT-NNNN-<slug>/feasibility.md`, creating the directory if it does not exist.

## Output Format

```markdown
---
issue: "#<N>"
title: "<Feature Name>"
status: draft
---

# Feasibility Assessment: <Feature Name>

## Overview

<One paragraph summarizing the feature idea and why it is being considered.>

## Technical Feasibility

| Criterion | Assessment |
|---|---|
| Required technologies | <Available in-house / New / Unknown> |
| Integration complexity | <Low / Medium / High> |
| Technical risks | <Key technical unknowns> |
| Existing components to reuse | <What can be leveraged> |

**Verdict:** Feasible / Feasible with conditions / Not feasible

## Financial Feasibility

| Criterion | Assessment |
|---|---|
| Estimated effort | <S / M / L / XL> |
| Infrastructure costs | <Ongoing costs, hosting, licenses> |
| Third-party costs | <APIs, SaaS, tooling> |
| ROI expectation | <Expected value vs. cost> |

**Verdict:** Feasible / Feasible with conditions / Not feasible

## Operational Feasibility

| Criterion | Assessment |
|---|---|
| Team availability | <Available / Partially / Not available> |
| Skill gaps | <What training or hiring is needed> |
| Maintenance burden | <Low / Medium / High> |
| Organizational alignment | <Fits roadmap / Tangential / Misaligned> |

**Verdict:** Feasible / Feasible with conditions / Not feasible

## Go/No-Go Decision

**Overall verdict:** Go / Go with conditions / No-go

**Conditions (if any):**

- <Condition that must be met before proceeding to requirements>

## Open Questions

1. <Question that needs an answer before a final decision>
```

## Handling No-Go Verdicts

If the overall verdict is **No-go**:
- Update the issue with the feasibility findings and the rejection rationale.
- Do not create the feature directory or proceed to requirements.
- The issue may be revisited if conditions change (new budget, new technology, reprioritized roadmap).

## Example Usage

**Scenario 1: Straightforward feature**
User describes "add CSV export to the dashboard."
Current stack already handles file generation. Low effort, no new dependencies. Verdict: Go.

**Scenario 2: Feature with unknowns**
User describes "add real-time collaboration like Google Docs."
Requires WebSocket infrastructure not currently in the stack, high effort, significant operational burden. Verdict: Feasible with conditions (requires infrastructure spike and dedicated team).

**Scenario 3: Clear no-go**
User describes "migrate the entire platform to a different cloud provider in 2 weeks."
Not operationally feasible given team size and timeline. Verdict: No-go.

## Next Step

Run `/review-feasibility` to audit the assessment for completeness, risk coverage, and soundness of the go/no-go decision.
If approved, continue with `/create-requirements`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh-cached issue view <url> --comments` | Fetch issue details and comments (cached) |
