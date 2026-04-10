---
name: quick-pr-review
description: Rapidly review and approve a GitHub pull request to unblock others. Approves unless there are significant risks or irreversible public interface changes.
allowed-tools: Bash(gh:*, git:*)
argument-hint: <pr-number>
---

# Quick PR Review

Rapidly reviews a GitHub pull request and approves it to unblock others. Creates or updates a single review comment per PR, keyed to the latest commit. Approves automatically unless there are significant risks or irreversible public interface changes.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- PR number (`$1`) identifying an open pull request

## Workflow

```
Fetch PR metadata + latest commit SHA
              |
              v
     Find existing review comment
     (<!-- quick-pr-review --> marker)
              |
        Same commit?
         /         \
       Yes           No (new or updated)
        |                    |
   No-op, done         Run review checks
                             |
                             v
                  - Documentation updated?
                  - Tests/CI passing?
                  - Change is reversible?
                  - Change is part of the spec?
                  - Public interface impact?
                             |
                  Any irreversible public
                  interface changes?
                     /           \
                   Yes             No
                    |               |
              Do not approve    All checks pass?
              Post/update          /       \
              comment            Yes        No
                               Approve   Post/update
                                         comment only
```

## Steps

### 1. Gather PR information

```bash
gh pr view $1 --json number,title,body,headRefName,headRefOid,baseRefName,state,reviews,statusCheckRollup,url
gh pr diff $1
gh repo view --json owner,name --jq '"\\(.owner.login)/\\(.name)"'
```

Extract:
- `HEAD_COMMIT`: the `headRefOid` (latest commit SHA, full)
- `SHORT_SHA`: first 7 characters of HEAD_COMMIT
- `REPO`: `owner/repo` string

### 2. Find existing review comment

```bash
gh api repos/{REPO}/issues/$1/comments \
  --jq '.[] | select(.body | test("<!-- quick-pr-review -->")) | {id: .id, body: .body}' \
  | head -1
```

If a comment exists, extract the commit SHA from the marker line `<!-- quick-pr-review:COMMIT_SHA -->`.

If `COMMENT_COMMIT == HEAD_COMMIT`: the PR has not changed since last review. Output "Review already up to date for commit `SHORT_SHA`." and stop.

### 3. Run review checks

Evaluate each item below. Record each as passing (`[x]`) or failing (`[ ]`).

#### Documentation updated
- Does the diff include updates to README, docs/, or relevant user-facing documentation when the change adds or modifies user-visible behavior?
- For purely internal changes (refactors, tests), documentation is not required.

#### Tests pass
- Check CI status from `statusCheckRollup` in the PR JSON.
- All required checks must be passing or skipped (not failing).

#### Change is reversible
- Scan the diff for:
  - Database migrations that DROP columns, tables, or indexes without a corresponding rollback
  - Deletion of data files or configuration that cannot be recovered from source control
  - Permanent data transformations with no undo path
- Infrastructure-level destructive operations (e.g., `terraform destroy` patterns)

#### Change is part of the spec
- Read the PR title and description. Is there a linked issue or clear rationale?
- The change should align with the PR's stated goal - no unexplained scope creep.

#### Public interface impact (approval gate)
- Scan the diff for irreversible changes to public interfaces:
  - Removing or renaming exported functions, classes, or types
  - Removing or changing API endpoints (HTTP routes, RPC methods)
  - Removing public configuration keys or environment variables
  - Breaking changes to serialization formats (JSON fields removed, renamed)
- If any irreversible public interface changes are found: **do not approve**

### 4. Compose the review comment body

```
<!-- quick-pr-review:HEAD_COMMIT -->
## Quick PR Review

Reviewed commit: `SHORT_SHA`

- [x/[ ]] Documentation updated
- [x/[ ]] Tests pass
- [x/[ ]] Change is reversible
- [x/[ ]] Change is part of the spec
- [x/[ ]] No irreversible public interface changes
```

For each failing check, append a block after the bullet list:

```
# <Check name>
<One-line explanation of what failed and what needs to be addressed>
```

Example with two failures:

```
<!-- quick-pr-review:abc1234... -->
## Quick PR Review

Reviewed commit: `abc1234`

- [x] Documentation updated
- [ ] Tests pass
- [x] Change is reversible
- [x] Change is part of the spec
- [ ] No irreversible public interface changes

# Tests pass
CI check `unit-tests` is failing - fix the failing tests before merging.

# No irreversible public interface changes
`removeUser()` is removed from the public SDK without a deprecation period or major version bump.
```

### 5. Create or update the comment

**If no existing comment:**
```bash
gh pr comment $1 --repo {REPO} --body "{COMMENT_BODY}"
```

**If existing comment (different commit):**
```bash
gh api repos/{REPO}/issues/comments/{COMMENT_ID} \
  -X PATCH \
  -f body="{COMMENT_BODY}"
```

### 6. Approve or not

**Approve** when all of the following are true:
- No irreversible public interface changes
- No failing checks that represent significant risk (tests failing, or non-reversible destructive operations)

```bash
gh pr review $1 --repo {REPO} --approve --body "LGTM - no blocking issues found."
```

**Do not approve** when:
- Irreversible public interface changes are detected
- Tests are failing
- Change is not reversible and involves destructive operations

In the do-not-approve case, only post/update the comment. Do not request changes automatically unless the issue is clearly blocking (e.g., tests failing, data loss risk).

## Output

Report to the user:
- Whether the comment was created or updated
- The short commit SHA reviewed
- Whether the PR was approved or not, and why

## Example Usage

**Scenario 1: Clean PR, approve**
```
/quick-pr-review 42
```
All checks pass, no public interface changes. Approve and post review comment.

**Scenario 2: Failing CI**
```
/quick-pr-review 88
```
CI is red. Post comment with `[ ] Tests pass` and the failing check name. Do not approve.

**Scenario 3: Irreversible public interface change**
```
/quick-pr-review 55
```
Diff removes a public API method. Post comment with `[ ] No irreversible public interface changes`. Do not approve.

**Scenario 4: Re-run on same commit**
```
/quick-pr-review 42
```
Review comment already exists for the current HEAD commit. Skip and report "already up to date".

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr view <pr> --json headRefOid,statusCheckRollup,...` | Fetch PR metadata including latest commit and CI status |
| `gh pr diff <pr>` | Show the full PR diff |
| `gh pr comment <pr> --body "..."` | Post a new comment on the PR |
| `gh api repos/{owner}/{repo}/issues/comments/{id} -X PATCH -f body="..."` | Update an existing comment |
| `gh api repos/{owner}/{repo}/issues/<pr>/comments` | List all comments on a PR |
| `gh pr review <pr> --approve --body "..."` | Approve the PR |
| `gh repo view --json owner,name --jq '"\\(.owner.login)/\\(.name)"'` | Get the current repo's owner/name |
