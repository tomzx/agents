---
name: propagate-changes
description: Run a bidirectional propagation pass over the SDLC artifact chain after a change, updating the artifacts that depend on the change (downward) and re-checking the premises the change depends on (upward). Use when the user says /propagate-changes, "propagate changes", "propagate this change", "bring the artifacts back in sync", or wants consistency restored in both directions across issue, requirements, specification, plan, tasks, tests, code, and documentation after a change.
argument-hint: "[feature-id | all] [--entry <artifact>] [--fix] [--create-issues]"
---

# Propagate Changes

A change landing in one artifact invalidates two things at once: the artifacts built from it, and the artifacts it was built from.
The forward `/sdlc` pipeline propagates intent downstream, and each `review-*` skill checks one adjacent pair in isolation.
This skill runs one propagation pass in both directions along the artifact graph.
Downward, it updates dependents: every artifact that still describes the old version is rewritten when the resolution follows from the change.
Upward, it questions premises: every artifact the change depends on is re-checked, and drift is flagged for a human decision instead of guessed away.
Wherever two connected artifacts disagree in a way that admits more than one resolution, the pass raises a question rather than picking a side.

## Prerequisites

- Working directory is the root of the repository
- A populated `.sdlc/` directory (run `/sync-sdlc` first if absent)
- At least one feature under `.sdlc/features/N-<slug>/` with artifacts present
- Read access to the codebase
- Read any files present under `.sdlc/context/` for project-level context, and apply their style rules to rewritten artifacts and the report

## The Propagation Map

The artifacts of a feature form a directed graph: an artifact is built from the artifacts its edges come from.
The canonical map for SDLC features is:

```
issue
  └─> needs-assessment
        └─> requirements
              └─> specification
                    ├─> lifecycle.md / telemetry.md / observability.md
                    ├─> plan
                    │     └─> tasks
                    └─> tests
tasks -> code (implementation)
code -> documentation
code + tests -> PR title and description
```

Every edge is bidirectional for propagation purposes: downward updates the dependent, upward questions the premise.
If an artifact declares extra dependencies in a `depends_on` list in its frontmatter, treat those as additional edges.

## Direction Semantics

| Direction | What staleness means | Authority | Action |
|---|---|---|---|
| Downward (dependents) | A dependent still describes the old version of the change | The changed artifact is authoritative | Rewrite the dependent when a single resolution follows from the change. Raise a question when more than one resolution exists. |
| Upward (premises) | A premise may be stale, or the change itself may be wrong | Ambiguous by definition | Never rewrite. Classify the drift, and with `--fix` regress the stale artifact's review verdict so the forward pipeline resyncs it. Raise a question for the human. |

Both directions are required because each catches a different kind of staleness.
Downward-only propagation produces a consistent account of a decision that may be wrong.
Upward-only propagation questions everything and updates nothing.

## Scope

The `$1` argument selects which features to propagate. Defaults to `all`.

| Argument | Features Checked |
|---|---|
| `all` (default) | Every directory under `.sdlc/features/` that has at least one artifact |
| `FEAT-N` or `N` | A single feature (by feature ID or directory number; slug suffix optional) |

Flags:

- `--entry <artifact>`: the node the change entered at (`code` by default, detected from the diff when possible). The downward walk starts at the entry; the upward walk starts at its dependencies.
- `--fix`: apply the safe actions: downward rewrites that follow mechanically from the change, and upward review regressions. Without this flag the pass is read-only (proposed updates and findings only).
- `--create-issues`: after reporting, create GitHub issues for high-severity orphan-upstream findings.

## Steps

### 1. Parse arguments

Determine the target feature set, the entry artifact, and the flags.

```
/propagate-changes                                  # all features, report only
/propagate-changes FEAT-3                           # one feature, report only
/propagate-changes FEAT-7 --entry code --fix        # propagate the code change, applying updates
/propagate-changes FEAT-2 --entry requirements --fix
/propagate-changes all --fix --create-issues
```

### 2. Gather the artifact chain

