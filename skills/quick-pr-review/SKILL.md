---
name: quick-pr-review
description: Rapidly review and approve a GitHub pull request to unblock others. Approves unless there are significant risks or significant public interface changes.
allowed-tools: Bash(gh:*, git:*, say), Read
argument-hint: "<owner/repo> <pr-number>"
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
     Load author trust profile
     (neutral if not found)
              |
       always_reject?
        /          \
      Yes            No
       |              |
     Skip           Find existing review comment
     (report        (<!-- quick-pr-review: marker)
      to user)               |
                       Same commit?
                        /         \
                      Yes           No (new or updated)
                       |                    |
                     No-op            Run checks
                                     (cautious = stricter)
                                          |
                              Any blocking failures?
                                 /           \
                               Yes             No
                                |               |
                          Post/update        Approve +
                          comment only      post/update
                                              comment
                                                 |
                                       Update trust profile
```

## Steps

### 1. Gather PR information

```bash
gh pr view $2 --repo $1 --json number,title,body,headRefName,headRefOid,baseRefName,state,reviews,statusCheckRollup,url,author
gh pr diff $2 --repo $1
```

Extract:
- `REPO`: `$1` (`owner/repo`)
- `HEAD_COMMIT`: the `headRefOid` (latest commit SHA, full)
- `SHORT_SHA`: first 7 characters of HEAD_COMMIT
- `PR_AUTHOR`: the `author.login` (GitHub username of the PR author)

Also resolve dot-claude attribution for the review comment footer: read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and compute `SKILL_COMMIT`, `SKILL_SHORT_SHA`, `SKILL_FILE_URL`, and `{BASE}` for `SKILL_DIR` = `quick-pr-review`. Use the **Reviewed with** line and optional `{BASE}/issues/new` sub-line from that skill.

Extract:
- `SKILL_COMMIT`: full commit SHA of the dot-claude repo
- `SKILL_SHORT_SHA`: short SHA from the same procedure
- `SKILL_FILE_URL`: URL to `skills/quick-pr-review/SKILL.md` at `SKILL_COMMIT`

### 2. Load author trust profile

`TRUST_PROFILE_PATH`: `~/.developer-trust/{PR_AUTHOR}.md`

If the file exists, read it and extract:
- `TRUST_LEVEL`: the value after `**Level**:` (one of `trusted`, `neutral`, `cautious`, `always_reject`)
- `TRUST_REASON`: the value after `**Reason**:`

If the file does not exist, default to `TRUST_LEVEL=neutral` and `TRUST_REASON=` (no prior history).

**If `TRUST_LEVEL == always_reject`**: stop immediately. Do not fetch the diff, post a comment, or approve. Report to the user: "Skipped PR #{PR_NUMBER} ({REPO}) — author is flagged for manual review only."

The trust level modifies behavior in steps 2, 4, and 8:
- `trusted`: Standard checks. On borderline cases (e.g., a check that could go either way), lean toward passing.
- `neutral`: Standard behavior (no adjustment).
- `cautious`: Apply stricter interpretation. Flag marginal cases as failing.
- `always_reject`: Skip this PR entirely. Do not post a comment or approve. Report to the user that the PR was skipped.

### 3. Find existing review comment

```bash
gh api repos/{REPO}/issues/$2/comments \
  --jq '.[] | select(.body | test("<!-- quick-pr-review:")) | {id: .id, body: .body}' \
  | head -1
```

If a comment exists, extract the commit SHA from the marker line `<!-- quick-pr-review:COMMIT_SHA -->`.

If `COMMENT_COMMIT == HEAD_COMMIT`: output "Review already up to date for commit `SHORT_SHA`." and stop.

### 4. Run review checks

Evaluate each item below. Record each as passing (`[x]`) or failing (`[ ]`). Checks are ordered by impact/risk level (highest first).

When `TRUST_LEVEL == cautious`: apply stricter interpretation. When a check is borderline (e.g., a change is arguably a public interface addition but minor), treat it as failing.

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

### 5. Compose the review comment body

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
Reviewed with [quick-pr-review](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
<sub>This should not have been approved? [Let me know]({BASE}/issues/new).</sub>
```

