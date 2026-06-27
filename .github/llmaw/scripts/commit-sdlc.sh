#!/usr/bin/env bash
# Commit and push any .sdlc/ changes on the per-issue working branch so the next
# isolated rule run can read them.
#
# Forces .sdlc/state.yml and features/*/progress.md past .sdlc/.gitignore: those
# files are local-only by design for human sessions, but in automation there is
# no session to resume from, so the run state must live on the branch.
#
# No-op when there is nothing to commit, or when the current branch is not the
# working branch (e.g. create-implementation switched to its own impl/ branch to
# open a PR, in which case its .sdlc/ edits ride on that PR).
set -euo pipefail

: "${ISSUE_NUMBER:?ISSUE_NUMBER must be set by the dispatcher}"
BRANCH="sdlc/issue-${ISSUE_NUMBER}"

current="$(git rev-parse --abbrev-ref HEAD)"
if [ "$current" != "$BRANCH" ]; then
  echo "commit-sdlc: not on $BRANCH (on $current); skipping"
  exit 0
fi

# Stage all of .sdlc/, overriding the local-only gitignore for state files.
if [ -d .sdlc ]; then
  git add -f .sdlc
fi

if git diff --cached --quiet; then
  echo "commit-sdlc: no changes to commit"
  exit 0
fi

git commit -m "chore(sdlc): update .sdlc artifacts for issue #${ISSUE_NUMBER}

Committed by llmaw per-issue working-branch automation."

git push origin "$BRANCH"
echo "commit-sdlc: pushed $BRANCH"
