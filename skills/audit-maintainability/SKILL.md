---
name: audit-maintainability
description: Audit the codebase for maintainability, the ISO/IEC 25010 characteristic covering modularity, reusability, analyzability, modifiability, and testability. Computes architectural metrics (coupling, fan-out, circular dependencies, layering violations, God modules) that the find-* family does not cover, and aggregates find-* results into a single maintainability scorecard. Use when the user says /audit-maintainability, "coupling analysis", "circular dependencies", "layering violations", "modularity audit", or runs a 25010 sweep via /audit-sdlc. Read-only; produces a scorecard and findings report.
argument-hint: "[--severity critical|high|medium|low] [--path <dir>]"
allowed-tools: Bash, Read, Glob, Grep
---

TODAY=!`date +%Y-%m-%d`

# Maintainability Audit (ISO/IEC 25010)

Audits the codebase for **maintainability**: how easily it can be modified to fix bugs, improve performance, or adapt to a changed environment. It computes the **architectural** maintainability metrics that per-function scanners miss, then rolls the `find-*` family's output into one maintainability scorecard.

This is the **Maintainability** characteristic of the [ISO/IEC 25010](https://en.wikipedia.org/wiki/ISO/IEC_25010) quality model.

## What This Skill Adds Beyond the find-* Family

The `find-*` skills are per-function or per-file scanners (complexity, coverage, dead code, duplication, types). They cannot see **structure**: which module depends on which, whether layers are respected, whether cycles exist, whether one module is a God object. This skill computes those structural metrics and aggregates everything into one view.

| Source | What it provides here |
|---|---|
| `find-complexity-hotspots` | Modifiability: high cyclomatic complexity |
| `find-coverage-gaps` | Testability: untested code |
| `find-dead-code` | Reusability/analyzability: code that should be removed |
| `find-code-duplication` | Reusability: copy-paste to consolidate |
| `find-type-gaps` | Analyzability/modifiability: missing types |
| **This skill (unique)** | Modularity: coupling (fan-out), cohesion, circular dependencies, layering violations, God modules |

## Prerequisites

- Working directory is the root of the repository
- Read `.sdlc/context/architecture.md` if present (declares intended layering rules this audit checks against)
- `find-*` skills available (invoked as read-only scanners)

## What This Checks

| Sub-characteristic | Metric | How computed |
|---|---|---|
| Modularity | coupling / fan-out | count of distinct modules each module imports |
| Modularity | circular dependencies | import graph cycle detection |
| Modularity | layering violations | actual imports vs declared layers in `architecture.md` |
| Modularity | God modules | modules with LOC or import-count far above the median |
| Cohesion | mixed-concern modules | modules whose public functions span unrelated responsibilities (heuristic: divergent import sets) |
| Reusability | duplication | delegates to `find-code-duplication` |
| Analyzability | missing docs/types | delegates to `find-documentation-gaps`, `find-type-gaps` |
| Modifiability | complexity | delegates to `find-complexity-hotspots` |
| Testability | coverage gaps | delegates to `find-coverage-gaps` |

## Steps

### 1. Build the import graph

For the primary language, collect module-level imports to build a directed graph (module → imported module).

```
grep -rEn "^import |^from .* import |^const .* = require\(|^import .* from " --include="*.py" --include="*.ts" --include="*.js" --include="*.go" .
```

Keep imports that resolve to internal modules (drop stdlib and third-party).

### 2. Coupling (fan-out)

For each module, count distinct internal modules it imports. Modules above the 90th percentile (or a fixed threshold like 20) are high-coupling findings. God modules = high fan-out AND high LOC.

```
wc -l $(find . -name "*.py" -not -path "*/test*" -not -path "*/.venv/*") | sort -rn | head -20
```

### 3. Circular dependencies

Detect cycles in the internal import graph. A cycle means a change in any member can ripple to all. Report the smallest cycles first (easiest to break).

For Python, a quick check:
```
grep -rEn "^from \." --include="*.py" . | sort
```
Then trace relative-import chains for cycles. For JS/TS, map `import ... from "./..."` chains. Flag any cycle found.

### 4. Layering violations

If `.sdlc/context/architecture.md` declares layers (e.g., `api → service → repository`, or "UI must not import DB"), check actual imports against the rules. Every import that crosses a forbidden direction is a finding.

```
grep -rEn "import" --include="*.py" . | grep -E "api.*model|model.*api|ui.*db|db.*ui"
```

If no layering rules are declared, skip this step and recommend documenting them in `architecture.md`.

### 5. Delegate to find-* scanners

Invoke these read-only and collect their top findings as the per-characteristic detail:
- `/find-complexity-hotspots` (modifiability)
- `/find-coverage-gaps` (testability)
- `/find-dead-code` (reusability/analyzability)
- `/find-code-duplication` (reusability)
- `/find-type-gaps` (analyzability) — Python/TS/JS only
- `/find-documentation-gaps` (analyzability)

Skip any whose preconditions are not met.

### 6. Compute the maintainability scorecard

Roll up into a per-module and project-level score. Keep the formula simple and transparent:

```
maintainability_score = 100
  - (coupling findings × weight_c)
  - (cycles × weight_cycle)
  - (layering violations × weight_layer)
  - (complexity hotspots × weight_complex)
  - (coverage gap weight)
  - (duplication weight)
clamp to [0, 100]
```

Weights are illustrative; record the weights used in the report so the score is reproducible.

### 7. Report

Print the scorecard and findings. Do not modify files.

## Severity

| Severity | Criteria |
|---|---|
| Critical | Circular dependency on a core module; layering violation bypassing a security/correctness boundary |
| High | God module (>5x median LOC or fan-out); a layer consistently violated across a subsystem |
| Medium | High-coupling module; significant duplication not yet consolidated |
| Low | Missing types/docs; isolated complexity hotspot |

## Output Format

```
# Maintainability Audit — {TODAY}

## Scorecard
- Project maintainability score: NN/100 (weights: ...)
- Per-characteristic:
  - Modularity: N coupling findings, N cycles, N layering violations
  - Reusability: N duplication blocks (from find-code-duplication)
  - Analyzability: N undocumented APIs, N missing types
  - Modifiability: N complexity hotspots
  - Testability: N coverage gaps

## Modularity (unique to this audit)
### High-coupling / God modules
| Module | Fan-out | LOC | Severity |
|---|---|---|---|

### Circular dependencies
| Cycle | Members | Severity |
|---|---|---|

### Layering violations
| From | To | Declared rule | Severity |
|---|---|---|---|

## Aggregated from find-*
### Modifiability (find-complexity-hotspots)
| File:line | CC | Severity |
|---|---|---|

### Testability (find-coverage-gaps)
| File | Coverage | Severity |
|---|---|---|

### Reusability (find-code-duplication / find-dead-code)
| Location | Finding | Severity |
|---|---|---|

### Analyzability (find-type-gaps / find-documentation-gaps)
| Location | Finding | Severity |
|---|---|---|
```

## Example Usage

**Scenario 1: 25010 sweep**
```
/audit-sdlc maintainability
```

**Scenario 2: Structural only (skip find-* aggregation)**
```
/audit-maintainability --path src
```
Focuses on coupling, cycles, and layering.

**Scenario 3: Before a big refactor**
```
/audit-maintainability
```
Identifies the God modules and cycles that should be the refactor targets.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `audit-security`, `audit-functional-suitability`, `audit-performance-efficiency`, `audit-compatibility`, `audit-usability`, `audit-reliability`, `audit-portability` | The other seven ISO/IEC 25010 characteristics. Compose via `/audit-sdlc`. |
| `audit-sdlc` | Coordinator. The `maintainability` scope runs this skill. |
| `find-complexity-hotspots`, `find-coverage-gaps`, `find-dead-code`, `find-code-duplication`, `find-type-gaps`, `find-documentation-gaps` | Per-function scanners aggregated here. |
| `improve-codebase` | Acts on the safe subset of what this (and find-*) reports. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `grep -rEn "^import \|^from .* import " --include="*.py" .` | Build the Python import graph |
| `grep -rEn "^import .* from " --include="*.ts" --include="*.js" .` | Build the JS/TS import graph |
| `wc -l $(find . -name "*.py") \| sort -rn \| head` | LOC by file (God module detection) |
| `grep -rEn "^from \." --include="*.py" . \| sort` | Relative imports (cycle seed) |
