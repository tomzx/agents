---
name: create-feasibility
description: Assess technical, financial, and operational viability of a feature before committing to requirements.
argument-hint: "[issue-url or feature-name]"
---

# Create Feasibility Assessment

Produces a structured feasibility assessment for a proposed feature, evaluating technical, financial, and operational viability before the project invests in full requirements gathering. Acts as a go/no-go gate.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, use `$ISSUE_TITLE` and `$ISSUE_BODY` as the feature description (and `$ISSUE_NUMBER` to link the feature).
- A reviewed, prioritized GitHub issue or feature description provided as `$1`
- `.sdlc/features/N-<slug>/requirements.md`, `existing-solutions.md`, and `codebase-analysis.md` when available: the codebase analysis in particular feeds the cost and risk of changing existing code
- Read any files present under `.sdlc/context/` (`project-overview.md`, `architecture.md`, `conventions.md`) for project-level context
- Apply any artifact style rules found in `conventions.md` to the produced document

## Steps

1. Read the issue or feature description. Fetch from GitHub if a URL is provided.
2. Read `.sdlc/context/architecture.md` to understand the current system and technology stack.
3. Read `.sdlc/context/project-overview.md` to understand project scope and constraints.
4. Read `.sdlc/features/N-<slug>/codebase-analysis.md` when available, and carry its changeability assessments and migration risks into the technical and effort estimates below.
5. Assess **technical feasibility**: can the feature be built with the current stack and integrations? Are there unknowns that require a spike?
6. Assess **financial feasibility**: what is the estimated effort (S/M/L/XL)? Are there infrastructure, licensing, or third-party costs?
7. Assess **operational feasibility**: does the team have the skills and availability? Does it fit the roadmap? What is the maintenance burden?
8. For each dimension, assign a verdict: Feasible / Feasible with conditions / Not feasible.
9. Derive the overall go/no-go decision. If any dimension is "Not feasible", the overall verdict is "No-go". If any dimension is "Feasible with conditions", list the conditions.
10. Derive the feature directory name `N-<slug>` following the Feature Directory Naming convention in `skills/sdlc/references/shared.md`: use the issue number as `N` when one is available, otherwise a `p`-prefixed sequence number (`p1`, `p2`, ...) marking the feature as pending a placeholder issue. Record the related issue number in the frontmatter `issue` field only when an issue exists.
11. Write the output to `.sdlc/features/N-<slug>/feasibility.md`, creating the directory if it does not exist.

## Output Format

Use the template at `skills/sdlc/templates/features/feasibility.md` (copied to `.sdlc/templates/features/feasibility.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Handling No-Go Verdicts

If the overall verdict is **No-go**:
- Update the issue with the feasibility findings and the rejection rationale.
- Do not create the feature directory or proceed to requirements.
- The issue may be revisited if conditions change (new budget, new technology, reprioritized roadmap).

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | Overall go/no-go |
|---|---|
| `approved` | Go or Go with conditions |
| `rejected` | No-go (see Handling No-Go Verdicts) |

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
If approved, continue with `/create-specifications`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `ghx issue view <url> --comments` | Fetch issue details and comments (cached) |
