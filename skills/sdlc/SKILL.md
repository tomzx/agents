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

## Load Each Phase Skill (mandatory)

Before performing any work that belongs to a pipeline phase, load that phase's skill with the `skill` tool.

A skill's `allowed-tools`, workflow, attribution steps, and gates only apply once its content is in context.
Never execute a phase's actions from memory or general knowledge.
This is especially true for skills that commit, push, or open PRs (`create-pr`, `fix-issue`, `publish-plan`, `merge-pr`, `deploy-pr`, `handle-pr-ci`, `handle-pr-feedback`): their commit and push rules are bypassed whenever they are not loaded.

This applies at every phase transition the orchestrator makes, on every entry point and fast path.
If you reach a phase that needs committing, pushing, or a PR and its skill is not yet loaded, load it before doing anything else, then follow its workflow.

## Pipeline Overview

```
Main flow — 8 SDLC stages (entry: issue → learnings)

  Stage 1 — Issue
  /create-issue           Create a structured GitHub issue
  /review-issue           Audit completeness, clarity, and AC quality
  /qualify-issue          Drive Q&A loop with reporter until issue is fully understood
          │
          ▼
  /triage-issues          Classify and label incoming issues
  /prioritize-issues      Rank the backlog by RICE score
          │
          ▼
  Stage 2 — Needs Validation
  /create-needs-assessment Evaluate whether the feature addresses a genuine need
  /review-needs-assessment Audit evidence rigor, stakeholder coverage, alternative paths, verdict soundness
                          (gate: stop if not needed, update issue with findings)
           │
           ▼
  Stage 3 — Requirements & Research
  /create-requirements    Draft functional + non-functional requirements
  /review-requirements    Audit for clarity, completeness, testability, conflicts
           │
           ▼
   /create-existing-solutions  Survey prior art (libraries, products, internal code) and recommend adopt vs. build
   /review-existing-solutions  Audit search coverage, evaluation rigor, recommendation soundness
            │
            ▼
   /create-codebase-analysis  Analyze existing internal code/architecture the feature will touch; assess changeability per component
   /review-codebase-analysis  Audit coverage, accuracy, changeability rigor, impact and migration
            │
            ▼
   /create-feasibility     Assess technical, financial, and operational viability
  /review-feasibility     Audit completeness, risk coverage, go/no-go soundness
                          (gate: stop if not feasible, update issue with findings)

  Stage 4 — Design
  /create-specifications  Define architecture, data models, API contracts
  /review-specifications  Audit for ambiguities, inconsistencies, gaps
          │
          ▼
  /create-mockups        Define UI wireframes, screens, states, and flows (UI features; skip if no UI surface)
  /review-mockups        Audit coverage, usability, accessibility, consistency, spec fidelity
          │
          ▼
  /create-telemetry       Define analytics events, success metrics, funnel, telemetry
  /review-telemetry       Audit completeness, measurability, actionability, consistency
          │
          ▼
  /create-observability   Define logging, metrics, tracing, alerts, SLOs
  /review-observability   Audit completeness, actionability, coverage, overlap
          │
          ▼
  /create-plan            Phases, milestones, dependencies, risk register
  /review-plan            Audit feasibility, coverage, timeline realism
  /publish-plan           Commit plan to branch, open draft PR, comment on issue
                          (gate: wait for author sign-off before continuing)
          │
          ▼
  /create-tasks-decomposition   Break plan into XS–L tasks with critical path
  /review-tasks-decomposition   Audit granularity, completeness, dependencies

  Stage 5 & 6 — Development & Testing
  /create-tests           Test plan covering acceptance criteria + edge cases
  /review-tests           Audit coverage, correctness, maintainability
          │
          ▼
  /create-implementation  Implement following spec + plan, run tests
  /review-implementation  Audit correctness, quality, security, spec alignment
          │
          ▼
  /create-documentation   Divio-structured docs (tutorial/how-to/reference/explanation)
  /review-documentation   Audit completeness, accuracy, clarity, structure
          │
          ▼
   /create-pr              Open a PR: description, AC coverage, issue link, reviewers
   /validate-pr            Runtime validation: build, run, prove claims, record CLI demos
   /verify-pr              Static verification: claim-to-code traceability, code quality inspection
   /review-pr              Comprehensive code review of the PR
  /handle-pr-ci           Diagnose failing CI checks, fix, push, confirm green (repeat until passing)
  /handle-pr-feedback     Address reviewer comments, push, re-request review (repeat until approved)
  /merge-pr               Verify approvals + CI, merge, delete branch, confirm issue closed

  Stage 7 — Deployment
  /deploy-pr              Deploy merged changes to target environment, run smoke tests, verify rollback plan
          │
          ▼
  /create-learnings       Retrospective: what went well, root causes, actions
  /review-learnings       Audit actionability, specificity, completeness, balance

  Other flows

Setup (run once per project, no dependencies on other flows)

  /sync-sdlc                   Create or update .sdlc/ by reconciling codebase with existing artifacts
  /initialize-sdlc-directory   Bootstrap .sdlc/ structure and populate templates (called automatically by sync-sdlc)
  /update-sdlc-templates       Pull upstream template improvements, merge with user edits
  /configure-labels            Configure the standard label taxonomy in the GitHub repository

Bug fix fast path (entry: bugfix)

  /check-duplicates        Search for duplicate issues and existing fix PRs
  /reproduce-issue         Bug report: create worktree, reproduce, post results
  /fix-issue               Orchestrator: check-duplicates → reproduce-issue → create-implementation → create-pr
                          (escalates to main flow at requirements if the fix is non-trivial)

Cross-cutting records (invoke at any point in any flow)

  /create-assumption      Record an assumption with basis, risk, and validation plan
  /review-assumption      Audit specificity, basis quality, risk, validation adequacy
  /create-decision        Record an architectural/implementation decision with context
  /review-decision        Audit clarity, reasoning quality, consequence coverage
  /supersede-decision     Mark a decision as superseded by a newer one (old-decision new-decision)

Cross-cutting guard (runs automatically before every phase via the Linked-PR Guard)

  /check-linked-pr        Detect a PR someone else linked to the current issue; offer continue / stop / review

Maintenance (entry: maintenance — run periodically, independent of any feature)

  Coordinated audit
  /audit-sdlc                Run multiple audit skills and produce a unified findings report

  Individual audit skills (also available via /audit-sdlc)

  Diagnose — surface what is risky or actively unstable
  /audit-dependencies         Audit dependencies for CVEs, outdated versions, unmaintained packages, and license issues
  /audit-security             Scan code for hardcoded secrets, injection risks, missing auth checks, and insecure patterns
  /analyze-git-churn          Identify high-churn files and generate improvement suggestions

  Harden — reduce structural risk before changing code
  /find-complexity-hotspots   Find functions and modules with high cyclomatic complexity, excessive length, or deep nesting
  /find-type-gaps             Identify missing type annotations in Python, TypeScript, and JavaScript
  /find-coverage-gaps         Identify files with missing or insufficient test coverage, ranked by churn and complexity

  Clean — remove what no longer belongs
  /find-dead-code             Find unused functions, classes, variables, exports, feature flags, and config keys
  /find-code-duplication      Identify copy-pasted blocks and near-duplicate logic to extract into shared helpers

  Document — record what remains
  /find-documentation-gaps    Find public APIs, CLI commands, and config keys that lack documentation

  Observe — monitor production health and surface runtime issues
  /observe-production         Check SLOs/SLIs, review error rates, latency, and throughput for deployed features
  /audit-observability        Identify missing logging, metrics, tracing, and alerting for production services

Fast paths               Abbreviated sequences from the main flow for small,
                          well-understood changes (see "Fast Paths for Small Work")
```

