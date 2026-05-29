---
name: audit-security
description: Scan the codebase for code-level security vulnerabilities including hardcoded secrets, injection risks, missing auth checks, and insecure patterns, then produce a prioritized remediation plan.
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "[path]"
---

TODAY=!`date +%Y-%m-%d`

# Security Audit

Scans your own code for vulnerabilities — distinct from `/audit-dependencies` which covers external packages. Covers hardcoded secrets, injection patterns, missing authentication and authorization checks, insecure defaults, and other OWASP-class issues. Produces a prioritized remediation plan with severity ratings.

## Prerequisites

- Working directory is the root of the repository
- Optional: `$1` — path to limit the scan (defaults to `.`)
- Language-specific tools (degrades to grep heuristics if unavailable):
  - Any language: `semgrep` (`pip install semgrep` or `brew install semgrep`)
  - Secrets: `trufflehog` (`pip install trufflehog`) or `gitleaks` (`brew install gitleaks`)
  - Python: `bandit` (`uv tool install bandit`)
  - JavaScript/TypeScript: `eslint` with `eslint-plugin-security`
  - Go: `gosec` (`go install github.com/securego/gosec/v2/cmd/gosec@latest`)

## Vulnerability Categories

| Category | Severity | Examples |
|----------|----------|---------|
| Hardcoded secrets | 🔴 Critical | API keys, passwords, tokens in source |
| Injection | 🔴 Critical | SQL, command, LDAP, XPath injection |
| Insecure deserialization | 🔴 Critical | `pickle.loads`, `eval`, `exec` on user input |
| Broken authentication | 🔴 High | Missing auth checks, weak session handling |
| Sensitive data exposure | 🔴 High | PII/secrets logged, transmitted unencrypted |
| Insecure direct object reference | 🟡 High | Missing ownership checks on resource access |
| Security misconfiguration | 🟡 Medium | Debug mode on, permissive CORS, weak TLS |
| Missing authorization | 🟡 Medium | Authenticated but not authorized |
| Cryptography issues | 🟡 Medium | Weak algorithms (MD5, SHA1), hardcoded IVs |
| Dependency confusion | 🟢 Low | Internal package names resolvable publicly |

## Steps

### 1. Detect Language and Available Tools

```
find ${1:-.} -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
command -v semgrep && semgrep --version
command -v bandit && bandit --version
command -v gosec && gosec --version
command -v gitleaks && gitleaks version
command -v trufflehog && trufflehog --version
```

### 2. Scan for Hardcoded Secrets

**gitleaks (preferred — scans git history too):**
```
gitleaks detect --source ${1:-.} --report-format json --report-path .gitleaks-report.json 2>/dev/null
cat .gitleaks-report.json 2>/dev/null | python3 -c "import json,sys; [print(f['RuleID'], f['File'], f['StartLine']) for f in json.load(sys.stdin)]" 2>/dev/null
```

**trufflehog:**
```
trufflehog filesystem ${1:-.} --json 2>/dev/null | head -50
```

**grep fallback:**
```
grep -rn --include="*.py" --include="*.js" --include="*.ts" --include="*.go" --include="*.env*" \
  -iE "(password|secret|api_key|apikey|token|private_key)\s*=\s*['\"][^'\"]{8,}" \
  ${1:-.} | grep -v "test\|spec\|mock\|example\|placeholder\|your_" | head -30
```

Also check for secrets accidentally committed in config files:
```
grep -rn --include="*.yaml" --include="*.yml" --include="*.json" --include="*.toml" \
  -iE "(password|secret|token|key)\s*:\s*['\"]?[A-Za-z0-9+/]{16,}" \
  ${1:-.} | grep -v "test\|example\|template" | head -20
```

### 3. Run Language-Specific Scanners

**Python — bandit:**
```
bandit -r ${1:-.} -f json -o .bandit-report.json 2>/dev/null
bandit -r ${1:-.} -ll 2>/dev/null | tail -40
```

**JavaScript/TypeScript — semgrep with security ruleset:**
```
semgrep --config=p/javascript --config=p/typescript --json --output .semgrep-report.json ${1:-.} 2>/dev/null
```

**Go — gosec:**
```
gosec -fmt=json -out=.gosec-report.json ./... 2>/dev/null
gosec -severity medium ./... 2>/dev/null | tail -40
```

**Any language — semgrep OWASP ruleset:**
```
semgrep --config=p/owasp-top-ten --config=p/secrets --json --output .semgrep-owasp.json ${1:-.} 2>/dev/null
```

### 4. Check for Injection Vulnerabilities

**SQL injection:**
```
grep -rn --include="*.py" --include="*.js" --include="*.ts" --include="*.go" \
  -E '(execute|query|cursor\.execute|db\.query)\s*\(\s*[f"'"'"']|\.format\s*\(' \
  ${1:-.} | grep -i "select\|insert\|update\|delete\|where" | head -20
```

