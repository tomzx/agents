---
name: audit-sdlc
description: Run multiple audit skills against the project and produce a unified findings report with prioritized action items.
argument-hint: "[scope: all | diagnose | harden | clean | observe | comma-separated skill names]"
---

# Audit SDLC

Orchestrates multiple audit skills against the project and produces a unified findings report ranked by severity and impact. Optionally feeds the highest-priority findings into issue creation.

Runs audit skills that scan code, dependencies, and infrastructure. Does not modify any files. Safe to run at any time.

## Prerequisites

- Working directory is the root of the repository
- `.sdlc/` directory exists (run `/sync-sdlc` first if not)
- Read any files present under `.sdlc/context/` for project-level context

## Audit Skills by Category

### Diagnose

Surface what is risky or actively unstable.

| Skill | What it finds |
|---|---|
| `audit-dependencies` | CVEs, outdated packages, unmaintained dependencies, license issues |
| `audit-security` | Hardcoded secrets, injection risks, missing auth, insecure patterns |
| `analyze-git-churn` | High-churn files indicating instability or code that needs refactoring |

### Harden

Reduce structural risk before changing code.

| Skill | What it finds |
|---|---|
| `find-complexity-hotspots` | High cyclomatic complexity, excessive length, deep nesting |
| `find-type-gaps` | Missing type annotations |
| `find-coverage-gaps` | Missing or insufficient test coverage |

### Clean

Remove what no longer belongs.

| Skill | What it finds |
|---|---|
| `find-dead-code` | Unused functions, classes, variables, exports, feature flags |
| `find-code-duplication` | Copy-pasted blocks and near-duplicate logic |

### Observe

Monitor production health and surface runtime issues.

| Skill | What it finds |
|---|---|
| `observe-production` | Current SLO status, error rates, latency, throughput |
| `audit-observability` | Missing logging, metrics, tracing, and alerting |

## Scopes

The `$1` argument controls which skills run. Defaults to `diagnose` if not specified.

| Scope | Skills run |
|---|---|
| `all` | Every skill listed above |
| `diagnose` | `audit-dependencies`, `audit-security`, `analyze-git-churn` |
| `harden` | `find-complexity-hotspots`, `find-type-gaps`, `find-coverage-gaps` |
| `clean` | `find-dead-code`, `find-code-duplication` |
| `observe` | `observe-production`, `audit-observability` |
| `security` | `audit-security`, `audit-dependencies` |
| `quality` | `find-complexity-hotspots`, `find-coverage-gaps`, `find-dead-code` |
| Comma-separated | Specific skills, e.g. `audit-security,find-dead-code` |

## Steps

1. Parse `$1` to determine which skills to run. Default to `diagnose`.
2. Read `.sdlc/context/` files for project-level context.
3. For each skill in the resolved scope:
   a. Invoke the skill, passing through any relevant arguments.
   b. Capture its findings in a structured format.
4. Merge all findings into a single unified report.
5. Rank findings by priority using the Severity Classification below.
6. Write the unified report to `.sdlc/audit-report.md`.
7. Present the summary to the user.
8. Ask the user whether to create issues for the highest-priority findings.

## Severity Classification

Each finding from every skill is mapped to a unified severity:

| Severity | Criteria | SDLC Action |
|---|---|---|
| 🔴 **Critical** | Active security vulnerability, data loss risk, production outage | Create issue immediately, fast path to fix |
| 🟠 **High** | Significant risk if unaddressed, degrading quality, no test coverage on critical paths | Create issue, schedule this sprint |
| 🟡 **Medium** | Moderate risk, technical debt accumulating, missing instrumentation | Create issue, schedule next sprint |
| 🟢 **Low** | Minor improvement, cleanup, code style | Batch into a single cleanup issue |

## Output Format

The unified report is written to `.sdlc/audit-report.md`:

```markdown
---
date: "<YYYY-MM-DD>"
scope: "<scope that was run>"
status: complete
---

# Audit Report — <Project Name>

**Date:** <YYYY-MM-DD>
**Scope:** <scope name, list of skills run>

## Summary

| Category | 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low | Total |
|---|---|---|---|---|---|
| Security | N | N | N | N | N |
| Dependencies | N | N | N | N | N |
| Code Quality | N | N | N | N | N |
| Test Coverage | N | N | N | N | N |
| Observability | N | N | N | N | N |
| Dead Code | N | N | N | N | N |
| Churn | N | N | N | N | N |
| **Total** | **N** | **N** | **N** | **N** | **N** |

## Critical Findings

### 1. <Title>
**Source:** <skill name>
**Location:** `<file>:<line>` or <service>
**Finding:** <what was found>
**Risk:** <impact if unaddressed>
**Recommendation:** <what to do>

## High Findings

### 1. <Title>
...

## Medium Findings

...

## Low Findings

...

## Skill Reports

<Links or references to the detailed output from each individual skill>

## Recommended Actions

| Priority | Action | Issue |
|---|---|---|
| 🔴 | <action description> | <issue link or "Not yet created"> |
| 🟠 | <action description> | <issue link or "Not yet created"> |
```

## Deduplication

When multiple skills surface the same issue (e.g., `analyze-git-churn` and `find-complexity-hotspots` both flagging a file), merge them into a single finding with both skills cited as sources. Do not report the same problem twice.

## Issue Creation

After presenting the report, ask the user:

> "Create issues for the N critical and N high findings?"

If the user agrees:
1. For each critical/high finding, invoke `/create-issue` with the finding details as input.
2. Label issues with the appropriate category (security, quality, observability, etc.).
3. Update the report's Recommended Actions table with the created issue links.

For medium/low findings, offer to batch them into a single cleanup issue per category rather than creating individual issues.

## Example Usage

**Scenario 1: Weekly health check**
```
/audit-sdlc diagnose
```
Runs `audit-dependencies`, `audit-security`, and `analyze-git-churn`. Finds 1 critical CVE and 2 high-churn files. Creates one issue for the CVE.

**Scenario 2: Pre-release audit**
```
/audit-sdlc all
```
Runs every audit skill. Produces a comprehensive report. Finds no critical issues, 3 high (missing test coverage on new endpoints, no alerting for new service, 1 SQL injection pattern), 12 medium/low. Creates issues for the 3 high findings.

**Scenario 3: Targeted security check**
```
/audit-sdlc security
```
Runs only `audit-security` and `audit-dependencies`. Confirms no new vulnerabilities since last audit.

**Scenario 4: Quick quality pass**
```
/audit-sdlc find-complexity-hotspots,find-dead-code
```
Runs only the two named skills. Identifies 3 functions that should be refactored and 2 unused exports.

## Next Step

After the report is produced and issues are created (or skipped), the session is complete.
To address findings through the full SDLC pipeline, use `/sdlc issue` or the appropriate fast path.

## Useful Commands Reference

No direct CLI commands. This skill invokes other skills and coordinates their output.
