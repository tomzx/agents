---
name: create-pr
description: Create a GitHub pull request with a structured description linked to its issue, with acceptance criteria coverage and reviewer assignment. Embeds visual proof that was captured beforehand by /validate-implementation (single asset, or a before/after pair for bug fixes) by reading the proof manifest; create-pr is a consumer and does not capture recordings itself. If no proof was captured, it omits the Visual proof section and suggests running /validate-implementation first.
allowed-tools: Bash(gh:*, git:*, ghx:*, base64:*, ~/.agents/scripts/get-env:*, ~/.agents/scripts/should-post-to-github:*), Read, Write, Glob, Grep
argument-hint: "[repository] [issue-number]"
---

# Create Pull Request

Opens a GitHub pull request for the current branch with a structured description that maps implementation changes to acceptance criteria, links the originating issue, and requests reviewers. Whether the PR is created on GitHub (and visual-proof assets uploaded, reviewers assigned) is decided by `should-post-to-github` (based on `~/.sdlc/config.yaml`); when posting is disabled it drafts the description and shows it for review instead. It is a pure consumer of visual proof: it reads the manifest written by [`/validate-implementation`](../validate-implementation/SKILL.md) and embeds any captured asset inline so reviewers see proof the moment the PR opens. It does not capture recordings itself; recording happens at human-review time, before the PR exists.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, use `$REPO` and link `$ISSUE_NUMBER`.
- `gh` CLI authenticated with write access to the target repository
- Current branch has commits not on the base branch
- A related GitHub issue number (strongly recommended; omit only for housekeeping PRs)
- Tests passing locally before the PR is opened
- For visual proof (captured beforehand): run [`/validate-implementation`](../validate-implementation/SKILL.md) on the branch first. It records a CLI demo (via [`/record-asciinema`](../record-asciinema/SKILL.md)) or a web screenshot (via [`/record-playwright`](../record-playwright/SKILL.md)) and writes `$PROOF_DIR/captured-proof.json`. If that manifest is absent, `create-pr` omits the Visual proof section and suggests running `/validate-implementation` first (it never captures on its own).

> **Note:** This skill uses `gh` (GitHub CLI) directly. For a Graphite-based workflow that diffs against the Graphite parent branch, use `/create-pr-description` instead.

### Skill attribution (GitHub)

Before creating the PR with `gh pr create`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Created with** footer for `SKILL_DIR` = `create-pr` to the PR body.

## Workflow

```
Verify branch has commits + tests pass
            |
            v
Compute diff (base..HEAD)
            |
            v
Issue provided? ($1 $2)
   /              \
 Yes               No
  |                 |
  v                 v
Fetch issue       Skip AC
+ map ACs         coverage
  |                 |
  +--------+--------+
           |
           v
Pre-captured proof? ($PROOF_DIR/captured-proof.json)
   /              \
 Yes               No
  |                 |
  v                 v
Read manifest   Before-only state? (proof-manifest.txt
(mode + assets)  exists, captured-proof.json absent)
  |                 /          \
  |               Yes           No
  |                |            |
  |                v            v
  |          Embed before      Omit Visual proof;
  |          alone, note       suggest /validate-
  |          after pending     implementation first
  |                |            |
  +--------+-------+------------+
           |
           v
Embed proof in description (single, or before/after pair)
            |
            v
     should-post-to-github allows?
       /          \
     No            Yes
      |             |
      v             v
Show draft    Upload resolved
to user,      assets to branch
stop           |
                v
           gh pr create (draft if incomplete)
                |
                v
           Assign reviewers (if known)
```

## Steps

1. Confirm the branch has commits ahead of the base:
   ```
   git log origin/$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null | sed 's|origin/||')..HEAD --oneline
   ```
   If no commits, stop and inform the user.

2. Confirm tests pass before opening:
   Run the project's test command. If tests fail, stop and list the failures.

3. Compute the diff against the base branch:
   ```
   git diff $(git merge-base HEAD origin/main)..HEAD
   ```

4. If `$1` (repository) and `$2` (issue number) are provided, fetch the issue:
   ```
   ghx issue view $2 --repo $1
   ```
   Map each acceptance criterion to the changes in the diff.
   Note any ACs not yet addressed (to call out in the description).

