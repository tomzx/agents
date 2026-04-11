---
name: quick-pr-review
description: Rapidly review and approve a GitHub pull request to unblock others. Approves unless there are significant risks or significant public interface changes.
allowed-tools: Bash(uv:*)
argument-hint: <owner/repo> <pr-number>
---

# Quick PR Review

Rapidly reviews a GitHub pull request and approves it to unblock others. Creates or updates a single review comment per PR, keyed to the latest commit. Approves automatically unless there are significant risks or significant public interface changes (removals, breaking changes, or substantial new API surface).

## Prerequisites

- `GITHUB_TOKEN` environment variable set with repo read/write access
- `uv` available on PATH
- `$1`: repository in `owner/repo` format
- `$2`: PR number identifying an open pull request

## Workflow

```
scripts/quick-pr-review fetch
              |
       status == up_to_date?
          /          \
        Yes            No
         |              |
       No-op        Analyze diff
                   (LLM work)
                        |
              Compose comment body
                        |
              scripts/quick-pr-review post
                   [--approve]
```

## Steps

### 1. Fetch PR data

```bash
uv run scripts/quick-pr-review fetch $1 $2
```

Parse the JSON output:

- If `status == "up_to_date"`: print the `message` field and stop.
- If `status == "needs_review"`: continue with the fields below.

Key fields:
- `pr.head_commit` - full SHA of the HEAD commit
- `pr.title`, `pr.body` - PR title and description
- `diff` - unified diff of all changed files
- `ci` - `{ all_passing, pending: [...], failing: [{name, conclusion}] }`
- `dependency_files_changed` - list of dependency manifest filenames modified
- `has_new_dependency_additions` - true if any dependency file has added lines
- `existing_comment` - `{ id, commit_sha }` or null
- `head_commit` - full HEAD commit SHA
- `skill_commit` - commit SHA of this dot-claude repo (for the footer link)

Derive:
- `SHORT_SHA`: first 7 characters of `head_commit`
- `SKILL_SHORT_SHA`: first 7 characters of `skill_commit`

### 2. Run review checks

Evaluate each item. The first three are **approval gates**: a failure blocks approval.

#### No significant public interface changes (approval gate)
Scan the diff for:
- Removing or renaming exported functions, classes, or types
- Removing or changing API endpoints (HTTP routes, RPC methods)
- Removing public configuration keys or environment variables
- Breaking changes to serialization formats (JSON fields removed or renamed)
- Substantial new exported API surface (new classes, types, protocols, public method signatures)
- ADRs, specs, or design docs that commit to new public API contracts
- Pre-release dependency bumps that are equivalent to a major version change (e.g. 0.20 to 0.22)

#### No security-sensitive changes (approval gate)
Scan the diff for:
- Authentication or authorization logic (login, token validation, sessions, permission checks)
- Cryptographic code (hashing, encryption, key generation, certificate handling)
- Secret or credential patterns (API keys, tokens, passwords, `.env` files)
- Security-critical configuration (CORS, CSP, TLS, OAuth scopes, RBAC rules)
- Input validation or sanitization guarding against injection attacks

#### No new dependencies (approval gate)
Use the data already provided by the script:
- If `has_new_dependency_additions` is true: check fails.
- List `dependency_files_changed` as evidence.
- Note: version bumps of existing packages alone do not fail this check.

#### Change is reversible
Scan the diff for:
- Database migrations that DROP columns, tables, or indexes without a rollback
- Deletion of data files or configuration not recoverable from source control
- Permanent data transformations with no undo path
- Infrastructure-level destructive operations (e.g. `terraform destroy` patterns)

#### Tests pass
Use the CI data already provided by the script:
- `ci.all_passing == true` -> check passes
- `ci.failing` non-empty -> check fails; list the failing check names
- `ci.pending` non-empty -> check fails; list the pending check names

#### Change is part of the spec
Read `pr.title` and `pr.body`. Is there a linked issue or clear rationale? Does the diff align with the stated goal? Flag unexplained scope creep.

#### Documentation updated
Does the diff include updates to README, docs/, or relevant user-facing documentation when the change adds or modifies user-visible behavior? For purely internal changes (refactors, tests), documentation is not required.

### 3. Compose the review comment body

Approval decision:
- **Approve** if all three gates pass (no significant public interface changes, no security-sensitive changes, no new dependencies) AND tests are passing.
- **Do not approve** otherwise.

Comment format:

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

For each failing check, append a block after the checklist:

```
# <Check name>
<One-line explanation of what failed and what needs to be addressed>
```

### 4. Post the comment and approve

Pass the comment body via stdin to the post subcommand. Include `--approve` only if the approval decision is "Approve".

```bash
uv run scripts/quick-pr-review post $1 $2 [--approve] << 'EOF'
<comment body>
EOF
```

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
`ci.failing` is non-empty. Post comment with `[ ] Tests pass`. Do not approve.

**Scenario 3: Significant public interface change**
```
/quick-pr-review owner/myrepo 55
```
Diff removes a public API method. Post comment with `[ ] No significant public interface changes`. Do not approve.

**Scenario 4: Re-run on same commit**
```
/quick-pr-review owner/myrepo 42
```
Script returns `status: up_to_date`. Report "already up to date" and stop.