## Fast Paths for Small Work

Not every change needs the full pipeline.
Use the table below to determine the minimum viable path for common small-work scenarios.
When in doubt, include more phases rather than fewer.

| Scenario | Example | Path |
|---|---|---|
| **Bug fix** | Fix an off-by-one error, correct a typo in logic | `fix-issue` (dedicated fast path with worktree + reproduction) |
| **Hotfix** | Patch a production incident, revert a bad deploy | `create-implementation` → `create-pr` → `merge-pr` → `deploy-pr` |
| **Config change** | Update a threshold, toggle a feature flag, fix a YAML typo | `create-implementation` → `create-pr` → `merge-pr` → `deploy-pr` |
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

## Directory Structure

All SDLC artifacts live under `.sdlc/` in the repository root.
When the `SDLC_DIR` environment variable is set, the same tree can also live (or be mirrored) outside the repo under `$SDLC_DIR/{owner}/{repository}/.sdlc/`; see Artifact Location Resolution below and `references/shared.md` for the full rules.

```
.sdlc/
├── .gitignore                     # Excludes state.yml and features/*/progress.md (local-only)
├── context/
│   ├── project-overview.md        # Project goals, scope, key stakeholders
│   ├── architecture.md            # Architecture decisions and patterns
│   └── conventions.md             # Naming, structure, coding standards
├── state.yml                      # Orchestrator run state (local-only, gitignored)
├── features/
│   └── N-<slug>/          # One directory per feature (e.g., 42-notification-system)
│       ├── progress.md            # Feature-level progress + session log (local-only, gitignored)
│       ├── needs-assessment.md
│       ├── requirements.md
│       ├── existing-solutions.md
│       ├── codebase-analysis.md
│       ├── feasibility.md
│       ├── specification.md
│       ├── mockups.md
│       ├── telemetry.md
│       ├── observability.md
│       ├── plan.md
│       ├── tasks/                 # One file per task (e.g., 1-setup-db-schema.md)
│       │   └── N-<slug>.md
│       └── tests.md
├── templates/                     # Editable defaults used by create-* skills; kept in sync by /update-sdlc-templates
│   ├── features/
│   │   ├── needs-assessment.md
│   │   ├── requirements.md
│   │   ├── existing-solutions.md
│   │   ├── codebase-analysis.md
│   │   ├── feasibility.md
│   │   ├── specification.md
│   │   ├── mockups.md
│   │   ├── telemetry.md
│   │   ├── observability.md
│   │   ├── plan.md
│   │   ├── progress.md            # Template for feature-level progress tracking
│   │   ├── task.md                # Template for a single task file
│   │   └── tests.md
│   └── knowledge/
│       ├── assumption.md
│       ├── decision.md
│       └── learning.md
└── knowledge/
    ├── assumptions/
    │   └── N-<slug>.md         # Created by /create-assumption; one file per assumption
    ├── decisions/
    │   └── N-<slug>.md         # Created by /create-decision; one file per decision
    └── learnings/
        └── N-<slug>.md         # Created by /create-learnings; one file per retrospective
```

