---
name: check-issue-status
description: Determine whether a GitHub issue is already addressed in the codebase by extracting its requested behavior and verifying it against the code. Works for feature requests and bug reports in any format, with or without formal acceptance criteria. Use before starting work on an issue, or to triage stale issues, to avoid implementing or fixing something that is already present. Triggers on "is this issue already done", "is this already implemented", "is this bug already fixed", "check issue status", "is the issue still valid", or "is this issue stale".
allowed-tools: Bash(gh:*, git:*, ghx:*, scripts/get-env:*), Read, Write, Glob, Grep
argument-hint: "<issue-number> [repository]"
---

# Check Issue Status

Determines whether a GitHub issue is already addressed in the codebase.
Reads the issue, extracts the behavior it requests in whatever format it is written,
and inspects the code to verify whether that behavior is already present.
Use before starting work, or to surface stale issues that can be closed.

This skill inspects code, not GitHub metadata.
For duplicate issues and existing fix PRs use `check-duplicates`.
To actually trigger a reported bug at runtime, use `reproduce-issue`.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the issue from `$ISSUE_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read access to the target repository.
- The current working directory is a checkout of the target repository (this skill reads code).
- A GitHub issue number describing a feature request, a bug, or a task.

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `check-issue-status`.

## Steps

### 1. Fetch the issue

Fetch the issue to understand what it asks for:

```bash
ghx issue view $ISSUE_NUMBER --repo $REPO
```

Read any files present under `.sdlc/context/` (`architecture.md`, `vocabulary.md`, `conventions.md`) for context that helps locate the relevant code.

If the working directory is not a checkout of `$REPO` (different `git remote get-url origin`), warn the user and stop, since code evidence would be from the wrong repository.

### 2. Classify the issue

Decide which of these the issue is:

- **Feature request**: asks for new behavior or a capability to exist.
- **Bug report**: states that existing behavior is wrong and should be different.
- **Other** (question, task, refactor): treat the desired end state as the behavior to verify.

Record the classification. It only changes how evidence is framed, not the procedure.

### 3. Extract behavioral claims

Issues arrive in many formats: formal acceptance criteria, prose, screenshots, error logs, checklists, or a single sentence. Do not assume a structure. Read the whole body and distill 1 to N discrete **behavioral claims**, each a single testable assertion about what the code should do.

For a bug, each claim is usually "X should happen, but Y happens instead". The desired half ("X should happen") is the claim to verify against the code.
For a feature, each claim is one capability the code should provide.
For other types, each claim is one concrete aspect of the desired end state.

If the body is too vague to extract any claim (for example, a one-liner with no detail), say so and apply the author rule: if the author is the current user, gather detail from context and help refine the issue; otherwise post a comment asking for details. Then stop. Do not guess claims from a vague report.

### 4. Locate the relevant code

For each claim, derive 2 to 4 search signals:

- Identifiers: function, class, variable, endpoint, or CLI names mentioned or implied.
- File paths or module names.
- Distinctive strings: error messages, log lines, UI labels, config keys.
- Domain nouns from `.sdlc/context/vocabulary.md`.

Search the codebase with `Glob` (by file name) and `Grep` (by content), or `rg` directly:

```bash
rg -n --type py "def login_with_sso" .
rg -n "AUTH_TOKEN_EXPIRED" .
```

Read each match with `Read`. Record `file:line` for every relevant location.

If no code touches the area at all, the behavior is almost certainly not implemented. Note what was searched and move to the next claim.

### 5. Verify each claim against the code

For every claim, decide a status using only what the code shows:

- **Met**: the code already does what the claim asks. Capture the proof (`file:line`, a function body, a route, a config value, or a test that asserts it).
- **Partially met**: some of the claim is satisfied but a required part is missing. Capture both the present part and the gap.
- **Not met**: nothing in the code provides this behavior. Capture what was searched and why it is absent.

Prefer static evidence first. Run a targeted check only when a claim is about runtime behavior and static reading is ambiguous:

```bash
# run a single existing test that covers the behavior
pytest -q path/to/test_sso.py::test_login_sso
```

Never run broad test suites or anything destructive. One targeted test or one-off check is enough. If a targeted check still cannot decide, mark the claim Partially met and defer runtime proof to `reproduce-issue`.

### 6. Determine the overall verdict

Combine the per-claim statuses:

| Claim statuses | Verdict |
|---|---|
| All Met | `implemented` |
| Mix of Met and Partially met, none Not met | `partial` |
| Any Not met | `not-implemented` |

For a bug, `implemented` means the bug is already fixed (the code already does the desired behavior, so the issue is likely stale); `not-implemented` means the bug is still present and the issue is live.

### 7. Check for a prior status comment

This skill must not spam an issue with repeated "already addressed" comments. Before posting, capture the code commit being analyzed and look for a prior status comment from this skill:

```bash
CODE_SHA=$(git rev-parse --short HEAD)

