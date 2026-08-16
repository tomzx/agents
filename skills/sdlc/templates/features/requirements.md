---
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

Order rows by priority: Must first, then Should, then May.

| ID | Priority | Requirement |
|---|---|---|
| FR-1 | Must / Should / May | The system shall ... |

## Non-Functional Requirements

Order rows by priority: Must first, then Should, then May.

| ID | Priority | Category | Requirement |
|---|---|---|---|
| NFR-1 | Must / Should / May | Performance / Security / Availability / ... | The system shall ... |

## Constraints

- <Constraint 1>

## Acceptance Criteria

Every FR and NFR shall have at least one acceptance criterion.

Order criteria by FRs first (sorted by ID), then NFRs (sorted by ID).

Acceptance criteria verify how a requirement is proven done, they do not restate it.
Write concrete, scenario-based criteria (happy path, edge cases and error states where applicable).
Write each criterion as a fenced `gherkin` block with a tag matching its requirement ID, so the criteria are parseable and later executable via BDD tooling (pytest-bdd, cucumber).
Multiple scenarios per requirement are allowed; tag each with the requirement ID.

- [ ] **FR-1**

    ```gherkin
    @FR-1
    Scenario: <short name>
      Given <precondition>
      When <action>
      Then <observable result>
    ```

- [ ] **NFR-1**

    ```gherkin
    @NFR-1
    Scenario: <short name>
      Given <precondition>
      When <action>
      Then <observable result with a quantitative threshold, e.g., responds in < 200 ms>
    ```

## Conflicts

<!-- Identified and populated by /review-requirements: pairs or groups of requirements that cannot all be satisfied at once. Reconcile before approval, or promote to an open question. -->

None identified yet.

## Open Questions

1. <Question that needs an answer before implementation can begin>
