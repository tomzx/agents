---
name: find-code-duplication
description: Identify copy-pasted code blocks and near-duplicate logic that should be extracted into shared helpers or modules, ranked by duplication size and churn.
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "[path]"
---

TODAY=!`date +%Y-%m-%d`

# Find Code Duplication

Detects copy-pasted blocks and near-duplicate logic across the codebase and produces a prioritized extraction plan. Duplicated code multiplies the cost of every future change and is a leading source of bugs where a fix is applied in one copy but not others.

## Prerequisites

- Working directory is the root of the repository
- Optional: `$1` — path to limit the scan (defaults to `.`)
- Language-specific tools (degrades to heuristics if unavailable):
  - Any language: `jscpd` (`npm install -g jscpd`)
  - Python: `pylint` similarity checker or `flake8-bugbear`
  - Java/others: `cpd` (from PMD, `brew install pmd`)

## What to Look For

| Type | Description | Threshold to flag |
|------|-------------|------------------|
| Exact duplication | Identical code blocks copy-pasted verbatim | ≥ 5 lines |
| Near-duplication | Same structure with minor variations (different variable names, literals) | ≥ 8 lines |
| Structural duplication | Same algorithm implemented independently in multiple places | Judgment |
| Cross-file patterns | The same sequence of operations repeated across many call sites | ≥ 3 occurrences |

## Steps

### 1. Detect Language and Available Tools

```
find ${1:-.} -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
command -v jscpd && jscpd --version
command -v cpd && cpd --version 2>/dev/null
```

### 2. Run Duplication Detector

**jscpd (preferred — language-agnostic, handles near-duplicates):**
```
jscpd ${1:-.} \
  --min-lines 5 \
  --min-tokens 50 \
  --reporters console,json \
  --output .jscpd-report \
  --ignore "**/*.test.*,**/*.spec.*,**/node_modules/**,**/.venv/**" \
  2>/dev/null | tail -60
```

Parse the JSON report for the top duplicates:
```
python3 -c "
import json, sys
try:
    data = json.load(open('.jscpd-report/jscpd-report.json'))
    dupes = data.get('duplicates', [])
    dupes.sort(key=lambda d: d.get('lines', 0), reverse=True)
    for d in dupes[:20]:
        a = d['firstFile']
        b = d['secondFile']
        print(f\"{d.get('lines',0):4d} lines  {a['name']}:{a['start']}  <->  {b['name']}:{b['start']}\")
except: pass
" 2>/dev/null
```

**CPD (Java/Apex/others):**
```
cpd --minimum-tokens 50 --dir ${1:-.} --language python 2>/dev/null | head -60
```

**pylint similarity (Python fallback):**
```
python3 -m pylint ${1:-.} --disable=all --enable=similarities \
  --min-similarity-lines=5 2>/dev/null | grep -A5 "Similar lines"
```

### 3. Heuristic Detection (no tools required)

Find files with identical or near-identical function signatures:
```
grep -rh --include="*.py" --include="*.js" --include="*.ts" --include="*.go" \
  -E "^(def |function |func |async function )" ${1:-.} | \
  sort | uniq -d | head -20
```

Find repeated import blocks (often signals copy-pasted module scaffolding):
```
grep -rh --include="*.py" "^from \|^import " ${1:-.} | \
  sort | uniq -c | sort -rn | awk '$1 > 3' | head -20
```

Find repeated error-handling patterns:
```
grep -rn --include="*.py" --include="*.js" --include="*.ts" \
  -A3 "except Exception\|catch (err\|catch (error" ${1:-.} | \
  grep -v "^--$" | sort | uniq -c | sort -rn | head -20
```

### 4. Cross-Reference with Churn

Duplicated code in high-churn files is highest priority — every commit risks fixing only one copy:
```
git log --since="1 month ago" --name-only --pretty=format: | sort | uniq -c | sort -rn | head -30
```

Flag any duplicate pair where at least one file appears in the top-20 churn list.

### 5. Inspect Top Duplicates

For each of the top-15 duplicate pairs:
1. Read both code blocks.
2. Identify the variation between them (different variable names, extra/missing step, different error handling).
3. Determine the extraction strategy:
   - **Identical** → extract as-is into a shared helper
   - **Minor variation** → parameterize the differing parts
   - **Structural** → extract with an abstraction (base class, strategy, template method)
   - **Cross-module** → consider whether it belongs in a shared utility module or a separate library

### 6. Prioritize

| Priority | Criteria |
|----------|---------|
| 🔴 High | ≥ 20 lines duplicated, or appears in high-churn files, or the copies have already diverged |
| 🟡 Medium | 10–19 lines, stable files, copies still in sync |
| 🟢 Low | 5–9 lines, trivial pattern, low extraction value |

Diverged copies (where the duplicates are no longer identical) are always High — a bug has already been fixed in one but not the other, or will be soon.

### 7. Print the Report

```
# Code Duplication Report — {TODAY}

## Summary

- Files scanned: N
- Duplicate pairs found: N
- Total duplicated lines: N
- 🔴 High-priority extractions: N
- Tools used: <jscpd / cpd / pylint / heuristics>

## Duplication Map

| Rank | Lines | File A | File B | Diverged? | Churn? | Priority |
|------|-------|--------|--------|-----------|--------|---------|
| 1    | 45    | `src/billing/invoice.py:120` | `src/reporting/export.py:88` | yes | yes | 🔴 |

## Extraction Plan

### 1. `<description of the duplicated logic>` — 45 lines, 🔴 High

**Appears in:**
- `src/billing/invoice.py:120–165`
- `src/reporting/export.py:88–133`

**Variation:** `export.py` version adds a currency conversion step missing from `invoice.py`.

**Recommended extraction:**
```python
# src/utils/formatting.py
def format_line_items(items, *, convert_currency=False):
    ...
```

**Steps:**
1. Write tests covering both variants
2. Extract to `src/utils/formatting.py`
3. Replace both call sites
4. Verify tests pass

### 2. …

## Already-Diverged Copies (Fix First)

These duplicates have drifted apart — a bug fix or feature likely exists in one but not the other:
- `<file A>:<line>` vs `<file B>:<line>` — diff: <what differs>

## Quick Wins

3–5 extractions that eliminate the most duplicated lines for the least effort.
```

## Example Usage

**Scenario 1: Full project scan**
```
/find-code-duplication
```
Finds 8% duplication ratio. Top pair: a 60-line pagination helper copy-pasted into 4 different API handlers, already diverged (one has a bug fix the others lack). Recommends extracting to `src/utils/pagination.py`.

**Scenario 2: Pre-refactor check**
```
/find-code-duplication src/payments
```
Before refactoring the payments module, confirms 3 duplicate validation blocks that should be unified first to avoid fixing the same logic multiple times during the refactor.

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `jscpd . --min-lines 5 --reporters console` | Duplication scan with console output |
| `jscpd . --ignore "**/*.test.*"` | Exclude test files from scan |
| `python3 -m pylint . --disable=all --enable=similarities` | Python similarity checker |
| `cpd --minimum-tokens 50 --dir . --language python` | CPD for Python |
| `git log --since="1 month ago" --name-only --pretty=format: \| sort \| uniq -c \| sort -rn` | Churn cross-reference |
