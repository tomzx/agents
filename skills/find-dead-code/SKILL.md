---
name: find-dead-code
description: Find unused functions, classes, variables, exports, feature flags, and config keys across the codebase and produce a prioritized removal list.
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "[path]"
---

TODAY=!`date +%Y-%m-%d`

# Dead Code Scan

Identifies code that is defined but never used — functions, classes, variables, exports, feature flags, and config keys — and produces a prioritized list of safe removals. Dead code increases cognitive load, slows onboarding, and creates false surface area for future bugs.

## Prerequisites

- Working directory is the root of the repository (or a subdirectory)
- Optional: `$1` — path to limit the scan (defaults to `.`)
- Language-specific tools installed as available (degrades to heuristics):
  - Python: `vulture` (`uv tool install vulture` or `pip install vulture`)
  - JavaScript/TypeScript: `ts-prune` (`npx ts-prune`) or `knip` (`npx knip`)
  - Go: `deadcode` (`go install golang.org/x/tools/cmd/deadcode@latest`)

## Categories of Dead Code

| Category | Examples |
|----------|---------|
| Unused functions / methods | Defined but never called anywhere in the codebase |
| Unused classes / types | Defined but never instantiated or referenced |
| Unused variables / constants | Assigned but never read |
| Unused imports | Imported but not used in the file |
| Unreachable code | Code after a `return`/`raise`/`exit`, or in a branch that can never be true |
| Stale feature flags | Flags that are always-true or always-false in all environments |
| Orphaned config keys | Keys present in config files but never read by the application |
| Unused exports | Symbols exported from a module but not imported anywhere |

## Steps

### 1. Detect Language and Available Tools

```
find ${1:-.} -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
command -v vulture
command -v ts-prune || npx --yes ts-prune --version 2>/dev/null
command -v deadcode
```

### 2. Run Language-Specific Dead Code Detection

**Python — vulture:**
```
vulture ${1:-.} --min-confidence 80 --sort-by-size
```
`--min-confidence 80` reduces false positives from dynamic attribute access.

**JavaScript/TypeScript — knip (preferred) or ts-prune:**
```
npx knip --reporter compact 2>/dev/null || npx ts-prune ${1:-.}
```

**Go — deadcode:**
```
deadcode -test ./...
```

**Generic heuristics (any language):**

Unused imports:
```
grep -rn --include="*.py" "^import \|^from .* import" ${1:-.} | \
  awk '{print $NF, FILENAME}' | sort | uniq > /tmp/imported.txt
# Cross-reference with actual usage — report imports that appear only once (the import line itself)
```

Functions defined but never called (rough signal):
```
grep -rn --include="*.py" "^def \|^    def " ${1:-.} | \
  sed 's/.*def \([a-zA-Z_][a-zA-Z0-9_]*\).*/\1/' | \
  while read fn; do
    count=$(grep -r "$fn" ${1:-.} | wc -l)
    [ "$count" -le 1 ] && echo "$count $fn"
  done | sort -n | head -30
```

Always-true/false feature flags:
```
grep -rn --include="*.py" --include="*.js" --include="*.ts" \
  -E "(if|when|enabled)\s*\(?\s*(True|true|False|false)\s*\)?" ${1:-.} | head -20
```

### 3. Find Unreachable Code

```
grep -rn --include="*.py" --include="*.go" --include="*.js" --include="*.ts" \
  -A1 -E "^\s*(return|raise|exit|panic|os\.Exit)" ${1:-.} | \
  grep -v "^--$" | grep -v -E "(return|raise|exit|panic)" | \
  grep -v "^\s*$" | head -30
```

### 4. Scan Config Files for Orphaned Keys

Find all config keys:
```
grep -rn --include="*.yaml" --include="*.yml" --include="*.toml" --include="*.env*" \
  -E "^[a-zA-Z_][a-zA-Z0-9_]*\s*[:=]" ${1:-.} | \
  sed 's/.*:\s*\([a-zA-Z_][a-zA-Z0-9_]*\)\s*[:=].*/\1/' | sort -u > /tmp/config_keys.txt
```

Cross-reference against source reads:
```
while read key; do
  count=$(grep -r "\"$key\"\|'$key'\|\b$key\b" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" ${1:-.} | wc -l)
  [ "$count" -eq 0 ] && echo "$key"
done < /tmp/config_keys.txt
```

### 5. Filter False Positives

Before reporting, filter out:
- Functions whose names start with `_` in Python (may be intentionally semi-private but called via `getattr`)
- Functions matching test framework patterns (`test_*`, `setUp`, `tearDown`)
- Names referenced only in strings (dynamic dispatch, `getattr`, `eval`)
- Symbols marked with `# noqa`, `//nolint`, or similar suppression comments
- Entry points (`main`, `__main__`, CLI commands, route handlers)

### 6. Rank by Removal Safety

| Safety | Criteria |
|--------|---------|
| 🟢 Safe to remove | Zero references anywhere, not an entry point, not dynamic |
| 🟡 Verify first | One or two references, or used in tests only |
| 🔴 Needs investigation | Dynamic access patterns, plugin/hook systems, public API |

### 7. Inspect Top Candidates

For the top 20 findings, read the defining file and the call sites to confirm the finding is genuine before including it in the report.

### 8. Print the Report

```
# Dead Code Scan — {TODAY}

## Summary

- Files scanned: N
- Dead code candidates: N
- Confirmed safe removals: N

## By Category

### Unused Functions / Methods (N)
| Safety | Symbol | File | Line | Notes |
|--------|--------|------|------|-------|
| 🟢 | `foo()` | `src/utils.py` | 42 | Zero references |

### Unused Imports (N)
…

### Unreachable Code (N)
…

### Stale Feature Flags (N)
…

### Orphaned Config Keys (N)
…

## Recommended Removal Order

1. <highest-confidence, lowest-risk removals first>
2. …

## Items Needing Manual Review

- `<symbol>`: <why it needs a human look before removing>
```

## Example Usage

**Scenario 1: Full project scan**
```
/dead-code-scan
```
Finds 12 unused Python functions, 3 always-true feature flags, and 7 orphaned config keys. Recommends removing the flags first as they also simplify surrounding logic.

**Scenario 2: Targeted scan before a refactor**
```
/dead-code-scan src/payments
```
Confirms that two helper functions in the payments module are no longer called after a recent refactor; safe to delete.

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `vulture . --min-confidence 80 --sort-by-size` | Python dead code, sorted by size of dead symbol |
| `npx knip` | JS/TS unused exports, dependencies, and files |
| `deadcode -test ./...` | Go unreachable functions |
| `grep -rn "def " . \| wc -l` | Count total function definitions |
