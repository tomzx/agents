---
name: requirements-gatherer
description: Collect and surface raw requirements from an issue, user story, or stakeholder description.
argument-hint: "<issue-url-or-description>"
---

# Requirements Gatherer

Reads an issue, user story, or free-form stakeholder input and produces a structured raw requirements list, flagging ambiguities and open questions before any analysis or implementation begins.

## Prerequisites

- Issue URL, user story, or stakeholder notes provided as input
- `gh` CLI available if fetching from GitHub

## Steps

1. Fetch or read the input:
   - GitHub issue: `gh issue view $1 --comments`
   - Otherwise: read the provided text directly
2. Extract all stated and implied requirements (functional and non-functional).
3. Record stakeholder assumptions embedded in the description.
4. Flag every ambiguous, vague, or contradictory statement as an open question.
5. Do not resolve ambiguities — surface them for the Requirements Analyst.

## Output Format

```markdown
## Raw Requirements

Numbered list of requirements exactly as understood from the input. One requirement per line. No interpretation.

## Stakeholder Assumptions

Beliefs that appear to be taken for granted in the input but are never stated explicitly.

## Open Questions

Specific questions that must be answered before requirements can be made precise. Reference the requirement number each question relates to.
```

## Example Usage

**Scenario 1: GitHub issue**
```
/requirements-gatherer https://github.com/owner/repo/issues/42
```
Issue says "users should be able to export their data." Output lists export as a requirement, flags open questions: which formats? which data? bulk or filtered?

**Scenario 2: Stakeholder note**
```
/requirements-gatherer "We need a dashboard that shows sales in real time"
```
Output captures real-time dashboard requirement; flags: definition of "real time" (polling interval?), which sales metrics, user roles, time range filters.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh issue view <url> --comments` | Fetch issue and all comments |
