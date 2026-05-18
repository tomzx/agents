---
name: sdlc
description: Run the full software development lifecycle pipeline, from issue creation through implementation, documentation, and learnings capture.
argument-hint: "[phase-name]"
---

# Software Development Lifecycle

Orchestrates the full SDLC pipeline by invoking the appropriate sub-skills in sequence.
Each phase accepts the previous phase's output as input.
Pass an optional phase name to enter the pipeline at a specific stage.

## When to Use `/sdlc` vs Individual Skills

- Use **`/sdlc`** (with an optional phase name) when you want the orchestrator to run multiple phases in sequence, handle review cycles, and manage backtracking automatically.
- Use **individual skills directly** (e.g., `/create-pr`, `/review-implementation`) when you need a single phase and want full control over inputs and outputs without the pipeline orchestration overhead.

## Pipeline Overview

```
Setup (run once per project)
  │
  ├─ /initialize-sdlc-directory   Bootstrap .sdlc/ structure and populate templates
  ├─ /update-sdlc-templates       Pull upstream template improvements, merge with user edits
  │
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

### Cross-cutting skills (use at any phase)

| Skill | When to use |
|---|---|
| `/create-assumption` | When a phase proceeds on an unverified belief — log it with basis, risk, and validation plan |
| `/review-assumption` | Audit an assumption record for specificity, basis quality, and validation adequacy |
| `/create-decision` | When an architectural or implementation choice is made — record it as a lightweight ADR |
| `/review-decision` | Audit a decision record for clarity, completeness, and consequence coverage |

## Directory Structure

All SDLC artifacts live under `.sdlc/` in the repository root.

```
.sdlc/
├── context/
│   ├── project-overview.md        # Project goals, scope, key stakeholders
│   ├── architecture.md            # Architecture decisions and patterns
│   └── conventions.md             # Naming, structure, coding standards
├── features/
│   └── NNNN-<slug>/               # One directory per feature (e.g., 0001-notification-system)
│       ├── requirements.md
│       ├── specification.md
│       ├── plan.md
│       ├── tasks/                 # One file per task (e.g., 0001-setup-db-schema.md)
│       │   └── NNNN-<slug>.md
│       ├── tests.md
│       └── questions.md           # Running log of open questions from all review phases
├── templates/                     # Editable defaults used by create-* skills; kept in sync by /update-sdlc-templates
│   ├── features/
│   │   ├── requirements.md
│   │   ├── specification.md
│   │   ├── plan.md
│   │   ├── task.md                # Template for a single task file
│   │   ├── tests.md
│   │   └── questions.md
│   └── knowledge/
│       ├── assumption.md
│       ├── decision.md
│       └── learning.md
└── knowledge/
    ├── assumptions/
    │   └── NNNN-<slug>.md         # Created by /create-assumption; one file per assumption
    ├── decisions/
    │   └── NNNN-<slug>.md         # Created by /create-decision; one file per decision
    └── learnings/
        └── NNNN-<slug>.md         # Created by /create-learnings; one file per retrospective
