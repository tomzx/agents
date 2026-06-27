---
issue: "#5"
title: "Accuracy Pass on Daily Summaries"
status: approved
---

# Requirements: Accuracy Pass on Daily Summaries

## Overview

The end-of-day pipeline produces daily summaries (GitHub activity, Slack activity, overall summary, timeline, standup) that are written once and never reviewed. Inaccuracies in individual summaries compound over time, making weekly, monthly, and historical reviews unreliable. This feature provides tooling to review existing daily summaries for accuracy, apply corrections, and prevent future inaccuracies from compounding.

## Stakeholders

| Stakeholder | Interest |
|---|---|
| Tom (user) | Needs to audit daily summaries for accuracy, correct errors, and trust accumulated records for weekly/monthly reviews |
| Pipeline consumer | Downstream review processes (weekly, monthly, end-month) depend on accurate source data |

## Functional Requirements

| ID | Priority | Requirement |
|---|---|---|
| FR-01 | Must | The system shall provide a command or skill that presents an existing daily summary file for accuracy review |
| FR-02 | Must | The system shall allow the user to flag individual facts or claims within a summary as inaccurate |
| FR-03 | Must | The system shall allow the user to provide corrected text for each flagged inaccuracy |
| FR-04 | Must | The system shall ensure that future reads of the summary present the corrected version, whether through in-place editing or by composing original content with stored deltas |
| FR-05 | Should | The system shall support reviewing summaries within a configurable date range (single day, week, month, custom range) |
| FR-06 | Should | The system shall skip days that have already been reviewed when invoked again for the same date range |
| FR-07 | Should | The system shall record corrections as separate delta files, preserving the original text and providing an audit trail |
| FR-08 | Should | The system shall surface a summary of corrections made at the end of each review session |
| FR-09 | May | The system shall propagate corrections into downstream review files (weekly, monthly, historical) that already consumed the inaccurate data |
| FR-10 | May | The system shall flag potential inaccuracies during the initial end-of-day summary generation stage |

## Non-Functional Requirements

| ID | Requirement | Category |
|---|---|---|
| NFR-01 | Reviewing and correcting a single daily summary shall require no more than 5 seconds of interactive latency per claim reviewed | Performance |
| NFR-02 | The original summary text must be preserved when corrections are stored as deltas, so every correction is auditable | Data Integrity |
| NFR-03 | The review flow shall be interruptible: the user can stop mid-review and resume later without re-reviewing already-checked items | Usability |
| NFR-04 | The system shall work with existing daily summary files produced by end-of-day-summary and end-day skills without requiring changes to those skills | Compatibility |
| NFR-05 | Corrections shall be applied atomically: a partial failure must not leave the file in an inconsistent state | Reliability |

## Constraints

- Must operate within the existing skills framework and conventions (AGENTS.md, SDLC references)
- Must process markdown files in the existing daily notes archive structure
- Must not change the output format of the end-of-day summary generation skills
- Corrections must not require manual git operations by the user

## Acceptance Criteria

- [ ] **FR-01** (happy path)
    - **Given** a daily summary file exists for a specific date
    - **When** the user invokes the accuracy-pass skill targeting that date
    - **Then** the summary content is presented to the user for review
- [ ] **FR-01** (no file)
    - **Given** no daily summary exists for the specified date
    - **When** the user invokes the accuracy-pass skill
    - **Then** the user is informed that no summary exists for that date
- [ ] **FR-02** (happy path)
    - **Given** a daily summary is being reviewed
    - **When** the user identifies a claim as inaccurate
    - **Then** the claim is marked as flagged and the user is prompted for a correction
- [ ] **FR-03** (happy path)
    - **Given** a claim has been flagged as inaccurate
    - **When** the user provides corrected text
    - **Then** the corrected text is accepted and associated with the flagged claim
- [ ] **FR-04** (happy path)
    - **Given** one or more corrections have been made during a review session
    - **When** the review session completes
    - **Then** the summary file is updated with the corrected content
- [ ] **FR-04** (no changes)
    - **Given** a review session where no inaccuracies were flagged
    - **When** the review session completes
    - **Then** the summary file is not modified
- [ ] **FR-05** (range)
    - **Given** the user specifies a date range covering multiple days
    - **When** the accuracy-pass skill is invoked
    - **Then** each daily summary in that range is presented for review in chronological order
- [ ] **FR-05** (empty range)
    - **Given** the user specifies a date range with no daily summaries
    - **When** the accuracy-pass skill is invoked
    - **Then** the user is informed that no summaries exist in that range
- [ ] **FR-06** (skip reviewed)
    - **Given** a date range where some days have already been reviewed
    - **When** the accuracy-pass skill is invoked for that entire range
    - **Then** only unreviewed days are presented for review
- [ ] **FR-07** (delta file)
    - **Given** corrections were applied during a review session
    - **When** the session completes
    - **Then** a delta file is written recording the original text, corrected text, and timestamp for each change
- [ ] **FR-08** (session summary)
    - **Given** a review session has completed with corrections
    - **When** the session ends
    - **Then** a summary of all corrections made is displayed to the user
- [ ] **FR-09** (propagation)
    - **Given** a correction has been applied to a daily summary
    - **When** the correction propagation is triggered
    - **Then** the downstream review files that referenced the inaccurate data are updated
- [ ] **FR-10** (generation flag)
    - **Given** a new daily summary is being generated
    - **When** the generation completes
    - **Then** the user is prompted to review the summary for accuracy before finalization

## Conflicts

| Requirements | Type | Resolution |
|---|---|---|
| FR-04 (Must), FR-07 (Should) | Direct contradiction | Amended FR-04 to be outcome-focused ("present the corrected version") rather than mechanism-focused, removing the conflict with FR-07's delta-based approach. See open question #2 for the implementation design choice. |

## Open Questions

1. Should the accuracy pass operate on individual daily files or offer a bulk-review mode across a date range?
2. Should corrections be recorded inline (editing the original file) or as separate correction deltas (keeping an audit trail)?
3. How are corrections propagated into downstream review files that already consumed the inaccurate data?
4. What constitutes an "inaccuracy" - factual errors, omissions, formatting issues, or tone?
5. Should the accuracy pass be a standalone skill or built into the existing end-day workflow?
6. How does the user identify which daily summaries still need review?
7. Should corrections trigger regeneration of downstream weekly/monthly summaries or should that be a manual step?
