---
name: create-placeholder-issue
description: Create a placeholder GitHub issue for a pending SDLC feature (one created without an issue, with a p-prefixed directory) and promote it to issue-driven form by renaming its directory and rewriting FEAT- cross-references. Use when the user says /create-placeholder-issue, wants to promote a pending feature, wants to back an existing SDLC feature with a GitHub issue, or wants to convert a p-prefixed feature directory into an issue-numbered one. For starting top-down from a feature request, use create-issue instead.
argument-hint: "[feature]"
---

# Create Placeholder Issue

Creates a minimal placeholder GitHub issue for a **pending** SDLC feature, then promotes the feature to issue-driven form: renames the directory to the new issue number and rewrites every `FEAT-p<seq>` cross-reference to `FEAT-<issue>`.

This is the promotion step defined by the Feature Directory Naming convention in `skills/sdlc/references/shared.md`. Use it for features created bottom-up (e.g. by `sync-sdlc` from code analysis) that have no GitHub issue yet. For top-down work where you start from a feature request, use `/create-issue`, which produces a full structured issue.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `gh` CLI authenticated with write access to create issues in the target repository.
- A pending feature directory `p<seq>-<slug>` under `.sdlc/features/` (resolved via SDLC_DIR if set).

### Skill attribution (GitHub)

Before creating the issue, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Created with** footer for `SKILL_DIR` = `create-placeholder-issue` to the issue body.

## Formatting

- Straight ASCII quotes only, no curly/typographic quotation marks (same rule as `/create-issue`).

## Steps

1. **Resolve the target feature.** Use `$1` if provided (a feature id like `FEAT-p1`, the token `p1`, or a directory name `p1-<slug>`). Otherwise read `.sdlc/state.yml` `feature`; if that is unset and exactly one `p`-prefixed directory exists under `.sdlc/features/`, use it. If none can be resolved, stop and report `not-found`.

2. **Locate the feature directory** via SDLC_DIR resolution (repo first, then `$SDLC_DIR/{owner}/{repo}/.sdlc/`). Record both locations when mirrored.

3. **Verify it is pending.** If the directory token is numeric, the feature is already issue-driven: stop and report `already-issue-driven` with the issue number from its frontmatter. If the token is not `p`-prefixed, stop with an error.

4. **Duplicate check.** Read the feature's frontmatter `issue` field; if it is already set, treat the feature as already promoted (`already-issue-driven`). Otherwise search for an existing open issue mentioning the feature slug and "placeholder":
   ```
   gh issue list --search "<slug> placeholder" --state open --limit 10
   ```
   If one is found that was produced by this skill, reuse its number `M` and skip to step 7 (rename), linking the existing issue instead of creating a duplicate.

5. **Derive the issue title and body.**
   - **Title:** the feature's frontmatter `title` if present, otherwise humanize the `<slug>` (e.g. `notification-system` -> `Notification system`).
   - **Body:** build a placeholder body. If the feature has a `requirements.md`, include its overview paragraph and acceptance criteria (rendered as a checklist) so the issue is immediately useful; otherwise use a minimal stub. Always include:
     - a visible one-line note that this is a placeholder auto-created for a pending SDLC feature, to be fleshed out (this visible text also makes the duplicate search work),
     - an HTML comment marker `<!-- sdlc-placeholder:p<seq>-<slug> -->` recording the originating feature directory,
     - a reference to the feature directory path.
   - Append the **Created with** attribution footer resolved from `github-post-attribution/SKILL.md`.

6. **Create the issue.** Apply labels only if they already exist: prefer a `sdlc-placeholder` label if present (so placeholders are filterable), otherwise apply no labels. Do not create labels. Omit `--repo` to let `gh` infer the repository from the working directory.
   ```
   gh issue create --title "<title>" --body "$(cat <<'EOF'
   <body>
   EOF
   )" [--label sdlc-placeholder]
   ```
   Capture the returned issue number as `M` and the URL.

7. **Rename the feature directory.** `p<seq>-<slug>` -> `M-<slug>`. Use `git mv` when the directory is inside a git work tree (`.sdlc/` is tracked); otherwise plain `mv`. Apply the rename in every resolved location (repo and SDLC_DIR mirror).
   ```
   git mv .sdlc/features/p<seq>-<slug> .sdlc/features/M-<slug>
   ```

