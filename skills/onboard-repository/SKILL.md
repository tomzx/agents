---
name: onboard-repository
description: Bootstrap SDLC, configure automated issue triaging, and apply standardization skills to bring a repository in line with the practices encoded in this skill library. Run once per repository to establish baseline structure, health assessment, and continuous triage.
allowed-tools: Bash(gh:*, ghx:*, git:*, scripts/get-env:*), Read, Write, Glob, Grep
argument-hint: "[project-root]"
---

TODAY=!`date +%Y-%m-%d`

# Onboard Repository

Runs a one-time onboarding sequence that brings a repository up to the standard practices encoded in this skill library. The sequence bootstraps the SDLC structure, configures automated issue triaging, generates a README if needed, runs diagnostic skills, creates prioritized issues from findings, and triages any existing backlog.

## Prerequisites

- `git` repository with commit history
- `gh` CLI authenticated with write access to the target repository
- Working directory is the root of the repository (or `$1` is provided)
- Network access for vulnerability database lookups and GitHub API calls
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to produced documents
- Follow `skills/github-post-attribution/SKILL.md` to resolve commit SHA and append attribution footers to every issue body and comment posted to GitHub

## Pipeline Overview

```
Phase 1: SDLC Bootstrap
  /sync-sdlc                   Create or update .sdlc/ with populated context files
          |
          v
Phase 2: Automated Triage Workflow
  Create GitHub Actions        Scheduled workflow to run /triage-issues
  workflow file                on unlabeled issues
          |
          v
Phase 3: README
  /create-readme                Generate README.md if missing or minimal
          |
          v
Phase 4: Repository Health Assessment
  /audit-dependencies          CVEs, outdated, unmaintained, license issues
  /audit-security              Hardcoded secrets, injection, missing auth
  /analyze-git-churn           High-churn files needing refactor
  /find-complexity-hotspots    Cyclomatic complexity, nesting, length
  /find-type-gaps              Missing type annotations (Python/TS/JS)
  /find-coverage-gaps          Missing or insufficient test coverage
  /find-dead-code              Unused functions, classes, exports, flags
  /find-code-duplication       Copy-pasted blocks, near-duplicate logic
  /find-documentation-gaps     Undocumented public APIs, CLI, config
          |
          v
Phase 5: Create Issues from Findings
  /create-issue                One issue per high/critical finding
  Prioritize by severity       Critical findings first, then high, medium
          |
          v
Phase 6: Triage Existing Backlog
  /triage-issues               Classify and label all existing unlabeled issues
```

## Steps

### 1. Determine the project root

Use `$1` if provided, otherwise use the current working directory.
Verify it is a git repository with a GitHub remote:

```
git rev-parse --is-inside-work-tree
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

If no GitHub remote exists, skip Phase 2 (triage workflow), Phase 5 (issue creation), and Phase 6 (existing backlog triage).
Report the limitation and continue with the remaining phases.

### 2. Phase 1 — SDLC Bootstrap

Run `/sync-sdlc` (passing `$1` if provided).

This creates the `.sdlc/` directory tree (if absent) and populates context files with real content derived from the codebase: `project-overview.md`, `architecture.md`, `conventions.md`, and feature directories with `requirements.md` and `specification.md`.

If `.sdlc/` already exists, report what is already present and skip to verifying completeness.
If any context file still contains `<…>` placeholders, fill them in from the codebase.

Report what was created and what was already present.

### 3. Phase 2 — Automated Triage Workflow

Create a GitHub Actions workflow that runs `/triage-issues` on a schedule.
This ensures incoming issues are automatically classified and labeled without manual intervention.

First, check if a triage workflow already exists:

```
ls -la .github/workflows/triage*.yml .github/workflows/triage*.yaml 2>/dev/null
```

If one exists, report it and skip.
If none exists, create `.github/workflows/triage-issues.yml` with the following content, adapting the schedule and repository name to the project:

```yaml
name: Triage Issues

on:
  schedule:
    - cron: "0 6 * * 1-5"
  workflow_dispatch:
    inputs:
      repository:
        description: "Repository to triage (owner/repo)"
        required: false

jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Triage issues
        uses: ./
        with:
          command: /triage-issues
          repository: ${{ github.event.inputs.repository || github.repository }}