For each target feature directory, read every artifact that exists and skip the ones that do not.

```
.sdlc/features/N-<slug>/
├── needs-assessment.md
├── requirements.md        # FR-N, NFR-N, acceptance criteria
├── existing-solutions.md
├── codebase-analysis.md
├── feasibility.md
├── specification.md
├── lifecycle.md
├── telemetry.md
├── observability.md
├── plan.md
├── assumption-validation.md
├── tasks/N-<slug>.md      # one file per task
└── tests.md               # TC-N
```

Also resolve the originating GitHub issue number from frontmatter, and read the linked PR if one exists (use `ghx pr view` if available, otherwise `gh pr view`).

If a feature directory has no requirements.md and no specification.md, report it as "insufficient artifacts" and skip it.

### 3. Establish the change set

The entry artifact is the change, and what it now says is authoritative for the downward walk.

- Default entry is `code`: use `git status` and `git diff` to identify what currently changed, or, when invoked after a merge, the diff of the merge.
- With `--entry`, use the named artifact as the entry and diff it against its last approved review (`review-<artifact>.md` and its `reviewed_at`, plus any `revision` counter).
- Enumerate the entry's current observable content: behaviors, public APIs, CLI commands, config keys, emitted events, metrics, requirements, or spec sections, whichever apply.
- For `all` with no detectable change, fall back to a full-consistency pass: every adjacent pair in the map is checked in both directions, with the code and tests as global ground truth.

Record this as the change set every later comparison uses.

### 4. Run the downward walk (update dependents)

Follow the map outward from the entry, one edge at a time.
For each dependent, compare it against the change set:

| Result | Action |
|---|---|
| In sync | Record the edge clean. Stop descending through it: its own dependents were built from a version that already matches. |
| Drifted, one resolution | With `--fix`, apply the minimal rewrite that makes the dependent describe the change. Without `--fix`, record the proposed rewrite. Then descend through the dependent. |
| Drifted, more than one resolution | Raise a question (step 6). Stop descending through the edge: the resolution may change the subtree below it. |

Typical downward updates by artifact:

| Dependent | Typical update |
|---|---|
| `tests.md` and test files | Update expectations, add or remove `TC-N` entries, so tests assert the change |
| documentation | Describe the new behavior, parameter, command, or name |
| PR title and description | Rewrite so both describe the current diff: what changed, why, and which suggestions were rejected and why |
| `tasks/` | Update checklist items that no longer match the change |
| `lifecycle.md`, `telemetry.md`, `observability.md` | Update the state, event, metric, and alert definitions the change moved |
| `plan.md` | Re-home or reword phases that described the superseded approach |
| `specification.md`, `requirements.md` | Updated only when the change entered above them (for example `--entry requirements`) |

A rewritten artifact gets `status: in-review` in its frontmatter and a bumped `revision` counter, so the matching `review-*` skill re-reviews it.
Never rewrite an artifact that sits upstream of the entry.

### 5. Run the upward walk (question premises)

Walk inward from the entry along the map.
For each adjacent pair, check both links: the forward link (a downstream item traces to an upstream origin) and the reverse link (an upstream item has a downstream realization).
Record a finding for every missing link.

Stop ascending at the first pair that is fully consistent: review-approval monotonicity (step 7) guarantees the artifacts above an approved pair were approved against a consistent version.
In a full-consistency pass (`all` with no change set), do not stop: check every pair.

The pair checks, in execution order:

#### Edge: Code ↔ Tests

- Every realized behavior in code has at least one test covering it (reverse link). Missing coverage is a finding.
- Every test in `tests.md` (`TC-N`) and in the test files traces to behavior the code still exhibits (forward link). A test for removed behavior is a dangling test finding.

#### Edge: Tests ↔ Tasks

- Every test case maps to at least one task in `tasks/` (forward link). Orphan tests are findings.
- Every task has at least one test covering its acceptance checklist (reverse link). Untested tasks are findings.

#### Edge: Tasks ↔ Plan

