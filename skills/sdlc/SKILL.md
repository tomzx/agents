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
This is especially true for skills that commit, push, or open PRs (`create-pr`, `fix-issue`, `publish-plan`, `merge-pr`, `deploy-pr`, `handle-pr-ci`, `handle-pr-reviewer-feedback`): their commit and push rules are bypassed whenever they are not loaded.

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
  /create-lifecycle       Document resource states, transitions, invariants, retention (resource lifecycle features; skip if no lifecycle)
  /review-lifecycle       Audit completeness, consistency, spec alignment, transition correctness
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
  /validate-assumptions          Design and run minimal code experiments to verify risky technical assumptions before implementation
  /review-assumption-validation  Audit completeness, experiment quality, result rigor, and proceed/backtrack soundness
                                 (gate: backtrack if critical assumptions invalidated)
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
   /validate-implementation Capture visual proof on the branch and get user sign-off before the PR (no-op for non-visual changes)
           │
           ▼
    /create-pr              Open a PR: description, AC coverage, issue link, reviewers (embeds pre-captured proof)
    /validate-pr            Needs alignment: is the PR the right product; are the criteria sound
    /verify-pr              Conformance: criteria-to-code traceability + runtime proof per criterion
   /review-pr              Comprehensive code review of the PR
  /handle-pr-ci           Diagnose failing CI checks, fix, push, confirm green (repeat until passing)
  /handle-pr-reviewer-feedback  Address reviewer comments, push, re-request review (repeat until approved)
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

Project context (invoke when establishing or revising project-level context that features align to)

  /create-project        Interview the user to populate the core .sdlc/context/ files for a new or empty project
  /review-project        Audit the context files for completeness, consistency, clarity, actionability
  /identify-feature-opportunities  Generate and rank new feature opportunities from the software surface and signals (bottom-up discovery feeding roadmap)
  /create-goals          Define objectives, key results, and KPIs the project aligns to
  /review-goals          Audit measurability, ownership, alignment, focus
  /create-roadmap        Sequence initiatives across Now/Next/Later horizons, aligned to goals
  /review-roadmap        Audit alignment, sequencing, focus, horizon discipline, currency
  /create-service-levels  Define SLOs, SLIs, SLAs, and error budgets for the service
  /review-service-levels  Audit measurability, coverage, error-budget policy, alignment

  Greenfield continuation: once the roadmap is reviewed, enter the main flow at the
  requirements stage with the first Now initiative as the feature brief, skipping
  create-issue (the requirements skill creates a p-prefixed pending feature; promote
  it to an issue later via /create-placeholder-issue)

Bug fix fast path (entry: bugfix)

  /check-duplicates        Search for duplicate issues and existing fix PRs
  /reproduce-issue         Bug report: create worktree, reproduce, record "before" video, post results
  /fix-issue               Orchestrator: check-duplicates → reproduce-issue → create-implementation → validate-implementation → create-pr
                           (validate-implementation replays the reproduce-issue before-command on the fixed code
                            to capture a comparable after recording; create-pr embeds the pair)
                           (escalates to main flow at requirements if the fix is non-trivial)

Cross-cutting records (invoke at any point in any flow)

  /create-domain-model    Model an unfamiliar domain (entities, relationships, glossary, invariants) as a one-off
  /review-domain-model    Audit entity coverage, relationship correctness, vocabulary, invariants, boundaries
  /create-question        Record an open question with context, answerer, impact, needed-by date
  /review-question        Audit specificity, answerability, impact; record the resolution
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
| **Hotfix** | Patch a production incident, revert a bad deploy | `create-implementation` → `validate-implementation` → `create-pr` → `merge-pr` → `deploy-pr` |
| **Config change** | Update a threshold, toggle a feature flag, fix a YAML typo | `create-implementation` → `create-pr` → `merge-pr` → `deploy-pr` |
| **Dependency update** | Bump a library version, patch a CVE in a transitive dep | `create-implementation` → `validate-implementation` → `create-pr` → `review-pr` → `merge-pr` |
| **Refactor (no behavior change)** | Rename a method, extract a helper, improve naming | `create-tests` → `create-implementation` → `validate-implementation` → `create-pr` → `review-pr` → `merge-pr` |
| **Documentation-only** | Fix a typo in docs, add a missing API example | `create-documentation` → `create-pr` → `merge-pr` |