8. **Rewrite the feature identifier everywhere.** Replace every occurrence of `FEAT-p<seq>` with `FEAT-M` across all `.md` and `.yml` files under `.sdlc/` (and the mirror). This covers frontmatter `feature:` fields, qualified cross-references like `FEAT-p1-FR-2`, and progress/state files.

   Match the token with a trailing non-digit boundary so adjacent ids are not corrupted (e.g. `FEAT-p2` must not match inside `FEAT-p20`). With the real values substituted (here `p2` -> `137`):
   ```
   rg -l --no-ignore 'FEAT-p2' .sdlc | xargs perl -i -pe 's/\bFEAT-p2(?!\d)/FEAT-137/g'
   ```
   The `(?!\d)` lookahead prevents the partial-match problem; `\b` anchors the left side at the `F`.

9. **Set the issue reference in frontmatter.** In every artifact under the renamed feature directory that has YAML frontmatter, set `issue: "#M"` (add the field if absent, update if present). Update `.sdlc/state.yml`: set `github_ref: "#M"` and, if its `feature:` field referenced this feature, update it to `FEAT-M-<slug>`.

10. **Leave the placeholder marker in place.** Do not flesh out the issue body here. The `<!-- sdlc-placeholder -->` marker is cleared only once a later pass (or `/create-issue` in revision) replaces the stub with full background, acceptance criteria, and time budget.

11. **Emit outcome** (see Outcome).

## Output Format

```
## Placeholder issue created

- Feature: FEAT-p<seq>-<slug> -> FEAT-M-<slug>
- Issue: #M  <url>
- Directory renamed: .sdlc/features/p<seq>-<slug>/ -> .sdlc/features/M-<slug>/
- Cross-references rewritten: <count> occurrences across <n> files
- Frontmatter issue field set: "#M"
- Labels: sdlc-placeholder (or none)
```

No-op cases:

```
## Already issue-driven
- Feature FEAT-M-<slug> already has issue #M. Nothing to do.
```

## Outcome

When `$OUTCOME_YAML` is set, write exactly one `verdict`:

| Verdict | When |
|---|---|
| `promoted` | Placeholder issue created (or reused) and feature promoted to `FEAT-M`. |
| `already-issue-driven` | The feature was already numeric, or its frontmatter `issue:` was already set. No change. |
| `not-found` | No pending feature directory could be resolved. |
| `error` | Issue creation failed (no write access, `gh` not authenticated, rename failed, etc.). |

Example:
```yaml
verdict: promoted
reason: "Created issue #137 and renamed p2-billing to 137-billing"
```

## Example Usage

**Scenario 1: Promote a single pending feature**
```
/create-placeholder-issue FEAT-p1
```
Creates a placeholder issue (#137), renames `p1-notification-system` -> `137-notification-system`, rewrites `FEAT-p1` -> `FEAT-137` everywhere, sets `issue: "#137"`.

**Scenario 2: Promote the only pending feature (no argument)**
```
/create-placeholder-issue
```
Resolves the single `p*` directory under `.sdlc/features/` and promotes it.

**Scenario 3: Re-run is safe (duplicate check)**
```
/create-placeholder-issue FEAT-p1
```
If the skill was interrupted after issue creation but before the rename, the duplicate search finds the existing placeholder issue and resumes at the rename step instead of creating a second issue.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh issue create --title "..." --body "..."` | Create the placeholder issue |
| `gh issue list --search "<slug> placeholder" --state open --limit 10` | Duplicate check before creating |
| `gh label list --json name --jq '.[].name'` | Check whether a `sdlc-placeholder` label exists |
| `rg -l --no-ignore 'FEAT-p2' .sdlc` | Find every file referencing the old feature id |
| `perl -i -pe 's/\bFEAT-p2(?!\d)/FEAT-137/g' <file>` | Boundary-safe id rewrite (avoids corrupting `FEAT-p20`) |
| `git mv .sdlc/features/p<seq>-<slug> .sdlc/features/M-<slug>` | Rename the directory inside a tracked repo |