gh api repos/$REPO/issues/$ISSUE_NUMBER/comments \
  --jq '[.[] | select(.body | test("<!-- check-issue-status:"))] | last | {id: .id, body: .body}'
```

A posted comment carries a hidden marker of the form `<!-- check-issue-status:<verdict>:<code-sha> -->`. From the prior comment (if any), extract `PRIOR_VERDICT`, `PRIOR_CODE_SHA`, and the comment `id`.

- No prior marker: proceed to step 8 and post normally when the verdict is `implemented`.
- Prior marker with `PRIOR_VERDICT = implemented` and `PRIOR_CODE_SHA = CODE_SHA`: the finding is unchanged. Skip posting and report "already flagged as implemented (code unchanged since)".
- Prior marker with `PRIOR_VERDICT = implemented` and a different `PRIOR_CODE_SHA`: the finding still stands or has changed. If the new verdict is still `implemented`, edit the existing comment in place (using its `id`) to refresh the evidence and marker rather than posting a new one. If the new verdict is `not-implemented` (the fix was reverted), edit the prior comment to note it is no longer current.
- Prior marker with a non-implemented verdict: ignore it; non-implemented verdicts do not normally post.

Edit a prior comment in place via:

```bash
gh api --method PATCH repos/$REPO/issues/comments/$COMMENT_ID \
  -F body="<refreshed body with updated marker and footer>"
```

### 8. Report

Present the findings in this form:

```markdown
## Issue #<n> status: <verdict>

**Classification:** feature request | bug report | other

### Claims

1. **<claim>** - Met
   - `path/to/file.py:42` - <one-line proof>
2. **<claim>** - Not met
   - Searched <signals>; <why absent>.
```

Then act by verdict:

| Verdict | Action |
|---|---|
| `implemented` | Suggest closing the issue. Post a comment idempotently (per step 7) with the proof and the attribution footer. Do not start work. |
| `partial` | Report what exists and what is missing so the user can narrow the issue or proceed. Do not post unless asked. |
| `not-implemented` | Report clear to work on. Do not post a comment. |

When posting, link the strongest piece of evidence. Resolve `CODE_SHA`, `SKILL_FILE_URL`, and `SKILL_SHORT_SHA` to their actual values before constructing the command (they are literal inside the quoted heredoc):

```bash
gh issue comment $ISSUE_NUMBER --repo $REPO --body "$(cat <<'EOF'
<!-- check-issue-status:implemented:CODE_SHA -->
This appears to already be addressed in the code.

**Evidence:**
- <claim> - `path/to/file.py:42`

If this covers the request, the issue can be closed. If something is still missing, please clarify.

---

Posted with [check-issue-status](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
EOF
)"
```

## Failure Modes

| Mode | Response |
|---|---|
| **Issue too vague to extract claims** | Apply the author rule (refine if yours, ask if not), then stop |
| **Working directory is not a checkout of `$REPO`** | Warn the user and stop |
| **Code area found but a claim needs runtime proof** | Run one targeted test; if undecided, mark Partially met and defer to `reproduce-issue` |
| **Issue is neither a feature nor a bug** | Classify as "other", verify the desired end state, proceed |
| **Prior `implemented` comment already on the issue** | Compare stored code SHA; skip if unchanged, edit in place if code moved (step 7) |

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `implemented` | All claims are met in the code |
| `partial` | Some claims met or partially met, none absent |
| `not-implemented` | At least one claim is absent from the code |

## Example Usage

**Scenario 1: Feature already implemented**
```
/check-issue-status 42 owner/myrepo
```
Issue #42 asks for CSV export of audit logs. The claim "export audit logs as CSV" is verified at `src/export/csv.go:88`. Verdict `implemented`. Suggests closing the issue with evidence.

**Scenario 2: Bug already fixed**
```
/check-issue-status 15 owner/myrepo
```
Issue #15 reports a null pointer on SSO login. The desired behavior (handle a missing token) is present at `auth/sso.py:31`. Verdict `implemented` (bug already fixed). Suggests closing as stale.

**Scenario 3: Partially implemented**
```
/check-issue-status 30 owner/myrepo
```
Issue #30 asks for rate limiting with two claims (per-user and per-IP). Per-user exists at `middleware/ratelimit.py:20`; per-IP is absent. Verdict `partial`. Reports the gap without posting.

**Scenario 4: Not implemented**
```
/check-issue-status 7 owner/myrepo
```
Issue #7 asks for dark mode. No theme or color-scheme code exists. Verdict `not-implemented`. Reports clear to work on.

**Scenario 5: Too vague**
```
/check-issue-status 9 owner/myrepo
```
Issue #9 is a one-line report with no detail. No claim can be extracted. The author is someone else, so a comment asks for details and the skill stops.

## Next Step

- If `not-implemented` and the issue is a bug, continue with `reproduce-issue`, then `fix-issue`.
- If `not-implemented` and the issue is a feature, continue with `create-implementation` or the `sdlc` orchestrator.
- If `implemented`, propose closing the issue.
- If `partial`, let the user decide whether to narrow the issue before continuing.
