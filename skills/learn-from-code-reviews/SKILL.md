---
name: learn-from-code-reviews
description: Collect the code review feedback you received on your own pull requests and distill it into durable, cited rules to consult before design and implementation work so the same mistakes stop recurring. Use when the user says /learn-from-code-reviews, "learn from my code reviews", "learn from my PR reviews", "what do reviewers keep telling me", "turn review feedback into rules", "why do I keep getting the same review comments", "review my feedback history", or wants a review-rules checklist to apply before writing code or designs.
allowed-tools: Bash(ghx:*, uv:*, git:*), Read, Write, Edit, Glob, Grep
argument-hint: "[owner/repo ... | --mine] [--since YYYY-MM-DD] [--consult] [--dry-run] [--publish [path]] [--all]"
---

TODAY=!`date +%Y-%m-%d`

# Learn From Code Reviews

Mines the review feedback you have received on pull requests you authored, clusters it into recurring patterns, and distills those patterns into durable rules stored under `$HOME/.sdlc/review-rules/`.
The rules are written to be read before design and implementation work, so feedback a reviewer gave once becomes a habit you apply without being told again.

Two jobs:

- **Synthesize** (default): collect reviews, cluster them, and merge new rules into the store. Incremental: `state.json` records the last run, so only new feedback is processed.
- **Consult** (`--consult`): print the rules that apply to the current repository, grouped by strength, as a checklist to apply now.

## Prerequisites

- `ghx` installed and authenticated (reads `GH_TOKEN`/`GITHUB_TOKEN`, or falls back to `gh auth token`).
- The target repositories are present in the ghx cache. Run `ghx cache -R <owner>/<repo>` first so their PRs and conversation comments are stored; the collector reads PRs and conversation comments from `~/.cache/ghx/cache/cache.db` (override with `GHX_CACHE_DIR`) and fetches inline review threads via `ghx pr threads`. It never calls the GitHub API directly.
- `uv` available (the collector runs via its `uv run --script` shebang).
- The collector script in this skill directory:
  `~/.agents/skills/learn-from-code-reviews/scripts/collect_reviews.py`.

## Scope boundaries

| Skill | Relationship |
|-------|--------------|
| `handle-pr-reviewer-feedback` | Responds to feedback on **open** PRs, one PR at a time, to land code. This skill mines **historical** feedback across PRs to change your future behavior. |
| `triage-pr-feedback` | Orchestrates the open-feedback response loop on a schedule. Orthogonal: it acts, this skill learns. |
| `create-learnings` / `run-retrospective` | Reflect on one feature, sprint, or project. This skill reflects on the review record itself across repos. |
| `improve-sessions` | Mines **agent sessions** for friction. This skill mines **human and bot review feedback** for recurring mistakes. |
| `review-pr` | Performs a review as the reviewer. This skill learns from reviews you received as the author. |

## What counts as a rule

A candidate pattern becomes a rule only when it clears every gate:

- **Recurrence**: at least two independent feedback items, and either two distinct reviewers or two distinct PRs.
- **Specificity**: it names a concrete, checkable action, not a vague aspiration ("validate external input at the boundary", not "be more careful").
- **Attribution**: every rule cites the PR and comment permalinks it came from.
- **Strength**: `must` when the feedback concerns correctness, security, data loss, broken builds, or missing tests; `prefer` when it concerns style, consistency, or taste.

Bot-only evidence (an AI reviewer such as `greptile-apps[bot]`) can support a rule but never by itself makes it `must`.
A single reviewer's stylistic preference never becomes a `must`.
Items that do not clear the gates go into an **Observations** appendix in the report, not into the store.

## The rule store

The store lives outside any repository and is never committed:

```
$HOME/.sdlc/review-rules/
  rules.md              # global rules that apply to every repository
  <owner>/<repo>.md     # rules scoped to one repository
  state.json            # collector watermark, owned by the script
```

Each rule uses a stable id, `<CATEGORY>-<NNN>`, assigned once and never reused (categories: `DESIGN`, `ERR`, `TEST`, `PERF`, `SEC`, `API`, `DATA`, `DOC`, `STYLE`, `PROCESS`).
A rule carries its category, strength, the imperative rule text, why it exists, when to apply it, and its evidence.