### Rules for fast paths

1. Create an issue when the change needs context, discussion, or prioritization. For self-explanatory changes (typo fix, config toggle, version bump), the PR description is sufficient traceability.
2. Always open a PR, even for hotfixes, so CI runs and the change is reviewable after the fact.
3. Skip requirements, specifications, plan, and tasks only when the change is well-understood and fits in a single commit.
4. Include `review-implementation` when the fix is non-trivial or touches security-adjacent code.
5. Include `create-tests` when the change affects behavior or could regress.
6. Include `validate-implementation` before `create-pr` whenever the change has a CLI or web UI surface; it self-reports `surface: none` (a no-op) for config and documentation-only changes, which is why those fast paths omit it.
7. Never skip CI verification before merging.

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
│   ├── goals.md                   # Objectives, key results, KPIs (optional, via /create-goals)
│   ├── roadmap.md                 # Initiatives sequenced Now/Next/Later, aligned to goals (optional, via /create-roadmap)
│   ├── service-levels.md         # SLOs, SLIs, SLAs, error budgets (optional, via /create-service-levels)
│   ├── service-levels.yaml       # OpenSLO definitions, normative companion to service-levels.md (optional)
│   ├── architecture.md            # Architecture decisions and patterns
│   ├── schema.dbml                # Database schema in DBML format (present when the project uses a database)
│   ├── conventions.md             # Naming, structure, coding standards
│   ├── infrastructure.md          # Technology stack, dev tooling, CI/CD, environments, deployment
│   ├── observability.md           # Monitoring stack, instrumentation, alerting, dashboards (optional)
│   ├── telemetry.md               # Analytics platform, event conventions, taxonomy, privacy (optional)
│   └── vocabulary.md              # Domain and technical terms
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
│       ├── api.yaml                 # OpenAPI 3 contract, companion to specification.md (when the feature has an API surface)
│       ├── lifecycle.md
│       ├── mockups.md
│       ├── telemetry.md
│       ├── observability.md
│       ├── alerts.yaml              # Prometheus alert rules, companion to observability.md (when alerts are defined)
│       ├── plan.md
│       ├── assumption-validation.md
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
│   │   ├── api.yaml                 # OpenAPI 3 contract, companion to specification.md (when the feature has an API surface)
│   │   ├── lifecycle.md
│   │   ├── mockups.md
│   │   ├── telemetry.md
│   │   ├── observability.md
│   │   ├── alerts.yaml              # Prometheus alert rules, companion to observability.md (when alerts are defined)
│   │   ├── plan.md
│   │   ├── assumption-validation.md
│   │   ├── progress.md            # Template for feature-level progress tracking
│   │   ├── task.md                # Template for a single task file
│   │   └── tests.md
│   └── knowledge/
│       ├── assumption.md
│       ├── decision.md
│       ├── learning.md
│       └── question.md
└── knowledge/
    ├── assumptions/
    │   └── N-<slug>.md         # Created by /create-assumption; one file per assumption
    ├── decisions/
    │   └── N-<slug>.md         # Created by /create-decision; one file per decision
    ├── learnings/
    │   └── N-<slug>.md         # Created by /create-learnings; one file per retrospective
    └── questions/
        └── N-<slug>.md         # Created by /create-question; one file per question
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
| Question | `N` | Project-wide | `5` |

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
Domain lifecycle statuses are the exception and are still set by their review skill: task `pending` (set by `review-tasks-decomposition`), and the knowledge-record terminals: assumption (`Active → Validated | Invalidated | Deferred`), decision (`Proposed → Accepted | Deprecated | Superseded`), question (`Open → Resolved | Deferred | Dismissed`), and learnings (`draft → complete`).

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

