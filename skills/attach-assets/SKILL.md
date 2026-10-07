---
name: attach-assets
description: Upload files (images, logs, screenshots) to a dedicated orphan branch in the repository and embed them in a GitHub issue or PR comment or description, so sensitive content stays out of the main branch and out of inline user-attachments. Use when the user says /attach-assets, "attach image to issue", "attach screenshot to PR", "add image to a GitHub comment programmatically", "host issue images on a branch", "upload sensitive images for an issue", or wants to embed files in a GitHub description or comment without committing them to main.
allowed-tools: Bash(gh:*, git:*), Read
argument-hint: "<issue-or-pr-url-or-number> <file> [<file>...] [--pr] [--to-body] [--branch assets]"
---

# Attach Assets

Copies one or more local files onto a dedicated **orphan branch** in the repository via a throwaway git worktree, then embeds them in a GitHub issue or PR as a comment (default) or appended to the description body.
The files never land on the default branch and never become inline `user-attachments`, which suits sensitive screenshots, logs, and internal diagrams.

Because the branch is orphan (no shared history with `main`) and the files are placed through a temporary worktree, the user's working branch and tree are left untouched.
The assets are still in git history on that branch, so they are visible to everyone with read access to the repo and persist until the branch is deleted and history rewritten; do not use this for material that must never enter the repo at all (use signed expiring object-store URLs for that).

## Prerequisites

- The command runs inside a working clone of the target repository.
- `git` with push access to the repository.
- `gh` CLI authenticated with write access, for posting the comment or patching the description body.
- Files must be under GitHub's per-file size limit (roughly 100 MB), since they are committed through ordinary git.
- A target issue or PR.
  Provide a full GitHub URL for unambiguous parsing, or a bare number with `--pr` / `--issue` (default) using the current repository.
- For private repos, the rendered image is visible to collaborators when viewed in the issue or PR, but the raw URL itself requires a token for a direct fetch.

## Skill attribution (GitHub)

Before posting the comment or patching the body, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Posted with** footer for `SKILL_DIR` = `attach-assets` to the posted body.

## Path scheme

Each upload is written to the orphan branch under a directory named after the issue or PR number.
GitHub issues and PRs share one number sequence, so the number alone is unambiguous:

```
<number>/<filename>
```

If the same filename is uploaded twice to the same number, the second upload overwrites the first on the branch; give the file a distinct name instead.

## Workflow

```
Parse target ref -> (REPO, KIND=issues|pulls, NUMBER)
             |
             v
Verify files exist
             |
             v
Add a throwaway worktree on orphan branch `assets`
(existing branch checked out; new branch created empty with --orphan)
             |
             v
Copy files into <NUMBER>/ and git add + commit
             |
             v
Push to origin <ASSET_BRANCH>, then remove the worktree
             |
             v
Build markdown (image vs. link per extension)
             |
             v
Attach: comment (default) or append to body (--to-body)
             |
             v
Print raw URLs + branch paths
```

## Steps

### 1. Parse the target reference

```bash
TARGET="$1"; shift
FILES=("$@")
ASSET_BRANCH="${ASSET_BRANCH:-assets}"   # override via --branch <name>
MODE="comment"                            # --to-body switches this to "body"
KIND_DEFAULT="issues"                     # --pr switches to "pulls"
# Parse --pr / --issue / --to-body / --branch out of FILES as needed.
```

Resolve `REPO`, `KIND`, `NUMBER`:

```bash
case "$TARGET" in
  *github.com*)
    REPO=$(printf '%s' "$TARGET" | sed -E 's#https?://github.com/([^/]+/[^/]+)(/.*)?#\1#')
    KIND=$(printf '%s' "$TARGET" | grep -oE '/(issues|pull)/' | tr -d '/' | sed 's#^pull$#pulls#')
    NUMBER=$(printf '%s' "$TARGET" | grep -oE '/(issues|pull)/[0-9]+' | grep -oE '[0-9]+$')
    ;;
  *)
    REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
    NUMBER="$TARGET"
    KIND="$KIND_DEFAULT"
    ;;
esac
```

`KIND` is only used to choose the body endpoint; the asset path uses `NUMBER` alone.

### 2. Verify the files

```bash
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "::error::not a file: $f"; exit 1; }
done
```

### 3. Stage a temporary worktree on the orphan branch

```bash
STAGE=$(mktemp -d)
if git ls-remote --exit-code --heads origin "$ASSET_BRANCH" >/dev/null 2>&1; then
  git fetch origin "$ASSET_BRANCH" --quiet
  git worktree add --detach --quiet "$STAGE" "origin/$ASSET_BRANCH" >/dev/null
else
  git worktree add --no-checkout --detach --quiet "$STAGE" >/dev/null
  git -C "$STAGE" checkout --orphan "$ASSET_BRANCH" >/dev/null
  git -C "$STAGE" read-tree --empty          # start the orphan with no staged files
fi
```