**Feature directory naming:** directories under `features/` are named `N-<slug>` (no `FEAT-` prefix, since the parent directory already conveys the kind). `N` is the issue number, used verbatim with no zero-padding, when the work is tied to a GitHub issue (e.g., issue `#42` → directory `42-<slug>` with feature ID `FEAT-42`); otherwise `N` is a `p`-prefixed sequence number marking a feature that is **pending a placeholder issue** (e.g., `p1-<slug>` with feature ID `FEAT-p1`). Slug is lowercase, hyphens for spaces, no special characters. The related GitHub issue is recorded in frontmatter when present. The **feature ID** `FEAT-N` is used in cross-references (see ID Formats below). The full rules live in `references/shared.md` under Feature Directory Naming.

## Artifact Location Resolution (SDLC_DIR)

The complete resolution rules — `{owner}/{repository}` derivation, the repo-first read fallback, write mirroring, and what is never mirrored — live in `references/shared.md`, the single source shared across all SDLC skills.
Apply them to every `.sdlc/` read and write in this pipeline.
Summary: reads check the repo's `.sdlc/` first, then `$SDLC_DIR/{owner}/{repository}/.sdlc/`; writes go to the repo and mirror to `SDLC_DIR` when set; `state.yml` and `features/*/progress.md` are never mirrored.

## ID Formats and Cross-References

Each artifact type uses a consistent ID format:

| Artifact | Format | Scope | Example |
|---|---|---|---|
| Feature | `FEAT-N` | Project-wide | `FEAT-42` |
| Functional requirement | `FR-N` | Per-feature | `FR-1` |
| Non-functional requirement | `NFR-N` | Per-feature | `NFR-2` |
| Task | `N` | Per-feature | `3` |
| Test case | `TC-N` | Per-feature | `TC-5` |
| Assumption | `N` | Project-wide | `1` |
| Decision | `N` | Project-wide | `2` |

All SDLC numeric identifiers are unpadded: `FEAT-42`, `FR-1`, `TC-5`, task `3` use the bare number, never zero-padded. A feature with no issue yet uses a `p`-prefixed id instead (e.g. `FEAT-p1`, directory `p1-<slug>`); see Feature Directory Naming. The `FEAT-` prefix marks the feature **cross-reference ID** only; the on-disk directory drops it (`N-<slug>` under `features/`).

**Within a feature document**, use bare IDs (`FR-1`, `NFR-2`, `TC-5`) — the feature scope is implied by the file location.

**Across features**, qualify with the feature prefix: `FEAT-1-FR-1`, `FEAT-2-NFR-3`. Use this form whenever a requirement, test case, or task is referenced from outside its own feature directory (e.g., in a plan dependency, a cross-cutting assumption, or a shared specification).

Each pipeline artifact carries YAML frontmatter tracking its state:

```yaml
---
issue: "#42"
title: "Notification System"
status: draft        # set on creation; review outcome lives in review-<artifact>.md
---
```

