---
name: create-needs-assessment
description: Evaluate whether a proposed feature addresses a genuine need before investing in feasibility or requirements, examining the problem, stakeholders, alternatives, and cost of inaction.
argument-hint: "[issue-url or feature-description]"
---

# Assess Needs

Evaluates whether a proposed feature addresses a genuine need before investing in feasibility or requirements. Acts as the earliest "should we build this?" gate in the SDLC pipeline by examining the problem, the stakeholders, the alternatives already available, and the cost of not building it.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, use `$ISSUE_TITLE` and `$ISSUE_BODY` as the feature description (and `$ISSUE_NUMBER` to link the feature).
- A reviewed, prioritized GitHub issue or feature description provided as `$1`
- Read any files present under `.sdlc/context/` (`project-overview.md`, `goals.md`, `architecture.md`, `conventions.md`) for project-level context
- Apply any artifact style rules found in `conventions.md` to the produced document

## Steps

1. Read the issue or feature description. Fetch from GitHub if a URL is provided.
2. Read `.sdlc/context/project-overview.md` to understand project scope, goals, and constraints.
3. Identify the **problem** the feature claims to solve. If the issue only describes a solution (a feature), work backward to the underlying problem.
4. Identify the **stakeholders**: who experiences this problem and who benefits from the solution.
5. Assess the **evidence**: is the need demonstrated by user requests, support tickets, usage data, competitive analysis, or is it an assumption?
6. Assess **what happens if we do nothing**: the cost of the status quo, including workarounds people already use.
7. Assess **alternative paths**: could this need be met by an existing feature, a configuration change, better documentation, or a process change instead of new code?
8. Read `.sdlc/context/goals.md` if present, then assess **strategic alignment**: which specific objective and key result does this need advance, or is it tangential? If `goals.md` is absent, note that alignment cannot be checked and flag it as an open question.
9. For each dimension, assign a rating: Strong / Moderate / Weak / None.
10. Derive the overall needs verdict: Needed / Nice-to-have / Not needed.
11. Derive the feature directory name `N-<slug>` following the Feature Directory Naming convention in `skills/sdlc/references/shared.md`: use the issue number as `N` when one is available, otherwise a `p`-prefixed sequence number (`p1`, `p2`, ...) marking the feature as pending a placeholder issue. Record the related issue number in the frontmatter `issue` field only when an issue exists.
12. Write the output to `.sdlc/features/N-<slug>/needs-assessment.md`, creating the directory if it does not exist.

## Output Format

Use the template at `skills/sdlc/templates/features/needs-assessment.md` (copied to `.sdlc/templates/features/needs-assessment.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Handling Not-Needed Verdicts

If the overall verdict is **Not needed**:
- Update the issue with the needs assessment findings and the rejection rationale.
- Do not create the feature directory or proceed to feasibility.
- The issue may be revisited if new evidence emerges (user demand increases, strategic direction changes).

If the overall verdict is **Nice-to-have**:
- The feature may proceed to `/create-feasibility`, but the downstream artifacts should reflect the lower priority.
- Flag the verdict in the feasibility assessment so cost-benefit is weighted accordingly.

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | Overall needs verdict |
|---|---|
| `approved` | Needed or Nice-to-have |
| `rejected` | Not needed (see Handling Not-Needed Verdicts) |
| `needs-info` | Insufficient evidence to decide |

## Example Usage

**Scenario 1: Clear need**
Issue asks for SSO support. Multiple enterprise customers have requested it, the sales team reports lost deals without it, and the cost of inaction is growing. Evidence is strong, strategic alignment is strong. Verdict: Needed.

**Scenario 2: Solution without a stated problem**
Issue asks for a "dashboard redesign." No user complaints about the current dashboard, usage data shows it is actively used, and no stakeholder is identified beyond the author. Verdict: Not needed (or Nice-to-have at best, pending evidence).

**Scenario 3: Need met by existing tooling**
Issue asks for a notification system. Investigation reveals the project already uses Slack webhooks for this purpose, and stakeholders report satisfaction. Alternative path exists. Verdict: Not needed, suggest documenting the existing approach instead.

**Scenario 4: Genuine need but weak evidence**
Issue describes a problem that sounds real (slow onboarding for new developers) but no data or tickets back it up. Evidence rating is Weak. Verdict: Nice-to-have, with an open question asking the team to validate the pain before investing further.

## Next Step

Run `/review-needs-assessment` to audit the assessment for rigor, evidence quality, and soundness of the verdict.
If the need is validated (Needed or Nice-to-have), continue with `/create-requirements`.
If the need is rejected (Not needed), update the issue and stop the pipeline.

## Useful Commands Reference

| Command | Description |
|---|---|
| `ghx issue view <url> --comments` | Fetch issue details and comments (cached) |