- Every task references its parent plan phase (forward link). Tasks without a plan home are findings.
- Every phase in `plan.md` has tasks realizing it (reverse link). Empty plan phases are findings.

#### Edge: Telemetry / Observability ↔ Specification

- Every event in `telemetry.md` maps to a spec behavior (forward link) and is emitted by code (ground-truth check). Unemitted events are findings.
- Every metric, log, trace, and alert in `observability.md` maps to a spec behavior and is produced by code.

#### Edge: Lifecycle ↔ Specification

- Every state and transition in `lifecycle.md` maps to a spec data model field or API contract (forward link). Lifecycle states with no spec backing are findings.
- Every spec data model that implies a state machine has corresponding states and transitions documented in `lifecycle.md` (reverse link). Undocumented lifecycles are findings.
- Every transition in `lifecycle.md` traces to code that implements it (ground-truth check). Transitions with no code are orphan upstream findings.
- Every state transition the code implements that is not in `lifecycle.md` is an orphan downstream finding.

#### Edge: Plan ↔ Specification

- Every plan phase and architectural decision traces to a specification section (forward link).
- Every specification section is covered by the plan (reverse link).

#### Edge: Specification ↔ Requirements

- Every spec element (data model field, API contract, sequence step) satisfies an `FR-N` or `NFR-N` (forward link). Spec with no requirement home is scope creep.
- Every `FR-N` and `NFR-N` is realized in the spec (reverse link). Unrealized requirements are findings.

#### Edge: Requirements ↔ Needs-assessment

- Every `FR-N` maps to a need documented in `needs-assessment.md` (forward link).
- Every documented need has at least one requirement addressing it (reverse link).

#### Edge: Needs-assessment ↔ Issue

- Every need traces to a part of the issue body (forward link).
- Every acceptance criterion or scope item in the issue has a corresponding need (reverse link).
- If the issue has been edited since the feature was created (compare dates), flag it for re-check.

#### Edge: Documentation ↔ Code / Spec

- Every public API, CLI command, and config key documented matches the code's current signature (forward link from docs to code).
- Every public API in code has matching documentation (reverse link).
- Documentation describing removed parameters, renamed fields, or deleted commands is doc drift.

When the change entered below the code (for example `--entry documentation`), the same pair checks run unchanged: the downward walk has nothing below to update, and the upward walk questions the code the documentation was written from.

### 6. Raise questions

Wherever two connected artifacts disagree in a way that admits more than one resolution, the pass raises a question instead of guessing.
Both walks produce questions: a dependent that could be updated in several ways (downward), and a premise conflict where either the change or the premise may be wrong (upward).

- When the question needs a named answerer or blocks downstream work, record it via `/create-question` with its context, who can answer it, and when the answer is needed.
- Otherwise, list it in the report's Questions section.

This is the escalation path that replaces guessing: ambiguity flows to the human, mechanical resolutions flow to the artifacts.

### 7. Cross-cutting checks

Run these across the whole chain after the walks complete.

#### ID integrity

Collect every cross-reference in every artifact (`FR-N`, `NFR-N`, `TC-N`, task `N`, `FEAT-N`, qualified `FEAT-N-FR-N`).
Verify each one resolves to an artifact that exists.
Broken references are findings.
Duplicate IDs within a feature (two `FR-3`, for example) are findings.

#### Review-approval monotonicity

Read each artifact's `review-<artifact>.md` findings verdict (see `skills/sdlc/references/shared.md`); for tasks and implementation, `done`/`in-progress` count as downstream signals.
Review approval should flow consistently downstream: an upstream artifact should not lack an approved review (or carry a `changes-requested`/`rejected` verdict) when a downstream artifact has an approved review or has been implemented.
Flag inversions, for example `specification.md` with no approved review while `tasks/*.md` are `done`.

#### Orphan classification

Every drift item falls into exactly one of three classes, which determines severity and the recommended fix.