The worktree isolates all work from the user's current branch.
On an existing asset branch the asset tree is checked out so new files sit beside prior uploads; on a new branch an empty orphan is created (no shared history with `main`).

### 4. Place the files, commit, and push

```bash
mkdir -p "$STAGE/$NUMBER"
for f in "${FILES[@]}"; do cp -f "$f" "$STAGE/$NUMBER/"; done
git -C "$STAGE" add "$NUMBER/"
git -C "$STAGE" commit -q -m "Add assets via /attach-assets (#$NUMBER)"
git -C "$STAGE" push --quiet origin "HEAD:refs/heads/$ASSET_BRANCH"
git worktree remove --force "$STAGE"
```

`HEAD:refs/heads/$ASSET_BRANCH` creates the branch on first push and fast-forwards it afterwards.
If the remote advanced since the fetch, the push is rejected (non-fast-forward); refetch and rerun.

If a file's path already exists on the branch (same name, same number), git records it as a modification and overwrites the prior blob; rename the file to keep the previous version.

### 5. Build the markdown

```bash
raw="https://raw.githubusercontent.com/$REPO/$ASSET_BRANCH"
md=""
for f in "${FILES[@]}"; do
  name=$(basename "$f")
  url="$raw/$NUMBER/$name"
  case "$name" in
    *.png|*.jpg|*.jpeg|*.gif|*.webp|*.svg) md+="![${name%.*}]($url)"$'\n\n' ;;
    *) md+="[\`$name\`]($url)"$'\n\n' ;;
  esac
done
# Append the attribution footer per github-post-attribution.
md+="$(footer_for attach-assets)"
```

### 6. Attach to the issue or PR

Post a comment (default):

```bash
if [ "$MODE" = "body" ]; then
  ep="$KIND"  # issues/$N or pulls/$N
  body=$(gh api "repos/$REPO/$ep/$NUMBER" --jq '.body // ""')
  body+=$'\n\n### Assets\n\n'"$md"
  gh api "repos/$REPO/$ep/$NUMBER" -X PATCH -f body="$body" >/dev/null
else
  gh api "repos/$REPO/issues/$NUMBER/comments" -f body="$md" >/dev/null
fi
```

The `issues/$NUMBER/comments` endpoint accepts comments on both issues and pull requests.

## Output Format

After attaching, print a short summary:

```
## Attached assets -> {REPO}#{NUMBER} ({KIND})

Branch: {ASSET_BRANCH} ({new|existing})
Mode:   comment | body

- 42/error.png
  https://raw.githubusercontent.com/<owner>/<repo>/assets/42/error.png
- ...

Comment: https://github.com/<owner>/<repo>/issues/42#issuecomment-<id>
```

## Example Usage

**Scenario 1: Attach screenshots to an issue by URL**
```
/attach-assets https://github.com/owner/repo/issues/42 ./error.png ./trace.png
```
Creates the orphan branch `assets`, writes `42/error.png` and `42/trace.png`, and posts a comment embedding both.

**Scenario 2: Attach to a PR by number**
```
/attach-assets 88 ./before.png ./after.png --pr
```
Uses the current repo, writes under `88/`, and posts the comment on PR 88.

**Scenario 3: Append to the PR description instead of a comment**
```
/attach-assets https://github.com/owner/repo/pull/88 ./diagram.png --to-body
```
Fetches the PR body, appends an `### Assets` section with the image, and PATCHes the description.

**Scenario 4: Custom asset branch**
```
ASSET_BRANCH=internal-assets /attach-assets 42 ./secret.png
```
Uses `internal-assets` instead of the default `assets`.

**Scenario 5: Large or non-image file**
```
/attach-assets 42 ./heap-dump.bin
```
Commits the binary through git (no encoding) and posts a `[heap-dump.bin](url)` link.

## Completion Checklist

- [ ] Target parsed to `(REPO, KIND, NUMBER)` with no ambiguity (URL or explicit `--pr`)
- [ ] Every file verified to exist before any upload
- [ ] Worktree created on the orphan branch (empty on first run, checked out afterwards) and removed after push
- [ ] Markdown uses image syntax for images and link syntax for other files
- [ ] Comment posted or body patched, with the `github-post-attribution` footer attached
- [ ] Raw URLs printed back to the user

## Useful Commands Reference

| Command | Description |
|---|---|
| `git ls-remote --exit-code --heads origin <branch>` | Test whether the asset branch already exists on the remote |
| `git worktree add --no-checkout --detach <path>` | Add an isolated worktree without touching the current branch |
| `git checkout --orphan <branch> && git read-tree --empty` | Start an empty orphan branch with no shared history |
| `git -C <stage> add <number>/ && git commit && git push origin HEAD:refs/heads/<branch>` | Stage, commit, and push the assets |
| `git worktree remove --force <path>` | Tear down the temporary worktree |
| `gh api repos/<repo>/issues/<n>/comments -f body=<md>` | Post a comment to an issue or PR |
| `gh api repos/<repo>/pulls/<n> -X PATCH -f body=<md>` | Append assets to a PR description |