5. Resolve the visual proof to embed. `create-pr` consumes proof captured beforehand by [`/validate-implementation`](../validate-implementation/SKILL.md); it does not capture recordings itself. Resolve the proof directory and detect what is available:

   ```bash
   REPO="${1:-$REPO}"
   ISSUE_NUMBER="${2:-$ISSUE_NUMBER}"
   PROOF_DIR="/tmp/$REPO/${ISSUE_NUMBER:-housekeeping}"   # /tmp/<owner>/<repo>/<issue-id>
   ```

   **Authoritative source — `captured-proof.json`** (written by `/validate-implementation`):

   ```bash
   test -f "$PROOF_DIR/captured-proof.json"
   ```

   If present, read it. It is authoritative for which assets to embed:

   ```json
   {
     "captured_at": "<ISO>",
     "surface": "cli" | "web" | "none",
     "mode": "single" | "bugfix-pair" | "bugfix-before-only",
     "assets": ["pr-demo.gif"] | ["before-bug.gif", "after-fix.gif"]
   }
   ```

   Embed exactly the files listed in `assets` (resolved against `$PROOF_DIR`), in listed order. Render Before / After layout when `mode` is `bugfix-pair` (or `bugfix-before-only`, embedding just the before with a note that after is pending via `/validate-implementation`). Render the single-asset block when `mode` is `single`.

   **Partial state — before only, no manifest yet:** If `captured-proof.json` is absent but `$PROOF_DIR/proof-manifest.txt` exists (reproduce-issue captured a before, but `/validate-implementation` has not yet produced the after), embed the existing `$PROOF_DIR/before-bug.*` alone with a note that the after recording is pending, and suggest running `/validate-implementation` to complete the pair.

   **No proof captured:** If neither manifest exists, omit the Visual proof section entirely and note in the PR description (or in console output before creation) that `/validate-implementation` can capture proof. Do not attempt to capture here.

    This is a representative proof, not a claim-by-claim demonstration (that is `/verify-pr`'s job).

6. Decide whether to create the PR on GitHub: set `PR_AUTHOR=$(gh api user --jq .login)` and run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`. If it exits 1, skip asset upload and PR creation: present the draft description to the user (referencing local file paths for any proof) and stop.

7. Upload the resolved asset(s) (from step 5) to the branch and note their raw URLs for the description. Upload only the assets chosen in step 5, not everything in `$PROOF_DIR`:
   ```
   for asset in "$PROOF_DIR"/<asset-from-step-5>; do
     [ -f "$asset" ] || continue
     gh api repos/$1/contents/.create-pr-proof/$(basename "$asset") \
       --method PUT \
       -f message="Add visual proof" \
       -f content="$(base64 -w 0 "$asset")" \
       -f branch="$(git rev-parse --abbrev-ref HEAD)"
   done
   ```
   When `captured-proof.json` is the source, iterate its `assets` list rather than a glob, so unrelated files in `$PROOF_DIR` are not uploaded. Omit `--repo` if the repository can be inferred from the current working directory. For each uploaded asset, derive its raw URL as `https://raw.githubusercontent.com/$1/<branch>/.create-pr-proof/<basename>`.

8. Draft the PR description following the output format below, embedding the proof if one was captured. Do not line wrap the description; each paragraph/bullet should be a single long line.

9. Create the PR. Use `--draft` if any acceptance criteria are unmet:
   ```
   gh pr create --repo $1 --title "<title>" --body "$(cat <<'EOF'
   <description>
   EOF
   )" [--draft]
   ```
   Omit `--repo` if the repository can be inferred from the current working directory.

10. If reviewer GitHub handles are known from context, assign them:
   ```
   gh pr edit <pr-number> --add-reviewer <handle>
   ```

## PR Description Format

```markdown
# What

<Present-tense summary of changes. Bullet points for multiple changes.>

# Why

<Problem being solved or feature being added. Reference the issue.>

# How to test

<Manual verification steps only. Exclude anything already covered by CI (lint, typecheck, unit tests, integration tests, build, etc.) since reviewers can see those results automated. Focus on steps that require human judgment or manual interaction.>

1. <Step to manually verify the change works>
2. <Step for a manual edge case or error path>

# Visual proof

![demo](raw-github-url-to-asset)

*Captured beforehand by `/validate-implementation`. Run `/verify-pr` for claim-by-claim conformance proof. Omit this section entirely if no proof was captured.*

For a bug fix with a paired before/after recording, use the Before / After layout instead of the single-asset block above:

```markdown
# Visual proof

**Before (bug reproduces):**

![before-bug](raw-github-url-to-before-asset)

**After (fixed):**

![after-fix](raw-github-url-to-after-asset)

*Before captured by `/reproduce-issue`; after captured by `/validate-implementation`. Run `/verify-pr` for claim-by-claim conformance proof.*
```

If only the before asset exists (after not yet captured), keep the Before block and note that the after will be added once `/validate-implementation` is run. Omit the section entirely if no proof was captured.

# Acceptance criteria coverage

- [x] <AC that is fully addressed>
- [x] <AC that is fully addressed>
- [ ] <AC not addressed in this PR — note why (out of scope, follow-up issue)>

# References

- Closes #<issue-number>

---

Created with [create-pr]({SKILL_FILE_URL}) (`SKILL_SHORT_SHA`)
```

Resolve `SKILL_FILE_URL` and `SKILL_SHORT_SHA` per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md).