| Class | Meaning | Severity | Default fix |
|---|---|---|---|
| Orphan upstream | An artifact describes something with no downstream realization (a requirement with no code) | High | Human decides: implement it, or remove the artifact |
| Orphan downstream | A downstream item traces to no upstream artifact (code with no requirement) | Medium | Human decides: add the requirement, or remove the code |
| Broken reference | A cross-reference ID points to nothing | Low | Repair the ID, or remove the reference |

### 8. Aggregate and report

Merge all findings, updates, and questions into a single report per feature.
Deduplicate when the same drift surfaces in multiple walks (a requirement with no code will appear in several edges; collapse into one finding citing all of them).

Write one report per feature to `.sdlc/features/N-<slug>/propagation-report.md` (for an `all` run, write one file per feature).
Present the summary to the user.

### 9. Apply fixes (only with `--fix`)

Downward:

1. Apply each proposed rewrite whose resolution follows mechanically from the change.
2. Set the artifact frontmatter `status: in-review` and bump its `revision` counter.
3. Do not expand a rewrite beyond what the change justifies: preserve everything the change did not touch.

Upward:

1. For each confirmed drift, if the stale artifact's `review-<artifact>.md` has `verdict: approved`, regress it: set `verdict: changes-requested` and append a `## Propagation drift: <date>` section naming the edge, the IDs involved, the discrepancy, and the class. The forward pipeline then resyncs the artifact via revision mode and the matching `review-*` skill restores `approved` once the drift is resolved.
2. Never rewrite upstream artifact prose. Never delete a requirement, spec section, or test. These are human decisions.

If `--create-issues` is set, after fixes, ask the user which orphan-upstream findings should become GitHub issues, then create them with a short body linking the feature directory and the drift class.

## Output Format

```markdown
---
date: "<YYYY-MM-DD>"
scope: "<feature ids checked>"
entry: "<entry artifact>"
flags: "<fix: true/false, create-issues: true/false>"
status: complete
---

# Propagation Report

**Date:** <YYYY-MM-DD>
**Scope:** <features>
**Entry:** <artifact the change entered at>

## Consistency Status

| Feature | Downward updates | Upward drift | IDs | Review order | Status |
|---|---|---|---|---|---|
| FEAT-1-<slug> | 3 applied / 1 proposed | 2 findings | clean / broken | monotonic / inverted | in sync / drifted |

## Updates (downward)

| # | Artifact | Edge | Change | Resolution | Status |
|---|---|---|---|---|---|
| 1 | docs/users.md | code -> documentation | endpoint renamed | rewrite section 2 | applied / proposed |

## Questions Raised

| # | Edge | Disagreement | Resolutions | Where recorded |
|---|---|---|---|---|
| 1 | spec ↔ requirements | FR-4 conflicts with the new API | two viable readings | /create-question Q-3 / report only |

## Traceability Matrix (per feature)

### FEAT-1-<slug>

| FR / NFR | Spec section | Plan phase | Task(s) | Test(s) | Code location | Docs | Issue AC |
|---|---|---|---|---|---|---|---|
| FR-1 | 3.1 Users | Phase 1 | 3 | TC-1, TC-2 | src/users.py:42 | docs/users.md | AC-1 |
| FR-2 | (none) | (none) | (none) | (none) | (none) | (none) | AC-2 | ← orphan upstream |
| (none) | 3.4 Exports | Phase 2 | 7 | TC-9 | src/export.py:8 | (none) | (none) | ← orphan downstream |

## Summary

| Class | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|
| Orphan upstream | N | N | N | N | N |
| Orphan downstream | N | N | N | N | N |
| Broken reference | N | N | N | N | N |
| Status inversion | N | N | N | N | N |
| **Total** | **N** | **N** | **N** | **N** | **N** |

## Findings

### 1. <Title>
**Feature:** FEAT-1-<slug>
**Class:** Orphan upstream / Orphan downstream / Broken reference / Status inversion
**Severity:** Critical / High / Medium / Low
**Direction:** Downward / Upward
**Edge(s):** <edge name(s)>
**Location:** `<file>:<line>` or `<artifact> §<section>`
**Finding:** <what was found>
**Impact:** <what breaks if unaddressed>
**Recommendation:** <update, implement, remove, or repair, and which side is likely wrong>

## Fixes Applied

<Only present if --fix was specified>
| Finding / Update | Fix applied | Files changed |
|---|---|---|
| <description> | rewrite applied (status: in-review) / review regressed to changes-requested | <list> |

## Recommended Actions

| Priority | Action | Owner decision |
|---|---|---|
| High | <description> | implement / remove / answer question |
| Medium | <description> | implement / remove |
| Low | <description> | repair ID |
```

