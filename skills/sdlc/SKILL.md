---
name: sdlc
description: Run the full software development lifecycle pipeline, from issue creation through implementation, documentation, and learnings capture.
argument-hint: "[phase-name]"
---

# Software Development Lifecycle

Orchestrates the full SDLC pipeline by invoking the appropriate sub-skills in sequence.
Each phase accepts the previous phase's output as input.
Pass an optional phase name to enter the pipeline at a specific stage.

## Pipeline Overview

```
Idea / Brief
  │
  ├─ /create-issue           Create a structured GitHub issue
  ├─ /review-issue           Audit completeness, clarity, and AC quality
  │
  ▼
Issues
  │
  ├─ /triage-issues          Classify and label incoming issues
  │
  ├─ /prioritize-issues      Rank the backlog by RICE score
  │
  ▼
Requirements
  │
  ├─ /create-requirements    Draft functional + non-functional requirements
  ├─ /review-requirements    Audit for clarity, completeness, testability
  │
  ▼
Specifications
  │
  ├─ /create-specifications  Define architecture, data models, API contracts
  ├─ /review-specifications  Audit for ambiguities, inconsistencies, gaps
  │
  ▼
Plan
  │
  ├─ /create-plan            Phases, milestones, dependencies, risk register
  ├─ /review-plan            Audit feasibility, coverage, timeline realism
  │
  ▼
Tasks
  │
  ├─ /create-tasks-decomposition   Break plan into XS–L tasks with critical path
  ├─ /review-tasks-decomposition   Audit granularity, completeness, dependencies
  │
  ▼
Tests
  │
  ├─ /create-tests           Test plan covering acceptance criteria + edge cases
  ├─ /review-tests           Audit coverage, correctness, maintainability
  │
  ▼
Implementation
  │
  ├─ /create-implementation  Implement following spec + plan, run tests
  ├─ /review-implementation  Audit correctness, quality, security, spec alignment
  │
  ▼
Documentation
  │
  ├─ /create-documentation   Divio-structured docs (tutorial/how-to/reference/explanation)
  ├─ /review-documentation   Audit completeness, accuracy, clarity, structure
  │
  ▼
Learnings
  │
  ├─ /create-learnings       Retrospective: what went well, root causes, actions
  └─ /review-learnings       Audit actionability, specificity, completeness, balance
```

## Entry Points

| Phase | Start here when you have... |
|---|---|
| `issue` | A feature idea or bug to capture as a GitHub issue |
| `issues` | A backlog of unlabeled/unranked issues |
| `requirements` | An issue that has been reviewed and is ready to develop |
| `specifications` | Approved requirements ready for technical design |
| `plan` | A specification ready for planning |
| `tasks` | An approved plan ready to decompose |
| `tests` | A task decomposition ready for test design |
| `implementation` | Tests ready; time to write code |
| `documentation` | Shipped code that needs docs |
| `learnings` | A completed feature or sprint to reflect on |

## Steps

1. Determine the entry point: use `$1` if provided, otherwise ask the user where they are in the lifecycle.
2. Confirm the artifacts available for the current phase (previous phase output, existing files, or context).
3. Execute each sub-skill in order from the entry point to the end of the pipeline.
4. After each `create-*` phase, always run the corresponding `review-*` phase and address findings before advancing.
5. When all review findings are resolved, move to the next phase.
6. After learnings are captured and reviewed, the cycle is complete.

## Phase Contracts

Each phase consumes output from the previous phase:

| Phase | Input | Output |
|---|---|---|
| create-issue | Feature idea / bug description | Structured GitHub issue |
| review-issue | GitHub issue | Findings + improved ACs (resolve before next phase) |
| triage-issues | Open issues | Labeled, classified issues |
| prioritize-issues | Labeled issues | RICE-ranked backlog |
| create-requirements | Reviewed issue | Requirements doc |
| review-requirements | Requirements doc | Findings (resolve before next phase) |
| create-specifications | Requirements doc | Specification doc |
| review-specifications | Specification doc | Findings (resolve before next phase) |
| create-plan | Specification doc | Implementation plan |
| review-plan | Implementation plan | Findings (resolve before next phase) |
| create-tasks-decomposition | Implementation plan | Task list |
| review-tasks-decomposition | Task list | Findings (resolve before next phase) |
| create-tests | Requirements + spec | Test plan |
| review-tests | Test plan | Findings (resolve before next phase) |
| create-implementation | Task + spec + test plan | Working code |
| review-implementation | Code + spec | Findings (resolve before next phase) |
| create-documentation | Implemented feature | Documentation |
| review-documentation | Documentation | Findings (resolve before next phase) |
| create-learnings | Completed feature/sprint | Learnings doc |
| review-learnings | Learnings doc | Findings (resolve as action items) |

## Skipping Review Phases

Review phases may be skipped in low-risk or exploratory contexts.
State the skip explicitly: "Skipping review-requirements — prototype context."
Never skip reviews for security-sensitive features or production-bound work.

## Example Usage

**Scenario 1: Full pipeline from scratch**
```
/sdlc
```
No argument. Ask: "Where are you in the lifecycle?" User says "I have a feature idea."
Start at `create-issue`, run every phase to `review-learnings`.

**Scenario 2: Issue exists but needs review**
```
/sdlc issue
```
Issue already created. Run `review-issue` to audit completeness and AC quality, resolve findings, then continue from `create-requirements`.

**Scenario 3: Enter mid-pipeline**
```
/sdlc implementation
```
Jump directly to `create-implementation`.
Confirm that a task list, specification, and test plan are in context before starting.

**Scenario 4: Issue backlog triage + prioritization only**
```
/sdlc issues
```
Run `triage-issues` then `prioritize-issues`. Stop after the ranked backlog is produced.

**Scenario 5: Post-sprint retrospective**
```
/sdlc learnings
```
Run `create-learnings` then `review-learnings` for the sprint just completed.
