---
name: security-reviewer
description: Audit a pull request or code change for security vulnerabilities.
argument-hint: "<pr-number-or-file-path>"
---

# Security Reviewer

Performs a targeted security audit of a code change, covering OWASP Top 10 and common implementation vulnerabilities. Produces findings with severity ratings and actionable remediation.

## Prerequisites

- Pull request diff or file path available
- `gh` CLI available if reviewing a GitHub PR

## Steps

1. Fetch the change:
   - PR: `gh pr diff $1`
   - File: read directly
2. Review against each category below.
3. For every finding, record: location, severity, description, and remediation.
4. Produce the findings report.

## Review Categories

### Input Validation
- Are all external inputs (user, API, file, env) validated and sanitized?
- Are boundary conditions and null/empty cases handled?
- Is input length bounded to prevent DoS via large payloads?

### Authentication and Authorization
- Are authentication checks present on all protected routes?
- Is authorization enforced at the resource level (not just the route)?
- Are session tokens generated securely (sufficient entropy, proper expiry)?

### Injection
- Are all database queries parameterized (no string concatenation)?
- Is user input escaped before rendering in HTML (XSS)?
- Are shell commands constructed safely (no unsanitized interpolation)?

### Secrets and Credentials
- No hardcoded secrets, API keys, or passwords in code or config?
- Are secrets loaded from environment variables or a secrets manager?

### Data Exposure
- Is PII logged, returned in API responses, or stored beyond its retention period?
- Are error messages sanitized before returning to the client?
- Is sensitive data encrypted at rest and in transit?

### Dependency Security
- Are new dependencies from reputable sources?
- Are pinned versions checked against known CVEs?

### Cryptography
- Are approved algorithms used (no MD5, SHA-1 for security purposes, no ECB mode)?
- Are cryptographic keys of sufficient length?

## Severity Ratings

- **CRITICAL:** Exploitable without authentication; immediate data breach or system compromise.
- **HIGH:** Exploitable with minimal privilege; significant data or system risk.
- **MEDIUM:** Requires specific conditions; limited blast radius.
- **LOW:** Best-practice violation; low likelihood or impact.
- **INFO:** Observation worth noting; no direct risk.

## Output Format

```markdown
## Security Review: <PR or File>

### Findings

#### SEC-1: <Title> [CRITICAL|HIGH|MEDIUM|LOW|INFO]
**Location:** file.py:line
**Description:** What the vulnerability is and how it could be exploited.
**Remediation:** Specific change required to fix it.

### Summary
- Critical: N
- High: N
- Medium: N
- Low: N
- Info: N
```

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr diff <pr-number>` | Fetch the full PR diff |
| `gh pr view <pr-number> --comments` | View existing review comments |
