---
name: quick-pr-review
description: Rapidly review and approve a GitHub pull request to unblock others. Approves unless there are significant risks or significant public interface changes.
allowed-tools: Bash(gh:*, git:*)
argument-hint: <owner/repo> <pr-number>
---

# Quick PR Review

Rapidly reviews a GitHub pull request and approves it to unblock others. Creates or updates a single review comment per PR, keyed to the latest commit. Approves automatically unless there are significant risks or significant public interface changes (removals, breaking changes, or substantial new API surface).

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- `$1`: repository in `owner/repo` format
- `$2`: PR number identifying an open pull request

## Workflow

```
Fetch PR metadata + latest commit SHA
              |
              v
     Find existing review comment
     (<!-- quick-pr-review: marker)
              |
        Same commit?
         /         \
       Yes           No (new or updated)
        |                    |
      No-op            Run checks
                            |
                 Any blocking failures?
                    /           \
                  Yes             No
                   |               |
             Post/update        Approve +
             comment only      post/update
                                 comment
```

## Steps

### 1. Gather PR information

```bash
gh pr view $2 --repo $1 --json number,title,body,headRefName,headRefOid,baseRefName,state,reviews,statusCheckRollup,url
gh pr diff $2 --repo $1
```

Extract:
- `REPO`: `$1` (`owner/repo`)
- `HEAD_COMMIT`: the `headRefOid` (latest commit SHA, full)
- `SHORT_SHA`: first 7 characters of HEAD_COMMIT

Also determine the commit of the dot-claude repository (where this skill lives):

```bash
git -C "$(dirname "$(dirname "$0")")" rev-parse HEAD
```

Or if the skill directory path is known (e.g. from the skill loader path), run `git rev-parse HEAD` from that directory.

Extract:
- `SKILL_COMMIT`: full commit SHA of the dot-claude repo
- `SKILL_SHORT_SHA`: first 7 characters of SKILL_COMMIT

### 2. Find existing review comment

```bash
gh api repos/{REPO}/issues/$2/comments \
  --jq '.[] | select(.body | test("<!-- quick-pr-review:")) | {id: .id, body: .body}' \
  | head -1
```

If a comment exists, extract the commit SHA from the marker line `<!-- quick-pr-review:COMMIT_SHA -->`.

If `COMMENT_COMMIT == HEAD_COMMIT`: output "Review already up to date for commit `SHORT_SHA`." and stop.

### 3. Run review checks

Evaluate each item below. Record each as passing (`[x]`) or failing (`[ ]`). Checks are ordered by impact/risk level (highest first).

#### Public interface impact (approval gate)
- Scan the diff for **significant changes to public interfaces**, both removals and additions:
  - Removing or renaming exported functions, classes, or types
  - Removing or changing API endpoints (HTTP routes, RPC methods)
  - Removing public configuration keys or environment variables
  - Breaking changes to serialization formats (JSON fields removed, renamed)
  - Introducing new exported classes, types, protocols, or public method signatures
  - ADRs, specs, or design docs that define or commit to new public API contracts (even if the diff is markdown, the intent is to establish an interface)
  - Dependency version bumps that are effectively major: for pre-release packages (version < 1.0.0), a minor version bump (e.g. 0.20→0.22) is equivalent to a major version change under semver and may introduce breaking API changes
- If any significant public interface changes are found (removals, breaking changes, or substantial new API surface): **do not approve**

#### Security-sensitive changes (approval gate)
- Scan the diff for changes to:
  - Authentication or authorization logic (login, token validation, session management, permission checks)
  - Cryptographic code (hashing, encryption, key generation, certificate handling)
  - Secret/credential patterns (API keys, tokens, passwords, `.env` files, credentials in config)
  - Security-critical configuration (CORS, CSP, TLS settings, OAuth scopes, RBAC rules)
  - Input validation or sanitization that guards against injection attacks
- If any security-sensitive changes are found: **do not approve**

#### New dependencies (approval gate)
- Scan the diff for additions to dependency manifests:
  - `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
  - `Gemfile`, `Gemfile.lock`
  - `requirements.txt`, `pyproject.toml`, `uv.lock`, `poetry.lock`
  - `go.mod`, `go.sum`
  - `Cargo.toml`, `Cargo.lock`
  - Or any other language-specific dependency file
- If new dependencies are introduced (not just version bumps of existing ones): **do not approve**

#### Change is reversible
- Scan the diff for:
  - Database migrations that DROP columns, tables, or indexes without a corresponding rollback
  - Deletion of data files or configuration that cannot be recovered from source control
  - Permanent data transformations with no undo path
- Infrastructure-level destructive operations (e.g., `terraform destroy` patterns)

#### Tests pass
- Check CI status from `statusCheckRollup` in the PR JSON.
- All required checks must be passing or skipped (not failing).

#### Change is part of the spec
- Read the PR title and description. Is there a linked issue or clear rationale?
- The change should align with the PR's stated goal - no unexplained scope creep.

#### Documentation updated
- Does the diff include updates to README, docs/, or relevant user-facing documentation when the change adds or modifies user-visible behavior?
- For purely internal changes (refactors, tests), documentation is not required.

### 4. Compose the review comment body

```
<!-- quick-pr-review:HEAD_COMMIT -->
## Quick PR Review

Automated review to unblock merging.

Reviewed commit: SHORT_SHA
✅ **Approved** _or_ ❌ **Not approved**

