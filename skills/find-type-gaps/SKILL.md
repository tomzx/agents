---
name: find-type-gaps
description: Identify functions, methods, and modules missing type annotations in gradually-typed languages (Python, TypeScript, JavaScript), ranked by public visibility and churn.
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "[path]"
---

TODAY=!`date +%Y-%m-%d`

# Find Type Gaps

Identifies missing or incomplete type annotations in gradually-typed codebases. Type coverage is a safety net that sits alongside test coverage: typed code catches a class of bugs at analysis time, makes refactoring safer, and reduces the cognitive load of reading unfamiliar code. This skill surfaces gaps ranked by how much adding types would help — prioritizing public API surfaces and high-churn files.

## Prerequisites

- Working directory is the root of the repository
- Optional: `$1` — path to limit the scan (defaults to `.`)
- Language support:
  - **Python**: `mypy` (`uv tool install mypy`) or `pyright` (`npm install -g pyright`)
  - **TypeScript**: type errors via `tsc --noEmit`; strict mode gaps via `tsconfig.json` flags
  - **JavaScript**: `@ts-check` JSDoc annotations; `tsc --allowJs --checkJs`
- Not applicable to fully-typed languages (Go, Rust, Java, C#)

## What Counts as a Type Gap

| Language | Gap |
|----------|-----|
| Python | Function parameter with no annotation; return type missing; `Any` used where a concrete type is possible; untyped class attribute |
| TypeScript | `any` used explicitly; `as any` cast; function with implicit `any` parameter; missing return type on exported function |
| JavaScript | No JSDoc `@param`/`@returns`; no `@ts-check` at file top; untyped exported function |

## Steps

### 1. Detect Language

```
find ${1:-.} -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -5
```

Proceed only if Python, TypeScript, or JavaScript files are present. Report "not applicable" for fully-typed languages.

### 2. Measure Type Coverage

**Python — mypy:**
```
mypy ${1:-.} \
  --ignore-missing-imports \
  --no-error-summary \
  --any-exprs-report .mypy-type-report \
  2>/dev/null | grep -E "error:|note:" | head -40
```

Parse the any-exprs report for per-file coverage:
```
cat .mypy-type-report/any-exprs.txt 2>/dev/null | \
  awk 'NR>1 {print $3"% typed\t"$1}' | sort -n | head -30
```

**Python — pyright (stricter, faster):**
```
pyright ${1:-.} --outputjson 2>/dev/null | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for d in data.get('generalDiagnostics', []):
    if 'unknown' in d.get('message','').lower() or 'Any' in d.get('message',''):
        print(d['file'].split('/')[-1], d['range']['start']['line'], d['message'][:80])
" 2>/dev/null | head -30
```

**Python — grep fallback (untyped function signatures):**
```
grep -rn --include="*.py" -E "^(    )?def [a-zA-Z_]" ${1:-.} | \
  grep -v "->.*:" | grep -v "#" | \
  awk -F: '{ if ($0 !~ /: [a-zA-Z\[]/) print }' | head -30
```

Count untyped vs typed:
```
total=$(grep -rc --include="*.py" -E "^(    )?def " ${1:-.} | awk -F: '{s+=$2} END{print s}')
typed=$(grep -rc --include="*.py" -E "^(    )?def .*->|^(    )?def .*\) -> " ${1:-.} | awk -F: '{s+=$2} END{print s}')
echo "Typed functions: $typed / $total"
```

**TypeScript — count explicit `any`:**
```
grep -rn --include="*.ts" --include="*.tsx" \
  -E ": any\b|as any\b|<any>" \
  ${1:-.} | grep -v "node_modules\|\.d\.ts\|test\|spec" | \
  awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -20
```

Check strictness configuration:
```
cat tsconfig.json 2>/dev/null | python3 -c "
import json, sys
cfg = json.load(sys.stdin).get('compilerOptions', {})
flags = ['strict','noImplicitAny','strictNullChecks','strictFunctionTypes','noImplicitReturns']
for f in flags:
    print(f, ':', cfg.get(f, 'not set'))
" 2>/dev/null
```

**JavaScript — check for `@ts-check` adoption:**
```
total_js=$(find ${1:-.} -name "*.js" ! -path "*/node_modules/*" | wc -l)
checked_js=$(grep -rl "@ts-check" ${1:-.} --include="*.js" | wc -l)
echo "JS files with @ts-check: $checked_js / $total_js"
```

### 3. Identify High-Value Gaps

Focus on gaps that would provide the most benefit:

**Public API surface** — exported/public functions without types are the highest priority since callers cannot rely on them safely:
```
# Python: public functions (no leading underscore) without return type
grep -rn --include="*.py" -E "^def [a-zA-Z]" ${1:-.} | grep -v " -> " | head -20

# TypeScript: exported functions without return type
grep -rn --include="*.ts" -E "^export (async )?function [a-zA-Z]" ${1:-.} | \
  grep -v "): [a-zA-Z<]" | head -20
```

**`Any` escape hatches** — uses of `Any`/`any` that bypass the type system:
```
grep -rn --include="*.py" -E "\bAny\b" ${1:-.} | grep -v "typing_extensions\|from typing\|import" | head -20
grep -rn --include="*.ts" --include="*.tsx" -E ": any\b|as any" ${1:-.} | \
  grep -v "node_modules\|\.d\.ts" | head -20
```

**Untyped class attributes (Python):**
```
grep -rn --include="*.py" -B1 "self\.[a-zA-Z_]* =" ${1:-.} | \
  grep -v "__init__\|#\|annotated\|: " | head -20
```

### 4. Cross-Reference with Churn

Untyped code in high-churn files is highest priority — types would catch regressions on every change:
```
git log --since="1 month ago" --name-only --pretty=format: | sort | uniq -c | sort -rn | head -30
```

### 5. Rank Gaps

| Priority | Criteria |
|----------|---------|
| 🔴 High | Public/exported function; appears in high-churn file; `Any` on a core data structure |
| 🟡 Medium | Internal function called from multiple modules; class with untyped attributes |
| 🟢 Low | Private helper; test file; one-off script |

### 6. Suggest Concrete Annotations

For each high-priority gap, read the function and infer the correct type signature from usage:
- Look at call sites to determine what types are actually passed
- Look at return statements to determine return type
- Prefer specific types over `Any`; use `Optional[X]` / `X | None` for nullable values
- Suggest `TypedDict` or `dataclass` where `dict` is used as a structured record

### 7. Check Type Configuration

**Python — verify `mypy` or `pyright` is configured:**
```
cat mypy.ini setup.cfg pyproject.toml 2>/dev/null | grep -A10 "\[mypy\]\|\[tool.mypy\]\|\[tool.pyright\]"
```

Recommend adding to CI if not present.

**TypeScript — check for strict mode:**
If `strict: true` is not set in `tsconfig.json`, recommend enabling it incrementally:
1. Enable `noImplicitAny` first
2. Then `strictNullChecks`
3. Then full `strict`

### 8. Print the Report

```
# Type Gap Report — {TODAY}

## Summary

- Language(s): <Python / TypeScript / JavaScript>
- Type coverage: X% of functions annotated
- Explicit Any / untyped escapes: N
- 🔴 High-priority gaps: N
- Tools used: <mypy / pyright / tsc / grep>

## Configuration

- mypy / pyright / tsc configured: yes / no
- Strict mode: enabled / partial / not set
- Recommendation: <enable strict mode incrementally / add mypy to CI>

## High-Priority Gaps

### Public API — Untyped Exported Functions (N)

| File | Line | Function | Missing |
|------|------|----------|---------|
| `src/client.py` | 42 | `def fetch(url, timeout)` | param types + return type |

### `Any` Escape Hatches (N)

| File | Line | Usage | Suggested type |
|------|------|-------|---------------|

### Untyped Core Data Structures (N)

…

## Suggested Annotations

For each high-priority function, a concrete suggested signature:

### `fetch` in `src/client.py:42`

```python
# Before
def fetch(url, timeout=30):

# After
def fetch(url: str, timeout: int = 30) -> dict[str, Any]:
```

## Quick Wins

3–5 annotation additions that would cover the most-used untyped surface area.

## Next Steps

1. Add mypy/pyright to CI with `--strict` (or incremental flags)
2. Address 🔴 gaps in priority order
3. Set a coverage floor and enforce it in CI
```

## Example Usage

**Scenario 1: Python project baseline**
```
/find-type-gaps
```
61% of functions are typed. Public `Client` class has 8 untyped methods — the primary entry point for library users. Generates suggested signatures for all 8 based on call-site analysis.

**Scenario 2: TypeScript strictness audit**
```
/find-type-gaps src/api
```
`strict` mode is off. Finds 34 uses of `as any` and 12 implicit-any function parameters. Recommends enabling `noImplicitAny` first and lists the 12 parameters to fix.

**Scenario 3: Pre-refactor safety check**
```
/find-type-gaps src/payments
```
The payments module is 20% typed. Before refactoring, recommends annotating the 5 core functions so mypy can catch regressions during the refactor.

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `mypy . --ignore-missing-imports` | Python type check |
| `mypy . --any-exprs-report .report` | Per-file Any expression count |
| `pyright . --outputjson` | Strict Python type check with JSON output |
| `tsc --noEmit` | TypeScript type check without emitting files |
| `grep -rn ": any" --include="*.ts"` | Find explicit any in TypeScript |
| `grep -rn "^def " --include="*.py" \| grep -v " -> "` | Untyped Python functions |
