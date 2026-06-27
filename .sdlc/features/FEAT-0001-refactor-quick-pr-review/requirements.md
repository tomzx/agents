---
issue: "#15"
title: "Refactor quick-pr-review skill"
status: approved
---

# Requirements: Refactor quick-pr-review skill

## Overview

The `quick-pr-review` skill at 451 lines is the highest-complexity hotspot in the skill library. It contains 8 inline review checks and trust-level branching spread across multiple workflow steps (3 decision points). This refactoring extracts the review checklist into a shared reference and simplifies the trust-level branching to a single top-level conditional, reducing the file to under 200 lines while preserving all behavior.

## Stakeholders

| Stakeholder | Interest |
|---|---|
| Skill author | Maintainable code that is easy to modify and extend |
| Skill user | No change to observable behavior (review output, approval logic) |
| Skill reviewer | Clear separation between shared conventions and skill-specific logic |

## Functional Requirements

| ID | Priority | Requirement |
|---|---|---|
| FR-01 | Must | The skill shall produce identical review comments for the same PR input before and after refactoring |
| FR-02 | Must | The review checklist items (public interface changes, security-sensitive changes, new dependencies, reversibility, tests, issue linkage, docs) shall be defined in a shared reference file |
| FR-03 | Must | Trust-level branching (trusted, neutral, cautious, always_reject) shall be evaluated at a single top-level conditional before checks begin |
| FR-04 | Must | The skill file shall be under 200 lines |
| FR-05 | Should | The shared reference file shall be reusable by other review skills |
| FR-06 | Should | Each review check shall be independently testable via the shared reference |
| FR-07 | May | A changelog entry shall be added to document the refactoring |

## Non-Functional Requirements

| ID | Requirement | Category |
|---|---|---|
| NFR-01 | The skill shall pass all existing integration tests after refactoring | Correctness |
| NFR-02 | The shared reference shall follow the same documentation conventions as other SDLC shared references | Maintainability |
| NFR-03 | The refactored skill shall be reviewed by the skill library maintainer before merging | Process |

## Constraints

- The refactored skill must remain at the same file path (`skills/quick-pr-review/SKILL.md`) to preserve existing references
- The shared reference must be placed in `skills/sdlc/references/` to align with existing SDLC shared conventions
- The review comment output format (marker, checklist, evaluation details, footer) must not change
- The trust level names (trusted, neutral, cautious, always_reject) must remain unchanged

## Acceptance Criteria

- [ ] **FR-01**
    - **Given** the original `quick-pr-review/SKILL.md` at 451 lines
    - **When** the refactoring is applied
    - **Then** every workflow step (gather PR info, load trust, find existing comment, run checks, compose comment, save, post, approve, update profile) is preserved without functional change
- [ ] **FR-01** (edge case)
    - **Given** any of the 9 example scenarios in the original skill
    - **When** the refactored skill processes the same inputs
    - **Then** the output review comment and approval decision are identical
- [ ] **FR-02**
    - **Given** the refactored skill
    - **When** inspecting the review check definitions
    - **Then** they are not inline in `SKILL.md` but imported from a shared reference file at `skills/sdlc/references/`
- [ ] **FR-03**
    - **Given** the refactored skill
    - **When** inspecting the trust-level branching logic
    - **Then** a single conditional branch (trusted/neutral/cautious/always_reject) appears at the top of the workflow, and no trust-level checks are scattered inside individual step descriptions
- [ ] **FR-03** (always_reject)
    - **Given** a PR author with `always_reject` trust level
    - **When** the skill runs
    - **Then** it stops at the top-level conditional without fetching the diff or running any checks, identical to current behavior
- [ ] **FR-04**
    - **Given** the refactored `skills/quick-pr-review/SKILL.md`
    - **When** counting lines
    - **Then** the total is under 200 lines (excluding blank trailing lines)
- [ ] **FR-05**
    - **Given** the shared reference file
    - **When** another review skill (e.g. `review-pr`) references it
    - **Then** it works without modification to the shared reference
- [ ] **FR-06**
    - **Given** a review check defined in the shared reference
    - **When** it is invoked with sample inputs
    - **Then** it returns a pass/fail result without requiring the full skill workflow

## Conflicts

None found during review.

## Open Questions

1. Should the shared reference be a new SKILL.md (with its own frontmatter and name) or a plain markdown file under `skills/sdlc/references/`?
2. Should the review checklist shared reference also include the evaluation detail templates (the `<details>` section content)?
3. Should the changelog entry (FR-07) point to a centralized changelog or be part of the skill file itself?
