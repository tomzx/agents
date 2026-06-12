---
name: sync-repository
description: Ensure the entire repository is consistent by running skills in the right order to sync SDLC, code, tests, documentation, types, and observability. Use when the user says /sync-repository, "sync repo", "keep repo consistent", "run all checks", or wants to detect and fix drift between code, SDLC, and documentation.
argument-hint: "[scope: all | foundation | diagnose | harden | clean | document | observe | comma-separated phase names] [--fix] [--create-issues]"
---

# Sync Repository

Ensures the entire repository is consistent by running skills in dependency order.
Detects and optionally fixes drift between code, SDLC artifacts, tests, documentation, types, and observability.

The core problem this skill solves: changes to one layer (code, SDLC, docs, tests) often go unpropagated to dependent layers.
Code changes without updating SDLC. SDLC changes without updating documentation. New code without tests or types.
This skill runs every check in the right order so nothing falls through the cracks.

## Prerequisites

- Working directory is the root of the repository
- Read access to the project root and its subdirectories
- Write access to `.sdlc/` (for foundation phase)
- `git` repository with commit history
- Read any files present under `.sdlc/context/` for project-level context

## Drift Scenarios This Skill Prevents

| Drift | Root Cause | Phase That Detects It |
|---|---|---|
| `.sdlc/context/` stale after code changes | Code changed without re-running sync-sdlc | Foundation |
| New features not tracked in `.sdlc/features/` | Code added without SDLC tracking | Foundation |
| SDLC features orphaned after code removal | Code removed without updating SDLC | Foundation |
| Requirements drift from implementation | Code evolved beyond original requirements | Foundation |
| Specs drift from implementation | Implementation diverged from spec | Foundation |
| Dependencies vulnerable or outdated | New CVEs published after last audit | Diagnose |
| Security issues introduced | Hardcoded secrets, injection patterns | Diagnose |
| Files changing too frequently | Instability signal from churn | Diagnose |
| Code too complex to change safely | High cyclomatic complexity, deep nesting | Harden |
| Missing type annotations on new code | Functions added without types | Harden |
| Missing test coverage on new code | Code added without tests | Harden |
| Dead code accumulated | Features removed, refactoring left orphans | Clean |
| Copy-paste duplication across modules | Copy-paste across modules | Clean |
| Public APIs undocumented | New exports with no docstrings | Document |
| Missing logging, metrics, tracing | New code paths without observability | Observe |
| No docs site infrastructure | Project has no MkDocs/GitHub Pages setup | Document (auto-detect) |

## Pipeline Overview

```
Phase 0: Foundation ─── /sync-sdlc
    |                         Creates/updates .sdlc/ context files
    |                         Creates new features for untracked code
    |                         Detects drift in existing features
    |                         Flags orphaned features
    |
    v
Phase 1: Diagnose ────── /audit-dependencies
    |                     /audit-security
    |                     /analyze-git-churn
    |
    v
Phase 2: Harden ──────── /find-complexity-hotspots
    |                     /find-type-gaps
    |                     /find-coverage-gaps
    |
    v
Phase 3: Clean ───────── /find-dead-code
    |                     /find-code-duplication
    |
    v
Phase 4: Document ────── /setup-docs-site (if no mkdocs.yml exists)
    |                     /find-documentation-gaps
    |
    v
Phase 5: Observe ─────── /audit-observability
    |
    v
Phase 6: Report ──────── Aggregate findings, optionally create issues
```

**Why this order:**

1. **Foundation before everything.** `.sdlc/context/` provides architectural and convention context that other skills read. Without it, audits operate on stale understanding.
2. **Diagnose before harden.** Churn data from Phase 1 feeds risk scoring in Phase 2 (coverage gaps ranked by churn x complexity).
3. **Harden before clean.** You need to know which files are complex and untested before removing code from them.
4. **Clean before document.** No point documenting code that will be removed as dead or consolidated as duplicated.
5. **Document before observe.** Observability is assessed against the cleaned public surface.
6. **All checks before any fixes.** The report aggregates everything before action.

## Scopes

The `$1` argument controls which phases run. Defaults to `all` if not specified.

| Scope | Phases Run |
|---|---|
| `all` | Every phase (Foundation through Observe) |
| `foundation` | Phase 0 only (`/sync-sdlc`) |
| `diagnose` | Phase 1 only |
| `harden` | Phase 2 only |
| `clean` | Phase 3 only |
| `document` | Phase 4 only (`/setup-docs-site` if needed + `/find-documentation-gaps`) |
| `observe` | Phase 5 only |
| `quality` | Phases 2 + 3 (harden + clean) |
| `security` | Phase 1 only (alias for diagnose) |
| `health` | Phases 0 + 1 + 2 (foundation + diagnose + harden) |
| Comma-separated | Specific phases, e.g. `foundation,clean,document` |

Flags:
- `--fix` — After reporting, apply fixes where a skill has a fix action (update SDLC, remove dead code, add types). Without this flag, the skill is read-only (except Phase 0 which always writes to `.sdlc/`).
- `--create-issues` — Create GitHub issues for critical and high findings after the report.

