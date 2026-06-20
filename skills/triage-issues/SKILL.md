---
name: triage-issues
description: Classify and label incoming GitHub issues by type, component, platform, provider, urgency, and importance.
allowed-tools: Bash(gh:*, gh-cached:*, scripts/get-env:*), Read, Write
argument-hint: "[repository]"
---

# Triage Issues

Lists all open, unlabeled issues in a GitHub repository and delegates each one to `triage-issue` for classification.
`triage-issue` owns all per-issue work: setup (permissions, label catalog, issue types, Priority field), classification across all dimensions, area-label creation, label/type/priority application, duplicate detection, and clarification comments.

Use this skill for batch triage of a backlog. For event-driven triage of a single issue (e.g., on issue open), invoke `/triage-issue <number> [repository]` directly without this orchestrator.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- Repository in `owner/repo` format (`$1`), or omit to use the repository in the current working directory
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document
- Attribution footers on every comment posted to GitHub are handled inside `triage-issue` (per `skills/github-post-attribution/SKILL.md`)

## Workflow

```
List open issues via gh-cached --json
             |
             v
Filter: exclude issues with area:* labels
(untriaged = no area label applied)
             |
             v
For each untriaged issue (newest first):
  Delegate to /triage-issue <number> <repo>
             |
             v
Aggregate per-issue summaries
             |
             v
Output combined triage summary
```

## Steps

1. List open issues that need triage (those without an `area:` label are considered untriaged), sorted by creation date descending (newest first):
   ```
   gh-cached issue list [--repo $1] --json | jq '[.[] | select(([.labels // [] | .[] | .name // "" | startswith("area:")] | any | not))] | sort_by(.createdAt) | reverse'
   ```
   This filters out issues that already have at least one `area:` label, as those are considered triaged. Process issues from newest to oldest so that recent issues get triaged first, reflecting current state and receiving timely maintainer attention.
2. For each issue returned (processing in creation-date order, newest first), invoke the singular skill:
   ```
   /triage-issue <number> [$1]
   ```
   `triage-issue` performs the full per-issue workflow against the given issue: repo setup (visibility, permissions, label catalog, issue types, Priority field), classification across all dimensions, area-label creation when needed, label/type/priority application, duplicate detection against the full issue corpus, and clarification comments. Each invocation is self-contained and idempotent.
3. Collect each invocation's single-issue triage summary row and assemble them into the combined summary table below. If no untriaged issues were found, output an empty summary stating that.

## Output Format

```markdown
## Triage Summary

| Issue | Title | Type | Area | Platform | Provider | Severity | Repro | Priority | Duplicate | Action |
|---|---|---|---|---|---|---|---|---|---|---|
| #42 | Login crash on mobile | bug | area:ui | platform:ios | - | - | has-repro | Urgent | - | Labeled, type set, priority set |
| #43 | Files deleted after update | bug | area:core | platform:macos | - | data-loss, regression | has-repro | Urgent | - | Labeled, type set, priority set |
| #44 | Add dark mode | feature | area:ui | - | - | - | - | Medium | - | Labeled, type set, priority set |
| #45 | Bedrock request timeout | bug | area:api | - | api:bedrock | - | has-repro | High | - | Labeled, type set, priority set |
| #46 | Something broke | bug | - | platform:windows | - | - | needs-repro | - | - | needs-info, needs-repro applied, comment posted |
| #47 | Login crash on iOS | bug | area:ui | platform:ios | - | - | has-repro | Urgent | #42 | Duplicate label applied, comment posted |
```

Each row corresponds to one `/triage-issue` invocation's output.

## Example Usage

**Scenario 1: Repository with a backlog of unlabeled issues**
```
/triage-issues owner/myrepo
```
Lists all open untriaged issues and delegates each to `/triage-issue`, which classifies and applies type + area + platform + provider + urgency + importance labels.

**Scenario 2: Single new issue (event-driven, no orchestrator)**
```
/triage-issue 42 owner/myrepo
```
Triages one specific issue directly. Use this from webhook-triggered flows, GitHub Actions on `issues` events, or other skills that need per-issue triage without scanning the whole backlog.

## Notes

- The label catalog is rebuilt by each `/triage-issue` invocation. In the previous integrated flow, newly created `area:*` labels were cached for reuse within the same run; that intra-run caching is gone in the delegated model. `gh label list` is cheap and the impact is negligible.
- Duplicate detection inside `triage-issue` still fetches the full open + closed issue corpus for comparison, so the per-issue cost is the same whether triaging one issue or many.
- If the orchestrator's `gh-cached issue list` call returns a very large backlog, consider invoking `/triage-issue` for the most recent N issues first and reporting the remainder as "deferred" rather than processing hundreds of issues in a single run.
