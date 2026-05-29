---
name: find-documentation-gaps
description: Find public APIs, modules, CLI entry points, and configuration options that lack documentation, ranked by usage and visibility, and suggest what to document first.
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "[path]"
---

TODAY=!`date +%Y-%m-%d`

# Documentation Gaps

Identifies public-facing code — functions, classes, modules, CLI commands, REST endpoints, and config options — that is missing or has stale documentation. Ranks gaps by how visible and heavily-used the surface area is, so the most impactful docs get written first.

## Prerequisites

- Working directory is the root of the repository
- Optional: `$1` — path to limit the scan (defaults to `.`)
- Optional language-specific tools:
  - Python: `interrogate` (`uv tool install interrogate`) for docstring coverage
  - JavaScript/TypeScript: `typedoc` or `jsdoc` comment detection via grep
  - Go: `golint` or grep for unexported godoc

## What Counts as a Documentation Gap

| Surface | Missing if... |
|---------|--------------|
| Public function / method | No docstring, no JSDoc/godoc comment |
| Public class / interface | No class-level docstring or comment |
| Module / package | No module docstring or `__init__.py` docstring |
| CLI command / subcommand | No `help=` / `--help` text, or help text is a placeholder |
| REST / RPC endpoint | No docstring, no OpenAPI annotation, no comment describing purpose, params, and response |
| Config key / env variable | Key present in config file or `.env.example` but not documented in README or reference doc |
| Exported type / constant | No accompanying comment explaining purpose and valid values |

## Steps

### 1. Detect Language and Project Type

```
find ${1:-.} -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
ls README* docs/ CHANGELOG* openapi* swagger* 2>/dev/null
```

### 2. Measure Docstring / Comment Coverage

**Python — interrogate:**
```
interrogate ${1:-.} -v --ignore-init-method --ignore-magic --ignore-private 2>/dev/null | tail -30
```
Flag any module, class, or function with `MISSING` in the output.

**Python — grep fallback:**
```
# Find public functions/classes with no immediately following docstring
python3 -c "
import ast, sys, os
for root, dirs, files in os.walk('${1:-.}'):
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', '.venv', 'node_modules')]
    for f in files:
        if not f.endswith('.py'): continue
        path = os.path.join(root, f)
        try:
            tree = ast.parse(open(path).read())
        except:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith('_'): continue
                if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
                    print(f'{path}:{node.lineno}  {type(node).__name__}  {node.name}')
" 2>/dev/null | head -50
```

**JavaScript/TypeScript — find exported functions without JSDoc:**
```
grep -rn --include="*.ts" --include="*.js" -B1 "^export " ${1:-.} | \
  grep -v "/\*\*" | grep "^export " | head -30
```

**Go — find exported functions without godoc:**
```
grep -rn --include="*.go" -B1 "^func [A-Z]" ${1:-.} | \
  grep -v "^--$" | \
  awk '/^func [A-Z]/{if(prev !~ /^\/\//) print FILENAME, $0} {prev=$0}' | head -30
```

### 3. Find Undocumented CLI Commands

**Click / Typer (Python):**
```
grep -rn --include="*.py" -A3 "@.*\.command\|@app\.command\|@click\.command" ${1:-.} | \
  grep -v 'help=' | grep -v "#" | grep "@" | head -20
```

**argparse:**
```
grep -rn --include="*.py" "add_parser\|add_argument" ${1:-.} | grep -v "help=" | head -20
```

**Go cobra:**
```
grep -rn --include="*.go" -A5 "cobra.Command{" ${1:-.} | grep -v "Short:\|Long:\|Use:" | grep "cobra.Command{" | head -10
```

### 4. Find Undocumented API Endpoints

**FastAPI / Flask (Python):**
```
grep -rn --include="*.py" -B2 "@.*\.(get|post|put|delete|patch)\(" ${1:-.} | \
  grep -v '"""' | grep -v "#" | grep "@" | head -20
```

**Express (JavaScript):**
```
grep -rn --include="*.js" --include="*.ts" -B2 "router\.\(get\|post\|put\|delete\|patch\)" ${1:-.} | \
  grep -v "/\*\*\|//" | grep "router\." | head -20
```

**Go net/http or gin:**
```
grep -rn --include="*.go" -B2 "HandleFunc\|\.GET\|\.POST\|\.PUT\|\.DELETE" ${1:-.} | \
  grep -v "^--$\|//" | grep "HandleFunc\|\.GET\|\.POST" | head -20
```