```

**Feature directory naming:** `NNNN-<slug>` where `NNNN` is the next available four-digit sequence number within `.sdlc/features/` (e.g., `0001-notification-system`, `0002-password-reset`). Slug is lowercase, hyphens for spaces, no special characters. The related GitHub issue, if any, is recorded in frontmatter only.

Each pipeline artifact carries YAML frontmatter tracking its state:

```yaml
---
issue: "#42"
title: "Notification System"
status: draft        # draft → in-review → approved (learnings: → complete)
---
```

`create-*` pipeline skills write artifacts with `status: draft`.
`review-*` pipeline skills set `status: in-review` when the review begins and `status: approved` (or `complete` for learnings) when all findings are resolved.
Assumption and decision records use their own status vocabulary (`Active → Validated | Invalidated | Deferred`; `Proposed → Accepted | Deprecated | Superseded`) updated by `review-assumption` and `review-decision` respectively.
Open questions from review phases are appended to `.sdlc/features/NNNN-<slug>/questions.md`. When a question carries meaningful risk, promote it to a formal assumption via `/create-assumption`.
Architectural choices made during any phase are logged via `/create-decision` to `.sdlc/knowledge/decisions/`.

## Entry Points

| Phase | Start here when you have... |
|---|---|
| `setup` | A new project that needs the `.sdlc/` structure bootstrapped |
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
2. Read any files present under `.sdlc/context/` (`project-overview.md`, `architecture.md`, `conventions.md`) for project-level context before invoking any sub-skill.
3. Confirm the artifacts available for the current phase (previous phase output under `.sdlc/features/<feature>/`, existing files, or context).
4. Execute each sub-skill in order from the entry point to the end of the pipeline.
5. After each `create-*` phase, always run the corresponding `review-*` phase and address findings before advancing.
6. When all review findings are resolved, move to the next phase.
7. After learnings are captured and reviewed, the cycle is complete.

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
| initialize-sdlc-directory | Project root (optional) | `.sdlc/` directory tree + templates populated |
| update-sdlc-templates | `.sdlc/templates/` + canonical templates | Merged/updated templates; conflicts flagged |
| create-issue | Feature idea / bug description | Structured GitHub issue |
| review-issue | GitHub issue | Findings + improved ACs (resolve before next phase) |
| triage-issues | Open issues | Labeled, classified issues |
| prioritize-issues | Labeled issues | RICE-ranked backlog |
| create-requirements | Reviewed issue | `.sdlc/features/<feature>/requirements.md` (`status: draft`) |
| review-requirements | `.sdlc/features/<feature>/requirements.md` | Findings; sets `status: approved` when resolved |
| create-specifications | `.sdlc/features/<feature>/requirements.md` | `.sdlc/features/<feature>/specification.md` (`status: draft`) |
| review-specifications | `.sdlc/features/<feature>/specification.md` | Findings; sets `status: approved` when resolved |
| create-plan | `.sdlc/features/<feature>/specification.md` | `.sdlc/features/<feature>/plan.md` (`status: draft`) |
| review-plan | `.sdlc/features/<feature>/plan.md` | Findings; sets `status: approved` when resolved |
| publish-plan | `.sdlc/features/<feature>/plan.md` | Draft PR + issue comment (gate: author sign-off) |
| create-tasks-decomposition | `.sdlc/features/<feature>/plan.md` | `.sdlc/features/<feature>/tasks/NNNN-<slug>.md` per task (`status: draft`) |
| review-tasks-decomposition | `.sdlc/features/<feature>/tasks/` (all task files) | Findings; sets each task `status: pending` when resolved |
| create-tests | `.sdlc/features/<feature>/requirements.md` + `specification.md` | `.sdlc/features/<feature>/tests.md` (`status: draft`) |
| review-tests | `.sdlc/features/<feature>/tests.md` | Findings; sets `status: approved` when resolved |
| create-implementation | `.sdlc/features/<feature>/tasks/` + `specification.md` + `tests.md` | Working code |
| review-implementation | Code + spec | Findings (resolve before next phase) |
| create-documentation | Implemented feature | Documentation |
| review-documentation | Documentation | Findings (resolve before next phase) |
| create-pr | Reviewed code + docs + issue | Pull request |
| review-pr | Pull request | Code review findings (resolve before merge) |
| handle-pr-ci | PR with failing CI checks | Root cause diagnosed, fix committed, CI green (repeat until passing) |
| handle-pr-feedback | PR with reviewer comments | Addressed comments, pushed, re-review requested (repeat until approved) |
| merge-pr | Approved PR with green CI | Merged PR, deleted branch, closed issue |
| create-learnings | Completed feature/sprint | `.sdlc/knowledge/learnings/NNNN-<slug>.md` (`status: draft`) |
| review-learnings | `.sdlc/knowledge/learnings/NNNN-<slug>.md` | Findings; sets `status: complete` when resolved |
| create-assumption | Any phase context | `.sdlc/knowledge/assumptions/NNNN-<slug>.md` |
| review-assumption | `.sdlc/knowledge/assumptions/NNNN-<slug>.md` | Findings (improve basis, risk, validation) |
| create-decision | Any phase context | `.sdlc/knowledge/decisions/NNNN-<slug>.md` |
| review-decision | `.sdlc/knowledge/decisions/NNNN-<slug>.md` | Findings (improve clarity, reasoning, consequences) |

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
