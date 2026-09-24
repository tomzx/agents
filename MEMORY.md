# Memory

## 2026-09-24: scheduled runs and interactive sessions collide in one repo

- Repos with scheduled agent tasks (e.g. the blog's daily 03:00 refresh) can have a scheduled run commit mid-way through an interactive owner-driven session; twice in one day the scheduled run's wholesale `git add agents/` swept finished-but-uncommitted files from the concurrent session into its own commit.
- When working such a repo interactively, check `git log` for new commits before staging, prefer staging the exact paths touched over directory adds, and expect a mid-session commit to publish in-flight work; the section logs record who wrote what, so reconcile through the log rather than reverting.

## 2026-09-24: duplicate search before codebase investigation

- When filing an issue (create-issue or similar), run the duplicate search before any codebase investigation: the bug report itself usually provides enough search keywords, and deep code tracing only pays off once no duplicate exists or filing is confirmed.

## 2026-09-23: assess-pr-risk is self-contained

- `assess-pr-risk` deliberately never consumes `analyze-test-coverage` / `validate-pr` / `verify-pr` / `review-pr` reports: the orchestrators dispatch it in parallel with the chain, so those reports do not exist yet when it runs. Do not "fix" it back to reading sibling reports.

## 2026-09-21: backpropagate-sdlc replaced by propagate-changes

- `skills/backpropagate-sdlc/` was renamed to `skills/propagate-changes/` and made bidirectional (rewrites dependents, questions premises); old references to backpropagate-sdlc mean this skill.

## 2026-09-21: dot-claude is out of scope

- Never modify `/home/tomzx/src/dot-claude/` (local opencode/claude install copies of skills). It is managed outside the agents repo and should be ignored.