`create-*` pipeline skills write artifacts with `status: draft`.
`review-*` pipeline skills do not modify the artifact `status`; they write a `review-<artifact>.md` findings file (verdict `approved` / `changes-requested` / `rejected`) beside the artifact, per `skills/sdlc/references/shared.md`. Downstream phases gate on that findings verdict, not on the artifact `status`.
Domain lifecycle statuses are the exception and are still set by their review skill: task `pending` (set by `review-tasks-decomposition`), and the knowledge-record terminals: assumption (`Active → Validated | Invalidated | Deferred`), decision (`Proposed → Accepted | Deprecated | Superseded`), and learnings (`draft → complete`).

### Task Status Lifecycle

Tasks use an expanded status vocabulary to track progress across sessions:

```
draft → pending → in-progress → done
                   |                 ↑
                   → blocked ────────┘
                   |
                   → cancelled
```

| Status | Meaning | Set by |
|---|---|---|
| `draft` | Initial state, created by decomposition | `create-tasks-decomposition` |
| `pending` | Reviewed and approved, ready to start | `review-tasks-decomposition` |
| `in-progress` | Actively being worked on | `create-implementation` or manually |
| `blocked` | Cannot proceed, waiting on external dependency | `create-implementation` or manually |
| `done` | All acceptance criteria met, tests passing | `create-implementation` after checklist |
| `cancelled` | No longer needed (superseded or descoped) | Manually |

When a task reaches `done`, set `completed_date` to the current date (ISO format).
When a task is `blocked`, set `blocker` to a brief description in the task frontmatter.

Open questions surfaced during review are recorded in that review's findings body. When `backpropagate-sdlc` or `sync-sdlc` detects that an artifact drifted from the code, it regresses that artifact's `review-<artifact>.md` from `approved` to `changes-requested` (recording the drift in the body) so the forward pipeline resyncs and re-reviews it. When a question carries meaningful risk, promote it to a formal assumption via `/create-assumption`.
Architectural choices made during any phase are logged via `/create-decision` to `.sdlc/knowledge/decisions/`.

## Entry Points

| Phase | Start here when you have... |
|---|---|
| `status` | Want to see current progress on a feature or pick up where you left off (runs progress report, no side effects) |
| `setup` | A new project that needs the `.sdlc/` structure bootstrapped (runs `sync-sdlc`, which creates `.sdlc/` if absent) |
| `sync` | An existing `.sdlc/` that needs reconciling with the current codebase (runs `sync-sdlc`) |
| `configure-labels` | A repository that needs the standard label taxonomy created or updated |
| `issue` | A feature idea or bug to capture as a GitHub issue |
| `issues` | A backlog of unlabeled/unranked issues |
| `qualify` | An externally submitted issue that needs iterative Q&A before requirements |
| `needs` | An issue ready to assess whether it addresses a genuine need before investing in requirements |
| `requirements` | An issue ready to develop requirements |
| `existing-solutions` | Approved requirements ready to survey for prior art |
| `codebase-analysis` | Approved requirements (and existing-solutions survey) ready to analyze the internal code/architecture the feature will touch |
| `feasibility` | Requirements, existing solutions, and codebase analysis ready for viability assessment |
| `specifications` | Requirements, solutions survey, and feasibility ready for technical design |
| `mockups` | An approved specification ready to define the UI wireframes, screens, and interaction states (UI features) |
| `telemetry` | A specification ready to define how feature usage will be measured |
| `observability` | A specification ready to define how feature health will be monitored |
| `plan` | A specification (and telemetry/observability plans) ready for planning |
| `publish-plan` | A reviewed plan ready to commit and share with the issue author |
| `tasks` | An approved plan signed off by the issue author |
| `tests` | A task decomposition ready for test design |
| `implementation` | Tests ready; time to write code |
| `documentation` | Implementation reviewed; code needs docs |
| `pr` | Documentation done and ready to open a pull request |
| `validate-pr` | PR is open and claims need runtime validation (build, run, record demos) |
| `verify-pr` | PR claims validated at runtime, ready for static code inspection |
| `handle-pr-ci` | PR has failing CI checks to fix |
| `handle-pr-feedback` | PR is open and has reviewer comments to address |
| `merge-pr` | PR is approved and CI is green, ready to merge |
| `deploy` | PR is merged and ready to deploy to the target environment |
| `bugfix` | A bug report issue to reproduce, fix, and submit as a PR (runs `fix-issue`) |
| `reproduce` | A bug report issue to reproduce only, without implementing a fix (runs `reproduce-issue`) |
| `learnings` | A completed feature or sprint to reflect on |
| `assumption` | An assumption to record (can be invoked at any phase) |
| `decision` | A decision to record (can be invoked at any phase) |
| `continue` | Resume an in-progress feature by scanning `.sdlc/features/` for unfinished work (runs Automatic Resume) |
| `maintenance` | Run one or more maintenance skills (see Maintenance section in Pipeline Overview) to surface technical debt; findings feed into issue creation and backlog prioritization |
| `audit` | Run `/audit-sdlc` to coordinate multiple audit skills and produce a unified findings report |

