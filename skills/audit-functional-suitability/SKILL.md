---
name: audit-functional-suitability
description: Audit whether the software actually does what it should, completely and correctly. This is the Functional suitability characteristic of the ISO/IEC 25010 software quality model (completeness, correctness, appropriateness). Cross-checks implemented behavior against requirements in .sdlc/ and surfaces stubs, TODOs, skipped tests, and open bug clusters. Use when the user says /audit-functional-suitability, "functional audit", "does it do what it should", "requirements coverage", "completeness check", or runs a 25010 sweep via /audit-sdlc. Read-only; produces a findings report.
argument-hint: "[--severity critical|high|medium|low] [--feature <slug>]"
allowed-tools: Bash, Read, Glob, Grep
---

TODAY=!`date +%Y-%m-%d`

# Functional Suitability Audit (ISO/IEC 25010)

Audits the codebase for **functional suitability**: does the software provide the functions needed to meet stated requirements, completely and correctly? It is the bottom-up check that what was supposed to be built is actually built and working.

This is the **Functional suitability** characteristic of the [ISO/IEC 25010](https://en.wikipedia.org/wiki/ISO/IEC_25010) quality model. Distinct from `check-issue-status` (which checks whether a *single issue* is addressed), this audit scans the whole implementation against its requirements corpus and the code's own honesty markers (stubs, TODOs, disabled tests).

## Prerequisites

- Working directory is the root of the repository
- `.sdlc/features/*/requirements.md` present (improves completeness scoring; if absent, the audit falls back to code-honesty signals only)
- Read `.sdlc/context/project-overview.md` if present for scope
- `gh` CLI for open bug-issue signals (optional)

## What This Checks

| Sub-characteristic | What it means | Signals scanned |
|---|---|---|
| Functional completeness | All required functions are implemented | requirements with no matching code; `TODO`/`FIXME`/`NotImplemented`/`stub`/`501`/`raise NotImplementedError`; feature flags wired but never enabled |
| Functional correctness | Functions produce correct results | open bug issues; skipped/disabled/`xfail` tests; assertion-free tests; logic that silently no-ops (empty `except`, `return None` on happy paths) |
| Functional appropriateness | Functions are suitable for the intended use | requirements whose implementation exists but diverges from the stated acceptance criteria; over-broad or surprising behavior |

## Steps

### 1. Inventory requirements (if .sdlc exists)

For each `.sdlc/features/*/requirements.md`, extract functional requirements (`FR-N`) and their acceptance criteria. Record each as a completeness target.

```
find .sdlc/features -name requirements.md 2>/dev/null
```

If no `.sdlc/`, record "no requirements corpus" and rely on code-honesty signals (step 2) plus bug issues (step 3).

### 2. Scan code-honesty markers

Find places where the code admits it is incomplete:

```
grep -rEn "TODO|FIXME|XXX|HACK|NotImplemented|not implemented|raise NotImplemented|501 Not Implemented|stub|placeholder|coming soon" \
  --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.rs" --include="*.java" . \
  | grep -v -E "test|_test|spec|vendor|node_modules|\.venv"
```

Each marker is a completeness finding (the code states it is not done).

### 3. Check requirements coverage

For each functional requirement, search the code for evidence of implementation (keywords from the requirement). Requirements with no evidence are completeness gaps.

```
grep -rEn "<requirement keyword>" --include="*.py" .
```

### 4. Correctness signals

- Open bug issues (group by area to spot correctness hotspots):
  ```
  gh search issues --repo <repo> --state open --label bug --limit 100 --json number,title,labels
  ```
- Skipped / disabled / expected-fail tests:
  ```
  grep -rEn "pytest.mark.skip|@skip|@Ignore|xfail|\.skip\(|test\.todo|it.skip|describe.skip" --include="*.py" --include="*.ts" --include="*.js" .
  ```
- Assertion-free tests (tests with no assert/expect):
  ```
  grep -rL "assert\|expect\|should" --include="test_*.py" --include="*_test.*" .
  ```
- Silent no-ops: empty exception handlers and functions that return without acting:
  ```
  grep -rEnzB1 "except[^:]*:\s*\n\s*(pass|continue|\.\.\.)" --include="*.py" .
  ```

### 5. Appropriateness spot-check

For a sample of requirements where code exists, compare behavior to the acceptance criteria. Flag clear divergences (e.g., requirement says "soft delete" but code hard-deletes). This is judgment-based; keep it to a sample and flag for human review.

### 6. Report

Classify each finding by severity (below), then print the report in the Output Format. Do not modify any files.

## Severity

| Severity | Criteria |
|---|---|
| Critical | A documented requirement has zero implementation; a correctness bug on a critical path with an open issue |
| High | Completeness gap on a core function; cluster of skipped tests in a critical module |
| Medium | TODO/stub in a non-critical path; isolated skipped test |
| Low | Cosmetic TODO; minor divergence from acceptance criteria |

## Output Format

```
# Functional Suitability Audit — {TODAY}

## Summary
- Requirements corpus: <present (N FRs) | absent>
- Completeness gaps: N critical, N high
- Correctness signals: N bug issues, N skipped tests, N assertion-free tests
- Code-honesty markers: N

## Completeness (requirements with no implementation)
| FR | Feature | Requirement | Evidence found | Severity |
|---|---|---|---|---|

## Code-honesty markers (incomplete by the code's own admission)
| File:line | Marker | Text | Severity |
|---|---|---|---|

## Correctness
### Open bug clusters
| Area | Bug count | Sample issues |
|---|---|---|

### Skipped / disabled tests
| File:line | Marker | Severity |
|---|---|---|

### Appropriateness divergences
| FR | Expected | Actual | Severity |
|---|---|---|---|
```

## Example Usage

**Scenario 1: 25010 sweep**
```
/audit-sdlc functional-suitability
```
Runs this skill as part of the full quality-model sweep.

**Scenario 2: Single feature**
```
/audit-functional-suitability --feature 42-notification-system
```
Checks requirements coverage only for one feature directory.

**Scenario 3: No .sdlc yet**
```
/audit-functional-suitability
```
Falls back to code-honesty markers and bug issues. Recommends running `/sync-sdlc` to establish a requirements corpus.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `audit-security`, `audit-performance-efficiency`, `audit-compatibility`, `audit-usability`, `audit-reliability`, `audit-maintainability`, `audit-portability` | The other seven ISO/IEC 25010 characteristics. Compose via `/audit-sdlc`. |
| `audit-sdlc` | Coordinator that runs this and the sibling characteristic audits. |
| `check-issue-status` | Single-issue version of the completeness question. This is the whole-corpus version. |
| `sync-sdlc` | Establishes the requirements corpus this audit scores against. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `grep -rEn "TODO\|FIXME\|NotImplemented\|stub\|501" --include="*.py" .` | Code-honesty markers |
| `grep -rEn "pytest.mark.skip\|xfail\|@skip\|@Ignore" .` | Disabled tests |
| `gh search issues --repo <repo> --state open --label bug` | Open correctness bugs |
