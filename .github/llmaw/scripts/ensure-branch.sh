#!/usr/bin/env bash
# Ensure the per-issue working branch that carries the .sdlc/ artifact chain is
# checked out, creating it from the current branch if it does not exist yet.
#
# llmaw is stateless: every rule run starts from a fresh checkout, so the
# .sdlc/ artifacts a phase writes would be lost without persistence. This branch
# IS that persistence (state lives in GitHub, per the engine's design). Every
# SDLC phase that reads or writes .sdlc/ runs this as its first step.
#
# The branch name is derived deterministically from ISSUE_NUMBER, so no separate
# state is needed to locate it. Requires ISSUE_NUMBER (set by the dispatcher)
# and git push auth (provided by actions/checkout via the GITHUB_TOKEN remote).
set -euo pipefail

: "${ISSUE_NUMBER:?ISSUE_NUMBER must be set by the dispatcher}"
BRANCH="sdlc/issue-${ISSUE_NUMBER}"

# Identity for commits made by commit-sdlc.sh; safe-directory for the runner.
git config --global --add safe.directory '*' >/dev/null 2>&1 || true
git config user.email "llmaw-bot@users.noreply.github.com"
git config user.name "llmaw-bot"

if git fetch --depth=1 origin "$BRANCH" 2>/dev/null; then
  echo "ensure-branch: checking out existing $BRANCH"
  git checkout -B "$BRANCH" FETCH_HEAD
else
  echo "ensure-branch: creating $BRANCH from $(git rev-parse --abbrev-ref HEAD)"
  git checkout -B "$BRANCH"
fi

echo "ensure-branch: on $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"
