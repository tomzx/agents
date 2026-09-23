# Memory

## 2026-09-23: assess-pr-risk is self-contained

- `assess-pr-risk` deliberately never consumes `analyze-test-coverage` / `validate-pr` / `verify-pr` / `review-pr` reports: the orchestrators dispatch it in parallel with the chain, so those reports do not exist yet when it runs. Do not "fix" it back to reading sibling reports.

## 2026-09-21: backpropagate-sdlc replaced by propagate-changes

- `skills/backpropagate-sdlc/` was renamed to `skills/propagate-changes/` and made bidirectional (rewrites dependents, questions premises); old references to backpropagate-sdlc mean this skill.

## 2026-09-21: dot-claude is out of scope

- Never modify `/home/tomzx/src/dot-claude/` (local opencode/claude install copies of skills). It is managed outside the agents repo and should be ignored.
