---
name: create-pr
description: Create a GitHub pull request with a structured description linked to its issue, with acceptance criteria coverage and reviewer assignment. Optionally captures a lightweight visual proof (CLI demo via record-asciinema, or web screenshot via record-playwright) and embeds it in the PR body. For bug fixes, pairs a before recording (from reproduce-issue) with an after recording in a side-by-side section.
allowed-tools: Bash(gh:*, git:*, ghx:*, asciinema:*, agg:*, npx:*, node:*, uv:*, python:*, python3:*, curl:*, scripts/get-env:*), Read, Write, Glob, Grep
argument-hint: "[repository] [issue-number]"
---

# Create Pull Request

Opens a GitHub pull request for the current branch with a structured description that maps implementation changes to acceptance criteria, links the originating issue, and requests reviewers. When the diff touches a CLI or web UI surface, it captures a single lightweight recording or screenshot and embeds it inline so reviewers see proof the moment the PR opens.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, use `$REPO` and link `$ISSUE_NUMBER`.
- `gh` CLI authenticated with write access to the target repository
- Current branch has commits not on the base branch
- A related GitHub issue number (strongly recommended; omit only for housekeeping PRs)
- Tests passing locally before the PR is opened
- For visual proof (optional): `asciinema` + renderer for CLI changes (via [`/record-asciinema`](../record-asciinema/SKILL.md)), or Playwright for web UI changes (via [`/record-playwright`](../record-playwright/SKILL.md)). If unavailable, the visual-proof step is skipped silently.

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
Bug-fix manifest present?
   /              \
 Yes               No
  |                 |
  v                 v
Capture after    Classify diff
(same cmd/URL    (CLI or web UI?)
 as before)         /          \
  |               Yes           No
  |                |            |
  |                v            v
  |            Capture proof  Skip proof
  |           (record-asciinema /
  |            record-playwright)
  |                |
  +--------+-------+
           |
           v
Draft PR description (embed proof; before/after if paired)
           |
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