### 5. Find Undocumented Config Keys and Env Variables

```
# Keys in .env.example or config files
grep -rh --include=".env*" --include="*.env" -E "^[A-Z_]+=.*" ${1:-.} | \
  sed 's/=.*//' | sort -u > /tmp/env_keys.txt

# Check which appear in README or docs
while read key; do
  found=$(grep -rl "$key" README* docs/ 2>/dev/null | wc -l)
  [ "$found" -eq 0 ] && echo "UNDOCUMENTED: $key"
done < /tmp/env_keys.txt
```

### 6. Detect Stale Documentation

Find docs that reference symbols no longer present in the codebase:

```
# Extract function/class names mentioned in docs
grep -roh --include="*.md" --include="*.rst" '`[a-zA-Z_][a-zA-Z0-9_.]*`' docs/ README* 2>/dev/null | \
  sed 's/.*:`\(.*\)`/\1/' | sort -u > /tmp/doc_symbols.txt

# Check which no longer exist in source
while read sym; do
  found=$(grep -r "\b$sym\b" ${1:-.} --include="*.py" --include="*.ts" --include="*.go" 2>/dev/null | grep -v "\.md:" | wc -l)
  [ "$found" -eq 0 ] && echo "STALE REF: $sym"
done < /tmp/doc_symbols.txt | head -20
```

### 7. Rank by Visibility and Usage

For each gap, estimate visibility:

**High visibility** (document first):
- Public API endpoints called by external consumers
- CLI commands shown in README or help output
- Config keys required for deployment
- Classes/functions exported at the package root

**Medium visibility:**
- Internal helpers used by multiple modules
- Secondary CLI subcommands

**Low visibility:**
- Internal utilities used in one place
- Test helpers

Cross-reference with churn: a frequently-changed undocumented function is higher priority than a stable one.

### 8. Inspect Top Candidates

For each high-visibility gap, read the function/class to understand its purpose, parameters, return value, and side effects well enough to write or suggest a docstring.

### 9. Print the Report

```
# Documentation Gaps — {TODAY}

## Summary

- Public symbols scanned: N
- Docstring coverage: X% (N / N documented)
- 🔴 High-visibility gaps: N
- 🟡 Medium-visibility gaps: N
- Stale doc references: N

## High-Visibility Gaps

### Undocumented API Endpoints (N)
| File | Line | Endpoint | Method |
|------|------|----------|--------|

### Undocumented CLI Commands (N)
| File | Command | Missing |
|------|---------|---------|

### Undocumented Config / Env Keys (N)
| Key | Where defined | Action |
|-----|--------------|--------|

### Undocumented Public Functions / Classes (N)
| File | Line | Symbol | Visibility |
|------|------|--------|-----------|

## Stale Documentation References

| Doc file | Symbol referenced | Status |
|----------|------------------|--------|

## Suggested Docstrings

For each high-priority gap, a draft docstring based on reading the implementation:

### `<symbol>` in `<path>:<line>`

\`\`\`python
def foo(bar: str, baz: int = 0) -> dict:
    """<one-line summary>.

    <optional expanded description of non-obvious behavior>

    Args:
        bar: <what it is and valid values>
        baz: <what it is and valid values>

    Returns:
        <what the dict contains>

    Raises:
        ValueError: <when>
    """
\`\`\`

## Quick Wins

3–5 additions that would document the highest-impact surface area for the lowest effort.
```

## Example Usage

**Scenario 1: API surface audit**
```
/doc-gaps src/api
```
Finds 14 undocumented FastAPI endpoints and 3 config keys missing from README. Generates draft docstrings for the 5 highest-traffic routes based on their implementation.

**Scenario 2: Full project scan**
```
/doc-gaps
```
Docstring coverage is 34%. Identifies the public-facing `Client` class and its 8 methods as the top priority since it is the primary entry point for library consumers. Generates draft docstrings for all 8 methods.

**Scenario 3: Pre-release documentation gate**
```
/doc-gaps
```
All API endpoints are documented but 4 new CLI flags added last sprint have no help text. Generates the missing `help=` strings for each flag.

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `interrogate . -v --ignore-private` | Python docstring coverage report |
| `interrogate . --fail-under 80` | Fail if coverage below 80% (CI use) |
| `grep -rn "^export " --include="*.ts"` | Find all TypeScript exports |
| `grep -rn "^func [A-Z]" --include="*.go"` | Find all exported Go functions |
| `grep -rn "add_argument" --include="*.py" \| grep -v "help="` | argparse args missing help text |