```markdown
### ERR-003 Null-guard every value crossing a boundary
- **Category:** error-handling
- **Strength:** must
- **Rule:** Validate and null-guard every value that enters from outside the process (HTTP body, CLI argument, config file) before dereferencing it.
- **Why:** Reviewers repeatedly caught unguarded dereferences of request fields.
- **Apply when:** writing or changing any handler that consumes external input.
- **Last seen:** 2026-09-25
- **Evidence:** 4 items, 2 reviewers, openchamber/openchamber
  - https://github.com/openchamber/openchamber/pull/2862#discussion_r3840911534 (greptile-apps[bot], 2026-09-24)
  - https://github.com/openchamber/openchamber/pull/1234#discussion_r220 (alice, 2026-07-02)
```

Merge semantics when writing:

- **Match an existing rule** (same underlying lesson): append the new evidence, bump the counts, refresh `Last seen`, and refine the wording. Do not create a second rule for the same lesson.
- **New recurring pattern**: assign the next id in its category and add the rule.
- **Rule not seen in the run window**: leave it in place, but when a rule has no new evidence for 180 days, set `**Status:** dormant`; for 365 days, `**Status:** retired`. Never delete evidence or delete a rule outright.

## Steps

### 1. Scope the collection

Decide the sources and window from the arguments:

- Targets: `owner/repo` arguments or PR URLs. With no argument, the whole ghx cache (your PRs only). `--mine` is the explicit form of that default; `--include-all-authors` drops the "you authored it" restriction.
- The repositories must already be in the ghx cache; if the cache is stale, refresh it first with `ghx cache -R <owner>/<repo>`.
- Window: `--since YYYY-MM-DD`; with no argument the collector reuses `state.json` (last run minus one day) or defaults to the last 30 days.
- Bots are excluded by default; pass `--include-bots` to include substantive AI reviewers, which count as supporting (not `must`) evidence. Conversation comments are off by default (inline review threads are the signal); add `--include-conversation` to widen the net.

### 2. Collect the feedback

Refresh the cache if needed, then run the collector:

```bash
ghx cache -R <owner>/<repo>                                   # refresh (optional)
uv run ~/.agents/skills/learn-from-code-reviews/scripts/collect_reviews.py [targets] \
  [--mine] [--since YYYY-MM-DD] [--limit N] [--include-bots] --update-state
```

It emits one JSON document with `pull_requests`, a flat `feedback[]` array (each item has `repo`, `pr`, `kind`, `id`, `author`, `is_bot`, `path`, `line`, `body`, `url`), and `stats`.
Take the `feedback[]` array as the input to the next step. If it is empty, report "no new feedback in the window" and stop.

`kind` is `review_comment` for an inline review thread (with `path` and `line`) or `conversation` for a top-level PR comment.
Pass `--update-state` so the next run is incremental (it records `last_run` in `state.json`). Omit it under `--dry-run`, and if the run fails before the store is written, re-run with an explicit `--since` to recover the skipped window.

### 3. Cluster feedback into candidate patterns

Read every `feedback[]` item and group by underlying lesson, not by wording. Two comments on different files that both ask for the same guard belong together.
For each cluster record: the lesson, its category, the number of items and distinct reviewers and PRs, and the representative quotes with their permalinks.

Mark a cluster that clears the gates above as a rule candidate; put the rest in the Observations appendix.

### 4. Read the existing store

Read `$HOME/.sdlc/review-rules/rules.md` and, when scoped to a repository, `$HOME/.sdlc/review-rules/<owner>/<repo>.md` (create on first write).
Match each candidate against the existing rules: is this already covered, a refinement of one, or genuinely new?
Also flag existing rules whose referenced code no longer exists, so the rule can be narrowed or retired rather than blindly kept.

### 5. Update the store

For each candidate, apply the merge semantics above: append evidence and refresh an existing rule, or create a new rule with the next id.
Choose scope: a rule that generalizes beyond the repository goes in the global `rules.md`; a rule tied to one codebase or framework goes in the repo file.
Write the files under `$HOME/.sdlc/review-rules/`.

When `--dry-run` is set, present the proposed store changes and stop without writing.

