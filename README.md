<h1 align="center">agents</h1>

<p align="center">
  <strong>A library of composable skills, agents, and conventions that teach agents how to perform repeatable software-engineering and knowledge-work tasks</strong>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/tomzx/agents" alt="License"></a>
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/format-Agent%20Skills-blue" alt="Agent Skills format"></a>
  <img src="https://img.shields.io/badge/content-Markdown%20skills-blue" alt="Markdown skills">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20Windows-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/skills-123+-green" alt="Skill count">
</p>

## What

`agents` is a personal collection of reusable skills that teach agents how to perform repeatable software-engineering and knowledge-work tasks. It follows the open [Agent Skills](https://agentskills.io) format (originally developed by Anthropic), where each skill lives in its own directory under `skills/` as a self-contained `SKILL.md` with front matter metadata and step-by-step instructions. Because the format is standardized, these skills are portable across any compatible agent, including opencode, Claude Code, Cursor, Gemini CLI, GitHub Copilot, and the other clients listed on agentskills.io.

In a compatible agent, skills are discovered by name and description, loaded on demand via progressive disclosure, and invoked as slash commands (for example `/create-pr`, `/review-pr`, `/end-day`). They compose with one another, so a high-level skill like `/sdlc` orchestrates dozens of focused sub-skills into a full pipeline.

## Why

Prompting the same workflow by hand every session is slow, inconsistent, and easy to forget. Encoding a workflow as a skill turns a one-off conversation into a repeatable, reviewable, and incrementally improving capability. This repository exists to capture how work actually gets done, from triaging an issue to writing a PR to closing out the day, so the agent performs it the same way every time and the library gets better as workflows mature.

## Included

The library is organized into thematic groups covering the full software development lifecycle and surrounding knowledge work.

- **SDLC pipeline**, an end-to-end orchestrator and its stages: `/sdlc`, `/sdlc-status`, plus `create-*`, `review-*`, `qualify-issue`, `reproduce-issue`, `fix-issue`, `publish-plan`, `create-tasks-decomposition`, and the `initialize-sdlc-directory` / `sync-sdlc` / `update-sdlc-templates` bootstrap skills.
- **GitHub issues and PRs**: `create-issue`, `review-issue`, `triage-issues`, `prioritize-issues`, `label-issue`, `search-existing-issues`, `check-duplicates`, `configure-labels`, `handle-issue-comment`, `create-pr`, `create-pr-description`, `update-pr-description`, `review-pr`, `quick-pr-review`, `quick-pr-reviews`, `handle-pr-comment`, `handle-pr-ci`, `handle-pr-feedback`, `merge-pr`, `validate-pr`, `verify-pr`, `deploy-pr`, and `observe-production`.
- **Code quality audits**: `audit-dependencies`, `audit-observability`, `audit-sdlc`, `audit-security`, `analyze-git-churn`, `find-code-duplication`, `find-complexity-hotspots`, `find-coverage-gaps`, `find-dead-code`, `find-documentation-gaps`, `find-type-gaps`.
- **Daily, weekly, and monthly cadence**: `start-day`/`start-week`/`start-month`, `end-day`/`end-week`/`end-month`, `end-of-{day,week,month}-{review,summary}`, `what-to-demo`, `sprint-retro`, `summarize-meeting`.
- **Slack knowledge bases**: `slack-kb-channel`, `slack-kb-individual`, `kb-organized-memory`, `check-opinion-alignment`, `sync-opinions`.
- **Documentation and writing**: `create-documentation`, `divio-documentation`, `review-documentation`, `setup-docs-site`, `write-article`, `write-readme`, `write-message`, `write-recent-work-and-needs-article`, `review-article`.
- **Memory and reflection**: `para-memory-files`, `improve-autonomy`, `automate-session`, `identify-skill-gaps`, `session-review`, `create-learnings`, `create-decision`, `create-assumption`, `review-learnings`, `review-decision`, `review-assumption`.
- **Developer profiles**: `describe-colleague`, `developer-trust-profile`, `initialize-developer-trust-profile`, `user-code-familiarity`.
- **Research**: `arxiv-article`, `arxiv-catchup`, `create-existing-solutions`, `review-existing-solutions`, `create-feasibility`, `review-feasibility`.
- **Repository onboarding and tooling**: `onboard-repository`, `compare-skills`, `review-skills`, `directory-to-spec`, `sync-repository`, `gh-cached`, `ghx`, `github-post-attribution`, `pr-review-send`, `worktrunk`.
- **Conventions**: `AGENTS.md` (symlinked as `CLAUDE.md`) codifies house style for Python, prose, and commit hygiene, and is picked up automatically by opencode.

## Out of Scope

- A hosted product or web UI; this is a local configuration and prompt library consumed by any Agent Skills-compatible agent.
- Skills tied to a specific employer's proprietary systems; workflows are kept generic and config-driven.
- A universal prompt marketplace; the skills reflect one developer's workflows and opinions.

## Requirements

- [opencode](https://opencode.ai) (or Claude Code) to discover and run the skills.
- [gh CLI](https://cli.github.com) and [ghx](https://github.com) for the GitHub issue and PR skills.
- A Unix-like shell (Linux or macOS) for the shell-based skills; Windows works via WSL.
- Optional API credentials for Slack, Google Workspace, and arXiv skills (see `.env.example`).

## Install

Clone the repository and install the opencode plugin dependency:

```bash
git clone https://github.com/tomzx/agents.git
cd agents
```

Link it into opencode so the skills and agents are discovered. From the repository root:

```bash
ln -s "$(pwd)" ~/.opencode
```

Opencode reads `opencode.json`, `AGENTS.md`/`CLAUDE.md`, the `agents/` directory, and every `skills/*/SKILL.md` on startup, so no further registration is needed.

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

To add your own skill, create a new directory under `skills/` with a `SKILL.md` containing front matter (`name`, `description`) and a body of steps, then re-run opencode. Use `/write-readme` to bootstrap documentation and `/review-skills` to audit the library for duplicates and broken references.

## License

The code is licensed under the [MIT license](http://choosealicense.com/licenses/mit/). See [LICENSE](LICENSE).