## Steps

### 1. Parse arguments

Parse `$1` to determine scope and flags.

```
# Examples:
/sync-repository                     # all phases, report only
/sync-repository health              # foundation + diagnose + harden
/sync-repository clean,document      # clean + document phases
/sync-repository all --fix           # all phases, apply fixes
/sync-repository diagnose --create-issues  # diagnose, create issues for findings
```

### 2. Phase 0 — Foundation

Run `/sync-sdlc`.

This is always run as a write operation (not gated by `--fix`) because `.sdlc/` must be current before other phases can read it.

Capture the sync report for the final aggregated report.

### 3. Phase 1 — Diagnose

Run these skills, collecting findings from each:

| Skill | What it finds |
|---|---|
| `/audit-dependencies` | CVEs, outdated packages, unmaintained deps, license issues |
| `/audit-security` | Hardcoded secrets, injection risks, missing auth |
| `/analyze-git-churn` | High-churn files indicating instability |

Skip `/audit-dependencies` if no package manifest exists.
Skip `/analyze-git-churn` if fewer than 10 commits.

### 4. Phase 2 — Harden

Run these skills, collecting findings from each:

| Skill | What it finds |
|---|---|
| `/find-complexity-hotspots` | High cyclomatic complexity, excessive length, deep nesting |
| `/find-type-gaps` | Missing type annotations |
| `/find-coverage-gaps` | Missing or insufficient test coverage |

Skip `/find-type-gaps` if the project is not Python, TypeScript, or JavaScript.
Skip `/find-coverage-gaps` if no test files are found.

### 5. Phase 3 — Clean

Run these skills, collecting findings from each:

| Skill | What it finds |
|---|---|
| `/find-dead-code` | Unused functions, classes, variables, exports, feature flags |
| `/find-code-duplication` | Copy-pasted blocks and near-duplicate logic |

Skip `/find-code-duplication` if fewer than 10 source files.

### 6. Phase 4 — Document

First, check if a documentation site infrastructure exists:

```bash
ls mkdocs.yml 2>/dev/null
```

If `mkdocs.yml` does not exist, run `/setup-docs-site` to scaffold MkDocs with Material theme and the GHA Pages workflow. This is a one-time bootstrap that creates the docs infrastructure so `find-documentation-gaps` has a target to check against.

Then run `/find-documentation-gaps`, collecting findings:

| Skill | What it finds |
|---|---|
| `/find-documentation-gaps` | Undocumented public APIs, CLI, config |

### 7. Phase 5 — Observe

Run this skill, collecting findings:

| Skill | What it finds |
|---|---|
| `/audit-observability` | Missing logging, metrics, tracing, alerting |

### 8. Phase 6 — Aggregate and Report

Merge all findings from all phases into a unified report.

Deduplicate: when multiple skills flag the same file, merge into a single finding citing all sources.

Classify each finding by severity:

| Severity | Criteria |
|---|---|
| Critical | Active security vulnerability, data loss risk, production outage |
| High | Significant risk if unaddressed, degrading quality, no coverage on critical paths |
| Medium | Moderate risk, technical debt accumulating, missing instrumentation |
| Low | Minor improvement, cleanup, code style |

Write the report to `.sdlc/sync-report.md`.

Present the summary to the user.

If `--create-issues` was specified, ask to create issues for critical and high findings.
Batch medium and low findings into summary issues per category.

If `--fix` was specified, apply fix actions for findings that have automated fixes:

| Finding Type | Fix Action |
|---|---|
| SDLC drift | Already fixed by Phase 0 |
| Dead code | Remove flagged unused exports, functions, variables |
| Missing types | Add type annotations to flagged functions |
| Documentation gaps | Add docstrings to flagged public APIs |

Do NOT auto-fix security vulnerabilities, dependency issues, or complexity hotspots. These require manual review.

### 9. Consistency Check

After all phases complete, perform a cross-layer consistency check:

1. **SDLC vs Code**: For each feature in `.sdlc/features/`, check if `requirements.md` describes behavior the code no longer implements, or if the code implements behavior not captured in requirements. Report drift.
2. **Code vs Tests**: For each module with changed code, check if corresponding test files exist. Report gaps.
3. **Code vs Documentation**: For each public API in the code, check if documentation exists. Report gaps.
4. **SDLC vs Documentation**: For each feature with `specification.md`, check if documentation files reference or explain the feature. Report gaps.

This cross-layer check is the key value of this skill over running individual skills separately.

## Output Format

