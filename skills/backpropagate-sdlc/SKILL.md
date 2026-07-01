---
name: backpropagate-sdlc
description: Walk the SDLC artifact chain in reverse (code back to issue) to verify end-to-end consistency and traceability. Use when the user says /backpropagate-sdlc, "backpropagate", "verify SDLC trace", or wants to detect drift accumulated across artifacts after the forward pipeline has run.
argument-hint: "[feature-id | all] [--fix] [--create-issues]"
---

# Backpropagate SDLC

Walks the SDLC artifact chain in reverse, from the shipped code back to the originating issue, verifying that every layer stays consistent with what was actually built.

The forward `/sdlc` pipeline propagates intent downstream: issue, requirements, specification, plan, tasks, tests, code.
This skill is its complement.
It propagates reality upstream: starting from the code and tests as ground truth, it walks back through tasks, plan, specification, requirements, and the issue, checking each adjacent pair for bidirectional consistency.

The core problem this skill solves: artifacts go stale.
Code evolves past the spec without updating it.
A requirement is dropped during implementation but never removed from `requirements.md`.
A test case (`TC-07`) survives after the behavior it covered was deleted.
A plan task references `FR-04`, which no longer exists.
Each `review-*` phase checks one artifact in isolation against its immediate input.
None of them re-walks the whole chain end to end after the fact.
This skill does exactly that, and it is the only skill that builds a full traceability matrix from code back to the original issue.

## Prerequisites

- Working directory is the root of the repository
- A populated `.sdlc/` directory (run `/sync-sdlc` first if absent)
- At least one feature under `.sdlc/features/FEAT-NNNN-<slug>/` with artifacts present
- Read access to the codebase (the code is the ground truth)
- Read any files under `.sdlc/context/` for project-level conventions and apply their style rules to the produced report

## What This Skill Catches

| Drift | Example | Reverse Pass That Detects It |
|---|---|---|
| Orphan downstream (scope creep) | Code implements a behavior that no requirement or spec describes | Code ↔ Spec |
| Orphan upstream (unrealized intent) | An `FR-02` in requirements.md has no implementation, task, or test | Every pass, upstream direction |
| Stale spec | specification.md describes an API endpoint that was renamed or removed | Spec ↔ Code |
| Dangling test | `TC-05` covers a behavior that no longer exists in code | Tests ↔ Code |
| Missing coverage | A task or spec section has no corresponding test case | Tasks ↔ Tests, Spec ↔ Tests |
| Broken task link | A task references `FR-04` which is not in requirements.md | Tasks ↔ Requirements |
| Plan divergence | plan.md lists phases that do not map to any spec section | Plan ↔ Spec |
| Requirements drift | requirements.md lists an acceptance criterion with no matching AC in tests | Requirements ↔ Tests |
| Telemetry gap | telemetry.md defines an event never emitted by the code | Telemetry ↔ Code |
| Observability gap | observability.md defines a metric or alert the code never produces | Observability ↔ Code |
| Doc drift | documentation describes a parameter the code no longer accepts | Docs ↔ Code |
| ID corruption | A cross-reference like `FEAT-0001-FR-07` points to nothing | ID Integrity |
| Status regression | specification.md is `draft` while implementation is `done` | Status Monotonicity |

## The Reverse Trace Chain

```
Ground truth (start here)
  code + tests
      │  Pass 1: Code ↔ Tests
      ▼
  tasks/ (NNNN-*.md)
      │  Pass 2: Tests ↔ Tasks
      ▼
  plan.md
      │  Pass 3: Tasks ↔ Plan
      ▼
  specification.md  ←─ telemetry.md, observability.md
      │  Pass 3b: Telemetry/Observability ↔ Spec
      │  Pass 4: Plan ↔ Specification
      ▼
  requirements.md (FR-NN, NFR-NN, ACs)
      │  Pass 5: Specification ↔ Requirements
      ▼
  needs-assessment.md
      │  Pass 6: Requirements ↔ Needs
      ▼
  issue (GitHub)
      │  Pass 7: Needs ↔ Issue
      ▼
  documentation
      │  Pass 8: Documentation ↔ Code/Spec
      ▼
  Cross-cutting: ID integrity, status monotonicity, orphan classification
      │
      ▼
  Traceability matrix + findings report
```

## Scope