Open questions surfaced during review are recorded in that review's findings body; questions that need tracking (a named answerer and a needed-by date) are promoted to question records via `/create-question`. When `backpropagate-sdlc` or `sync-sdlc` detects that an artifact drifted from the code, it regresses that artifact's `review-<artifact>.md` from `approved` to `changes-requested` (recording the drift in the body) so the forward pipeline resyncs and re-reviews it. When a question carries meaningful risk, promote it to a formal assumption via `/create-assumption`.
Architectural choices made during any phase are logged via `/create-decision` to `.sdlc/knowledge/decisions/`.

## Entry Points

| Phase | Start here when you have... |
|---|---|
| `status` | Want to see current progress on a feature or pick up where you left off (runs progress report, no side effects) |
| `setup` | A new project that needs the `.sdlc/` structure bootstrapped (runs `sync-sdlc`, which creates `.sdlc/` if absent) |
| `project` | A new or empty project whose core context files need populating by interview (runs `create-project` → `review-project`; no code analysis, unlike `sync`) |
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
| `lifecycle` | An approved specification ready to document how resources evolve over time (resource lifecycle features) |
| `mockups` | An approved specification (and lifecycle document if produced) ready to define the UI wireframes, screens, and interaction states (UI features) |
| `telemetry` | A specification ready to define how feature usage will be measured |
| `observability` | A specification ready to define how feature health will be monitored |
| `plan` | A specification (and telemetry/observability plans) ready for planning |
| `publish-plan` | A reviewed plan ready to commit and share with the issue author |
| `validate-assumptions` | A published plan signed off by the issue author, ready to verify risky technical assumptions before task decomposition |
| `tasks` | An assumption validation report (approved, or no risky assumptions) ready for task decomposition |
| `implementation` | Tests ready; time to write code |
| `documentation` | Implementation reviewed; code needs docs |
| `validate-implementation` | Docs done and ready to capture visual proof + get user sign-off before opening a PR (records a CLI demo or web screenshot on the branch; no-op for non-visual changes) |
| `pr` | Visual proof captured (or skipped); ready to open a pull request |
| `validate-pr` | PR is open; judge whether it builds the right product before spending a build |
| `verify-pr` | Right product confirmed; verify conformance to the acceptance criteria (traceability + runtime proof) |
| `handle-pr-ci` | PR has failing CI checks to fix |
| `handle-pr-reviewer-feedback` | PR is open and has reviewer comments to address |
| `merge-pr` | PR is approved and CI is green, ready to merge |
| `deploy` | PR is merged and ready to deploy to the target environment |
| `bugfix` | A bug report issue to reproduce, fix, and submit as a PR (runs `fix-issue`) |
| `reproduce` | A bug report issue to reproduce only, without implementing a fix (runs `reproduce-issue`) |
| `learnings` | A completed feature or sprint to reflect on |
| `assumption` | An assumption to record (can be invoked at any phase) |
| `decision` | A decision to record (can be invoked at any phase) |
| `question` | An open question to track (can be invoked at any phase) |
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

`status-report.html` (the generated output of `/sdlc-status`) is also local-only. `/initialize-sdlc-directory` and `/sync-sdlc` add it to the project root `.gitignore`.

If you commit/push manually, never `git add` these paths or `status-report.html`.

## Steps