5. Capture visual proof (optional, best-effort). First detect whether this is a bug fix with a paired before/after recording, then fall back to a single representative asset.

   Resolve the proof directory (per-repo, per-issue, so assets never collide with other work):
   ```
   REPO="${1:-$REPO}"
   ISSUE_NUMBER="${2:-$ISSUE_NUMBER}"
   PROOF_DIR="/tmp/$REPO/${ISSUE_NUMBER:-housekeeping}"   # /tmp/<owner>/<repo>/<issue-id>
   mkdir -p "$PROOF_DIR" 2>/dev/null || true
   ```

   **Bug-fix fast path (before/after):** Check for a before-recording manifest written by `reproduce-issue`:
   ```
   test -f "$PROOF_DIR/proof-manifest.txt"
   ```
   If present, read it to recover the surface and the demonstration command/URL used to capture the bug:
   ```
   cat "$PROOF_DIR/proof-manifest.txt"
   ```
   Then capture the matching **after** recording on the now-fixed code using the exact same command/URL, so the pair is directly comparable:
   - `surface: cli` → read [`../record-asciinema/SKILL.md`](../record-asciinema/SKILL.md) and invoke it with `RECORD_SLUG` = `after-fix`, `RECORD_DIR` = `$PROOF_DIR`, `RECORD_COMMAND` = the manifest's command.
   - `surface: web` → read [`../record-playwright/SKILL.md`](../record-playwright/SKILL.md) and invoke it with `RECORD_SLUG` = `after-fix`, `RECORD_DIR` = `$PROOF_DIR`, `RECORD_URL` = the manifest's url, `RECORD_VIEWPORTS` = `1280x720`, `RECORD_SERVER_CMD` = the manifest's server_cmd.

   The before asset is the existing `$PROOF_DIR/before-bug.*`; the after asset is the freshly captured `$PROOF_DIR/after-fix.*`. Note both paths: step 6 uploads the pair and step 7 renders a Before / After section. If the after capture fails, fall back to embedding the before asset alone so the bug is still visible.

   **Default (single asset):** With no manifest present, classify the change surface from the diff in step 3 and capture one representative asset:
   - **CLI changes** (entry points, `cli/`, `cmd/`, argument parsing, `--help`): identify the CLI entry point from the codebase and pick one representative command that exercises the change. Read [`../record-asciinema/SKILL.md`](../record-asciinema/SKILL.md) and invoke it with:
     - `RECORD_SLUG` = `pr-demo`
     - `RECORD_DIR` = `$PROOF_DIR`
     - `RECORD_COMMAND` = the representative command
   - **Web UI changes** (`src/pages`, routes, components, templates, CSS): identify the dev server command (e.g. `npm run dev`) and the changed route, then read [`../record-playwright/SKILL.md`](../record-playwright/SKILL.md) and invoke it with:
     - `RECORD_SLUG` = `pr-demo`
     - `RECORD_DIR` = `$PROOF_DIR`
     - `RECORD_URL` = the changed route
     - `RECORD_VIEWPORTS` = `1280x720` (a single desktop shot is enough for the PR body)
     - `RECORD_SERVER_CMD` = the dev server command, so the skill starts, waits, and tears it down itself
   - **Neither / not determinable**: skip visual proof.

   Whether one or two assets are captured, this is a representative proof, not a claim-by-claim demonstration (that is `/validate-pr`'s job). If a recording skill is unavailable or the entry point cannot be determined, skip silently and proceed without proof.

6. Upload the captured asset(s) to the branch and note their raw URLs for the description:
   ```
   for asset in "$PROOF_DIR"/before-bug.* "$PROOF_DIR"/*.gif "$PROOF_DIR"/*.png "$PROOF_DIR"/*.svg; do
     [ -f "$asset" ] || continue
     gh api repos/$1/contents/.create-pr-proof/$(basename "$asset") \
       --method PUT \
       -f message="Add visual proof" \
       -f content="$(base64 -w 0 "$asset")" \
       -f branch="$(git rev-parse --abbrev-ref HEAD)"
   done
   ```
   Omit `--repo` if the repository can be inferred from the current working directory. For each uploaded asset, derive its raw URL as `https://raw.githubusercontent.com/$1/<branch>/.create-pr-proof/<basename>`.

7. Draft the PR description following the output format below, embedding the proof if one was captured. Do not line wrap the description; each paragraph/bullet should be a single long line.

8. Create the PR. Use `--draft` if any acceptance criteria are unmet:
   ```
   gh pr create --repo $1 --title "<title>" --body "$(cat <<'EOF'
   <description>
   EOF
   )" [--draft]
   ```
   Omit `--repo` if the repository can be inferred from the current working directory.

9. If reviewer GitHub handles are known from context, assign them:
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

1. <Step to verify the change works>
2. <Step for an edge case or error path>

# Visual proof

![demo](raw-github-url-to-asset)

*Captured at PR creation. Run `/validate-pr` for claim-by-claim validation. Omit this section entirely if no proof was captured.*

For a bug fix with a paired before/after recording, use the Before / After layout instead of the single-asset block above:

```markdown
# Visual proof

**Before (bug reproduces):**

![before-bug](raw-github-url-to-before-asset)

**After (fixed):**

![after-fix](raw-github-url-to-after-asset)

*Before captured by `/reproduce-issue`; after captured at PR creation. Run `/validate-pr` for claim-by-claim validation.*
```

If only the before asset exists (after capture failed), keep the Before block and note that the after will be added on re-run. Omit the section entirely if no proof was captured.

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
Diffs branch, fetches issue #42, maps all 4 ACs to changes, creates PR with "Closes #42" and requests reviewers.

**Scenario 2: PR covering only part of an issue**
```
/create-pr owner/myrepo 88
```
Issue has 5 ACs; this branch addresses 3. Creates a ready-for-review PR, marks the 2 unmet ACs as unchecked with a note, uses "Related to #88".

**Scenario 3: Housekeeping PR without an issue**
```
/create-pr
```
No issue provided. Creates PR with What/Why/How-to-test sections; omits AC coverage and References sections.

**Scenario 4: Incomplete implementation**
```
/create-pr owner/myrepo 100
```
One AC not yet met. Opens as a draft PR so it is not accidentally merged.

**Scenario 5: Web UI PR with embedded visual proof**
```
/create-pr owner/myrepo 130
```
Diff touches `src/pages/dashboard.tsx`. Starts the dev server, captures a desktop screenshot of `/dashboard` via `/record-playwright`, uploads it to `.create-pr-proof/`, and embeds it in a "Visual proof" section so reviewers see the change immediately.

**Scenario 6: CLI PR where recording tools are absent**
```
/create-pr owner/myrepo 130
```
Diff touches CLI code but `asciinema` is not installed. The visual-proof step is skipped silently; the PR opens with the standard sections and no "Visual proof" section.

**Scenario 7: Bug-fix PR with paired before/after recordings**
```
/create-pr owner/myrepo 42
```
Branch is `fix/42-null-pointer-login`. `/tmp/<owner>/<repo>/42/proof-manifest.txt` exists (written earlier by `/reproduce-issue`), recording `surface: cli` with the command that triggered the crash. `create-pr` replays that same command on the fixed code via `/record-asciinema` into `/tmp/<owner>/<repo>/42/after-fix.gif`, uploads both `before-bug.gif` and `after-fix.gif` to `.create-pr-proof/`, and renders a Before / After section in the PR body so reviewers see the bug and the fix side by side.

## Completion Checklist

Before requesting review, confirm:

- [ ] Issue linked (Closes vs Related to #N) with acceptance criteria mapped to coverage checkboxes
- [ ] Visual proof embedded if captured, the section omitted entirely if not (no placeholder left)

Self-check the PR against the [`review-pr` checklist](../review-pr/SKILL.md) and fix what you can, so review finds less to flag.

## Next Step

After the PR is open, use `/handle-pr-ci` if CI is failing, `/handle-pr-feedback` to address reviewer comments, and `/merge-pr` once CI is green and the PR is approved.
Run `/validate-pr` for claim-by-claim runtime validation with per-claim recordings (the proof captured here is a single representative asset).
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
