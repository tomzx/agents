---
name: audit-compatibility
description: Audit the codebase for compatibility, the ISO/IEC 25010 characteristic covering co-existence (running alongside other software without conflict) and interoperability (exchanging data via standards). Finds hardcoded shared resources, dependency conflicts, missing API versioning, non-standard data formats, and brittle integrations. Use when the user says /audit-compatibility, "interop audit", "co-existence", "API versioning check", "standards compliance", or runs a 25010 sweep via /audit-sdlc. Read-only; produces a findings report.
argument-hint: "[--severity critical|high|medium|low]"
allowed-tools: Bash, Read, Glob, Grep
---

TODAY=!`date +%Y-%m-%d`

# Compatibility Audit (ISO/IEC 25010)

Audits the codebase for **compatibility**: can the software co-exist with other software and interoperate with them through standards? It finds the things that make two systems fight over shared resources or fail to talk to each other cleanly.

This is the **Compatibility** characteristic of the [ISO/IEC 25010](https://en.wikipedia.org/wiki/ISO/IEC_25010) quality model.

## Prerequisites

- Working directory is the root of the repository
- Read `.sdlc/context/architecture.md` if present (for integration boundaries)
- Package manifest present for dependency-conflict checks (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`)

## What This Checks

| Sub-characteristic | What it means | Signals scanned |
|---|---|---|
| Co-existence | runs alongside other software without resource or dependency conflict | hardcoded ports/paths/hostnames; well-known shared resources (`/tmp`, fixed DB names); global mutable state; dependency version conflicts; over-pinned or conflicting transitive deps |
| Interoperability | exchanges data and uses standards correctly | missing API versioning; non-standard content types/charsets; unversioned data formats; missing schema validation on inputs/outputs; brittle string-parsing of external data; incorrect HTTP status codes |

## Steps

### 1. Co-existence: shared resources

Hardcoded ports, hostnames, absolute paths, and well-known shared locations that collide when two instances or two apps run together:

```
rg -n "localhost|127\.0\.0\.1|0\.0\.0\.0|:3000|:8080|:5432|:6379|:5672|/tmp/|/var/|/usr/|C:\\\\" -g '*.{py,ts,js,go}' . \
  | rg -v "test|spec|example|docs|README"
```

Flag hardcoded values that should be configurable (env vars, config). Two instances on the same host cannot both bind a hardcoded port or write to a hardcoded path.

Fixed resource names (DB names, queue names, cache keys without a prefix/namespacing):
```
rg -n "CREATE DATABASE|database=|DB_NAME|queue|exchange|routing_key" -g '*.{py,ts,sql}' .
```

### 2. Co-existence: dependency conflicts

Over-pinned exact versions and conflicting transitive ranges. Exact pins block co-installation with software needing a different version; unbounded ranges can pull a breaking major.

```
rg -n "==[0-9]|\"[a-z@/-]+\": *\"[0-9]" pyproject.toml requirements*.txt package.json 2>/dev/null
```

Use the language tool to detect conflicts:
```
uv pip tree --duplicates 2>/dev/null || pip check
npm ls --all 2>/dev/null | rg -i "deduped|invalid|missing"
```

### 3. Co-existence: global mutable state

Module-level mutable state that breaks under concurrency or co-hosting:
```
rg -n "^[_a-zA-Z]+ *:? *= *\[\]|^[_a-zA-Z]+ *:? *= *\{\}|^_cache|^_state|^_registry" -g '*.py' .
```

### 4. Interoperability: API versioning

Endpoints without a version prefix (`/v1/`, version header, or content negotiation). Unversioned APIs cannot evolve compatibly:
```
rg -n "@(app|router)\.(get|post|put|delete|patch|route)\(['\"]" -g '*.py' . | rg -v "/v[0-9]"
```

### 5. Interoperability: content types and encoding

Responses or requests not setting/explicit content types; missing charset on text; JSON parsed without encoding guards:
```
rg -n "json\.loads\(|JSON\.parse\(|Response\(|jsonify" -g '*.{py,ts}' .
rg -n "Content-Type|content_type|mimetype|charset" -g '*.{py,ts}' .
```

### 6. Interoperability: schema validation

Inputs consumed without schema validation (trusting external data):
```
rg -n -B2 "request\.(json|data|form|args|body)|req\.(body|query|params)|event\[" -g '*.{py,ts,js}' . | rg -v "validate|schema|pydantic|zod|joi|serde"
```

### 7. Interoperability: brittle external-data handling

Regex/string parsing of structured external data instead of a proper parser; hardcoded magic offsets/indices into external payloads.

### 8. Interoperability: HTTP status correctness

Handlers returning 200 for created resources (should be 201), 200 for async-accepted work (should be 202), 200 for errors, or generic 400/500 where a specific code applies:
```
rg -n "status_code\s*=\s*(200|400|500)|return.*200|\.send\(200\)|res\.(status\()?200" -g '*.{py,ts,js}' .
```

### 9. Report

Classify by severity and print. Do not modify files.

## Severity

| Severity | Criteria |
|---|---|
| Critical | Dependency conflict that breaks install; consuming external input with no validation on a public endpoint |
| High | Hardcoded port/path preventing co-existence; unversioned public API; wrong content type on a public response |
| Medium | Over-pinned exact version; missing charset; generic HTTP status where specific applies |
| Low | Missing namespace prefix on a cache key; brittle-but-isolated string parse |

## Output Format

```
# Compatibility Audit — {TODAY}

## Summary
- Co-existence findings: N critical, N high
- Interoperability findings: N critical, N high
- Dependency conflicts: N

## Co-existence
### Shared resources
| File:line | Resource | Hardcoded value | Severity | Recommendation |
|---|---|---|---|---|

### Dependency conflicts
| Package | Conflict | Severity | Recommendation |
|---|---|---|---|

### Global mutable state
| File:line | Symbol | Severity |
|---|---|---|

## Interoperability
### API versioning
| Endpoint | Versioned? | Severity |
|---|---|---|

### Schema validation gaps
| Endpoint | Input | Validated? | Severity |
|---|---|---|---|

### HTTP status issues
| File:line | Used | Expected | Severity |
|---|---|---|---|
```

## Example Usage

**Scenario 1: 25010 sweep**
```
/audit-sdlc compatibility
```

**Scenario 2: Before opening a public API**
```
/audit-compatibility
```
Confirms versioning, content types, and input validation before external consumers depend on it.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `audit-security`, `audit-functional-suitability`, `audit-performance-efficiency`, `audit-usability`, `audit-reliability`, `audit-maintainability`, `audit-portability` | The other seven ISO/IEC 25010 characteristics. Compose via `/audit-sdlc`. |
| `audit-sdlc` | Coordinator. |
| `audit-dependencies` | Deeper dependency drill-down (CVEs, outdated). This audit flags conflicts and pins that block co-existence. |
| `audit-portability` | Related but distinct: portability = runs in different environments; compatibility = runs alongside other software and talks standards. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `rg -n "localhost\|127\.0\.0\.1\|:8080\|/tmp/" -g '*.py' .` | Hardcoded shared resources |
| `uv pip tree --duplicates` / `npm ls --all` | Dependency conflicts |
| `rg -n "@(app\|router)\.(get\|post)" -g '*.py' . \| rg -v "/v[0-9]"` | Unversioned endpoints |
| `pip check` | Installed-package conflicts |
