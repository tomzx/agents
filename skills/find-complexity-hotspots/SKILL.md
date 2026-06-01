---
name: find-complexity-hotspots
description: Scan the codebase for functions and modules with high cyclomatic complexity, excessive length, or deep nesting, then produce prioritized refactoring suggestions.
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "[path]"
---

TODAY=!`date +%Y-%m-%d`

# Complexity Hotspots

Identifies the most complex code in the codebase — by cyclomatic complexity, function length, and nesting depth — and produces targeted refactoring suggestions. Pairs naturally with `/analyze-git-churn`: files that are both frequently changed and structurally complex are the highest-priority refactoring targets.

## Prerequisites

- Working directory is the root of the repository (or a subdirectory)
- Optional: `$1` — path to limit the scan (defaults to `.`)
- Language-specific tools installed as available (skill degrades gracefully to heuristics if not present):
  - Python: `radon` (`uv tool install radon` or `pip install radon`)
  - JavaScript/TypeScript: `complexity-report` or `eslint` with `complexity` rule
  - Go: `gocyclo` (`go install github.com/fzipp/gocyclo@latest`)
  - Generic fallback: line-count and nesting-depth heuristics via `grep`/`awk`

## Metrics

| Metric | What it measures | Threshold to flag |
|--------|-----------------|-------------------|
| Cyclomatic complexity | Number of independent paths through a function | ≥ 10 |
| Function length | Lines of code in a single function/method | ≥ 50 |
| Nesting depth | Maximum indentation depth inside a function | ≥ 4 levels |
| File length | Total lines in a file | ≥ 500 |

Flag any unit that exceeds **any** threshold. Rank by the number of thresholds exceeded, then by severity within each metric.

## Steps

### 1. Detect Language and Available Tools

Identify the primary language(s) in the target path:
```
find ${1:-.} -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
```

Check for available analysis tools:
```
command -v radon && radon --version
command -v gocyclo && gocyclo -version
```

### 2. Measure Cyclomatic Complexity

**Python — radon:**
```
radon cc ${1:-.} -s -a -n C --total-average
```
Flag anything graded C (complexity 10–14), D (15–19), E (20–24), or F (25+).

**Go — gocyclo:**
```
gocyclo -over 10 ${1:-.}
```

**JavaScript/TypeScript — eslint:**
```
npx eslint ${1:-.} --rule '{"complexity": ["warn", 10]}' --format compact 2>/dev/null | grep complexity
```

**Generic fallback (any language) — count `if`/`for`/`while`/`case` per function block:**
```
grep -rn --include="*.py" --include="*.js" --include="*.ts" --include="*.go" \
  -E '^\s*(if|elif|else|for|while|case|catch|&&|\|\|)' ${1:-.} | \
  awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -20
```

### 3. Measure Function Length

Find long functions using language-appropriate patterns:

**Python:**
```
grep -rn --include="*.py" -n "^\s*def " ${1:-.} | \
  awk -F: '{print $1, $2}' | \
  awk 'NR>1 && file==$1 {print file, prev_line, $2-prev_line} {file=$1; prev_line=$2}' | \
  awk '$3 >= 50 {print $3, $1, $2}' | sort -rn | head -20
```

**Generic — find files where any function-start-to-end span exceeds 50 lines:**
```
awk '/^(def |function |func |public |private |protected )/{if(start && NR-start>50) print FILENAME, start, NR-start; start=NR}' \
  $(find ${1:-.} -type f -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go") 2>/dev/null | \
  sort -t' ' -k3 -rn | head -20
```

### 4. Measure Nesting Depth

Detect excessive indentation as a proxy for nesting:

```
grep -rn --include="*.py" --include="*.js" --include="*.ts" --include="*.go" \
  -P "^\t{4,}|^ {16,}" ${1:-.} | \
  awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -20
```

### 5. Find Long Files

```
find ${1:-.} -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" \) \
  -exec wc -l {} + | sort -rn | grep -v total | head -20
```

### 6. Rank and Deduplicate

Build a unified hotspot list. Score each file/function: +1 for each threshold exceeded, weighted by severity. Deduplicate so each file appears once in the summary with all its violations listed.

### 7. Inspect Each Hotspot

For each top-10 file:
1. Read the file.
2. Identify the specific functions driving the complexity score.
3. Note the root cause: long conditionals, repeated logic, mixed abstraction levels, etc.

### 8. Generate Suggestions

For each hotspot, suggest from these categories (only what genuinely applies):

- **Extract function/method** — pull a coherent block into a named helper
- **Replace conditional with polymorphism or strategy pattern** — eliminate long `if/elif` chains
- **Introduce early returns** — flatten nested conditionals
- **Split class/module** — file is doing too many things; separate concerns
- **Replace manual logic with a library** — complex parsing, retry, validation, etc. handled by existing packages
- **Add tests before refactoring** — high complexity with no tests; write characterization tests first to make the refactor safe

Priority: 🔴 High (≥3 thresholds, or complexity ≥ 20), 🟡 Medium (2 thresholds, or complexity 10–19), 🟢 Low (1 threshold).

### 9. Cross-reference with Churn (optional)

If git is available, check whether the hotspots also appear in recent churn:
```
git log --since="1 month ago" --name-only --pretty=format: | sort | uniq -c | sort -rn | head -30
```
Flag any file that appears in both the complexity list and the churn list — these are the highest-priority targets.

### 10. Print the Report

```
# Complexity Hotspots — {TODAY}

## Summary

- Files scanned: N
- Hotspots found: N (files exceeding at least one threshold)
- Tools used: <radon / gocyclo / eslint / heuristics>

## Top Hotspots

| Rank | File | Cyclomatic | Max fn length | Max nesting | File length | Also high-churn? |
|------|------|-----------|---------------|-------------|-------------|-----------------|
| 1    | …    | F(28)     | 120 lines     | 6 levels    | 800 lines   | yes             |

## File-by-File Suggestions

### 1. `<path>`

<2–3 sentence description of what makes this file complex>

- 🔴 **[Category]** <specific suggestion>
- 🟡 **[Category]** <specific suggestion>

## Quick Wins

3–5 changes with the highest complexity-reduction for the lowest effort.

## Next Steps

Suggested order of operations, including whether to write tests before refactoring.
```

## Example Usage

**Scenario 1: Full scan**
```
/find-complexity-hotspots
```
Finds a 900-line router file with average cyclomatic complexity of F(31). Suggests splitting into sub-routers and replacing a 15-branch `if/elif` chain with a dispatch table.

**Scenario 2: Targeted scan**
```
/find-complexity-hotspots src/api
```
Scans only the `src/api` directory. Surfaces two handler functions each over 80 lines; recommends extracting validation and serialization into separate helpers.

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `radon cc . -s -a -n C` | Python cyclomatic complexity, grade C and worse |
| `radon mi . -s` | Python maintainability index |
| `gocyclo -over 10 .` | Go functions with complexity > 10 |
| `wc -l **/*.py \| sort -rn \| head -20` | Longest Python files |
| `git log --since="1 month ago" --name-only --pretty=format: \| sort \| uniq -c \| sort -rn` | Recent churn for cross-reference |
