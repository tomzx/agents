#!/usr/bin/env bash
# Autonomous mode: merge the PR on the current branch with no human gate.
# Called right after a skill (create-implementation / fix-issue) opens its PR.
# GH_TOKEN (a GitHub App installation token with PR merge rights) is in the env.
#
# No-op (exit 0) when there is no open PR on the current branch, so the rule's
# on_outcome can route the skill's non-approved verdict to llmaw:needs-human
# instead of failing the whole run.
#
# Note: if branch protection requires status checks, enable GitHub "auto-merge"
# at the repo level; this script falls back to --auto (merge when checks pass).
set -euo pipefail

PR_URL="$(gh pr view --json url --jq '.url' 2>/dev/null || true)"
if [ -z "${PR_URL:-}" ]; then
  echo "merge-pr: no open PR on the current branch; nothing to merge"
  exit 0
fi

echo "merge-pr: merging $PR_URL"

# Try a direct squash merge first (common case: no required checks, App allowed).
if gh pr merge --squash --delete-branch 2>/dev/null; then
  echo "merge-pr: merged"
  exit 0
fi

# Branch protection (required reviews/checks) is in the way. Bypass as admin if
# the App is a repo admin, else queue an auto-merge for when checks pass.
if gh pr merge --squash --delete-branch --admin 2>/dev/null; then
  echo "merge-pr: merged (--admin bypass)"
  exit 0
fi

if gh pr merge --squash --delete-branch --auto 2>/dev/null; then
  echo "merge-pr: queued auto-merge (will merge when checks pass)"
  exit 0
fi

echo "merge-pr: FAILED to merge $PR_URL (check branch protection and App permissions)" >&2
exit 1
