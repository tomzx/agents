# Memory

## 2026-09-21: backpropagate-sdlc replaced by propagate-changes

- `skills/propagate-changes/` replaces `skills/backpropagate-sdlc/`: same SDLC artifact-chain walks, now bidirectional (downward: rewrite dependents when the resolution follows mechanically; upward: question premises, flag drift, regress review verdicts only).
- Downward rewrites set artifact `status: in-review` and bump `revision`; report file is `propagation-report.md` (renamed from `backpropagation-report.md` in shared.md's never-mirrored list).
- References updated in: README.md, skills/trace-issues/SKILL.md, skills/sdlc/references/shared.md, skills/sdlc/SKILL.md, skills/pdlc/skills/audit-outcomes/SKILL.md, sdlc-slides.html.
- Grounded in the blog article `what-needs-updating-when-agents-do-the-work` (artifact graph, propagation in both directions, raise questions where resolutions are ambiguous).

## 2026-09-21: dot-claude is out of scope

- Never modify `/home/tomzx/src/dot-claude/` (local opencode/claude install copies of skills). It is managed outside the agents repo and should be ignored.

## 2026-09-21: PR review pipeline has five steps

- `review-pr-full` (and `review-requested-prs`) now run `assess-pr-risk` in parallel with the chain `analyze-test-coverage -> validate-pr -> verify-pr -> review-pr` (coverage first, so its report exists as evidence for the rest).
- `analyze-test-coverage` is the first chain step: it writes `analyze-test-coverage.<sha>.md` + `.report.md` under `~/.sdlc/<owner>/<repo>/pull-requests/<pr>/` with marker verdict `pass`/`fail` (fail = uncovered change or code path). Its verdict never gates anything, and because it precedes validate-pr, a validate `fail` does not cut it from the dispatch plan.
- Files touched: `~/.agents/scripts/review_requested_prs.py` (CHAIN_STEPS, markers, Coverage table column first, review-pr fail cuts the chain too), `~/.opencode/skills/{review-pr-full,review-requested-prs,analyze-test-coverage,assess-pr-risk}/SKILL.md`, and `skills/sdlc/references/shared.md` (PR Review Reports section).
- The script runs via `uv run --script`; quick logic checks live at `/tmp/opencode/test_coverage_step.py` (ephemeral).
