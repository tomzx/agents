---
name: audit-portability
description: Audit the codebase for portability, the ISO/IEC 25010 characteristic covering adaptability (runs in different environments), installability (easy to install), and replaceability (easy to swap out or migrate off). Finds hardcoded paths/hosts/OS assumptions, config baked into code (violating 12-factor), vendor lock-in, missing containerization/install tooling, and non-standard data formats that block migration. Use when the user says /audit-portability, "lock-in audit", "12-factor check", "can it run elsewhere", "migration readiness", or runs a 25010 sweep via /audit-sdlc. Read-only; produces a findings report.
argument-hint: "[--severity critical|high|medium|low]"
allowed-tools: Bash, Read, Glob, Grep
---

TODAY=!`date +%Y-%m-%d`

# Portability Audit (ISO/IEC 25010)

Audits the codebase for **portability**: can the software be adapted to a new environment, installed easily, and replaced or migrated off without lock-in? It finds the assumptions that make software brittle to relocation and hard to leave.

This is the **Portability** characteristic of the [ISO/IEC 25010](https://en.wikipedia.org/wiki/ISO/IEC_25010) quality model. Distinct from `audit-compatibility` (runs *alongside* other software and speaks standards), this is about running in a different *environment* and being *replaceable*.

## Prerequisites

- Working directory is the root of the repository
- Read `.sdlc/context/architecture.md` and `.sdlc/context/project-overview.md` if present (for declared target environments and providers)

## What This Checks

| Sub-characteristic | What it means | Signals scanned |
|---|---|---|
| Adaptability | runs in different environments without modification | hardcoded absolute paths, hostnames, IPs, OS-specific code without abstraction, config baked into code (violating 12-factor), platform-specific dependencies (C extensions, native bins) |
| Installability | easy to install in a new environment | install/setup docs, containerization, package manifest, declared system requirements, pinned vs floating deps |
| Replaceability | easy to swap out or migrate data off | vendor/provider lock-in without an abstraction, proprietary data formats, no standard data-export or API, missing OpenAPI/schema |

## Steps

### 1. Adaptability: environment assumptions

Hardcoded absolute paths and OS-specific locations:
```
rg -n "/usr/|/var/|/tmp/|/etc/|/opt/|C:\\\\|/home/|/Users/" -g '*.{py,ts,js,go}' . \
  | rg -v "test|spec|example|docs|README|node_modules|\.venv"
```
Hardcoded hostnames and IPs:
```
rg -n "https?://[a-zA-Z0-9.-]+|\\b[0-9]{1,3}(\\.[0-9]{1,3}){3}\\b" -g '*.{py,ts,js}' . \
  | rg -v "localhost|0\.0\.0\.0|example\.com|test|spec|127\.0\.0\.1"
```
OS-specific code and shell calls without abstraction:
```
rg -n "os\.name|platform\.|sys\.platform|subprocess\.(run|call|Popen)\(|os\.system\(" -g '*.py' .
rg -n "shelljs|execSync|child_process" -g '*.{ts,js}' .
```

### 2. Adaptability: 12-factor config

Configuration baked into code rather than environment. Flag hardcoded credentials, connection strings, feature toggles, and tuning constants that should be env/config:
```
rg -n "(password|secret|token|api_key|apikey|connection_string|dsn|url)\s*[:=]\s*['\"][^'\"]+['\"]" -g '*.{py,ts,js}' . \
  | rg -v "test|spec|example|os\.environ|getenv|process\.env|config\.|settings\."
```

### 3. Adaptability: platform-specific dependencies

Native/C-extension and platform-bound deps that block cross-platform or cross-arch:
```
rg -n "cuda|tensorflow|torch|pywin32|win32|libc|apt-get|yum|brew install|dylib|\.dll|\.so|\.dylib" -g '*.{py,ts,js,go}' .
```
(Flag, don't condemn: some are intentional. Record the platform assumption.)

### 4. Installability

- Containerization present:
  ```
  ls Dockerfile docker-compose.yml Containerfile 2>/dev/null
  ```
- Install/setup docs:
  ```
  ls INSTALL* GETTING_STARTED* 2>/dev/null; rg -n "^## (Install|Setup|Getting Started)" README.md 2>/dev/null
  ```
- Package manifest declares the runtime/version (engines, requires-python, go version):
  ```
  rg -n "requires-python|engines|go [0-9]" pyproject.toml package.json go.mod 2>/dev/null
  ```
- Deps over-pinned (blocks install in a different resolved environment) or under-pinned (pulls a breaking major): coordinate with `audit-compatibility`.

### 5. Replaceability: vendor lock-in

Direct, scattered use of a cloud/provider SDK with no abstraction layer (every call site couples to that provider):
```
rg -n "boto3\.|aws_|google\.cloud|azure\.|firebase\.|stripe\.|twilio\.|s3\.|dynamodb|cloudsql" -g '*.{py,ts,js}' .
```
Count distinct call sites per provider. A provider used directly across many modules is lock-in; one used behind a single interface/adaptor is fine.

### 6. Replaceability: data egress and standards

Can data be exported in a standard format, and is there a documented schema/API to migrate off?
```
ls openapi.yaml openapi.json schema.* 2>/dev/null
rg -n "export|dump|backup|csv|json|parquet" -g '*.{py,ts,js}' . | rg -i "endpoint|route|command|cli"
```
Proprietary/unversioned storage formats are replaceability findings.

### 7. Report

Classify by severity and print. Do not modify files.

## Severity

| Severity | Criteria |
|---|---|
| Critical | Hardcoded production credentials/DSNs in code; data locked in a proprietary format with no export |
| High | Hardcoded provider SDK used across many modules with no abstraction (deep lock-in); no containerization and no install docs for a service |
| Medium | Hardcoded absolute path; OS-specific code without abstraction; missing runtime version declaration |
| Low | Platform-specific optional dependency; minor config-in-code |

## Output Format

```
# Portability Audit — {TODAY}

## Summary
- Adaptability findings: N critical, N high
- Installability findings: N
- Replaceability findings: N critical, N high
- Target environments (from architecture.md): <list or "undeclared">

## Adaptability
### Environment assumptions
| File:line | Assumption | Type (path/host/OS/config) | Severity | Recommendation |
|---|---|---|---|---|

### 12-factor config violations
| File:line | What's baked in | Severity |
|---|---|---|

### Platform-specific dependencies
| Dependency | Platform bound | Severity |
|---|---|---|

## Installability
| Item | Present? | Severity |
|---|---|---|
| Containerfile | yes/no | |
| Install docs | yes/no | |
| Runtime version declared | yes/no | |

## Replaceability
### Vendor lock-in
| Provider | Direct call sites | Abstracted? | Severity |
|---|---|---|---|

### Data egress / standards
| Artifact | Present? | Severity |
|---|---|---|
| OpenAPI/schema | yes/no | |
| Standard export | yes/no | |
```

## Example Usage

**Scenario 1: 25010 sweep**
```
/audit-sdlc portability
```

**Scenario 2: Before migrating cloud providers**
```
/audit-portability
```
Quantifies the lock-in (call sites per provider) to scope a migration.

**Scenario 3: Before open-sourcing / distributing**
```
/audit-portability
```
Surfaces hardcoded paths, credentials, and missing install tooling that block others from running it.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `audit-security`, `audit-functional-suitability`, `audit-performance-efficiency`, `audit-compatibility`, `audit-usability`, `audit-reliability`, `audit-maintainability` | The other seven ISO/IEC 25010 characteristics. Compose via `/audit-sdlc`. |
| `audit-sdlc` | Coordinator. |
| `audit-security` | Overlaps on hardcoded credentials; coordinate to dedup (secrets live in security, environment-portability here). |
| `audit-compatibility` | Related but distinct: compatibility = co-existence + interop; portability = adaptability + installability + replaceability. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `rg -n "/usr/\|/tmp/\|/var/\|C:\\\\" -g '*.py' .` | Hardcoded absolute paths |
| `rg -n "(password\|secret\|token\|dsn)\s*[:=]\s*['\"]" -g '*.py' . \| rg -v "os\.environ\|getenv"` | Config baked into code |
| `rg -n "boto3\.\|google\.cloud\|azure\.\|stripe\." -g '*.py' .` | Direct cloud/provider SDK usage |
| `ls Dockerfile docker-compose.yml Containerfile 2>/dev/null` | Containerization present |
