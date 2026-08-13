---
name: validate-pr
description: Judge whether a PR builds the right product. Recovers the customer need behind the linked issue, then checks whether the acceptance criteria and the implemented behavior actually serve that need. Catches "faithfully built the wrong spec", symptom-not-cause fixes, and scope drift. No build or runtime execution (that is verify-pr's conformance role). By default does NOT post to GitHub; pass --post to post the validation report as a PR comment.
allowed-tools: Bash(gh:*, git:*, ghx:*, ~/.agents/scripts/get-env:*, ~/.agents/scripts/should-post-github-comment:*), Read, Write, Edit, Glob, Grep
argument-hint: "<pr-number> [repository] [--post]"
---

# Validate Pull Request

Answers the **validation** question: "Are we building the right product?" Given the linked issue, recover the underlying customer need (the problem being solved, the "why"), then judge whether the acceptance criteria and the implemented behavior actually serve that need.

This is the only review step that can catch a PR which faithfully implements its specification but targets the wrong problem. It does **not** build, run, or check conformance to the criteria, that is `/verify-pr`'s job ("are we building the product right?"). It does **not** judge code craft, that is `/review-pr`'s job.

The cheap, build-free nature of this step is intentional: it runs first as an early gate. If the target is wrong, there is no point spending a build to verify conformance to a wrong spec.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read access to the target repository
- `git worktree` available
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there. Of particular interest: `project-overview.md` (goals, scope, stakeholders), `goals.md` (objectives and key results), and `vocabulary.md` (domain terms). These reveal the intended outcomes the PR should serve.

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `validate-pr`.

## Workflow

```
Fetch PR metadata + diff + linked issue(s) ($1)
          |
          v
Create git worktree on PR branch
          |
          v
Recover the customer need from the issue
(problem, stakeholder, desired outcome)
          |
          v
Build the triple map: need <-> criteria <-> implemented behavior
          |
          v
Recoverable need?
   /          \
  Yes           No
   |             |
   v             v
Assess the three   Post comment: cannot
alignments         determine the need, stop
(need-fit, criteria-
soundness, scope)
   |
   v
Render validation verdict
(Right / Partially right / Wrong / Inconclusive)
   |
   v
Post validation report
```

## Steps

### 1. Fetch PR metadata, diff, and linked issue(s)

```bash
gh pr view $PR_NUMBER --repo $REPO --json title,body,headRefName,headRefOid,author,baseRefName,files,additions,deletions,changedFiles,closingIssuesReferences
```

```bash
gh pr diff $PR_NUMBER --repo $REPO
```

Extract:
- PR title and description (body)
- `HEAD_COMMIT`: the `headRefOid` (latest commit SHA, full)
- `SHORT_SHA`: first 7 characters of `HEAD_COMMIT`
- `PR_AUTHOR`: the `author.login` (GitHub username of the PR author)
- `HEAD_BRANCH`: the `headRefName` (PR branch name)
- List of changed files and diff stats
- Linked closing issues from `closingIssuesReferences` (each has `number` and `url`)
- `ISSUE_NUMBER`: the first linked issue number from `closingIssuesReferences` (or empty if none)

#### 1a. Resolve and fetch linked issue(s)

Use `closingIssuesReferences` as the authoritative source of linked issues. If empty, fall back to scanning the PR body for `Fixes #N`, `Closes #N`, `Resolves #N`, or bare `#N` references (in that order of priority).

For each linked issue number, fetch its full body:

```bash
gh issue view $ISSUE_NUMBER --repo $REPO --json number,title,body,state
```

### 1b. Create a git worktree on the PR branch

```bash
git fetch origin $HEAD_BRANCH
WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
mkdir -p /tmp/sdlc/$REPO
git worktree add $WORKTREE_DIR origin/$HEAD_BRANCH
```

All subsequent code reading happens inside the worktree directory.

If worktree creation fails, stop.

### 2. Recover the customer need

This step distinguishes validation from verification. The acceptance criteria state *what* the solution must do; the need states *why* it must do it, the problem the customer actually has. Recover the need from the issue, not the criteria.

From each linked issue body, extract:

- **The problem**: the pain or situation the customer faces, in the customer's terms (look at the issue title, the opening motivation, "As a ... I want ... so that ..." user stories, reproduction steps for bugs).
- **The stakeholder / user**: whose problem this is. A PR that solves the right problem for the wrong user is a validation miss.
- **The desired outcome**: what changes for the customer once this is solved, the goal, not the mechanism.
- **The proposed solution (the spec)**: the acceptance criteria and any described approach. This is the *how*, and it may or may not be the right way to meet the need.

Augment the need from project context when available:
- `.sdlc/context/project-overview.md` and `goals.md` for intended outcomes and objectives the PR should advance.
- `.sdlc/context/vocabulary.md` to read the problem in the right domain language.

If the issue is a bug report, the need is the underlying problem that produces the bug, and a key validation question is whether the bug is a symptom of a deeper cause.

Record the recovered need as a short statement (or a few), tagged with its stakeholder and desired outcome.

### 3. Build the triple map

Relate three layers and look for gaps between them:

| Layer | Source |
|---|---|
| **Need** | Recovered in Step 2 |
| **Criteria** | Parsed from the issue's acceptance criteria (`## Must` / `## Should` checklists, or inferred requirements) |
| **Implemented behavior** | Inferred from the diff and code read in the worktree (what the PR actually changes in the product) |

For each need, record which criteria and which implemented behaviors serve it. For each criterion and each implemented behavior, record which need (if any) it serves.

Three categories of gap matter:

- **Unmet need**: a recovered need that no criterion and no implemented behavior addresses.
- **Orphan work**: a criterion or implemented behavior that serves no recovered need (solutionizing beyond the problem, gold-plating, or scope creep).
- **Need/criteria mismatch**: the criteria describe a solution that would not satisfy the need even if perfectly implemented (the spec itself is the wrong target).

### 4. Assess alignment

#### 4a. Need fit (the core validation question)

Does the implemented behavior, as inferred from the diff, actually solve the customer's problem and produce the desired outcome? This is judged against the **need**, not the criteria. A PR can satisfy every criterion and still miss the need.

For bug fixes specifically, determine whether the change addresses the **root cause** of the reported problem or merely suppresses the **symptom**. Fixes that paper over a symptom are validation failures even when the reported error disappears.

#### 4b. Criteria soundness

Do the acceptance criteria actually serve the recovered need?

- Are there needs with no covering criterion? The criteria under-specify the problem.
- Are there criteria that serve no need? They over-constrain the solution or import assumptions that belong to a different problem.
- Do the criteria over-prescribe the *how* when the need is about the *what*, locking the implementation into a mechanism that may not be the right way to meet the need?

Sound criteria are a prerequisite for meaningful verification (`/verify-pr`); flagging unsound criteria here is a validation contribution.

#### 4c. Scope

- **Over-building (gold-plating)**: implemented behavior beyond any need or criterion.
- **Under-building**: a need left unaddressed by both criteria and implementation.
- **Scope creep**: changes that belong to a different problem and should be split out.

### 5. Render the validation verdict

| Verdict | When |
|---|---|
| **Right thing** | The implemented behavior and criteria serve the real need; no unmet need, no meaningful orphan work |
| **Partially right** | The core need is addressed but with gaps: an unmet secondary need, some orphan work, or criteria that partly miss the point |
| **Wrong thing** | The target itself is wrong: the need is not addressed, or the spec solves the wrong problem, or a fix treats the symptom not the cause |
| **Inconclusive** | The need could not be recovered from the issue (see failure modes) |

A **Wrong thing** verdict is the most valuable output of this skill: it means the PR should not proceed to verification or review until the target is corrected, regardless of how well it is built.

### 6. Post the validation report

Write the report to a file:

```bash
BODY="$(cat <<'EOF'
<!-- validate-pr:HEAD_COMMIT -->
## Validation Report

### Summary

Issue(s): #N
Validated commit: SHORT_SHA

**Verdict:** Right thing / Partially right / Wrong thing / Inconclusive

**Recovered need:** <one-line statement of the customer problem and desired outcome>
**Stakeholder:** <who the customer/user is>

<details>
<summary>Details</summary>

### Need <-> criteria <-> implementation

| Need | Served by criteria? | Served by implementation? | Notes |
|---|---|---|---|
| "<need>" | Yes / No / Partly | Yes / No / Partly | <observation> |

### Findings

#### Finding 1: <title>
- **Severity**: Blocks (wrong target) / Should address / Nitpick
- **Layer**: Need fit / Criteria soundness / Scope
- **Description**: <what is wrong relative to the need>
- **Suggestion**: <what would align the work with the need>

### Notes

<Any additional observations, including criteria-soundness notes for verify-pr>

</details>

---

EOF
)"

# Report location is reviewer-owned, not in the repo: see sdlc/references/shared.md
# (PR Review Reports). Survives worktree removal and never pollutes the checked-out repo.
PR_REVIEW_DIR="$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER"
mkdir -p "$PR_REVIEW_DIR"
printf '%s\n' "${BODY}" > "$PR_REVIEW_DIR/validate-pr.$SHORT_SHA.md"
```

### Post the validation report as a PR comment

By default, the report is saved to `$PR_REVIEW_DIR/validate-pr.$SHORT_SHA.md` and NOT posted to GitHub. To post it, pass `--post` to the skill.

Run `~/.agents/scripts/should-post-github-comment --repo "$REPO" --author "$PR_AUTHOR" [--post]`. The `--post` flag is included when the user passed `--post` to this skill. If it exits 1, skip posting; the report is already saved to `$PR_REVIEW_DIR/validate-pr.$SHORT_SHA.md`.

If it exits 0, post the report file as a comment on the PR. The file already contains the `<!-- validate-pr:HEAD_COMMIT -->` marker.

```bash
FOOTER="Posted with [validate-pr](${SKILL_FILE_URL}) (\`${SKILL_SHORT_SHA}\`)"
gh pr comment $PR_NUMBER --repo $REPO --body "$(cat "$PR_REVIEW_DIR/validate-pr.$SHORT_SHA.md")

${FOOTER}"
```

### 7. Clean up

```bash
git worktree remove $WORKTREE_DIR
```

## Failure Modes

| Mode | Response |
|------|----------|
| **No linked issue** | Save a comment asking author to link an issue describing the problem and the need, stop. Validation needs a problem statement; do not invent one from the diff alone |
| **Linked issue has no recoverable need** (e.g. pure refactor request with no customer problem) | Render verdict `Inconclusive`, note that no customer need could be recovered, and suggest the issue state the problem it solves. Do not fabricate a need |
| **PR description has no added context** | Proceed; the issue is the primary source of the need, the PR body is secondary |
| **Large diff (>1000 lines)** | Focus on the entry points and user-visible behavior changes to judge need fit; note that full assessment is impractical |
| **Worktree creation fails** | Stop |

## Example Usage

**Scenario 1: Right thing, well targeted**
```
/validate-pr 42 owner/myrepo
```
Issue #31 asks for faster report generation because users wait minutes for exports. The criteria specify a streaming export path and the diff implements it. The need (responsive exports) is served by both criteria and implementation. Verdict: Right thing.

**Scenario 2: Wrong thing, symptom not cause**
```
/validate-pr 88
```
Issue #80 reports crashes on empty email input. The diff wraps the field access in a null check at the call site, satisfying the criterion "no crash on empty email". But the recovered need is robust input handling, and the root cause (unvalidated input entering the domain layer) is unaddressed, the same class of crash will recur elsewhere. Verdict: Wrong thing (treats symptom, not cause).

**Scenario 3: Partially right, scope drift**
```
/validate-pr 77
```
Issue #50 needs a login page. The PR adds the login page (serves the need) but also ships a settings redesign no need or criterion mentions. Verdict: Partially right, with an orphan-work finding recommending the settings work be split out.

**Scenario 4: Wrong thing, spec solves the wrong problem**
```
/validate-pr 90
```
Issue #60's need is "stop users from accidentally deleting projects". The criteria and the diff implement an undo timer on deletion. Validation judges that an undo timer does serve the need, but a prior criterion locks the implementation into a specific mechanism that conflicts with the team's soft-delete architecture, the spec over-prescribes the how. Verdict: Partially right with a criteria-soundness finding.

**Scenario 5: Inconclusive**
```
/validate-pr 15
```
The linked issue is a one-line "refactor the auth module" with no stated problem or outcome. No customer need can be recovered. Verdict: Inconclusive, with a comment asking the author to state the problem the refactor solves.

## Next Step

If the verdict is Right thing (or Partially right with non-blocking findings), proceed to `/verify-pr` to confirm the implementation conforms to the acceptance criteria (static traceability plus runtime proof), then `/review-pr` for code-craft review. If the verdict is Wrong thing, stop and correct the target before further review.