## State File

The orchestrator maintains `.sdlc/state.yml` in the repository root to track the current run.
Read it at the start of every invocation to resume context; write it after every phase transition.
It is local-only workflow state and is never read from or mirrored to `SDLC_DIR` (see `references/shared.md`).

```yaml
current_phase: null             # the next phase to run (entry point name)
github_ref: null                # GitHub issue or PR number, e.g. "#42"
feature: null                   # N-<slug> directory name if one has been created, null otherwise
linked_prs_acknowledged: []     # PR numbers from other authors the user chose to ignore this run
```

- **On first entry**: create `.sdlc/state.yml`, populating `current_phase` with the entry point and `github_ref` if known.
- **After each phase completes**: update `current_phase` to the name of the next phase to run. This is the single rule: `current_phase` always holds what comes next.
- **When a feature directory is created**: populate `feature`.
- **When `github_ref` changes** (issue created, PR opened): update `github_ref`.
- **When the Linked-PR Guard runs** and the user dismisses a competing PR: append its number to `linked_prs_acknowledged` so the guard does not re-prompt for it (see Linked-PR Guard).
- **On pipeline completion**: set `current_phase` to `complete`.

### Local-only files (never commit)

`state.yml` and each feature's `progress.md` are local workflow state, regenerated per machine and per run.
They must never be committed or included in PRs.
`/initialize-sdlc-directory` creates a `.sdlc/.gitignore` that excludes them, and `/sync-sdlc` keeps it up to date:

```gitignore
# Local-only workflow state — do not commit
# Orchestrator run state
state.yml
# Per-feature progress tracking and session logs
features/*/progress.md
```

If you commit/push manually, never `git add` these two paths.

## Steps