```markdown
---
date: "<YYYY-MM-DD>"
scope: "<scope that was run>"
flags: "<fix: true/false, create-issues: true/false>"
status: complete
---

# Sync Report — <Project Name>

**Date:** <YYYY-MM-DD>
**Scope:** <phases run>

## Consistency Status

| Layer | Status | Drift Items |
|---|---|---|
| SDLC Foundation | up to date / drift detected | N |
| Dependencies | clean / issues found | N |
| Security | clean / issues found | N |
| Code Complexity | clean / hotspots found | N |
| Type Coverage | complete / gaps found | N |
| Test Coverage | adequate / gaps found | N |
| Dead Code | clean / items found | N |
| Duplication | clean / instances found | N |
| Documentation | complete / gaps found | N |
| Observability | complete / gaps found | N |

## Summary

| Category | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|
| SDLC Drift | N | N | N | N | N |
| Security | N | N | N | N | N |
| Dependencies | N | N | N | N | N |
| Code Quality | N | N | N | N | N |
| Test Coverage | N | N | N | N | N |
| Type Gaps | N | N | N | N | N |
| Dead Code | N | N | N | N | N |
| Duplication | N | N | N | N | N |
| Documentation | N | N | N | N | N |
| Observability | N | N | N | N | N |
| **Total** | **N** | **N** | **N** | **N** | **N** |

## Cross-Layer Consistency

| From | To | Status | Items |
|---|---|---|---|
| SDLC | Code | in sync / drift | <details> |
| Code | Tests | in sync / gaps | <details> |
| Code | Documentation | in sync / gaps | <details> |
| SDLC | Documentation | in sync / gaps | <details> |
| Docs site | Docs content | exists / missing infrastructure | <details> |

## Phase Details

### Phase 0: Foundation
<sync-sdlc report summary>

### Phase 1: Diagnose
<audit-dependencies summary>
<audit-security summary>
<analyze-git-churn summary>

### Phase 2: Harden
<find-complexity-hotspots summary>
<find-type-gaps summary>
<find-coverage-gaps summary>

### Phase 3: Clean
<find-dead-code summary>
<find-code-duplication summary>

### Phase 4: Document
<find-documentation-gaps summary>

### Phase 5: Observe
<audit-observability summary>

## Critical Findings

### 1. <Title>
**Source:** <phase / skill name>
**Location:** `<file>:<line>` or <service>
**Finding:** <what was found>
**Risk:** <impact if unaddressed>
**Recommendation:** <what to do>

## High Findings

<same format>

## Medium Findings

<same format>

## Low Findings

<same format>

## Fixes Applied

<Only present if --fix was specified>
| Finding | Fix Applied | Files Changed |
|---|---|---|
| <description> | <what was done> | <list of files> |

## Recommended Actions

| Priority | Action | Issue |
|---|---|---|
| Critical | <action description> | <issue link or "Not yet created"> |
| High | <action description> | <issue link or "Not yet created"> |
| Medium | <batch cleanup description> | <issue link or "Not yet created"> |
| Low | <batch cleanup description> | <issue link or "Not yet created"> |
```

## Example Usage

**Scenario 1: Weekly full sync**
```
/sync-repository
```
Runs all phases. Finds that `.sdlc/context/architecture.md` is stale after a recent refactor, 2 new features are untracked in SDLC, 3 functions lack type annotations, and 1 public API is undocumented. Reports all findings. No changes made (report-only mode).

**Scenario 2: After a feature implementation session**
```
/sync-repository all --fix
```
Runs all phases and applies safe fixes. Phase 0 updates SDLC to track the new feature. Phase 3 removes 2 dead exports from the old implementation. Phase 4 adds docstrings to 3 new public functions. Reports remaining findings that need manual review.

**Scenario 3: Quick check after dependency update**
```
/sync-repository diagnose
```
Runs only the diagnose phase. Confirms the updated dependency has no new CVEs. Reports 1 medium-severity churn hotspot in the dependency config file.

**Scenario 4: Pre-release consistency check**
```
/sync-repository all --create-issues
```
Runs all phases, produces the full report, and creates GitHub issues for 2 critical findings (missing auth check, CVE in transitive dependency) and 3 high findings (no test coverage on new endpoints, undocumented breaking API change, missing alerting for new service).

**Scenario 5: Targeted documentation sync**
```
/sync-repository foundation,document
```
Runs SDLC sync first, then checks documentation gaps. Finds that 2 new features added in the last sprint have no documentation. Reports the gaps without creating issues.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `sync-sdlc` | Phase 0 of this skill. Can be run standalone for SDLC-only sync. |
| `audit-sdlc` | Runs the audit skills (diagnose + harden + clean + observe) without the foundation sync or cross-layer consistency check. This skill is a superset. |
| `onboard-repository` | One-time bootstrap that includes SDLC setup, health assessment, README, triage workflow, and issue creation. Use for first-time setup; use `sync-repository` for ongoing maintenance. |
| `session-review` | Per-session end-of-work checklist. Use after each coding session. Use `sync-repository` for periodic full-repo sync (daily, weekly, or pre-release). |
| `sdlc-status` | Read-only dashboard showing SDLC pipeline progress. Does not detect drift or run checks. |
| `setup-docs-site` | Scaffolds MkDocs + Material + GHA Pages workflow. Sync-repository calls this in Phase 4 when no docs infrastructure exists. |

## Useful Commands Reference

No direct CLI commands. This skill invokes other skills and coordinates their output.
