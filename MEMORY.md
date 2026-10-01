# Memory

## 2026-09-30: dropped team review requests are only discoverable via notifications

- When a review is requested from a team, any teammate comment or review removes the team request for every member; afterwards the PR matches neither `review-requested:@me` nor `team-review-requested:` (verified on Shopify/davies#1633).
- The `review_requested` notification and the PR's `REVIEW_REQUESTED_EVENT` timeline item survive, so notifications are the only discovery source. The notifications REST endpoint has no `query` param (`repo:`/`reason:` filtering is web-inbox only) and GraphQL exposes no notifications at all.

## 2026-09-29: zsh does not word-split unquoted variables

- The `shell` tool runs under zsh, so `c="a b"; cmd $c` passes `"a b"` as one argument (unlike bash). Use `cmd ${=c}` or quote each word explicitly, otherwise loops silently invoke the wrong command.

## 2026-09-29: Playwright lives in the bun global install

- Browser verification (screenshots, real canvas/DOM behaviour) can be run anywhere with `require("/home/tomzx/.bun/install/global/node_modules/playwright")`, Chromium 1.62 is already downloaded under `~/.cache/ms-playwright`; there is no per-project dependency and no `npx playwright` install step needed.

## 2026-09-28: refactor-implementation sits inside the implementation phase

- The SDLC pipeline runs `refactor-implementation` between `create-implementation` and `review-implementation`; it refines the just-implemented diff with only the abstractions and seams it needs.
- In `.github/llmaw/flows.yml` it runs in the same `feat-implementation` rule, on the `impl/` branch, before `merge-pr.sh`, so the refactoring rides the implementation PR.
- Its `## Outcome` deliberately writes nothing to `$OUTCOME_YAML` when there is no implementation diff, so it cannot overwrite `create-implementation`'s routing verdict (approved -> merge, else -> needs-human). Do not "fix" it to always emit a verdict.

## 2026-09-24: scheduled runs and interactive sessions collide in one repo

- Repos with scheduled agent tasks (e.g. the blog's daily 03:00 refresh) can have a scheduled run commit mid-way through an interactive owner-driven session; twice in one day the scheduled run's wholesale `git add agents/` swept finished-but-uncommitted files from the concurrent session into its own commit.
- When working such a repo interactively, check `git log` for new commits before staging, prefer staging the exact paths touched over directory adds, and expect a mid-session commit to publish in-flight work; the section logs record who wrote what, so reconcile through the log rather than reverting.

## 2026-09-24: duplicate search before codebase investigation

- When filing an issue (create-issue or similar), run the duplicate search before any codebase investigation: the bug report itself usually provides enough search keywords, and deep code tracing only pays off once no duplicate exists or filing is confirmed.

## 2026-09-29: gs has no line-comment flag but gs api can post inline comments

- `gs pr comment` and `gs pr review` have no `--file`/`--line`/`--position` flag; they cannot anchor a new comment to a line.
- Workaround (verified on shop/world PR 2109620): `gs api repos/{owner}/{repo}/pulls/<N>/comments -F body=... -F commit_id=<head sha> -F path=<file> -F line=<n> -F side=RIGHT`. gitstream mirrors the GitHub review-comment API and returns line/side plus an `x_gitstream.thread_id`; `gs pr view <N> -c` renders it at that line. Delete test comments with `gs api repos/{owner}/{repo}/pulls/comments/<id> -X DELETE`.
- Existing inline threads can be replied to with `gs pr comment <N> --reply-to <thread-uuid>` and resolved with `gs pr resolve/unresolve <N> <thread-id>`.

## 2026-09-29: skill-creator and find-skills are broken symlinks

- `skills/skill-creator` and `skills/find-skills` symlink to `../../../../.agents/skills/<name>`, which resolves to `/Users/tom.rochette/.agents/skills/<name>` and symlinks back to itself (infinite loop). Do not try to read them; author skills directly, using `gh-stack`/`ghx` as structure models.

## 2026-09-23: handle-pr-reviewer-feedback owns the reviewer-feedback contract

- The analysis-file artifact, its location/ids/format, and the `implement | decline | defer` vocabulary are owned by `skills/handle-pr-reviewer-feedback/SKILL.md` (also mirrored in `skills/sdlc/references/shared.md`). `triage-pr-feedback` is an orchestrator only: it runs the discovery script, fans out `handle-pr-reviewer-feedback --analyze-only` per PR, prompts, and hands execution back. Do not restate the file format or vocabulary in `triage-pr-feedback`.

## 2026-09-23: assess-pr-risk is self-contained

- `assess-pr-risk` deliberately never consumes `analyze-test-coverage` / `validate-pr` / `verify-pr` / `review-pr` reports: the orchestrators dispatch it in parallel with the chain, so those reports do not exist yet when it runs. Do not "fix" it back to reading sibling reports.

## 2026-09-21: backpropagate-sdlc replaced by propagate-changes

- `skills/backpropagate-sdlc/` was renamed to `skills/propagate-changes/` and made bidirectional (rewrites dependents, questions premises); old references to backpropagate-sdlc mean this skill.

## 2026-09-21: dot-claude is out of scope

- Never modify `/home/tomzx/src/dot-claude/` (local opencode/claude install copies of skills). It is managed outside the agents repo and should be ignored.