**Command injection:**
```
grep -rn --include="*.py" --include="*.js" --include="*.ts" \
  -E "(os\.system|subprocess\.(call|run|Popen)|exec\(|eval\(|child_process)" \
  ${1:-.} | grep -v "shell=False\|#" | head -20
```

**Insecure deserialization:**
```
grep -rn --include="*.py" \
  -E "(pickle\.loads|yaml\.load\s*\([^,)]+\)|eval\s*\(|exec\s*\()" \
  ${1:-.} | grep -v "yaml\.safe_load\|#" | head -20
```

### 5. Check Authentication and Authorization

Find route/endpoint definitions and check for missing auth decorators:

**Python (Flask/FastAPI):**
```
grep -rn --include="*.py" -B2 \
  -E "@(app|router)\.(get|post|put|delete|patch)\(" \
  ${1:-.} | grep -v "login_required\|current_user\|Depends\|authenticate\|#" | head -30
```

**Express (JavaScript):**
```
grep -rn --include="*.js" --include="*.ts" -B3 \
  -E "router\.(get|post|put|delete|patch)\(" \
  ${1:-.} | grep -v "auth\|middleware\|protect\|verify\|#" | head -30
```

### 6. Check for Sensitive Data in Logs

```
grep -rn --include="*.py" --include="*.js" --include="*.ts" --include="*.go" \
  -iE "(log|logger|print|console\.log)\s*\(.*?(password|token|secret|credit_card|ssn|api_key)" \
  ${1:-.} | grep -v "test\|spec\|#" | head -20
```

### 7. Check Cryptography

```
grep -rn --include="*.py" --include="*.js" --include="*.ts" \
  -iE "(md5|sha1|des\b|rc4|random\(\)|Math\.random)" \
  ${1:-.} | grep -v "test\|comment\|#\|//" | head -20
```

### 8. Check Security Configuration

```
# Debug mode enabled
grep -rn --include="*.py" --include="*.js" --include="*.ts" \
  -E "DEBUG\s*=\s*True|debug\s*:\s*true" ${1:-.} | grep -v "test\|spec" | head -10

# Permissive CORS
grep -rn --include="*.py" --include="*.js" --include="*.ts" \
  -iE "allow_origins\s*=\s*\[?\s*['\"]?\*|cors\s*\(\s*\{.*origin.*\*" \
  ${1:-.} | head -10

# SSL verification disabled
grep -rn --include="*.py" \
  -E "verify\s*=\s*False|ssl_verify\s*=\s*False" \
  ${1:-.} | grep -v "test\|#" | head -10
```

### 9. Deduplicate and Prioritize

Filter false positives:
- Exclude test files, fixtures, and example configs unless they contain real credentials
- Exclude findings suppressed with `# nosec`, `// eslint-disable`, or equivalent
- Confirm injection findings are actually reachable with user-controlled input

Rank by severity using CVSS-inspired categories: Critical > High > Medium > Low.

### 10. Print the Report

```
# Security Audit — {TODAY}

## Summary

- Files scanned: N
- 🔴 Critical findings: N
- 🔴 High findings: N
- 🟡 Medium findings: N
- 🟢 Low findings: N
- Tools used: <semgrep / bandit / gosec / grep heuristics>

## Critical & High Findings

### 1. Hardcoded Secret — `<file>:<line>`
**Severity:** Critical
**Finding:** API key for <service> hardcoded in source
**Risk:** Anyone with read access to the repo can use this credential
**Fix:** Move to environment variable; rotate the exposed key immediately

### 2. SQL Injection — `<file>:<line>`
…

## Medium Findings

…

## Recommended Remediation Order

1. Rotate any exposed secrets immediately (before any code changes)
2. Fix injection vulnerabilities
3. Add missing auth checks
4. Address cryptography issues
5. Fix configuration issues

## False Positives Excluded

- `<finding>`: <reason excluded>
```

## Example Usage

**Scenario 1: Routine quarterly scan**
```
/audit-security
```
Finds 2 hardcoded API keys in a config file committed two years ago, 1 SQL injection in a legacy query, and permissive CORS on a staging endpoint. Recommends rotating keys immediately and parameterizing the query.

**Scenario 2: Pre-release gate**
```
/audit-security src/api
```
Scans only the API layer before a public launch. Finds 3 endpoints missing authorization checks.

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `bandit -r . -ll` | Python security scan, medium severity and above |
| `semgrep --config=p/owasp-top-ten .` | OWASP Top 10 scan (any language) |
| `semgrep --config=p/secrets .` | Secret detection via semgrep |
| `gosec ./...` | Go security scan |
| `gitleaks detect --source .` | Secret scan including git history |
| `trufflehog filesystem .` | High-signal secret detection |