## When to Run This

- After every push that changes code or an artifact, before requesting re-review, so dependents are updated and premises re-checked while the change is fresh.
- After `/merge-pr` or `/deploy-pr`, before starting the next feature, to confirm the just-shipped change did not silently invalidate an upstream artifact.
- Periodically (weekly or sprint-end) alongside `/sync-repository`, as a full pass, to catch drift that accumulated across multiple features.
- Before a release, as a release gate, to guarantee every shipped behavior traces back to a requirement and an issue.
- When inheriting an existing `.sdlc/` from another developer or another team, to establish a trust baseline before extending the pipeline.

## Example Usage

**Scenario 1: A code change mid-review**
```
/propagate-changes FEAT-7 --entry code --fix
```
Downward: rewrites the docs section describing the renamed endpoint, updates the two stale test expectations, and refreshes the PR title and description. Upward: finds `specification.md` still describes the old endpoint name, which is ambiguous (rename the spec, or revert the code), so it regresses `review-specification.md` to `changes-requested` and the next `/sdlc continue` resyncs the spec.

**Scenario 2: A requirements change**
```
/propagate-changes FEAT-3 --entry requirements --fix
```
Downward: the new `FR-6` flows into the spec, the plan gains a phase, tasks gain a task, and tests gain a `TC-9`. Upward: the issue body never mentioned this need, so the walk flags the gap as a question for the issue author.

**Scenario 3: Full pass as a release gate**
```
/propagate-changes all
```
Walks every feature with no entry bias: every pair is checked in both directions. FEAT-2 has a `TC-4` for removed behavior (dangling test), and FEAT-4 has an `FR-3` never implemented (orphan upstream). Reports both, no changes made.

**Scenario 4: Inheriting a project**
```
/propagate-changes all --create-issues
```
Establishes a trust baseline on an inherited `.sdlc/`. Surfaces 14 broken ID references, 3 orphan upstream requirements, and 2 review-approval inversions. Creates issues for the orphan upstream findings.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `sdlc` | The forward pipeline this skill guards. `/sdlc` propagates intent downstream; `/propagate-changes` restores consistency in both directions after a change. |
| `sync-sdlc` | Compares the codebase against requirements and specification for a feature (two layers). This skill walks every adjacent pair and updates dependents instead of only flagging them. |
| `sync-repository` | Cross-layer consistency for code surroundings (tests, docs, types, observability). Run both for full coverage: `sync-repository` for code health, `propagate-changes` for artifact-graph consistency. |
| `trace-issues` | The GitHub-native counterpart: traceability from issues to code on any repository, without an `.sdlc/` directory. |
| `review-*` (requirements, specifications, plan, implementation, tests) | Each reviews one artifact against its immediate input. This skill re-walks every pair after the fact, which is the only way to catch drift introduced by later phases editing earlier artifacts out of band. |
| `create-question` | Where every ambiguous disagreement a walk raises goes when it needs a named answerer or blocks work. |
| `verify-pr` | Claim-to-code traceability for a single PR. This skill is full-graph propagation for a whole feature (or all features), independent of any one PR. |
| `sdlc-status` | Read-only progress dashboard. Does not check consistency. This skill assumes progress and restores coherence. |

## Useful Commands Reference

No direct CLI commands are required.
The skill optionally invokes `ghx pr view` (or `gh pr view`) to read the linked PR, and `gh issue create` when `--create-issues` is set.
