---
name: audit-usability
description: Audit the software's interfaces (CLI, API, and web UI) for usability, the ISO/IEC 25010 characteristic covering recognizability, learnability, operability, user error protection, and accessibility. Finds missing help text, inconsistent flags, poor error messages, missing confirmations on destructive actions, and static accessibility gaps. Use when the user says /audit-usability, "CLI UX audit", "API ergonomics", "accessibility check", "error message quality", or runs a 25010 sweep via /audit-sdlc. Read-only; produces a findings report.
argument-hint: "[--surface cli|api|web|all] [--severity critical|high|medium|low]"
allowed-tools: Bash, Read, Glob, Grep
---

TODAY=!`date +%Y-%m-%d`

# Usability Audit (ISO/IEC 25010)

Audits the software's **interfaces** for usability: how easily the intended users can recognize what it does, learn it, operate it, recover from errors, and (for web UIs) access it. It treats the CLI, the API, and any web surface as the product's usability surface.

This is the **Usability** characteristic of the [ISO/IEC 25010](https://en.wikipedia.org/wiki/ISO/IEC_25010) quality model. It applies to user-facing software; for libraries with no CLI/API/UI surface, report "no usability surface" and exit.

## Prerequisites

- Working directory is the root of the repository
- Read `.sdlc/context/project-overview.md` if present (to identify the intended audience and surface)
- Determine the surface(s): CLI (argparse/click/typer/cobra), API (HTTP routes), or web (templates/components)

## What This Checks

| Sub-characteristic | What it means | Signals scanned |
|---|---|---|
| Recognizability | users can tell what the software does | README purpose statement; `--help`/`-h` support; API docs (OpenAPI) or README |
| Learnability | new users can get started | examples in help/docs; a getting-started/quickstart; consistent flag/command naming |
| Operability | users can control and observe behavior | sensible defaults; consistent exit codes; `--version`; verbose/dry-run flags; structured logs |
| User error protection | the system prevents and recovers from user mistakes | input validation with actionable messages; confirmation prompts on destructive actions; safe defaults for dangerous flags |
| User engagement | relevant and satisfying to use | (mostly out of static scope; flag missing progress indication for long operations) |
| Accessibility (web) | usable by people with diverse abilities | `alt` text on images; form `label` associations; ARIA roles where needed; sufficient contrast (static subset); keyboard-reachable interactive elements |

## Steps

### 1. Identify the surface

```
grep -rEn "argparse|click\.command|typer|cobra\.Command|@app\.command|yargs|commander" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" .
grep -rEn "@(app|router)\.(get|post|put|delete|patch|route)" --include="*.py" --include="*.ts" --include="*.js" .
ls src/components app/templates templates 2>/dev/null
```

Record which surfaces exist. If none, report "no usability surface" and stop.

### 2. Recognizability

- CLI: does every command have help? Missing `-h`/`--help` or empty help strings:
  ```
  grep -rEn "add_parser|@click|@app\.command|add_argument" --include="*.py" . | grep -v "help="
  ```
- API: is there an OpenAPI spec or documented endpoints?
  ```
  ls openapi.yaml openapi.json swagger.* 2>/dev/null
  grep -rEn "FastAPI|apispec|flask-restx|springdoc" --include="*.py" --include="*.java" .
  ```
- README states what the software does (first heading + first paragraph).

### 3. Learnability

- Examples present in help or docs (`examples/`, `--example`, usage strings).
- Quickstart in README.
- Naming consistency: do commands/flags follow one convention? Mixed styles (kebab + snake + camel across flags) is a finding.

### 4. Operability

- `--version` support:
  ```
  grep -rEn "version|--version|show_version" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" .
  ```
- Exit codes: handlers that `sys.exit(0)` on error, or exit non-zero without a reason; inconsistent exit codes across commands.
- Defaults: required arguments that could have safe defaults; dangerous operations without a dry-run.

### 5. User error protection

- Input validation present on user-facing inputs (see `audit-compatibility` step 6 for overlap; here focus on the *message* quality).
- Error messages that are actionable: flag bare `raise Exception("...")`, `print("error")`, `console.error` without a remediation hint.
  ```
  grep -rEn "raise (Exception|ValueError|RuntimeError)\(['\"]" --include="*.py" .
  grep -rEn "console\.error\(|print\(['\"]?(error|Error|ERROR)" --include="*.ts" --include="*.js" .
  ```
- Destructive operations (`delete`, `drop`, `purge`, `rm`, `reset`) without a confirmation or a `--force`/`--yes` gate:
  ```
  grep -rEn "delete|drop|purge|remove|reset|destroy|rm -" --include="*.py" --include="*.ts" --include="*.js" . | grep -v "confirm\|--force\|--yes\|-y\|dry.run\|test"
  ```

### 6. Accessibility (web surface only)

Static-checkable subset:
```
grep -rEn "<img" --include="*.html" --include="*.jsx" --include="*.tsx" --include="*.vue" . | grep -v "alt="
grep -rEn "<input" --include="*.html" --include="*.jsx" --include="*.tsx" . | grep -v -E "id=|aria-label|<label"
grep -rEn "onclick=|onClick=" --include="*.html" --include="*.jsx" --include="*.tsx" . 
```
Flag images without `alt`, inputs without an associated label, click-only handlers with no keyboard equivalent.

### 7. Report

Classify by severity and print. Note that some usability issues (contrast, copy quality) need human judgment; surface the static-checkable subset and flag the rest as "manual review".

## Severity

| Severity | Criteria |
|---|---|
| Critical | Destructive operation with no confirmation and no dry-run; a public command with no help at all |
| High | Error messages that do not tell the user how to recover; required inputs with no validation; web images missing alt at scale |
| Medium | Missing `--version`; inconsistent flag naming; missing quickstart |
| Low | Missing examples in help; minor naming inconsistency |

## Output Format

```
# Usability Audit — {TODAY}

## Summary
- Surface(s): CLI / API / web
- Recognizability findings: N
- Learnability findings: N
- Operability findings: N
- User error protection findings: N critical, N high
- Accessibility findings (web): N

## Recognizability
| Surface | Item | Issue | Severity |
|---|---|---|---|

## Operability
| File:line | Issue | Severity |
|---|---|---|

## User error protection
### Error message quality
| File:line | Message | Severity | Suggested rewrite |
|---|---|---|---|

### Destructive operations
| File:line | Operation | Guarded? | Severity |
|---|---|---|---|

## Accessibility (web)
| File:line | Element | Issue | Severity |
|---|---|---|---|

## Manual review (not statically checkable)
- Copy clarity, contrast, visual hierarchy, onboarding flow
```

## Example Usage

**Scenario 1: 25010 sweep**
```
/audit-sdlc usability
```

**Scenario 2: CLI-only project**
```
/audit-usability --surface cli
```

**Scenario 3: Before a public API release**
```
/audit-usability --surface api
```

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `audit-security`, `audit-functional-suitability`, `audit-performance-efficiency`, `audit-compatibility`, `audit-reliability`, `audit-maintainability`, `audit-portability` | The other seven ISO/IEC 25010 characteristics. Compose via `/audit-sdlc`. |
| `audit-sdlc` | Coordinator. |
| `audit-compatibility` | Overlaps on input validation; coordinate to dedup (validation gaps live in compatibility, message quality lives here). |
| `create-mockups` / `review-mockups` | Design-time UI work. This is the audit of an existing UI surface. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `grep -rEn "argparse\|click\.command\|@app\.command" --include="*.py" . \| grep -v "help="` | Commands missing help |
| `grep -rEn "raise (Exception\|ValueError)\(['\"]" --include="*.py" .` | Low-quality error messages |
| `grep -rEn "delete\|drop\|purge\|reset" --include="*.py" . \| grep -v "confirm\|--force"` | Unguarded destructive ops |
| `grep -rEn "<img" --include="*.html" --include="*.tsx" . \| grep -v "alt="` | Images missing alt text |