The `$1` argument selects which features to backpropagate. Defaults to `all`.

| Argument | Features Checked |
|---|---|
| `all` (default) | Every directory under `.sdlc/features/` that has at least one artifact |
| `FEAT-NNNN` | A single feature (matches by prefix, slug suffix optional) |

Flags:

- `--fix`: For each confirmed drift, append a dated entry to the feature's `questions.md` as a "Backpropagation drift" item, and regress the stale artifact's frontmatter `status` from `approved` back to `draft` so the forward pipeline knows it needs re-review. Never rewrites requirement or spec content: drift is ambiguous (the code may be wrong, or the artifact may be stale), so the skill flags it for a human decision rather than guessing which side to update.
- `--create-issues`: After reporting, create GitHub issues for high-severity drift (orphan upstream requirements, broken traceability for shipped behavior).

## Steps

### 1. Parse arguments

Determine the target feature set from `$1` (default `all`) and read the flags.

```
/backpropagate-sdlc                    # all features, report only
/backpropagate-sdlc FEAT-0003          # one feature, report only
/backpropagate-sdlc all --fix          # all features, append drift + regress status
/backpropagate-sdlc FEAT-0002 --create-issues
```

### 2. Gather the artifact chain

For each target feature directory, read every artifact that exists and skip the ones that do not.

```
.sdlc/features/FEAT-NNNN-<slug>/
├── needs-assessment.md
├── requirements.md        # FR-NN, NFR-NN, acceptance criteria
├── existing-solutions.md
├── codebase-analysis.md
├── feasibility.md
├── specification.md
├── telemetry.md
├── observability.md
├── plan.md
├── tasks/NNNN-<slug>.md   # one file per task
├── tests.md               # TC-NN
└── questions.md
```

Also resolve the originating GitHub issue number from frontmatter, and read the linked PR if one exists (use `ghx pr view` if available, otherwise `gh pr view`).

If a feature directory has no requirements.md and no specification.md, report it as "insufficient artifacts" and skip the reverse walk for that feature.

### 3. Establish ground truth

The code is the source of truth, not the artifacts.
Before walking back, identify what the feature actually implements today.

- Locate the code paths that belong to this feature (use spec section locations, task file checklists, and the feature slug as hints; fall back to grepping for the FEAT-NNNN id in the code).
- Enumerate the observable behaviors, public APIs, CLI commands, config keys, emitted events, and metrics the code currently produces.
- Enumerate the test cases that actually exist and what behavior each verifies.
- Record this as the **realized set** for the feature.

Every later pass compares an artifact layer against this realized set, not against the layer below it in the forward direction.

### 4. Run the reverse passes

Run each pass bidirectionally.
For adjacent layers `(downstream, upstream)`, a **forward link** (downstream item traces to an upstream origin) and a **reverse link** (upstream item has downstream realization) must both exist.
Record a finding for every missing link.

The passes, in execution order:

#### Pass 1: Code ↔ Tests

- Every realized behavior in code has at least one test covering it (reverse link). Missing coverage is a finding.
- Every test in `tests.md` (`TC-NN`) and in the test files traces to behavior the code still exhibits (forward link). A test for removed behavior is a **dangling test** finding.

#### Pass 2: Tests ↔ Tasks

- Every test case maps to at least one task in `tasks/` (forward link). Orphan tests are findings.
- Every task has at least one test covering its acceptance checklist (reverse link). Untested tasks are findings.

#### Pass 3: Tasks ↔ Plan

- Every task references its parent plan phase (forward link). Tasks without a plan home are findings.
- Every phase in `plan.md` has tasks realizing it (reverse link). Empty plan phases are findings.

#### Pass 3b: Telemetry / Observability ↔ Specification

- Every event in `telemetry.md` maps to a spec behavior (forward link) and is emitted by code (ground-truth check). Unemitted events are findings.
- Every metric, log, trace, and alert in `observability.md` maps to a spec behavior and is produced by code.

#### Pass 4: Plan ↔ Specification

- Every plan phase and architectural decision traces to a specification section (forward link).
- Every specification section is covered by the plan (reverse link).

#### Pass 5: Specification ↔ Requirements

- Every spec element (data model field, API contract, sequence step) satisfies an `FR-NN` or `NFR-NN` (forward link). Spec with no requirement home is **scope creep**.
- Every `FR-NN` and `NFR-NN` is realized in the spec (reverse link). Unrealized requirements are findings.

