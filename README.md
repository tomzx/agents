<h1 align="center">agents</h1>

<p align="center">
  <strong>A library of composable skills, agents, and conventions that teach agents how to perform repeatable software-engineering and knowledge-work tasks</strong>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/tomzx/agents" alt="License"></a>
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/format-Agent%20Skills-blue" alt="Agent Skills format"></a>
  <img src="https://img.shields.io/badge/content-Markdown%20skills-blue" alt="Markdown skills">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20Windows-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/skills-133-green" alt="Skill count">
</p>

## What

`agents` is a personal collection of reusable skills that teach agents how to perform repeatable software-engineering and knowledge-work tasks. It follows the open [Agent Skills](https://agentskills.io) format (originally developed by Anthropic), where each skill lives in its own directory under `skills/` as a self-contained `SKILL.md` with front matter metadata and step-by-step instructions. Because the format is standardized, these skills are portable across any compatible agent, including opencode, Claude Code, Cursor, Gemini CLI, GitHub Copilot, and the other clients listed on agentskills.io.

In a compatible agent, skills are discovered by name and description, loaded on demand via progressive disclosure, and invoked as slash commands (for example `/create-pr`, `/review-pr`, `/end-day`). They compose with one another, so a high-level skill like `/sdlc` orchestrates dozens of focused sub-skills into a full pipeline.

## Why

Prompting the same workflow by hand every session is slow, inconsistent, and easy to forget. Encoding a workflow as a skill turns a one-off conversation into a repeatable, reviewable, and incrementally improving capability. This repository exists to capture how work actually gets done, from triaging an issue to writing a PR to closing out the day, so the agent performs it the same way every time and the library gets better as workflows mature.

## Install

### Option 1: CLI Install (Recommended)

Use `npx skills` to install skills directly:

```bash
# Install all skills
npx skills add tomzx/agents

# Install specific skills
npx skills add tomzx/agents --skill create-pr review-pr

# List available skills
npx skills add tomzx/agents --list
```

### Option 2: Manual Clone

Clone the repository:

```bash
git clone https://github.com/tomzx/agents.git
cd agents
mkdir -p ~/.agents/skills
ln -s $(pwd)/agents/skills ~/.agents/skills
```

## Included

The library is organized into thematic groups covering the full software development lifecycle and surrounding knowledge work.

### SDLC Pipeline (orchestration)

| Skill | Purpose |
|-------|---------|
| `/sdlc` | Run the full lifecycle pipeline, from issue creation through learnings capture. |
| `/sdlc-status` | Display a progress dashboard for SDLC features from `.sdlc/` directory data. |
| `/backpropagate-sdlc` | Walk the artifact chain in reverse to verify end-to-end traceability. |
| `/initialize-sdlc-directory` | Bootstrap the `.sdlc/` directory structure in a project. |
| `/sync-sdlc` | Analyze code and reconcile it with the `.sdlc/` directory. |
| `/update-sdlc-templates` | Update `.sdlc/templates/` with the latest canonical practices. |

### Issue & Requirements

| Skill | Purpose |
|-------|---------|
| `/create-issue` | Create a GitHub issue with background, criteria, and time budget. |
| `/create-placeholder-issue` | Promote a pending (p-prefixed) SDLC feature to an issue-driven one by creating a placeholder GitHub issue and renaming its directory. |
| `/review-issue` | Review an issue for completeness, clarity, and criteria quality. |
| `/create-requirements` | Draft a requirements document from a feature brief or issue. |
| `/review-requirements` | Review requirements for clarity, completeness, and testability. |
| `/qualify-issue` | Drive a Q&A loop with a reporter to gather enough information. |
| `/reproduce-issue` | Reproduce a bug reported in a GitHub issue. |
| `/fix-issue` | Orchestrate a bug fix from issue to PR. |
| `/check-duplicates` | Check for duplicate issues and existing fix PRs. |
| `/check-linked-pr` | Detect a PR someone else linked to the current issue; offer continue, stop, or review. |
| `/triage-issue` | Classify and label a single GitHub issue. |
| `/triage-issues` | Classify and label incoming GitHub issues. |
| `/label-issue` | Add relevant labels to an issue based on its description. |
| `/prioritize-issues` | Score and rank a backlog by reach, impact, confidence, and effort. |
| `/configure-labels` | Configure the standard label set in a GitHub repository. |
| `/handle-issue-comment` | Reply to a comment on a GitHub issue. |

### Design & Research

| Skill | Purpose |
|-------|---------|
| `/create-needs-assessment` | Evaluate whether a proposed feature addresses a genuine need. |
| `/review-needs-assessment` | Review a needs assessment for evidence rigor and completeness. |
| `/create-feasibility` | Assess technical, financial, and operational viability. |
| `/review-feasibility` | Review a feasibility assessment for risk coverage and soundness. |
| `/create-existing-solutions` | Survey existing solutions and recommend adopt, extend, or build. |
| `/review-existing-solutions` | Review a solutions survey for rigor and soundness. |
| `/create-codebase-analysis` | Analyze code a feature will touch and assess changeability. |
| `/review-codebase-analysis` | Review a codebase analysis for coverage, accuracy, and rigor. |
| `/arxiv-article` | Download an arXiv article and return a structured summary. |
| `/arxiv-catchup` | Fetch new arXiv cs.AI papers since the last processed date. |

### Specifications & Plan

| Skill | Purpose |
|-------|---------|
| `/create-specifications` | Create a technical specification from requirements. |
| `/review-specifications` | Review a specification for ambiguities and missing information. |
| `/create-mockups` | Create UI wireframes, screens, states, and flows from a specification. |
| `/review-mockups` | Review mockups for coverage, usability, accessibility, and spec fidelity. |
| `/create-plan` | Create an implementation plan with phases, milestones, and risks. |
| `/review-plan` | Review a plan for completeness, feasibility, and risk coverage. |
| `/publish-plan` | Commit a plan to a branch and open a draft PR. |
| `/create-tasks-decomposition` | Decompose a plan into discrete, actionable tasks. |
| `/review-tasks-decomposition` | Review a task decomposition for granularity and clarity. |

### Implementation & Testing

| Skill | Purpose |
|-------|---------|
| `/create-implementation` | Implement a feature following the specification and plan. |
| `/review-implementation` | Review implementation for correctness, quality, and spec alignment. |
| `/create-tests` | Create a test plan and test cases covering criteria and edge cases. |
| `/review-tests` | Review a test suite for coverage, quality, and maintainability. |

### GitHub Pull Requests

| Skill | Purpose |
|-------|---------|
| `/create-pr` | Create a PR with a structured description linked to its issue. |
| `/review-pr` | Conduct a comprehensive code review of a PR. |
| `/create-pr-description` | Generate a PR description based on changes. |
| `/update-pr-description` | Update a PR description after new commits. |
| `/quick-pr-review` | Rapidly review and approve a PR to unblock others. |
| `/quick-pr-reviews` | Check all PRs where you are a requested reviewer. |
| `/handle-pr-comment` | Reply to a comment on a PR. |
| `/handle-pr-feedback` | Respond to developer comments, implement or explain, then push. |
| `/handle-pr-ci` | Diagnose failing CI, fix, and confirm pass. |
| `/resolve-pr-conflicts` | Resolve merge conflicts on all of the current user's PRs in parallel, one agent session per PR (reuses or creates a worktree). |
| `/merge-pr` | Check approval and CI, then merge and clean up. |
| `/validate-pr` | Checkout, build, run, and validate claims via runtime proof. |
| `/verify-pr` | Static code inspection after runtime validation. |
| `/deploy-pr` | Deploy merged changes, run smoke tests, verify rollback. |
| `/ghx` | Browse issues and PRs with local disk caching, and post inline review comments, thread replies, and stashes. |
| `/github-post-attribution` | Format attribution footers for skill-generated posts. |
| `/pr-review-send` | Send review comments to GitHub. |

### Documentation & Writing

| Skill | Purpose |
|-------|---------|
| `/create-documentation` | Create documentation following the Divio framework. |
| `/review-documentation` | Review docs for completeness, accuracy, clarity, and usability. |
| `/divio-documentation` | Comprehensive reference for writing in the Divio/Diataxis system. |
| `/setup-docs-site` | Scaffold a MkDocs site with Material theme and GitHub Actions. |
| `/sync-documentation` | Reconcile the `docs/` tree with code (stale refs, broken links, nav drift). |
| `/research-topic` | Research any topic, snapshot every visited page, and synthesize a structured document. |
| `/research-article` | Research a topic to map the state of the art and gather sources. |
| `/create-article` | Write a high-quality article for a given audience and sources. |
| `/review-article` | Review an article for accuracy, clarity, structure, and fit. |
| `/create-readme` | Generate a README with badges, feature list, and setup. |
| `/create-message` | Improve a message by removing negative tone. |
| `/write-recent-work-and-needs-article` | Write a personal status article about recent work and needs. |

### Observability & Telemetry

| Skill | Purpose |
|-------|---------|
| `/create-observability` | Define logging, metrics, tracing, and alerting for a feature. |
| `/review-observability` | Review an observability plan for completeness and alignment. |
| `/create-telemetry` | Define analytics events and success metrics for a feature. |
| `/review-telemetry` | Review a telemetry plan for completeness and measurability. |
| `/observe-production` | Check SLOs/SLIs, error rates, latency, and throughput. |

### Decisions & Learnings

| Skill | Purpose |
|-------|---------|
| `/create-decision` | Record an architectural decision with context and trade-offs. |
| `/review-decision` | Review a decision record for clarity and reasoning quality. |
| `/supersede-decision` | Mark a decision as superseded by a newer one. |
| `/create-assumption` | Record an assumption with its basis, risk, and validation plan. |
| `/review-assumption` | Review an assumption for specificity and risk assessment. |
| `/create-learnings` | Capture learnings in a retrospective format. |
| `/review-learnings` | Review a learnings document for actionability and completeness. |
| `/session-review` | End-of-session checklist for code quality and design concerns. |

### Code Quality Audits

| Skill | Purpose |
|-------|---------|
| `/audit-dependencies` | Audit dependencies for outdated versions and vulnerabilities. |
| `/audit-security` | Scan for code-level security vulnerabilities. |
| `/audit-observability` | Identify missing logging, metrics, tracing, and alerting. |
| `/audit-attention` | Audit time split between compounding and depreciating activities. |
| `/audit-sdlc` | Run multiple audits and produce a unified findings report. |
| `/analyze-git-churn` | Identify high-churn files from git history. |
| `/find-code-duplication` | Find copy-pasted blocks and near-duplicate logic. |
| `/find-complexity-hotspots` | Find high cyclomatic complexity and deep nesting. |
| `/find-coverage-gaps` | Find files with missing or insufficient test coverage. |
| `/find-dead-code` | Find unused functions, classes, exports, and config keys. |
| `/find-documentation-gaps` | Find public APIs and modules lacking documentation. |
| `/find-type-gaps` | Find functions and modules missing type annotations. |
| `/review-skills` | Audit the skill directory for duplicates and broken references. |

### Daily / Weekly / Monthly Cadence

| Skill | Purpose |
|-------|---------|
| `/start-day` | Open the workday grounded in yesterday's plan. |
| `/end-day` | Close the workday with summaries and next-day standup. |
| `/end-of-day-review` | Reflective review for alignment with goals. |
| `/end-of-day-summary` | Summarize GitHub and Slack activity for the day. |
| `/start-week` | Open the week with themes and outcomes. |
| `/end-week` | Summarize the week and run the attention audit. |
| `/end-of-week-review` | Reflective review covering goals, attention, and team health. |
| `/end-of-week-summary` | Summarize weekly Slack activity and action items. |
| `/start-month` | Open the month with a theme and outcomes. |
| `/end-month` | Close the month with summaries, action items, and thanks. |
| `/end-of-month-review` | Review OKR progress and strategic focus. |
| `/end-of-month-summary` | Summarize monthly GitHub and Slack activity. |
| `/what-to-demo` | Review notes to determine what to demo. |
| `/sprint-retro` | Generate a sprint retrospective. |
| `/summarize-meeting` | Produce a meeting summary from a transcript. |

### Slack Knowledge Bases

| Skill | Purpose |
|-------|---------|
| `/slack-kb-channel` | Build a channel knowledge base for a given month. |
| `/slack-kb-individual` | Collect conversations a person participated in. |
| `/kb-organized-memory` | Build theme-organized knowledge from temporal memory files. |

### Memory & Automation

| Skill | Purpose |
|-------|---------|
| `/improve-autonomy` | Assess what would be needed to run the session autonomously. |
| `/automate-session` | Surface ways the workflow could have been automated. |
| `/identify-skill-gaps` | Find workflows not yet encoded as skills. |
| `/git-commit` | Generate a commit message from changes. |
| `/git-commit-staged` | Generate a commit message from staged changes. |

### Developer Profiles

| Skill | Purpose |
|-------|---------|
| `/describe-colleague` | Profile a colleague from Slack and GitHub activity. |
| `/developer-trust-profile` | Manage a developer trust profile for a GitHub user. |
| `/initialize-developer-trust-profile` | Bootstrap a trust profile from recent PRs. |
| `/user-code-familiarity` | Build a familiarity profile from GitHub contributions. |

### Repository & Tooling

| Skill | Purpose |
|-------|---------|
| `/onboard-repository` | Bootstrap SDLC, triaging, and standardization. |
| `/compare-skills` | Compare skill directories and identify practices to adopt. |
| `/directory-to-spec` | Create a spec directory for code in the current directory. |
| `/sync-repository` | Keep SDLC, code, tests, and docs consistent. |
| `/worktrunk` | Guidance for Worktrunk CLI -- worktree management and hooks. |
| `/gws-pull-transcripts` | Pull Google Meet transcripts from Google Drive. |
| `/vacation-handoff` | Generate a handoff covering deadlines and in-flight work. |

### Conventions

In addition to skills, the repository includes an `AGENTS.md` (symlinked as `CLAUDE.md`) that codifies house style for Python, prose, and commit hygiene, and is picked up automatically by opencode. Per-repository overrides live in `repositories/{owner}/{repository}/AGENTS.md` and are applied automatically without touching the target repository.

## Out of Scope

- A hosted product or web UI; this is a local configuration and prompt library consumed by any Agent Skills-compatible agent.
- Skills tied to a specific employer's proprietary systems; workflows are kept generic and config-driven.
- A universal prompt marketplace; the skills reflect one developer's workflows and opinions.

## Requirements

- [opencode](https://opencode.ai) (or Claude Code) to discover and run the skills.
- [gh CLI](https://cli.github.com) and [ghx](https://github.com/TomzxCode/ghx) for the GitHub issue and PR skills.
- A Unix-like shell (Linux or macOS) for the shell-based skills; Windows works via WSL.
- Optional API credentials for Slack, Google Workspace, and arXiv skills (see `.env.example`).

## Getting Started

Once linked, skills appear as slash commands. Try a few:

```bash
# Start the SDLC orchestrator at a specific phase
/sdlc create-issue

# Open the workday
/start-day

# Review a pull request
/review-pr 42
```

To add your own skill, create a new directory under `skills/` with a `SKILL.md` containing front matter (`name`, `description`) and a body of steps, then re-run opencode. Use `/create-readme` to bootstrap documentation and `/review-skills` to audit the library for duplicates and broken references.

## License

The code is licensed under the [MIT license](http://choosealicense.com/licenses/mit/). See [LICENSE](LICENSE).
