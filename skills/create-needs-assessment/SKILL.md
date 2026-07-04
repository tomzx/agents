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
- Read any files present under `.sdlc/context/` (`project-overview.md`, `architecture.md`, `conventions.md`) for project-level context
- Apply any artifact style rules found in `conventions.md` to the produced document

## Steps

1. Read the issue or feature description. Fetch from GitHub if a URL is provided.
2. Read `.sdlc/context/project-overview.md` to understand project scope, goals, and constraints.
3. Identify the **problem** the feature claims to solve. If the issue only describes a solution (a feature), work backward to the underlying problem.
4. Identify the **stakeholders**: who experiences this problem and who benefits from the solution.
5. Assess the **evidence**: is the need demonstrated by user requests, support tickets, usage data, competitive analysis, or is it an assumption?
6. Assess **what happens if we do nothing**: the cost of the status quo, including workarounds people already use.
7. Assess **alternative paths**: could this need be met by an existing feature, a configuration change, better documentation, or a process change instead of new code?
8. Assess **strategic alignment**: does solving this need advance the project's stated goals, or is it tangential?
9. For each dimension, assign a rating: Strong / Moderate / Weak / None.
10. Derive the overall needs verdict: Needed / Nice-to-have / Not needed.
11. Derive the feature directory name `N-<slug>` following the Feature Directory Naming convention in `skills/sdlc/references/shared.md`: use the issue number as `N` when one is available, otherwise the next incremental sequence number. Record the related issue number in the frontmatter `issue` field.
12. Write the output to `.sdlc/features/N-<slug>/needs-assessment.md`, creating the directory if it does not exist.

## Output Format

```markdown
---
issue: "#<N>"
title: "<Feature Name>"
status: draft
---

# Needs Assessment: <Feature Name>

## Problem Statement

<One paragraph describing the underlying problem, not the proposed solution. If the issue only describes a solution, infer and state the problem explicitly.>

## Stakeholders

| Stakeholder | Role | How they experience the problem |
|---|---|---|
| <who> | <user / admin / developer / business> | <what they encounter today> |

## Evidence of Need

| Source | What it shows | Strength |
|---|---|---|
| <user requests / support tickets / usage data / competitive analysis / assumption> | <summary of evidence> | Strong / Moderate / Weak |

**Evidence rating:** Strong / Moderate / Weak / None

If evidence is None or Weak, state explicitly that the need is assumed rather than demonstrated, and flag this as an open question.

## Cost of Inaction

| Aspect | Impact |
|---|---|
| What breaks or degrades today | <current pain> |
| Existing workarounds | <what people do instead, and their cost> |
| Trend | <growing / stable / declining> |

**Cost-of-inaction rating:** Strong / Moderate / Weak / None

A Strong cost of inaction means the problem is getting worse or is already causing significant pain.
A Weak or None rating means the status quo is tolerable.

## Alternative Paths

| Alternative | How it addresses the need | Trade-offs |
|---|---|---|
| <existing feature / configuration / documentation / process change / third-party tool> | <what it covers> | <what it does not cover, or costs> |

**Could the need be met without new code?** Yes / Partially / No

If Yes, explain why new code is still justified (if at all).

## Strategic Alignment

| Criterion | Assessment |
|---|---|
| Aligns with project goals | <Yes, which goal / Partially / No> |
| Serves core or edge use case | <Core / Edge / Outlier> |
| Dependency enabler | <Unblocks how many other features> |

**Alignment rating:** Strong / Moderate / Weak / None

## Verdict

**Overall needs assessment:** Needed / Nice-to-have / Not needed

**Rationale:** <One paragraph summarizing why this verdict was reached, referencing the strongest and weakest dimensions.>

## Conditions to Proceed

- <Condition that must be true for the need to be considered validated, or "None" if the need is clearly established>

## Open Questions

1. <Question that must be answered before the need is fully validated>
```

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