```

If the project does not use GitHub Actions (no `.github/workflows/` directory and no indication of CI), ask the user whether to create the workflow or skip this phase.

Report what was created.

### 4. Phase 3 — README

Check if `README.md` exists and has substantive content (more than 10 non-blank lines):

```
wc -l README.md 2>/dev/null
grep -c "." README.md 2>/dev/null
```

If README.md is missing or minimal, run `/create-readme`.
If README.md exists and is substantive, skip and report.

Generating the README before the health assessment ensures that `find-documentation-gaps` can account for the new README content and avoid flagging a missing README as a finding.

### 5. Phase 4 — Repository Health Assessment

Detect the project's primary language(s) and framework(s):

```
ls pyproject.toml package.json go.mod Cargo.toml 2>/dev/null
```

Run the diagnostic skills that apply to the project.
Each skill produces a report with prioritized findings.
Collect all findings for Phase 5.

Select which skills to run based on the following table:

| Skill | When to Run | Skipped If |
|-------|-------------|------------|
| `/audit-dependencies` | Always (if a package manifest exists) | No package manager detected |
| `/audit-security` | Always | No source code files |
| `/analyze-git-churn` | Always (requires git history) | Fewer than 10 commits |
| `/find-complexity-hotspots` | Always | No source code files |
| `/find-type-gaps` | Python, TypeScript, or JavaScript project | Other languages |
| `/find-coverage-gaps` | Always (if test framework detected) | No test files found |
| `/find-dead-code` | Always | No source code files |
| `/find-code-duplication` | Always | Fewer than 10 source files |
| `/find-documentation-gaps` | Always | No public API surface |

For each skill, run it and collect the output.
If a skill fails due to missing tools (e.g., `vulture` not installed), note the failure, suggest the installation command, and continue with the next skill.

Aggregate all findings into a single health report, deduplicating across skills.
For example, a file flagged by both `analyze-git-churn` and `find-complexity-hotspots` should appear once with combined context.

### 6. Phase 5 — Create Issues from Findings

For each finding from Phase 4 that is rated **Critical** or **High** priority:

1. Create a GitHub issue using `/create-issue` with (every issue body must include the **Created with** attribution footer per `github-post-attribution/SKILL.md`):
   - A title derived from the finding (e.g., "Security: Hardcoded secret in config.py" or "Dependencies: Critical CVE in requests")
   - A background section citing the health assessment skill that produced the finding
   - Acceptance criteria drawn from the skill's recommended action
   - A time budget based on the finding category:
     - Security findings: 1-2 hours
     - Dependency CVEs: 30 minutes - 1 hour
     - Dead code removal: 1-3 hours
     - Complexity refactoring: 2-4 hours
     - Documentation gaps: 30 minutes - 1 hour

2. Apply a label indicating the finding source (e.g., `area:maintenance`, `security`, `tech-debt`).

For **Medium** and **Low** priority findings, batch them into a single summary issue titled "Repository health: medium/low priority findings" with a checklist of all items. Create this issue using `/create-issue` so it includes the **Created with** attribution footer per `github-post-attribution/SKILL.md`.
This keeps the backlog clean while preserving the findings.

Skip this phase if no GitHub remote is configured.

### 7. Phase 6 — Triage Existing Backlog

Run `/triage-issues` to classify and label all existing unlabeled issues in the repository.

This applies type, area, platform, provider, severity, priority labels, sets GitHub Issue Types, and detects duplicates across the full backlog.

Skip this phase if no GitHub remote is configured.

## Output Format

```markdown
## Repository Onboarding — {TODAY}

### Phase 1: SDLC Bootstrap
- .sdlc/ structure: created / already existed
- Context files populated: project-overview.md, architecture.md, conventions.md
- Features identified: N
- Items requiring manual review: N

### Phase 2: Automated Triage Workflow
- .github/workflows/triage-issues.yml: created / already existed / skipped (no GitHub remote)
- Schedule: weekdays at 06:00 UTC

### Phase 3: README
- README.md: created / updated / already present and substantive / skipped

### Phase 4: Repository Health Assessment

| Skill | Status | Critical | High | Medium | Low |
|-------|--------|----------|------|--------|-----|
| audit-dependencies | completed | N | N | N | N |
| audit-security | completed | N | N | N | N |
| analyze-git-churn | completed | N | N | N | N |
| find-complexity-hotspots | completed | N | N | N | N |
| find-type-gaps | completed / skipped | N | N | N | N |
| find-coverage-gaps | completed / skipped | N | N | N | N |
| find-dead-code | completed | N | N | N | N |
| find-code-duplication | completed | N | N | N | N |
| find-documentation-gaps | completed | N | N | N | N |

Total findings: N (N critical, N high, N medium, N low)

### Phase 5: Issues Created
- Critical/High issues: N
  - #42 — Security: Hardcoded secret in config.py
  - #43 — Dependencies: CVE-2024-XXXX in requests
- Batched medium/low issue: #44 — Repository health: medium/low priority findings
- Skipped: no GitHub remote configured

### Phase 6: Existing Backlog Triaged
- Issues triaged: N
- See /triage-issues output for details
- Skipped: no GitHub remote configured

### Onboarding Complete

Next steps:
1. Review .sdlc/context/ files and correct anything inferred incorrectly.
2. Review each feature's requirements.md and specification.md.
3. Address Critical and High priority findings first.
4. Commit .sdlc/ and .github/workflows/triage-issues.yml to version control.
5. Run /update-sdlc-templates after pulling new versions of dot-claude.
6. Re-run health assessment quarterly with /sdlc maintenance.
```

## Example Usage

**Scenario 1: Onboard a new Python project**
```
/onboard-repository
```
Bootstraps `.sdlc/`, creates the triage workflow, runs all 9 diagnostic skills, generates a README, creates 3 critical/high issues from findings (one security, two dependency CVEs), and triages 12 existing unlabeled issues.

**Scenario 2: Onboard from a different directory**
```
/onboard-repository /path/to/my-project
```
Same as above but targets the specified project root.

**Scenario 3: Onboard a project without GitHub**
```
/onboard-repository
```
Project has no GitHub remote. Skips triage workflow creation, issue creation, and backlog triage. Completes SDLC bootstrap, health assessment, and README generation. Reports the skipped phases.

**Scenario 4: Re-onboard an existing project**
```
/onboard-repository
```
Project already has `.sdlc/` and a triage workflow. Reports what exists, runs the health assessment fresh, and only creates issues for new findings not already tracked.