1. Read `.sdlc/state.yml` if it exists. Use its values as defaults for `current_phase`, `github_ref`, and `feature` unless the user provides explicit arguments.
2. Determine the entry point: normalize `$1` to lowercase and check against the supported entry points. If a match is found, use it. If `$1` does not match any supported entry point (case-insensitive), do not attempt to infer the phase from the text. Instead, inform the user that the phase is not recognized and ask them to pick a valid entry point. If the entry point is `continue`, run the Automatic Resume flow instead of advancing through the pipeline.
3. If the entry point is `status`, invoke the `sdlc-status` skill. Do not advance the pipeline or modify any artifacts.
4. If the entry point is `qualify`, invoke the `qualify-issue` skill directly. It drives a multi-round Q&A loop with the external reporter, updating the issue body once the issue is fully understood. It stops when all questions are answered (issue qualified) or when a clarification comment has been posted and the reporter must reply. Re-enter at `qualify` when the reporter replies. Proceed to `requirements` once qualification is complete.
5. If the entry point is `bugfix`, invoke the `fix-issue` skill directly. It orchestrates `reproduce-issue` → `create-implementation` → `create-pr` and does not proceed through the remaining SDLC phases. If the fix turns out to be non-trivial, `fix-issue` will escalate back to the full pipeline at the `requirements` phase.
6. If the entry point is `reproduce`, invoke the `reproduce-issue` skill directly. It handles worktree creation and reproduction. It stops after posting results and does not proceed to implementation.
7. If the entry point is `maintenance`, ask the user which maintenance skill to run (or run all applicable ones). Each maintenance skill runs independently and produces findings that can be fed into `create-issue` and `prioritize-issues`.
8. If the entry point is `sync`, invoke the `sync-sdlc` skill directly. It analyzes the codebase against the existing `.sdlc/` directory and produces a reconciliation report. This is a standalone operation that does not advance the pipeline.
9. Read `.sdlc/context/` (`project-overview.md`, `architecture.md`, `conventions.md`) for project-level context before invoking any sub-skill, and apply the style rules found in `conventions.md` to every document produced during the pipeline. The shared conventions (context reading and `.sdlc/` path resolution via `SDLC_DIR`) are defined in `references/shared.md` and are not repeated per sub-skill.
10. Confirm the artifacts available for the current phase (previous phase output under `.sdlc/features/N-<slug>/`, existing files, or context).
11. **Before executing each sub-skill**, run the [Linked-PR Guard](#linked-pr-guard-between-phases): invoke `check-linked-pr` against the current issue. If a competing PR is found that the user has not already dismissed, stop and present the continue / stop / review options. Only proceed to the sub-skill when the guard is clear or the user chose to continue. This runs at every phase transition.
12. **Before executing each sub-skill, load it with the `skill` tool.** This is mandatory (see *Load Each Phase Skill* above). A phase's rules take effect only once loaded, so always load first, then perform the skill's steps. Never run a phase's commit, push, or PR actions without loading the governing skill first. Execute sub-skills in order from the entry point to the end of the pipeline.
13. After each `create-*` phase, always run the corresponding `review-*` phase and address findings before advancing.
14. When all review findings are resolved, move to the next phase.
15. After each phase completes, update `.sdlc/state.yml`: set `current_phase` to the next phase to run (or `complete` if the pipeline is done), update `github_ref` and `feature` if they changed. Also update `.sdlc/features/N-<slug>/progress.md` (see Progress Tracking below). This update is mandatory before proceeding or ending the session.
16. When the session ends (user stops, pipeline stops, or session is complete), write a session boundary marker to `progress.md` (see Session Boundary Markers below).
17. After learnings are captured and reviewed, the cycle is complete.

### Status Report (entry: `status`)

Delegate to the `sdlc-status` skill, which handles all reporting logic including the HTML dashboard script and text-based fallback. See `sdlc-status/SKILL.md` for details.

### Linked-PR Guard (between phases)

Before every sub-skill runs (step 10), the orchestrator checks whether someone else has linked a pull request to the issue being worked on. This catches a competing PR that appears after work has already started, so effort is not duplicated.

Invoke the `check-linked-pr` skill against the current issue (resolved from `github_ref`):

```
/check-linked-pr <issue-number> <owner>/<repository>
```

The guard is **skipped** (treated as clear) when:

- The feature has no GitHub issue yet (a `p`-prefixed feature), so nothing can be linked.
- The current phase is the issue/PR plumbing itself (`create-issue`, `create-pr`, `merge-pr`, etc.) where no separate issue lookup is meaningful.
- `$OUTCOME_YAML` is set and no interactive user is present (see the skill's Outcome section; under automation the guard emits a verdict and never blocks).

When the guard finds a competing PR the user has not already dismissed, present the three options the `check-linked-pr` skill defines:

| Choice | Effect |
|---|---|
| **Continue** | The PR number is appended to `linked_prs_acknowledged` in `.sdlc/state.yml`; the guard will not re-prompt for it. Proceed with the current phase. |
| **Stop** | Pause the pipeline pending the external PR. Record the dependency (PR number, author) in `progress.md` and leave the pipeline resumable. |
| **Review** | Run `/review-pr <pr-number>`. If it approves, stop the flow and depend on the external PR. If it requests changes or rejects, acknowledge the PR and continue the current flow. |

Because dismissed PR numbers persist in `state.yml`, running the guard at every phase transition stays low-noise: it only surfaces genuinely new competing PRs.

### Automatic Resume (entry: `continue`)

When `/sdlc continue` is invoked:

1. Scan `.sdlc/features/*/progress.md` for features where `current_phase` is not `complete` and `re_entry_point` is set.
2. If exactly one in-progress feature is found, present its status report and ask: "Resume at `<re_entry_point>` for `<feature>`?"
3. If multiple in-progress features are found, show the summary table and ask which one to resume.
4. If no in-progress features are found, inform the user and ask for an entry point.
5. The user can always override by specifying an explicit entry point.

### Progress Tracking

The `progress.md` file in each feature directory is the single source of truth for feature status.
It is updated automatically by the orchestrator after each phase completes.

**When to update `progress.md`:**
- After any `create-*` or `review-*` phase completes (update the Pipeline Status table).
- When a task status changes (update the Task Progress table and completion count).
- When a blocker is encountered or resolved (update Current Blocker).
- At session start and end (add entry to Session Log).

**Updating task status during implementation:**
When `create-implementation` starts work on a task, set its frontmatter `status: in-progress`.
When the task checklist passes, set `status: done` and `completed_date`.
If blocked, set `status: blocked` and fill in `blocker`.
After each task status change, update the Task Progress table in `progress.md`.

### Session Boundary Markers

At the start and end of every session working on a feature, write a brief entry to the Session Log in `progress.md`.

**Session start** (when resuming work on a feature):
- Read the last Session Log entry to determine where you left off.
- Add a new row: `| <today> | Resumed. <what you plan to work on> | <expected next step> |`

**Session end** (when stopping, pausing, or completing the session):
- Add a new row: `| <today> | <what was accomplished> | <where to pick up next, with phase name> |`
- Update `re_entry_point` in frontmatter to the phase where the next session should start.
- Update `last_updated` in frontmatter to today's date.
- If blocked, update `current_phase` and the Current Blocker section.

These markers ensure the next session (which may be days or weeks later) can quickly determine where to resume without re-reading all artifacts.

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
| **Needs rejected** | `review-needs-assessment` concludes the feature does not address a genuine need | Update the issue with findings and the rejection rationale. Stop the pipeline. The issue may be revisited if new evidence emerges. |
| **Feasibility rejected** | `review-feasibility` concludes the feature is not viable | Update the issue with findings and the rejection rationale. Stop the pipeline. The issue may be revisited if conditions change. |
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
- Write a session end marker to `progress.md` with the re-entry point for the next session.
- Update `progress.md` frontmatter: `re_entry_point`, `current_phase`, and `last_updated`.

## Phase Contracts

Each phase consumes output from the previous phase:

| Phase | Input | Output |
|---|---|---|
| sync-sdlc | Existing project root (`.sdlc/` created if absent) | Updated `.sdlc/` with context files, new feature directories, drift report for existing features |
| initialize-sdlc-directory | Project root (optional) | `.sdlc/` directory tree + templates populated |
| update-sdlc-templates | `.sdlc/templates/` + canonical templates | Merged/updated templates; conflicts flagged |
| configure-labels | GitHub repository | Standard label taxonomy created/updated; summary of created, updated, and unchanged labels |
| create-issue | Feature idea / bug description | Structured GitHub issue |
| review-issue | GitHub issue | Findings + improved ACs (resolve before next phase) |
| qualify-issue | GitHub issue with open questions | Fully qualified issue; updated body + qualification comment posted |
| triage-issues | Open issues | Labeled, classified issues |
| prioritize-issues | Labeled issues | RICE-ranked backlog |
| create-needs-assessment | Reviewed, prioritized issue | `.sdlc/features/N-<slug>/needs-assessment.md` (`status: draft`) |
| review-needs-assessment | `.sdlc/features/N-<slug>/needs-assessment.md` | Findings → `review-needs-assessment.md` (verdict `approved`/`rejected`) |
| create-requirements | `.sdlc/features/N-<slug>/needs-assessment.md` (review approved) | `.sdlc/features/N-<slug>/requirements.md` (`status: draft`) |
| review-requirements | `.sdlc/features/N-<slug>/requirements.md` | Findings → `review-requirements.md` |
| create-existing-solutions | `.sdlc/features/N-<slug>/requirements.md` | `.sdlc/features/N-<slug>/existing-solutions.md` (`status: draft`) |
| review-existing-solutions | `.sdlc/features/N-<slug>/existing-solutions.md` | Findings → `review-existing-solutions.md` |
| create-codebase-analysis | `.sdlc/features/N-<slug>/requirements.md` (+ `existing-solutions.md`) | `.sdlc/features/N-<slug>/codebase-analysis.md` (`status: draft`) |
| review-codebase-analysis | `.sdlc/features/N-<slug>/codebase-analysis.md` | Findings → `review-codebase-analysis.md` |
| create-feasibility | `.sdlc/features/N-<slug>/requirements.md` + `existing-solutions.md` + `codebase-analysis.md` | `.sdlc/features/N-<slug>/feasibility.md` (`status: draft`) |
| review-feasibility | `.sdlc/features/N-<slug>/feasibility.md` | Findings → `review-feasibility.md` (verdict `approved`/`rejected`) |
| create-specifications | `.sdlc/features/N-<slug>/requirements.md` + `existing-solutions.md` + `codebase-analysis.md` + `feasibility.md` | `.sdlc/features/N-<slug>/specification.md` (`status: draft`) |
| review-specifications | `.sdlc/features/N-<slug>/specification.md` | Findings → `review-specifications.md` |
| create-mockups | `.sdlc/features/N-<slug>/requirements.md` + `specification.md` | `.sdlc/features/N-<slug>/mockups.md` (`status: draft`); skipped (no artifact) when the feature has no UI surface |
| review-mockups | `.sdlc/features/N-<slug>/mockups.md` | Findings → `review-mockups.md` |
| create-telemetry | `.sdlc/features/N-<slug>/specification.md` | `.sdlc/features/N-<slug>/telemetry.md` (`status: draft`) |
| review-telemetry | `.sdlc/features/N-<slug>/telemetry.md` | Findings → `review-telemetry.md` |
| create-observability | `.sdlc/features/N-<slug>/specification.md` | `.sdlc/features/N-<slug>/observability.md` (`status: draft`) |
| review-observability | `.sdlc/features/N-<slug>/observability.md` | Findings → `review-observability.md` |
| create-plan | `.sdlc/features/N-<slug>/specification.md` + `mockups.md` (if UI) + `telemetry.md` + `observability.md` | `.sdlc/features/N-<slug>/plan.md` (`status: draft`) |
| review-plan | `.sdlc/features/N-<slug>/plan.md` | Findings → `review-plan.md` |
| publish-plan | `.sdlc/features/N-<slug>/plan.md` | Draft PR + issue comment (gate: author sign-off) |
| create-tasks-decomposition | `.sdlc/features/N-<slug>/plan.md` | `.sdlc/features/N-<slug>/tasks/N-<slug>.md` per task (`status: draft`) + initializes `progress.md` |
| review-tasks-decomposition | `.sdlc/features/N-<slug>/tasks/` (all task files) | Findings → `review-tasks.md`; on approval sets each task `status: pending`; populates Task Progress table in `progress.md` |
| create-tests | `.sdlc/features/N-<slug>/requirements.md` + `specification.md` + `telemetry.md` + `observability.md` | `.sdlc/features/N-<slug>/tests.md` (`status: draft`) |
| review-tests | `.sdlc/features/N-<slug>/tests.md` | Findings → `review-tests.md` |
| create-implementation | `.sdlc/features/N-<slug>/tasks/` + `specification.md` + `tests.md` + `telemetry.md` + `observability.md` | Working code; task files updated to `status: in-progress` then `status: done`; `progress.md` Task Progress table updated |
| review-implementation | Code + spec + telemetry + observability | Findings → `review-implementation.md` |
| create-documentation | Implemented feature | Documentation |
| review-documentation | Documentation | Findings → `review-documentation.md` |
| create-pr | Reviewed code + docs + issue | Pull request |
| validate-pr | Pull request | Validation report: runtime proof of each claim, asciinema recordings for CLI changes |
| verify-pr | Pull request + validation report | Verification report: claim-to-code traceability, code quality findings |
| review-pr | Pull request | Code review findings (resolve before merge) |
| handle-pr-ci | PR with failing CI checks | Root cause diagnosed, fix committed, CI green (repeat until passing) |
| handle-pr-feedback | PR with reviewer comments | Addressed comments, pushed, re-review requested (repeat until approved) |
| merge-pr | Approved PR with green CI | Merged PR, deleted branch, closed issue |
| deploy-pr | Merged PR | Deployed changes, smoke tests passed, rollback plan verified |
| fix-issue | GitHub issue describing a bug | Orchestrated bug fix: check-duplicates, reproduction, implementation, PR |
| check-duplicates | GitHub issue | Duplicate issues and existing fix PRs checked, results posted |
| reproduce-issue | GitHub issue describing a bug | Worktree created, reproduction attempted, results posted |
| create-learnings | Completed feature/sprint | `.sdlc/knowledge/learnings/N-<slug>.md` (`status: draft`) |
| review-learnings | `.sdlc/knowledge/learnings/N-<slug>.md` | Findings; sets `status: complete` when resolved |
| create-assumption | Any phase context | `.sdlc/knowledge/assumptions/N-<slug>.md` |
| review-assumption | `.sdlc/knowledge/assumptions/N-<slug>.md` | Findings (improve basis, risk, validation) |
| create-decision | Any phase context | `.sdlc/knowledge/decisions/N-<slug>.md` |
| review-decision | `.sdlc/knowledge/decisions/N-<slug>.md` | Findings (improve clarity, reasoning, consequences) |
| supersede-decision | Two decisions under `.sdlc/knowledge/decisions/` | Old decision marked `Superseded by [N]`; new decision annotated with reverse link |
| observe-production | Deployed service + observability tools | Health report: SLO status, error rates, latency, throughput, alerts triggered |
| audit-observability | Codebase + running service | Gaps report: missing logs, metrics, traces, alerts for production services |

## Skipping Review Phases

Review phases may be skipped in low-risk or exploratory contexts.
State the skip explicitly: "Skipping review-requirements — prototype context."
Never skip reviews for security-sensitive features or production-bound work.

## Commit / Push / PR Gate (mandatory)

Never commit, push, or open a PR without an explicit request from the user, even when the pipeline flow reaches a phase that includes these actions (e.g. `publish-plan`, `create-pr`, `merge-pr`, `deploy-pr`, `fix-issue`).

When the pipeline reaches a phase that would commit, push, or open a PR:

1. Complete all non-destructive work for that phase (write code, update artifacts, run tests, run type-check and lint).
2. Stop and report what was done and what the next action would be.
3. Wait for the user to explicitly say to commit, push, or create the PR.

This applies to all entry points and fast paths, including `bugfix`.
