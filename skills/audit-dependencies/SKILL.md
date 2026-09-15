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
| Unsafe version ranges (no upper bound, or over-pinned) | 🟡 Soon | Tighten ranges, add constraints |

## Steps

### 1. Identify Package Manager(s)

```
ls pyproject.toml requirements*.txt package.json go.mod Cargo.toml 2>/dev/null
```

Handle monorepos by scanning subdirectories:
```
find . -name "pyproject.toml" -o -name "package.json" -o -name "go.mod" -o -name "Cargo.toml" | rg -v node_modules | rg -v ".venv"
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

**Forward compatibility check — version range strategy:** review how each dependency is constrained. Ranges with no upper bound can pull a breaking major on resolve; over-pinning to an exact patch blocks security upgrades and future evolution. Flag ranges that are unsafe for forward compatibility and recommend upper bounds or caret/tilde constraints that allow additive upgrades.

**Python (uv):**
```
uv pip list --outdated 2>/dev/null || pip list --outdated --format=columns
```

**Python (direct deps only from pyproject.toml):**
```
cat pyproject.toml | rg -A50 '\[project\]' | rg '^\s+"[a-zA-Z]' | \
  sed 's/.*"\([a-zA-Z0-9_-]*\).*/\1/' | \
  xargs -I{} sh -c 'latest=$(pip index versions {} 2>/dev/null | head -1 | sed "s/.*(\(.*\))/\1/"); installed=$(pip show {} 2>/dev/null | rg Version | awk "{print \$2}"); echo "${}  installed=$installed  latest=$latest"'
```

**JavaScript/TypeScript:**
```
npx npm-check-updates --format markdown 2>/dev/null || npm outdated
```

**Go:**
```
go list -m -u all 2>/dev/null | rg '\['
```

**Rust:**
```
cargo outdated 2>/dev/null
```

### 4. Identify Unmaintained Packages

For each direct dependency, check last release date and repository status.

**Python — check PyPI metadata:**
```
pip show <package> | rg Home-page
# Then check: last release on PyPI, GitHub archive status, deprecation notices
```

Signals of abandonment:
- No release in the past 24 months
- Repository archived on GitHub
- PyPI page shows "This project has been archived"
- README says "deprecated" or "use X instead"

**JavaScript — check npm:**
```
npm vie