#### Pass 6: Requirements ↔ Needs-assessment

- Every `FR-NN` maps to a need documented in `needs-assessment.md` (forward link).
- Every documented need has at least one requirement addressing it (reverse link).

#### Pass 7: Needs-assessment ↔ Issue

- Every need traces to a part of the issue body (forward link).
- Every acceptance criterion or scope item in the issue has a corresponding need (reverse link).
- If the issue has been edited since the feature was created (compare dates), flag it for re-check.

#### Pass 8: Documentation ↔ Code / Spec

- Every public API, CLI command, and config key documented matches the code's current signature (forward link from docs to code).
- Every public API in code has matching documentation (reverse link).
- Documentation that describes removed parameters, renamed fields, or deleted commands is **doc drift**.

### 5. Cross-cutting checks

Run these across the whole chain after the passes complete.

#### ID integrity

Collect every cross-reference in every artifact (`FR-NN`, `NFR-NN`, `TC-NN`, task `NNNN`, `FEAT-NNNN`, qualified `FEAT-NNNN-FR-NN`).
Verify each one resolves to an artifact that exists.
Broken references are findings.
Duplicate IDs within a feature (two `FR-03`, for example) are findings.

#### Status monotonicity

Read the `status` frontmatter from every artifact.
Status should flow consistently downstream: an upstream artifact should not still be `draft` when a downstream artifact is `approved` or `done`.
Flag inversions, for example `specification.md: draft` with `tasks/*.md: done`.

The legal status order, most-upstream to most-downstream, mirrors the pipeline.
A downstream `done` or `approved` implies every upstream artifact is at least `approved`.
A downstream `in-review` implies every upstream artifact is at least `approved` or also `in-review`.

#### Orphan classification

Every drift item falls into exactly one of three classes, which determines severity and the recommended fix.

| Class | Meaning | Severity | Default fix |
|---|---|---|---|
| Orphan upstream | An artifact describes something with no downstream realization (a requirement with no code) | High | Human decides: implement it, or remove the artifact |
| Orphan downstream | A downstream item traces to no upstream artifact (code with no requirement) | Medium | Human decides: add the requirement, or remove the code |
| Broken reference | A cross-reference ID points to nothing | Low | Repair the ID, or remove the reference |

### 6. Aggregate and report

Merge all findings into a single report.
Deduplicate when the same drift surfaces in multiple passes (a requirement with no code will appear in Pass 1, Pass 2, and Pass 5; collapse into one finding citing all passes).

Write the report to `.sdlc/backpropagation-report.md`.
Present the summary to the user.

### 7. Apply fixes (only if `--fix`)

For each confirmed drift:

1. Append a dated, one-line entry to the feature's `questions.md` under a `## Backpropagation drift` heading, naming the pass, the IDs involved, and the class.
2. If the artifact's frontmatter `status` is `approved` and the artifact is the stale side of the drift, regress it to `draft` so `/sdlc continue` will re-enter the forward pipeline at that phase.
3. Never rewrite artifact prose. Never delete a requirement, spec section, or test. These are human decisions.

If `--create-issues` is set, after fixes, ask the user which orphan-upstream findings should become GitHub issues, then create them with a short body linking the feature directory and the drift class.

## Output Format

