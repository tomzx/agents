---
name: create-requirements
description: Draft a requirements document with functional and non-functional requirements from a feature brief or issue.
argument-hint: "[feature-brief or issue-url]"
---

# Create Requirements

Drafts a structured requirements document from a feature brief, user story, or GitHub issue, capturing functional requirements, non-functional requirements, constraints, and acceptance criteria.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the issue from `$ISSUE_NUMBER` (and `$REPO`).
- A feature brief, user story, or issue description provided in context or as `$1`
- Stakeholder goals and constraints, if known

## Steps

1. Read and understand the input (feature brief, issue, or user story).
2. Identify the goal: what problem is being solved and for whom.
3. List functional requirements: behaviors the system must exhibit.
4. List non-functional requirements: quality attributes (performance, security, availability, etc.).
5. Identify constraints: technology choices, regulatory requirements, compatibility needs.
6. Write acceptance criteria: testable conditions that confirm each requirement is met.
7. Flag any open questions where requirements are unclear or missing.
8. Derive the feature directory name: `FEAT-NNNN-<slug>` where `NNNN` is the next available four-digit sequence number within `.sdlc/features/` (count existing subdirectories, zero-pad). Slug is lowercase, hyphens for spaces (e.g., `FEAT-0001-notification-system`). Record the related issue number in the frontmatter `issue` field, not in the directory name.
9. Write the output to `.sdlc/features/FEAT-NNNN-<slug>/requirements.md`, creating the directory if it does not exist.

## Output Format

```markdown
---
issue: "#<N>"
title: "<Feature Name>"
status: draft
---

# Requirements: <Feature Name>

## Overview

<One paragraph describing the problem and the goal of this feature.>

## Stakeholders

| Stakeholder | Interest |
|---|---|
| <role> | <what they need from this feature> |

## Functional Requirements

| ID | Priority | Requirement |
|---|---|---|
| FR-01 | Must / Should / May | The system shall ... |
| FR-02 | ... | ... |

## Non-Functional Requirements

| ID | Requirement | Category |
|---|---|---|
| NFR-01 | The system shall ... | Performance / Security / Availability / ... |

## Constraints

- <Constraint 1>
- <Constraint 2>

## Acceptance Criteria

- [ ] **FR-01**
    - **Given** <precondition>
    - **When** <action>
    - **Then** <observable result>
- [ ] **FR-01** (edge case)
    - **Given** <edge case>
    - **When** <action>
    - **Then** <expected handling>
- [ ] **FR-01** (error)
    - **Given** <error condition>
    - **When** <action>
    - **Then** <error is surfaced as ...>

## Conflicts

<!-- Populated by /review-requirements. Leave as "None identified yet." when drafting. -->

None identified yet.

## Open Questions

1. <Question that needs an answer before implementation can begin>
```

Use MoSCoW priority for functional requirements: **Must** (essential), **Should** (important), **May** (nice-to-have).

Functional requirements state *what* the system shall do; acceptance criteria state *how you verify* it is done.
Do not restate an FR as its acceptance criterion.
Write concrete, scenario-based criteria (happy path, edge cases, error states), usually several per requirement, each independently checkable and translatable into a test case.

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | Requirements drafted (artifact written with `status: approved`) |
| `needs-info` | Issue lacks the detail needed to derive requirements |

## Example Usage

**Scenario 1: Feature brief in context**
User describes "we need users to reset their passwords via email."
Draft FR for the email flow, NFR for token expiry and security, and acceptance criteria for each step.

**Scenario 2: GitHub issue as input**
```
/create-requirements https://github.com/owner/repo/issues/42
```
Fetch the issue, extract the described behavior, and produce a requirements document.

**Scenario 3: Incomplete brief**
User gives a vague description.
List open questions and draft requirements for the parts that are clear.

## Next Step

Run `/review-requirements` to audit the document for clarity, completeness, testability, and conflicts before moving on.
Once approved, continue with `/create-existing-solutions` to survey prior art.

## Useful Commands Reference

For document-only input, no CLI commands are required.
If given an issue URL, fetch it with:

| Command | Description |
|---|---|
| `gh-cached issue view <url> --comments` | Fetch issue details and comments (cached) |
