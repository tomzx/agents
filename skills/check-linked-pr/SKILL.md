---
name: check-linked-pr
description: Detect pull requests someone else linked to the issue being worked on, then offer to continue, stop, or review them. Use mid-flow to avoid duplicating in-progress work and to decide whether to depend on an external PR instead.
allowed-tools: Bash(gh:*, ghx:*, scripts/get-env:*), Read, Write, Edit
argument-hint: "<issue-number> [repository]"
---

# Check Linked PR

Detects pull requests authored by someone else that have been linked to a GitHub issue, and helps decide what to do about them.

Unlike `check-duplicates` (a one-time pre-flight check run before any work starts), this skill is meant to run **repeatedly during an in-progress SDLC flow** to catch a competing PR that appears after work has already begun.

It is read-only with respect to GitHub: it never comments, labels, or opens anything. The only side effect is updating `.sdlc/state.yml` to remember which PRs the user already decided to ignore (so the recurring check does not re-prompt every phase).

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the issue from `$ISSUE_NUMBER` (and `$REPO`), then from `.sdlc/state.yml` `github_ref`.
- `gh` CLI authenticated with read access to the target repository.
- A GitHub issue number to check. If the feature has no issue yet (a `p`-prefixed feature), there is nothing to link to: report clear and stop.

## What counts as "linked"

A PR is considered linked to the issue when GitHub records a connection. The skill checks, in order of reliability:

1. The issue **timeline** `cross-referenced` / `connected` events whose source is a pull request (covers manual "Development" links, PRs that reference the issue number in their body, and `closes #N` / `fixes #N` keywords).
2. A keyword **search** of open PRs mentioning the issue number (fallback when timeline is empty or unavailable).

A PR is **excluded** (not competing) when any of these hold:

- It is authored by the current authenticated user (`@me`) — that is the SDLC flow's own PR.
- Its number matches the SDLC flow's own PR (the PR number recorded in `.sdlc/state.yml` `github_ref` once `create-pr` has run).
- Its number is listed in `linked_prs_acknowledged` in `.sdlc/state.yml` (the user already chose to ignore it this run).

Only **open** PRs from other authors count as competing. A merged PR means the issue may already be resolved: surface it separately as a signal that the flow may be obsolete.

## Steps

### 1. Resolve the target

Determine the issue number and repository:

- `$1` if provided, else `$ISSUE_NUMBER`, else read `.sdlc/state.yml` `github_ref` and strip any leading `#`.
- `$REPO` if provided/set, else derive `{owner}/{repository}` from `git remote get-url origin`.

```bash
gh api user --jq .login    # the current user, used to exclude our own PRs
```

If no issue number can be resolved, report clear and stop.

### 2. Collect linked PRs (timeline, primary)

Fetch the issue timeline and extract pull-request cross-references:

```bash
gh api "repos/{owner}/{repo}/issues/$ISSUE_NUMBER/timeline" --paginate \
  --jq '[.[]
    | select(.event == "cross-referenced")
    | select(.source.issue.pull_request != null)
    | {number: .source.issue.number, title: .source.issue.title, state: .source.issue.state, author: .source.issue.user.login, draft: (.source.issue.draft // false)}]'
```

Deduplicate by PR number. Keep only `state == "OPEN"` entries as candidates; note any merged/closed ones separately.

### 3. Collect linked PRs (search, fallback)

If the timeline returned nothing, fall back to a keyword search:

```bash
ghx pr list --repo $REPO --search "$ISSUE_NUMBER is:pr" --state open --limit 20
```

For each result, confirm the PR body or title references the issue number, then capture number, title, state, and author.

### 4. Filter out non-competing PRs

Remove candidates that are:

- authored by the current user (`@me`), or
- equal to the own-PR number in `.sdlc/state.yml` `github_ref`, or
- present in `linked_prs_acknowledged` in `.sdlc/state.yml`.

### 5. Decide

- **No competing PRs:** report "clear" and stop. Emit `verdict: clear`.
- **Competing PR(s) found:** present each (number, author, draft/open, title, one-line summary of what it changes) and ask the user to choose, per the options below.

### 6. Handle the user's choice

When one or more competing PRs are found, ask the user which action to take (the questions are inherently interactive; under automation, see Outcome):

| Option | Action |
|---|---|
| **Continue** | Add the PR number(s) to `linked_prs_acknowledged` in `.sdlc/state.yml` so the guard does not re-prompt for them, then proceed with the current flow. Emit `verdict: continue`. |
| **Stop** | Stop the SDLC flow. Record in `.sdlc/features/N-<slug>/progress.md` that the flow paused pending an external PR (include the PR number and author). Leave the pipeline resumable. Emit `verdict: stop`. |
| **Review** | Invoke `/review-pr <pr-number>` against the chosen PR. Based on its verdict: if `approved`, stop the flow and depend on the external PR (record the dependency in `progress.md` and `state.yml`, emit `verdict: depend`); if `changes-requested` or `rejected`, add the PR to `linked_prs_acknowledged` and offer to continue the current flow (emit `verdict: continue`). |

When multiple competing PRs exist, default the Review option to the most relevant one (the open, non-draft PR that most directly addresses the issue's acceptance criteria) but let the user pick which to review.

## State

The only file this skill writes is `.sdlc/state.yml`, to extend `linked_prs_acknowledged` (a list of PR numbers already dismissed this run). It never modifies GitHub. `state.yml` is local-only and never committed (see `references/shared.md`).

```yaml
linked_prs_acknowledged: []   # PR numbers the user chose to ignore this run
```

If `state.yml` does not yet have the key, create it as an empty list before appending.

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `clear` | No competing PRs linked to the issue |
| `continue` | A competing PR was found but the user chose to keep working |
| `stop` | The user chose to stop the flow pending an external PR |
| `depend` | The reviewed PR was approved and the flow should depend on it |
| `competing-pr` | A competing PR was found but no decision could be made (e.g. automation with no user to ask) |

Under automation (`$OUTCOME_YAML` set, no interactive user), do not block: detect competing PRs, emit `competing-pr` (or `clear`), and let the runner route. Do not invoke `/review-pr` automatically.

## Example Usage

**Scenario 1: No competing PR**
```
/check-linked-pr 42
```
Timeline for #42 references no open PRs from other authors. Reports clear; the flow continues uninterrupted.

**Scenario 2: Someone opened a PR mid-flow**
```
/check-linked-pr 42
```
Finds open PR #88 by `@jane` linked to #42, not yet acknowledged. Presents continue / stop / review. The user picks **Review**; `/review-pr 88` returns `approved`, so the flow stops and records that it depends on #88.

**Scenario 3: Acknowledged PR, next phase**
```
/check-linked-pr 42
```
PR #88 is still linked but already in `linked_prs_acknowledged` (the user chose **Continue** last phase). Reports clear without re-prompting.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh api "repos/{o}/{r}/issues/$N/timeline" --paginate --jq ...` | Issue timeline; extract PR cross-references (primary) |
| `ghx pr list --repo <repo> --search "$N is:pr" --state open --limit 20` | PRs mentioning the issue number (fallback) |
| `gh api user --jq .login` | Current user, to exclude our own PRs |
