---
name: audit-dependencies
description: Audit project dependencies for outdated versions, known vulnerabilities, unmaintained packages, and license issues, then produce a prioritized upgrade and replacement plan.
allowed-tools: Bash, Read, Glob, Grep
---

TODAY=!`date +%Y-%m-%d`

# Dependency Audit

Audits all direct and transitive dependencies for four risk categories: security vulnerabilities, outdated versions, unmaintained packages, and license incompatibilities. Produces a prioritized action plan that maps directly to the SDLC fast path for dependency updates.

## Prerequisites

- Working directory is the root of the repository
- Package manager manifest present (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, etc.)
- Network access for vulnerability database lookups
- Language-specific tools:
  - Python: `pip-audit` (`uv tool install pip-audit`), `uv` or `pip`
  - JavaScript/TypeScript: `npm audit` or `pnpm audit`
  - Go: `govulncheck` (`go install golang.org/x/vuln/cmd/govulncheck@latest`)
  - Rust: `cargo audit` (`cargo install cargo-audit`)

## Risk Categories

| Category | Priority | Action |
|----------|----------|--------|
| Known CVE (critical/high) | 🔴 Immediate | Upgrade or replace within the sprint |
| Known CVE (medium/low) | 🟡 Soon | Schedule for next sprint |
| Outdated major version | 🟡 Soon | Review changelog, plan upgrade |
| Outdated minor/patch | 🟢 Routine | Batch update |
| Unmaintained (no release > 2 years, archived, or deprecated) | 🟡 Soon | Find replacement |
| License incompatibility | 🔴 Immediate (legal) | Remove or replace |
| Duplicate functionality | 🟢 Routine | Consolidate |

## Steps

### 1. Identify Package Manager(s)

```
ls pyproject.toml requirements*.txt package.json go.mod Cargo.toml 2>/dev/null
```

Handle monorepos by scanning subdirectories:
```
find . -name "pyproject.toml" -o -name "package.json" -o -name "go.mod" -o -name "Cargo.toml" | grep -v node_modules | grep -v ".venv"
```

### 2. Security Vulnerability Scan

**Python:**
```
pip-audit --format=markdown
```

**JavaScript/TypeScript:**
```
npm audit --json 2>/dev/null | jq '.vulnerabilities | to_entries[] | {name: .key, severity: .value.severity, via: .value.via[0].url // "transitive"}'
```
or
```
pnpm audit --json 2>/dev/null
```

**Go:**
```
govulncheck ./...
```

**Rust:**
```
cargo audit
```

### 3. Check for Outdated Packages

**Python (uv):**
```
uv pip list --outdated 2>/dev/null || pip list --outdated --format=columns
```

**Python (direct deps only from pyproject.toml):**
```
cat pyproject.toml | grep -A50 '\[project\]' | grep -E '^\s+"[a-zA-Z]' | \
  sed 's/.*"\([a-zA-Z0-9_-]*\).*/\1/' | \
  xargs -I{} sh -c 'latest=$(pip index versions {} 2>/dev/null | head -1 | sed "s/.*(\(.*\))/\1/"); installed=$(pip show {} 2>/dev/null | grep Version | awk "{print \$2}"); echo "${}  installed=$installed  latest=$latest"'
```

**JavaScript/TypeScript:**
```
npx npm-check-updates --format markdown 2>/dev/null || npm outdated
```

**Go:**
```
go list -m -u all 2>/dev/null | grep '\['
```

**Rust:**
```
cargo outdated 2>/dev/null
```

### 4. Identify Unmaintained Packages

For each direct dependency, check last release date and repository status.

**Python — check PyPI metadata:**
```
pip show <package> | grep Home-page
# Then check: last release on PyPI, GitHub archive status, deprecation notices
```

Signals of abandonment:
- No release in the past 24 months
- Repository archived on GitHub
- PyPI page shows "This project has been archived"
- README says "deprecated" or "use X instead"

**JavaScript — check npm:**
```
npm view <package> time.modified repository.url
```

### 5. License Compliance Check

**Python:**
```
pip-licenses --format=markdown --order=license 2>/dev/null || \
  pip show $(pip list --format=freeze | cut -d= -f1) 2>/dev/null | grep -E "^(Name|License):"
```

**JavaScript:**
```
npx license-checker --summary --production 2>/dev/null
```

Flag licenses that are typically incompatible with proprietary software:
- GPL, AGPL, LGPL (copyleft — may require source disclosure)
- SSPL (Server Side Public License)
- Unknown / no license declared

### 6. Identify Duplicate Functionality

Look for multiple packages solving the same problem:
- Multiple HTTP clients (`requests` + `httpx` + `urllib3` directly)
- Multiple date libraries (`arrow` + `pendulum` + `dateutil`)
- Multiple test runners or assertion libraries

```
cat pyproject.toml package.json 2>/dev/null | grep -E '"[a-z]' | head -40
```

### 7. Prioritize and Plan

Group findings into four action tracks:

**Track 1 — Fix now (this sprint)**
CVEs rated critical or high; license violations.

**Track 2 — Fix soon (next sprint)**
CVEs rated medium/low; unmaintained packages with viable replacements; major version upgrades with breaking changes that need planning.

**Track 3 — Routine batch update**
Outdated minor/patch versions with no known issues.

**Track 4 — Monitor**
Packages that are slightly outdated but actively maintained and stable.

### 8. Print the Report

```
# Dependency Audit — {TODAY}

## Summary

- Dependencies audited: N direct, N transitive
- 🔴 Critical/High CVEs: N
- 🟡 Medium/Low CVEs: N
- Outdated packages: N (N major, N minor/patch)
- Unmaintained packages: N
- License issues: N

## Track 1 — Fix Now

| Package | Installed | Issue | Action |
|---------|-----------|-------|--------|
| `foo` | 1.2.3 | CVE-2024-XXXX (critical) | Upgrade to ≥ 1.4.0 |

## Track 2 — Fix Soon

| Package | Installed | Latest | Issue | Action |
|---------|-----------|--------|-------|--------|

## Track 3 — Batch Update

<list packages suitable for a single "bump all minors" commit>

## Track 4 — Monitor

<packages to revisit in next quarter's audit>

## Replacement Recommendations

| Current | Reason | Recommended replacement |
|---------|--------|------------------------|
| `foo` | Unmaintained since 2021 | `bar` — actively maintained, API-compatible |

## License Issues

| Package | License | Risk | Action |
|---------|---------|------|--------|
```

## Example Usage

**Scenario 1: Routine quarterly audit**
```
/dependency-audit
```
Finds 2 medium CVEs in transitive deps, 8 outdated minor versions, and 1 unmaintained package. Produces a three-track plan; Track 1 is empty so no urgent work needed.

**Scenario 2: Pre-release security gate**
```
/dependency-audit
```
Finds a critical CVE in a direct HTTP library. Immediately creates a Track 1 item; feeds into `/create-issue` → `/sdlc dependency` fast path.

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `pip-audit --format=markdown` | Python vulnerability scan |
| `npm audit --json` | Node.js vulnerability scan |
| `govulncheck ./...` | Go vulnerability scan |
| `cargo audit` | Rust vulnerability scan |
| `pip-licenses --format=markdown` | Python license summary |
| `npx license-checker --summary --production` | JS/TS license summary |
| `npx npm-check-updates` | JS/TS outdated package check |
| `go list -m -u all` | Go module update availability |
