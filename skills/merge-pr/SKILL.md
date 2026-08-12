---
name: merge-pr
description: Check that a pull request is approved and CI is passing, then merge it and clean up the branch. By default does NOT merge on GitHub; it reports the merge readiness status. Pass --post to merge, delete the branch, and close the linked issue.
argument-hint: "<pr-number> [--post]"
---

# Merge PR

Verifies that a pull request has the required approvals and passing CI checks. By default, reports the merge readiness status without merging. Pass `--post` to merge, delete the branch, and close the linked issue.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with write access to the target repository
- PR number (`$1`) identifying an open pull request
- All review feedback addressed (run `/handle-pr-feedback` first if comments are unresolved)

## Workflow

```
Fetch PR status ($1)
        |
        v
  All approvals obtained?
     /         \
   Yes           No
    |             |
    v             v
  CI checks      Report missing
 passing?       approvals, stop
    /    \
  Yes     No
   |       |
   v       v
 Report   /handle-pr-ci
 merge    (fix, then re-check)
 readiness
   |
   v
 --post set?
  /         \
 No          Yes
  |            |
  v            v
 Stop      Merge PR
           |
           v
          Delete remote branch
           |
           v
          Confirm issue closed
```

## Steps

1. Fetch the current PR status:
   ```
   gh pr view $1 --json state,reviews,statusCheckRollup,mergeStateStatus,headRefName,closingIssuesReferences
   ```

2. Check approvals: confirm at least one reviewer has approved and no reviewers have requested changes. If approvals are missing or changes are requested, report the status and stop.

3. Check CI: confirm all required status checks are passing. If any are failing or pending, invoke `/handle-pr-ci $1` to diagnose and fix before continuing.

4. Present the merge summary to the user (PR title, approvals, checks). If `--post` is not set, report the merge readiness status and stop. If `--post` is set, proceed to merge.

5. On confirmation, merge the PR:
   ```
   gh pr merge $1 --squash --delete-branch
   ```
   Use `--squash` by default for a clean history. If the project uses merge commits or rebase, adjust accordingly.

6. Confirm the remote branch was deleted. If not, delete it:
   ```
   gh api repos/{owner}/{repo}/git/refs/heads/{branch} -X DELETE
   ```

7. Confirm the linked issue was closed automatically (via `Closes #N` in the PR description). If not, close it manually:
   ```
   gh issue close <issue-number>
   ```

8. Report the merge SHA and a link to the merged PR.

## Example Usage

**Scenario 1: Clean PR ready to merge**
```
/merge-pr 42 --post
```
PR has 2 approvals, all CI checks green. Present summary, squash-merge, delete branch, confirm issue closed. Without `--post`, reports readiness status without merging.

**Scenario 2: Missing approval**
```
/merge-pr 88
```
Only 1 of 2 required reviewers has approved. Report: "Waiting on approval from @reviewer2." Stop without merging.

**Scenario 3: Failing CI**
```
/merge-pr 55
```
Tests job is failing. Report: "CI check `test` is failing — resolve before merging." Stop without merging.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr view <pr-number> --json state,reviews,statusCheckRollup,mergeStateStatus,headRefName,closingIssuesReferences` | Fetch PR approval and CI status |
| `gh pr merge <pr-number> --squash --delete-branch` | Squash-merge and delete the branch |
| `gh issue close <issue-number>` | Close the linked issue if not auto-closed |