Substitute `SKILL_FILE_URL`, `SKILL_SHORT_SHA`, and `{BASE}` per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md).

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
Reviewed with [quick-pr-review](https://github.com/tomzx/dot-claude/blob/abc1234deadbeef.../skills/quick-pr-review/SKILL.md) (`abc1234`)
<sub>This should not have been approved? [Let me know](https://github.com/tomzx/dot-claude/issues/new).</sub>
```

(Example URLs illustrate shape; substitute real `SKILL_FILE_URL`, `{BASE}`, and SHAs from your repo.)

### 6. Save review to local repository

Write the comment body to a file in `~/.quick-pr-review` and commit it:

```bash
OWNER=$(echo {REPO} | cut -d/ -f1)
REPO_NAME=$(echo {REPO} | cut -d/ -f2)
REVIEW_DIR=~/.quick-pr-review/${OWNER}/${REPO_NAME}
REVIEW_FILE=${REVIEW_DIR}/$2-{SHORT_SHA}.md

git -C ~/.quick-pr-review rev-parse --git-dir > /dev/null 2>&1 || git init ~/.quick-pr-review
mkdir -p "${REVIEW_DIR}"
printf '%s' "{COMMENT_BODY}" > "${REVIEW_FILE}"
git -C ~/.quick-pr-review add "${REVIEW_FILE}"
git -C ~/.quick-pr-review commit -m "Review {REPO}: PR #$2 @ {SHORT_SHA}"
```

### 7. Create or update the comment

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

### 8. Approve or not

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

### 9. Update developer trust profile

After posting the comment and applying the approval decision, update the author's trust profile:

```
/developer-trust-profile {PR_AUTHOR} --after-review {REPO} {PR_NUMBER} {approved|not_approved}
```

This records the review outcome and observations in `~/.developer-trust/{PR_AUTHOR}.md`, creating the file if it does not exist.

## Output

Report to the user:
- Whether the comment was created or updated
- The short commit SHA reviewed
- Whether the PR was approved or not, and why
- Whether the trust profile was created or updated (and at which path)

### Notify the user when their review is needed

If the PR was **not approved** or you otherwise need the user to personally review the PR (e.g., ambiguous risk, policy judgment), speak a short audible alert on macOS so they notice even if the chat is in the background:

```bash
say "{REPO} #{PR_NUMBER} needs your review"
```

Use exactly that wording (substitute `REPO` and `PR_NUMBER` only). Run `say` **after** you have posted or updated the GitHub comment, in addition to the normal text report above.

**Do not** run `say` when the PR was **skipped** because `TRUST_LEVEL == always_reject` (no review, no comment—only the text report to the user).

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

**Scenario 5: Author with cautious trust level**
```
/quick-pr-review owner/myrepo 99
```
Author profile exists with `cautious` level. Applies stricter check interpretation. A borderline new export that might normally pass is flagged as failing. Profile is updated with new review entry.

**Scenario 6: Author with always_reject trust level**
```
/quick-pr-review owner/myrepo 77
```
Author profile has `always_reject` level. Skill stops immediately after loading the profile. No comment is posted, no approval issued. Reports: "Skipped PR #77 (owner/myrepo) — author is flagged for manual review only."

**Scenario 7: First review for an unknown author**
```
/quick-pr-review owner/myrepo 101
```
No trust profile found for the author. Defaults to `neutral`. After review, creates a new profile at `~/.developer-trust/{author}.md` with the first review history entry and initial observations.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr view <pr> --repo <owner/repo> --json headRefOid,statusCheckRollup,author,...` | Fetch PR metadata including latest commit, CI status, and author |
| `gh pr diff <pr> --repo <owner/repo>` | Show the full PR diff |
| `gh pr comment <pr> --repo <owner/repo> --body "..."` | Post a new comment on the PR |
| `gh api repos/{owner}/{repo}/issues/comments/{id} -X PATCH -f body="..."` | Update an existing comment |
| `gh api repos/{owner}/{repo}/issues/<pr>/comments` | List all comments on a PR |
| `gh pr review <pr> --repo <owner/repo> --approve` | Approve the PR |
| `say "..."` | macOS TTS: alert the user when manual review is needed (see **Output**) |