### 6. Report and optionally publish

Present the report (format below).
If `--publish [path]` is set, refresh a managed block in the target file (default: the current repository's `MEMORY.md`) so the rules load at the start of a session:

```markdown
<!-- review-rules:start -->
## Review rules learned from PR feedback

Full list: `~/.sdlc/review-rules/`. Apply these before design and implementation work.

- [must] Null-guard every value crossing a boundary (ERR-003)
- [prefer] ... (STYLE-002)
<!-- review-rules:end -->
```

Replace the block between the markers on every publish; never append a second one.
Warn the user first if the target file is tracked by git, since the rules are personal.

## Consult mode

When `--consult` is passed, skip collection and do not write anything:

1. Read the global `rules.md` and the current repository's `<owner>/<repo>.md` when it exists.
2. Filter to rules with `**Status:**` absent or `active`; drop `dormant` and `retired` unless `--all`.
3. Optionally filter by `--category` or free-text keywords from the task.
4. Print `must` rules first, then `prefer`, each as a one-line checklist item with its id, and note the store path.

## Output Format

```markdown
## Code Review Learnings ({TODAY})

**Window:** <since> to <until> | **PRs:** <N> | **Feedback items:** <N> | **Reviewers:** <N>

### New Rules

#### <ID> <title> (<category>, <strength>)
- **Rule:** <imperative>
- **Evidence:** <items> items, <reviewers> reviewers, <repos>
- **Citations:** <permalink>, <permalink>

### Updated Rules

| Rule | Change | New evidence |
|------|--------|--------------|
| ERR-003 | +1 citation, reworded | <permalink> |

### Dormant / Retired

| Rule | Reason |
|------|--------|
| STYLE-001 | No recurrence in 180 days |

### Observations (below the bar)

- <one-off nit>: <permalink>

### Recommendation

> <The one rule most worth applying immediately, in one sentence.>
```

## Anti-patterns

- **Mining your own replies**: filter out comments authored by the viewer; the collector already does, but do not re-introduce them when clustering.
- **Hardening a preference**: a style comment from one reviewer is `prefer` at most, and only after a second occurrence.
- **Raw dumps**: the store holds distilled rules with citations, never pasted comment bodies.
- **Duplicating lessons**: always match against the existing store before adding an id.
- **Stale truth**: a rule whose referenced code is gone is narrowed or retired, not preserved verbatim.
- **Stale cache**: the collector only sees what `ghx cache` has stored; refresh a repository's cache before a run or the window will look emptier than it is.
- **Silent rewrite**: every store change must appear in the report; `--dry-run` exists for review before writing.

## Example Usage

**Scenario 1: weekly synthesis across your repos**

```
/learn-from-code-reviews --mine --since 2026-09-01
```

Collects review feedback on every PR you authored since the date, finds "unguarded external input" across three PRs and two reviewers, refines `ERR-003`, adds `TEST-004`, records the one-offs as observations, and advances the watermark.

**Scenario 2: before starting a feature**

```
/learn-from-code-reviews --consult
```

Prints the global rules plus the current repository's rules as a short `must` then `prefer` checklist to apply while designing and implementing.

**Scenario 3: one repository, dry run**

```
/learn-from-code-reviews acme/api --since 2026-01-01 --dry-run
```

Refreshes the ghx cache for `acme/api` if needed, proposes the rule additions and refinements for that repository, and writes nothing, so you can approve them first.

## Useful Commands Reference

| Command | Description |
|---|---|
| `ghx cache -R <owner>/<repo>` | Refresh the local cache the collector reads from |
| `uv run ~/.agents/skills/learn-from-code-reviews/scripts/collect_reviews.py --mine --since <date> --include-bots` | Collect recent feedback across your PRs, bots included |
| `uv run ~/.agents/skills/learn-from-code-reviews/scripts/collect_reviews.py <owner/repo>` | Collect for one cached repository |
| `uv run ~/.agents/skills/learn-from-code-reviews/scripts/collect_reviews.py ... --update-state` | Collect and advance the incremental watermark |
| `ghx pr threads <n> -R <owner>/<repo> --state all` | Inspect a PR's inline review threads directly |