1. Read `.sdlc/state.yml` if it exists. Use its values as defaults for `current_phase`, `github_ref`, and `feature` unless the user provides explicit arguments.
2. Determine the entry point: normalize `$1` to lowercase and check against the supported entry points. If a match is found, use it. If `$1` does not match any supported entry point (case-insensitive), do not attempt to infer the phase from the text. Instead, inform the user that the phase is not recognized and ask them to pick a valid entry point. If the entry point is `continue`, run the Automatic Resume flow instead of advancing through the pipeline.
3. If the entry point is `status`, invoke the `sdlc-status` skill. Do not advance the pipeline or modify any artifacts.
4. If the entry point is `qualify`, invoke the `qualify-issue` skill directly. It drives a multi-round Q&A loop with the external reporter, updating the issue body once the issue is fully understood. It stops when all questions are answered (issue qualified) or when a clarification comment has been posted and the reporter must reply. Re-enter at `qualify` when the reporter replies. Proceed to `requirements` once qualification is complete.
5. If the entry point is `bugfix`, invoke the `fix-issue` skill directly. It orchestrates `reproduce-issue` → `create-implementation` → `validate-implementation` → `create-pr` and does not proceed through the remaining SDLC phases. If the fix turns out to be non-trivial, `fix-issue` will escalate back to the full pipeline at the `requirements` phase.
6. If the entry point is `reproduce`, invoke the `reproduce-issue` skill directly. It handles worktree creation and reproduction. It stops after posting results and does not proceed to implementation.
7. If the entry point is `maintenance`, ask the user which maintenance skill to run (or run all applicable ones). Each maintenance skill runs independently and produces findings that can be fed into `create-issue` and `prioritize-issues`.
8. If the entry point is `sync`, invoke the `sync-sdlc` skill directly. It analyzes the codebase against the existing `.sdlc/` directory and produces a reconciliation report. This is a standalone operation that does not advance the pipeline.
9. If the entry point is `project`, invoke the `create-project` skill directly. It interviews the user to populate the core context files under `.sdlc/context/` (running `initialize-sdlc-directory` first when `.sdlc/` is absent), then invoke `review-project` and address findings. This is a standalone operation that does not advance the pipeline. Prefer it over `sync` when the project has no code to analyze.
10. Read `.sdlc/context/` (`project-overview.md`, `architecture.md`, `conventions.md`, `schema.dbml`, `infrastructure.md`) for project-level context before invoking any sub-skill, and apply the style rules found in `conventions.md` to every document produced during the pipeline. The shared conventions (context reading and `.sdlc/` path resolution via `SDLC_DIR`) are defined in `references/shared.md` and are not repeated per sub-skill.
11. Confirm the artifacts available for the current phase (previous phase output under `.sdlc/features/N-<slug>/`, existing files, or context).
12. **Before executing each sub-skill**, run the [Linked-PR Guard](#linked-pr-guard-between-phases): invoke `check-linked-pr` against the current issue. If a competing PR is found that the user has not already dismissed, stop and present the continue / stop / review options. Only proceed to the sub-skill when the guard is clear or the user chose to continue. This runs at every phase transition.
13. **Before executing each sub-skill, load it with the `skill` tool.** This is mandatory (see *Load Each Phase Skill* above). A phase's rules take effect only once loaded, so always load first, then perform the skill's steps. Never run a phase's commit, push, or PR actions without loading the governing skill first. Execute sub-skills in order from the entry point to the end of the pipeline.
14. After each `create-*` phase, always run the corresponding `review-*` phase and address findings before advancing.
15. When all review findings are resolved, move to the next phase.
16. After each phase completes, update `.sdlc/state.yml`: set `current_phase` to the next phase to run (or `complete` if the pipeline is done), update `github_ref` and `feature` if they changed. Also update `.sdlc/features/N-<slug>/progress.md` (see Progress Tracking below). This update is mandatory before proceeding or ending the session.
17. When the session ends (user stops, pipeline stops, or session is complete), write a session boundary marker to `progress.md` (see Session Boundary Markers below).
18. After learnings are captured and reviewed, the cycle is complete.

### Status Report (entry: `status`)

Delegate to the `sdlc-status` skill, which handles all reporting logic including the HTML dashboard script and text-based fallback. See `sdlc-status/SKILL.md` for details.

### Linked-PR Guard (between phases)

Before every sub-skill runs (step 12), the orchestrator checks whether someone else has linked a pull request to the issue being worked on. This catches a competing PR that appears after work has already started, so effort is not duplicated.

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
| **Review** | Run `/review-pr <pr-number>` (it posts the review comment unless `should-post-to-github` disables posting). If it approves, stop the flow and depend on the external PR. If it requests changes or rejects, acknowledge the PR and continue the current flow. |

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
| **Assumption invalidated** | `validate-assumptions` disproves a critical (High-risk) assumption that the specification or plan depends on | Backtrack to the affected design phase (specification or plan), revise the affected artifact, re-derive downstream artifacts, and re-run validation for any new assumptions. Record the backtrack via `/create-decision`. |
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
| sync-sdlc | Existing project root (`.sdlc/` created if absent) | Updated `.sdlc/` with context files, database schema in DBML (if the project uses a database), new feature directories, drift report for existing features, SDLC anchor in `AGENTS.md` |
| initialize-sdlc-directory | Project root (optional) | `.sdlc/` directory tree + templates populated + SDLC anchor in `AGENTS.md` |
| update-sdlc-templates | `.sdlc/templates/` + canonical templates | Merged/updated templates; conflicts flagged |
| configure-labels | GitHub repository | Standard label taxonomy created/updated; summary of created, updated, and unchanged labels |
| create-project | Project root with `.sdlc/` (created if absent) + user answering the interview | Populated core `.sdlc/context/` files (`project-overview.md`, `architecture.md`, `infrastructure.md`, `conventions.md`, `vocabulary.md`); placeholders remain for skipped questions |
| review-project | Core `.sdlc/context/` files | Findings → `.sdlc/context/review-project.md` (verdict `approved`/`changes-requested`/`rejected`) |
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
| create-specifications | `.sdlc/features/N-<slug>/requirements.md` + `existing-solutions.md` + `codebase-analysis.md` + `feasibility.md` | `.sdlc/features/N-<slug>/specification.md` (`status: draft`) + `api.yaml` (OpenAPI 3, when the feature has an API surface) |
| review-specifications | `.sdlc/features/N-<slug>/specification.md` | Findings → `review-specifications.md` |
| create-lifecycle | `.sdlc/features/N-<slug>/specification.md` | `.sdlc/features/N-<slug>/lifecycle.md` (`status: draft`); skipped (no artifact) when the feature manages no resources with a lifecycle |
| review-lifecycle | `.sdlc/features/N-<slug>/lifecycle.md` | Findings → `review-lifecycle.md` |
| create-mockups | `.sdlc/features/N-<slug>/requirements.md` + `specification.md` + `lifecycle.md` (if produced) | `.sdlc/features/N-<slug>/mockups.md` (`status: draft`); skipped (no artifact) when the feature has no UI surface |
| review-mockups | `.sdlc/features/N-<slug>/mockups.md` | Findings → `review-mockups.md` |
| create-telemetry | `.sdlc/features/N-<slug>/specification.md` + `lifecycle.md` (if produced) | `.sdlc/features/N-<slug>/telemetry.md` (`status: draft`) |
| review-telemetry | `.sdlc/features/N-<slug>/telemetry.md` | Findings → `review-telemetry.md` |
| create-observability | `.sdlc/features/N-<slug>/specification.md` + `lifecycle.md` (if produced) | `.sdlc/features/N-<slug>/observability.md` (`status: draft`) + `alerts.yaml` (Prometheus rules, when alerts are defined and the stack is Prometheus-compatible) |
| review-observability | `.sdlc/features/N-<slug>/observability.md` | Findings → `review-observability.md` |
| create-plan | `.sdlc/features/N-<slug>/specification.md` + `lifecycle.md` (if produced) + `mockups.md` (if UI) + `telemetry.md` + `observability.md` | `.sdlc/features/N-<slug>/plan.md` (`status: draft`) |
| review-plan | `.sdlc/features/N-<slug>/plan.md` | Findings → `review-plan.md` |
| publish-plan | `.sdlc/features/N-<slug>/plan.md` | Draft PR + issue comment (gate: author sign-off) |
| validate-assumptions | `.sdlc/features/N-<slug>/specification.md` + `plan.md` + `codebase-analysis.md` + `feasibility.md` + `.sdlc/knowledge/assumptions/` | `.sdlc/features/N-<slug>/assumption-validation.md` (`status: draft`); assumption statuses updated via `/review-assumption` |
| review-assumption-validation | `.sdlc/features/N-<slug>/assumption-validation.md` + `.sdlc/knowledge/assumptions/` | Findings → `review-assumption-validation.md` |
| create-tasks-decomposition | `.sdlc/features/N-<slug>/plan.md` (and assumption validation if produced) | `.sdlc/features/N-<slug>/tasks/N-<slug>.md` per task (`status: draft`) + initializes `progress.md` |
| review-tasks-decomposition | `.sdlc/features/N-<slug>/tasks/` (all task files) | Findings → `review-tasks.md`; on approval sets each task `status: pending`; populates Task Progress table in `progress.md` |
| create-tests | `.sdlc/features/N-<slug>/requirements.md` + `specification.md` + `lifecycle.md` (if produced) + `telemetry.md` + `observability.md` | `.sdlc/features/N-<slug>/tests.md` (`status: draft`) |
| review-tests | `.sdlc/features/N-<slug>/tests.md` | Findings → `review-tests.md` |
| create-implementation | `.sdlc/features/N-<slug>/tasks/` + `specification.md` + `lifecycle.md` (if produced) + `tests.md` + `telemetry.md` + `observability.md` | Working code; task files updated to `status: in-progress` then `status: done`; `progress.md` Task Progress table updated |
| review-implementation | Code + spec + telemetry + observability | Findings → `review-implementation.md` |
| create-documentation | Implemented feature | Documentation |
| review-documentation | Documentation | Findings → `review-documentation.md` |
| validate-implementation | Implemented feature on the branch (+ optional `proof-manifest.txt` from reproduce-issue for bug fixes) | Visual proof captured on the branch + `$PROOF_DIR/captured-proof.json` manifest; user sign-off (or `surface: none` for non-visual changes) |
| create-pr | Reviewed code + docs + issue + `captured-proof.json` (if any) | Pull request; embeds pre-captured proof (single asset, or before/after pair for bug fixes); never captures recordings itself |
| validate-pr | Pull request | Validation report: verdict on whether the PR builds the right product; needs/criteria/scope findings |
| verify-pr | Pull request | Conformance report: criteria-to-code traceability + runtime proof per criterion (asciinema/Playwright recordings) |
| review-pr | Pull request | Code review findings (resolve before merge) |
| handle-pr-ci | PR with failing CI checks | Root cause diagnosed, fix committed, CI green (repeat until passing) |
| handle-pr-reviewer-feedback | PR with reviewer comments | Addressed comments, pushed, re-review requested (repeat until approved) |
| merge-pr | Approved PR with green CI | Merged PR, deleted branch, closed issue |
| deploy-pr | Merged PR | Deployed changes, smoke tests passed, rollback plan verified |
| fix-issue | GitHub issue describing a bug | Orchestrated bug fix: check-duplicates, reproduction (with before recording), implementation, PR (with after recording paired against before) |
| check-duplicates | GitHub issue | Duplicate issues and existing fix PRs checked, results posted |
| reproduce-issue | GitHub issue describing a bug | Worktree created, reproduction attempted, before recording captured, results posted |
| create-learnings | Completed feature/sprint | `.sdlc/knowledge/learnings/N-<slug>.md` (`status: draft`) |
| review-learnings | `.sdlc/knowledge/learnings/N-<slug>.md` | Findings; sets `status: complete` when resolved |
| create-domain-model | Any phase context (typically design/specification) | Domain model document (`status: draft`) |
| review-domain-model | Domain model document | Findings → `review-domain-model.md` |
| create-question | Any phase context | `.sdlc/knowledge/questions/N-<slug>.md` |
| review-question | `.sdlc/knowledge/questions/N-<slug>.md` | Findings; records the answer and sets status `Resolved`/`Deferred`/`Dismissed` when appropriate |
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

GitHub content writes (PR creation, PR description updates, comments, reviews) are gated by the `should-post-to-github` script (`~/.sdlc/config.yaml`), which `create-pr`, `validate-pr`, `verify-pr`, and `review-pr` consult. Git write operations (push, merge, deploy) are not gated by that script.