Use `Closes #N` to auto-close the issue on merge. Use `Related to #N` if the PR only partially addresses the issue.

## Example Usage

**Scenario 1: Feature PR linked to an issue**
```
/create-pr owner/myrepo 42
```
Diffs branch, fetches issue #42, maps all 4 ACs to changes, creates PR with "Closes #42" and requests reviewers (unless `should-post-to-github` disables posting, in which case it drafts the description without creating the PR).

**Scenario 2: PR covering only part of an issue**
```
/create-pr owner/myrepo 88
```
Issue has 5 ACs; this branch addresses 3. Creates a ready-for-review PR, marks the 2 unmet ACs as unchecked with a note, uses "Related to #88" (or drafts the description without creating the PR if posting is disabled).

**Scenario 3: Housekeeping PR without an issue**
```
/create-pr
```
No issue provided. Creates PR with What/Why/How-to-test sections; omits AC coverage and References sections (or drafts the description without creating the PR if posting is disabled).

**Scenario 4: Incomplete implementation**
```
/create-pr owner/myrepo 100
```
One AC not yet met. Opens as a draft PR so it is not accidentally merged (or drafts the description without creating the PR if posting is disabled).

**Scenario 5: Web UI PR with embedded visual proof**
```
/create-pr owner/myrepo 130
```
`/validate-implementation` was run first and wrote `/tmp/<owner>/<repo>/130/captured-proof.json` listing `pr-demo-1280x720.png`. `create-pr` reads the manifest, uploads that PNG to `.create-pr-proof/`, and embeds it in a "Visual proof" section so reviewers see the change immediately. It does not start the dev server or capture anything itself. If posting is disabled, it drafts the description with local file references without uploading or creating the PR.

**Scenario 6: PR where no proof was captured**
```
/create-pr owner/myrepo 130
```
No `$PROOF_DIR/captured-proof.json` exists (the user skipped `/validate-implementation`). `create-pr` omits the "Visual proof" section and notes that `/validate-implementation` can capture proof first. The PR opens with the standard sections (or drafts the description without creating the PR if posting is disabled).

**Scenario 7: Bug-fix PR with paired before/after recordings**
```
/create-pr owner/myrepo 42
```
Branch is `fix/42-null-pointer-login`. `/validate-implementation` was run after the fix: it found `/tmp/<owner>/<repo>/42/proof-manifest.txt` (written earlier by `/reproduce-issue`, `surface: cli`), replayed that command on the fixed code into `after-fix.gif`, and wrote `captured-proof.json` with `mode: bugfix-pair` listing both `before-bug.gif` and `after-fix.gif`. `create-pr` reads the manifest, uploads both to `.create-pr-proof/`, and renders a Before / After section in the PR body so reviewers see the bug and the fix side by side. If posting is disabled, it drafts the description with local file references without uploading or creating the PR.

## Completion Checklist

Before requesting review, confirm:

- [ ] Issue linked (Closes vs Related to #N) with acceptance criteria mapped to coverage checkboxes
- [ ] Visual proof embedded if `/validate-implementation` captured it, the section omitted entirely if not (no placeholder left)

Self-check the PR against the [`review-pr` checklist](../review-pr/SKILL.md) and fix what you can, so review finds less to flag.

## Next Step

After the PR is open, use `/handle-pr-ci` if CI is failing, `/handle-pr-feedback` to address reviewer comments, and `/merge-pr` once CI is green and the PR is approved.
Run `/validate-pr` to confirm the PR builds the right product, then `/verify-pr` for claim-by-claim conformance proof with per-criterion recordings (the proof embedded here is a single representative asset captured by `/validate-implementation`).
Close the loop with `/create-learnings` after the feature is merged.

## Useful Commands Reference

| Command | Description |
|---|---|
| `git log origin/<base>..HEAD --oneline` | List commits ahead of the base branch |
| `git diff $(git merge-base HEAD origin/main)..HEAD` | Diff against the merge base |
| `ghx issue view <number> --repo <owner/repo>` | Fetch issue details (cached) |
| `gh pr create --repo <repo> --title "..." --body "..." [--draft]` | Open the pull request |
| `gh pr edit <number> --add-reviewer <handle>` | Assign a reviewer after creation |
| `gh api repos/<repo>/contents/<path> --method PUT -f content="$(base64 -w 0 <asset>)"` | Upload a visual-proof asset to the branch |
