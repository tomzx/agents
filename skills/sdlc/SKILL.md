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
  ├─ /publish-plan           Commit plan to branch, open draft PR, comment on issue
  │                          (gate: wait for author sign-off before continuing)
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
Pull Request
  │
  ├─ /create-pr              Open a PR: description, AC coverage, issue link, reviewers
  ├─ /review-pr              Comprehensive code review of the PR
  ├─ /handle-pr-ci           Diagnose failing CI checks, fix, push, confirm green (repeat until passing)
  ├─ /handle-pr-feedback     Address reviewer comments, push, re-request review (repeat until approved)
  ├─ /merge-pr               Verify approvals + CI, merge, delete branch, confirm issue closed
  │
  ▼
Learnings
  │
  ├─ /create-learnings       Retrospective: what went well, root causes, actions
  └─ /review-learnings       Audit actionability, specificity, completeness, balance

Cross-cutting records (invoke at any phase)
  │
  ├─ /create-assumption      Record an assumption with basis, risk, and validation plan
  ├─ /review-assumption      Audit specificity, basis quality, risk, validation adequacy
  ├─ /create-decision        Record an architectural/implementation decision with context
  └─ /review-decision        Audit clarity, reasoning quality, consequence coverage
```

## Entry Points

| Phase | Start here when you have... |
|---|---|
| `issue` | A feature idea or bug to capture as a GitHub issue |
| `issues` | A backlog of unlabeled/unranked issues |
| `requirements` | An issue that has been reviewed and is ready to develop |
| `specifications` | Approved requirements ready for technical design |
| `plan` | A specification ready for planning |
| `publish-plan` | A reviewed plan ready to commit and share with the issue author |
| `tasks` | An approved plan signed off by the issue author |
| `tests` | A task decomposition ready for test design |
| `implementation` | Tests ready; time to write code |
| `documentation` | Implementation reviewed; code needs docs |
| `pr` | Documentation done and ready to open a pull request |
| `handle-pr-ci` | PR has failing CI checks to fix |
| `handle-pr-feedback` | PR is open and has reviewer comments to address |
| `merge-pr` | PR is approved and CI is green, ready to merge |
| `learnings` | A completed feature or sprint to reflect on |
| `assumption` | An assumption to record (can be invoked at any phase) |
| `decision` | A decision to record (can be invoked at any phase) |

## Steps

1. Determine the entry point: use `$1` if provided, otherwise ask the user where they are in the lifecycle.
2. Confirm the artifacts available for the current phase (previous phase output, existing files, or context).
3. Execute each sub-skill in order from the entry point to the end of the pipeline.
4. After each `create-*` phase, always run the corresponding `review-*` phase and address findings before advancing.
5. When all review findings are resolved, move to the next phase.
6. After learnings are captured and reviewed, the cycle is complete.

## Backtracking and Failure Recovery

Not every phase succeeds on the first attempt.
A phase may fail because upstream artifacts are incomplete, incoherent, or missing dependencies.
Use the rules below to decide whether to backtrack, retry, or stop.

### Failure modes

| Mode | Example | Response |
|---|---|---|
| **Blocked** | `create-implementation` discovers a missing dependency or unclear spec | Record the blocker as an assumption or decision, backtrack to the phase that owns the missing artifact, resolve it, and re-enter the pipeline at that point. |
| **Incoherent input** | `create-specifications` reveals requirements that contradict each other | Stop the current phase, backtrack to `review-requirements`, resolve contradictions, and continue forward from there. |
| **Scope change** | `create-plan` shows the feature is much larger than the issue suggested | Backtrack to `create-issue` to rewrite scope and ACs, then re-derive downstream artifacts. |
| **External blocker** | Third-party API unavailable, infrastructure not provisioned | Record as an assumption with a validation plan. If the blocker is resolved within the session, continue. Otherwise, stop after the current phase and note the blocker in the issue. |
| **Review escalation** | `review-implementation` finds a fundamental design flaw | Backtrack to the phase where the flawed decision was made (often `create-specifications` or `create-plan`), revise, and re-derive downstream artifacts. |

### Backtracking rules

1. **Backtrack to the nearest phase that owns the root cause.** If `create-implementation` fails because the spec is ambiguous, backtrack to `create-specifications`, not to `create-issue`.
2. **Re-derive downstream artifacts after revising.** Any change to an upstream artifact invalidates everything below it. Re-run each `create-*` phase from the revision point forward.
3. **Record why you backtracked.** Use `/create-decision` to capture the backtrack reason and the corrective action taken.
4. **Limit backtrack depth.** If backtracking would return you more than two phases upstream (e.g., from `implementation` back to `issue`), stop and ask the user whether to continue or split the work.
5. **Do not silently skip a failed phase.** If a phase cannot produce its output, explicitly state why and either backtrack or stop.

### Stopping the pipeline

Stop and report to the user when:
- The root cause is outside the project's control (external blocker with no timeline).
- Backtracking would exceed two phases and the user has not confirmed.
- The work is no longer worth pursuing (invalidated by new information).

When stopping, leave the pipeline in a resumable state:
- Update the issue with current status and blockers.
- Save any artifacts produced so far.
- Note the re-entry point for the next session.

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
| publish-plan | Reviewed plan | Draft PR + issue comment (gate: author sign-off) |
| create-tasks-decomposition | Implementation plan | Task list |
| review-tasks-decomposition | Task list | Findings (resolve before next phase) |
| create-tests | Requirements + spec | Test plan |
| review-tests | Test plan | Findings (resolve before next phase) |
| create-implementation | Task + spec + test plan | Working code |
| review-implementation | Code + spec | Findings (resolve before next phase) |
| create-documentation | Implemented feature | Documentation |
| review-documentation | Documentation | Findings (resolve before next phase) |
| create-pr | Reviewed code + docs + issue | Pull request |
| review-pr | Pull request | Code review findings (resolve before merge) |
| handle-pr-ci | PR with failing CI checks | Root cause diagnosed, fix committed, CI green (repeat until passing) |
| handle-pr-feedback | PR with reviewer comments | Addressed comments, pushed, re-review requested (repeat until approved) |
| merge-pr | Approved PR with green CI | Merged PR, deleted branch, closed issue |
| create-learnings | Completed feature/sprint | Learnings doc |
| review-learnings | Learnings doc | Findings (resolve as action items) |
| create-assumption | Any phase context | Assumption record |
| review-assumption | Assumption record | Findings (improve basis, risk, validation) |
| create-decision | Any phase context | Decision record |
| review-decision | Decision record | Findings (improve clarity, reasoning, consequences) |

## Skipping Review Phases

Review phases may be skipped in low-risk or exploratory contexts.
State the skip explicitly: "Skipping review-requirements — prototype context."
Never skip reviews for security-sensitive features or production-bound work.

## Fast Paths for Small Work

Not every change needs the full pipeline.
Use the table below to determine the minimum viable path for common small-work scenarios.
When in doubt, include more phases rather than fewer.

| Scenario | Example | Path |
|---|---|---|
| **Bug fix** | Fix an off-by-one error, correct a typo in logic | `create-implementation` → `review-implementation` → `create-pr` → `review-pr` → `merge-pr` |
| **Hotfix** | Patch a production incident, revert a bad deploy | `create-implementation` → `create-pr` → `merge-pr` |
| **Config change** | Update a threshold, toggle a feature flag, fix a YAML typo | `create-implementation` → `create-pr` → `merge-pr` |
| **Dependency update** | Bump a library version, patch a CVE in a transitive dep | `create-implementation` → `create-pr` → `review-pr` → `merge-pr` |
| **Refactor (no behavior change)** | Rename a method, extract a helper, improve naming | `create-tests` → `create-implementation` → `create-pr` → `review-pr` → `merge-pr` |
| **Documentation-only** | Fix a typo in docs, add a missing API example | `create-documentation` → `create-pr` → `merge-pr` |

### Rules for fast paths

1. Create an issue when the change needs context, discussion, or prioritization. For self-explanatory changes (typo fix, config toggle, version bump), the PR description is sufficient traceability.
2. Always open a PR, even for hotfixes, so CI runs and the change is reviewable after the fact.
3. Skip requirements, specifications, plan, and tasks only when the change is well-understood and fits in a single commit.
4. Include `review-implementation` when the fix is non-trivial or touches security-adjacent code.
5. Include `create-tests` when the change affects behavior or could regress.
6. Never skip CI verification before merging.

### Using fast paths

Enter the pipeline normally and state which fast path applies.
The orchestrator will skip the intermediate phases.

```
/sdlc issue
"This is a bug fix for an off-by-one error in the pagination logic."
```

The orchestrator recognizes the fast path and runs the abbreviated pipeline automatically.
If the work turns out to be more complex than expected, escalate to the full pipeline.

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

**Scenario 4: Open a PR for finished work**
```
/sdlc pr
```
Run `create-pr` to open the pull request, then `review-pr` to review it.
Confirm implementation and documentation are done before opening.

**Scenario 5: Fix failing CI on an open PR**
```
/sdlc handle-pr-ci
```
Run `handle-pr-ci` to diagnose failing checks, implement fixes, push, and confirm CI is green.

**Scenario 6: Address reviewer feedback on an open PR**
```
/sdlc handle-pr-feedback
```
Run `handle-pr-feedback` to address all reviewer comments, push, and re-request review.
Repeat each time new feedback arrives until the PR is approved.

**Scenario 7: Merge an approved PR**
```
/sdlc merge-pr
```
Run `merge-pr` to verify approvals and CI, then squash-merge, delete the branch, and confirm the linked issue is closed.

**Scenario 7: Issue backlog triage + prioritization only**
```
/sdlc issues
```
Run `triage-issues` then `prioritize-issues`. Stop after the ranked backlog is produced.

**Scenario 8: Post-sprint retrospective**
```
/sdlc learnings
```
Run `create-learnings` then `review-learnings` for the sprint just completed.

**Scenario 9: Record an assumption mid-pipeline**
```
/sdlc assumption
```
Run `create-assumption` to record an assumption discovered during any phase, then `review-assumption` to validate it.

**Scenario 10: Record a decision mid-pipeline**
```
/sdlc decision
```
Run `create-decision` to capture an architectural or implementation choice, then `review-decision` to ensure quality.

**Scenario 11: Bug fix (fast path)**
```
/sdlc
```
User says "Fix off-by-one error in pagination."
Orchestrator recognizes bug fix fast path: `create-issue` → `create-implementation` → `review-implementation` → `create-pr` → `review-pr` → `merge-pr`.
Skips requirements, specifications, plan, tasks, and documentation.

**Scenario 12: Hotfix (fast path)**
```
/sdlc
```
User says "Production is 500ing on /api/users, need a hotfix."
Orchestrator recognizes hotfix fast path: `create-issue` → `create-implementation` → `create-pr` → `merge-pr`.
Skips reviews to minimize time-to-deploy.
Post-merge retrospective is recommended but not blocking.