- [x/[ ]] No significant public interface changes
- [x/[ ]] No security-sensitive changes
- [x/[ ]] No new dependencies
- [x/[ ]] Change is reversible
- [x/[ ]] Tests pass
- [x/[ ]] Change is part of the spec
- [x/[ ]] Documentation updated

<details>
<summary>Evaluation details</summary>

### No significant public interface changes
<Reasoning>

### No security-sensitive changes
<Reasoning>

### No new dependencies
<Reasoning>

### Change is reversible
<Reasoning>

### Tests pass
<Reasoning>

### Change is part of the spec
<Reasoning>

### Documentation updated
<Reasoning>

</details>

---
Reviewed with [quick-pr-review](https://github.com/tomzx/dot-claude/blob/SKILL_COMMIT/skills/quick-pr-review/SKILL.md) (`SKILL_SHORT_SHA`)
<sub>This should not have been approved? [Let me know](https://github.com/tomzx/dot-claude/issues/new).</sub>
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

Automated review to unblock merging.

Reviewed commit: abc1234
❌ **Not approved**

- [ ] No significant public interface changes
- [x] No security-sensitive changes
- [x] No new dependencies
- [x] Change is reversible
- [ ] Tests pass
- [x] Change is part of the spec
- [x] Documentation updated

# No significant public interface changes
`removeUser()` is removed from the public SDK without a deprecation period or major version bump.

# Tests pass
CI check `unit-tests` is failing - fix the failing tests before merging.

<details>
<summary>Evaluation details</summary>

### No significant public interface changes
`removeUser()` is deleted from `sdk/public.ts` (an exported function) without a deprecation period or major version bump. This is an irreversible breaking change.

### No security-sensitive changes
No authentication, authorization, cryptographic, or security-critical configuration changes detected in the diff.

### No new dependencies
No changes to dependency manifests detected in the diff.

### Change is reversible
No database migrations, data deletions, or infrastructure-level destructive operations found in the diff.

### Tests pass
CI check `unit-tests` is failing with 3 test failures in `test_user.py`. All other checks (lint, build) are passing.

### Change is part of the spec
PR links issue #41 and the diff matches the stated goal of refactoring the user module. No unexplained scope creep.

### Documentation updated
No user-facing behavior changes detected; documentation update not required.

</details>

---
Reviewed with [quick-pr-review](https://github.com/tomzx/dot-claude/blob/abc1234.../skills/quick-pr-review/SKILL.md) (`abc1234`)
<sub>This should not have been approved? [Let me know](https://github.com/tomzx/dot-claude/issues/new).</sub>
```

### 5. Save review to local repository

Write the comment body to a file in `~/.quick-pr-review` and commit it:

```bash
OWNER=$(echo {REPO} | cut -d/ -f1)
REPO_NAME=$(echo {REPO} | cut -d/ -f2)
REVIEW_DIR=~/.quick-pr-review/${OWNER}/${REPO_NAME}
REVIEW_FILE=${REVIEW_DIR}/$2-{SHORT_SHA}.md

mkdir -p "${REVIEW_DIR}"
printf '%s' "{COMMENT_BODY}" > "${REVIEW_FILE}"
git -C ~/.quick-pr-review add "${REVIEW_FILE}"
git -C ~/.quick-pr-review commit -m "Review {REPO}: PR #$2 @ {SHORT_SHA}"
```

### 6. Create or update the comment

**If no existing comment:**
```bash
gh pr comment $2 --repo {REPO} --body "{COMMENT_BODY}"
```

**If existing comment (different commit):**
```bash
gh api repos/{REPO}/issues/comments/{COMMENT_ID} \
  -X PATCH \
  -f body="{COMMENT_BODY}"
```

### 7. Approve or not

**Approve** when all of the following are true:
- No significant public interface changes (removals, breaking changes, or substantial new API surface)
- No security-sensitive changes
- No new dependencies added
- No failing checks that represent significant risk (tests failing, or non-reversible destructive operations)

```bash
gh pr review $2 --repo {REPO} --approve
```

**Do not approve** when:
- Significant public interface changes are detected (removals, breaking changes, or substantial new API surface including specs/ADRs that define new public contracts)
- Security-sensitive changes are detected (auth, crypto, secrets, security config, input validation)
- New dependencies are introduced
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
/quick-pr-review owner/myrepo 42
```
All checks pass, no public interface changes. Approve and post review comment.

**Scenario 2: Failing CI**
```
/quick-pr-review owner/myrepo 88
```
CI is red. Post comment with `[ ] Tests pass` and the failing check name. Do not approve.

**Scenario 3: Significant public interface change**
```
/quick-pr-review owner/myrepo 55
```
Diff removes a public API method or introduces substantial new API surface. Post comment with `[ ] No significant public interface changes`. Do not approve.

**Scenario 4: Re-run on same commit**
```
/quick-pr-review owner/myrepo 42
```
Review comment already exists for the current HEAD commit. Skip and report "already up to date".

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr view <pr> --repo <owner/repo> --json headRefOid,statusCheckRollup,...` | Fetch PR metadata including latest commit and CI status |
| `gh pr diff <pr> --repo <owner/repo>` | Show the full PR diff |
| `gh pr comment <pr> --repo <owner/repo> --body "..."` | Post a new comment on the PR |
| `gh api repos/{owner}/{repo}/issues/comments/{id} -X PATCH -f body="..."` | Update an existing comment |
| `gh api repos/{owner}/{repo}/issues/<pr>/comments` | List all comments on a PR |
| `gh pr review <pr> --repo <owner/repo> --approve` | Approve the PR |