```markdown
---
date: "<YYYY-MM-DD>"
scope: "<feature ids checked>"
flags: "<fix: true/false, create-issues: true/false>"
status: complete
---

# Backpropagation Report

**Date:** <YYYY-MM-DD>
**Scope:** <features>

## Consistency Status

| Feature | Code↔Tests | Tasks↔Plan | Spec↔Req | Req↔Issue | Telemetry | Observability | Docs | IDs | Status |
|---|---|---|---|---|---|---|---|---|---|
| FEAT-0001-<slug> | in sync / drift | ... | ... | ... | ... | ... | ... | clean / broken | monotonic / inverted |

## Traceability Matrix (per feature)

### FEAT-0001-<slug>

| FR / NFR | Spec section | Plan phase | Task(s) | Test(s) | Code location | Docs | Issue AC |
|---|---|---|---|---|---|---|---|
| FR-01 | 3.1 Users | Phase 1 | 0003 | TC-01, TC-02 | src/users.py:42 | docs/users.md | AC-1 |
| FR-02 | (none) | (none) | (none) | (none) | (none) | (none) | AC-2 | ← orphan upstream
| (none) | 3.4 Exports | Phase 2 | 0007 | TC-09 | src/export.py:8 | (none) | (none) | ← orphan downstream

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
**Feature:** FEAT-0001-<slug>
**Class:** Orphan upstream / Orphan downstream / Broken reference / Status inversion
**Severity:** Critical / High / Medium / Low
**Pass(es):** Pass 5 (Spec ↔ Requirements), Pass 1 (Code ↔ Tests)
**Location:** `<file>:<line>` or `<artifact> §<section>`
**Finding:** <what was found>
**Impact:** <what breaks if unaddressed>
**Recommendation:** <implement, remove, or repair, and which side is likely wrong>

## Fixes Applied

<Only present if --fix was specified>
| Finding | Fix applied | Files changed |
|---|---|---|
| <description> | <appended drift note, regressed status> | questions.md, <artifact> |

## Recommended Actions

| Priority | Action | Owner decision |
|---|---|---|
| High | <description> | implement / remove |
| Medium | <description> | implement / remove |
| Low | <description> | repair ID |
```

## When to Run This

- After `/merge-pr` or `/deploy-pr`, before starting the next feature, to confirm the just-shipped code did not silently invalidate an upstream artifact.
- Periodically (weekly or sprint-end) alongside `/sync-repository`, to catch drift that accumulated across multiple features.
- Before a release, as a release gate, to guarantee every shipped behavior traces back to a requirement and an issue.
- When inheriting an existing `.sdlc/` from another developer or another team, to establish a trust baseline before extending the pipeline.

`/sync-repository` checks code against its surrounding layers (tests, docs, types).
This skill checks the SDLC artifact chain against itself, end to end.
They are complementary: run both for full coverage.

## Example Usage

**Scenario 1: Pre-release release gate**
```
/backpropagate-sdlc all
```
Walks every feature. Finds that FEAT-0002 has a `TC-04` for a behavior removed last sprint (dangling test), and FEAT-0004 has an `FR-03` never implemented (orphan upstream). Reports both. No changes made.

**Scenario 2: After a feature ships**
```
/backpropagate-sdlc FEAT-0007 --fix
```
Finds specification.md drifted: it describes a `POST /invites` endpoint that the code renamed to `POST /invitations`. Appends a drift note to `questions.md`, regresses `specification.md` from `approved` to `draft`. The next `/sdlc continue` re-enters at the specifications phase.

**Scenario 3: Inheriting a project**
```
/backpropagate-sdlc all --create-issues
```
Establishes a trust baseline on a `.sdlc/` inherited from another team. Surfaces 14 broken ID references, 3 orphan upstream requirements, and 2 status inversions. Creates issues for the orphan upstream findings.

**Scenario 4: Single layer quick check**
```
/backpropagate-sdlc FEAT-0001
```
Focused on one feature. The traceability matrix shows every FR maps cleanly through spec, task, test, code, and docs. Reports clean.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `sdlc` | The forward pipeline this skill complements. `/sdlc` propagates intent downstream; `/backpropagate-sdlc` verifies reality upstream. |
| `sync-sdlc` | Compares the codebase against `requirements.md` and `specification.md` for a feature (two layers). This skill walks the full chain across all artifacts and all layers, end to end. |
| `sync-repository` | Cross-layer consistency for code surroundings (tests, docs, types, observability). This skill is artifact-chain consistency for the SDLC trace. Run both for full coverage: `sync-repository` for code health, `backpropagate-sdlc` for intent traceability. |
| `verify-pr` | Claim-to-code traceability for a single PR. This skill is full-chain traceability for a whole feature (or all features), independent of any one PR. |
| `review-*` (requirements, specifications, plan, implementation, tests) | Each reviews one artifact against its immediate input. This skill re-walks every adjacent pair after the fact, which is the only way to catch drift introduced by later phases editing earlier artifacts out of band. |
| `sdlc-status` | Read-only progress dashboard. Does not check consistency. This skill assumes progress and checks coherence. |

## Useful Commands Reference

No direct CLI commands are required.
The skill optionally invokes `ghx pr view` (or `gh pr view`) to read the linked PR, and `gh issue create` when `--create-issues` is set.
