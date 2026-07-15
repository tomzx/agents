---
name: improve-codebase
description: Make a bounded set of safe, verified improvements to a codebase each run (remove dead code, add missing types, auto-fix lint, drop unused deps, patch dependencies). Designed to run weekly as a routine. Use when the user says /improve-codebase, "improve the codebase", "weekly cleanup", "tend the repo", or wants incremental hands-off improvements that pass the project's own tests and open a reviewable PR.
argument-hint: "[--scope all|safety|types|deps|dead-code|lint|docs] [--budget N] [--dry-run] [--no-pr] [--label NAME]"
---

# Improve Codebase

Makes a bounded set of **safe, verified** improvements to a codebase, then opens a single reviewable PR. Designed to run on a weekly cadence so the codebase gets incrementally better without a big-bang refactor.

## The Core Problem This Solves

`/audit-sdlc` and `/sync-repository` tell you what is wrong. They produce reports and issues, but the work of actually deleting the dead export, adding the missing type annotation, and running the formatter still falls to a human. That backlog grows faster than anyone clears it.

This skill closes that loop. Each run it scans for the same opportunities the audit skills find, picks a small batch that is safe to apply automatically, applies it, proves it is safe by running the project's own lint/typecheck/test suite, and ships it as one PR. Over weeks, the backlog shrinks instead of grows.

## How It Differs From Related Skills

| Skill | Reads code | Writes code | Opens PR | Cadence |
|---|---|---|---|---|
| `audit-sdlc` | yes | no (report only) | no | on demand |
| `sync-repository` | yes | `.sdlc/` only, or `--fix` | no | on demand |
| **`improve-codebase`** | yes | **yes, source code** | **yes** | **weekly routine** |

Use `audit-sdlc` to find problems. Use `improve-codebase` to fix the safe ones automatically.

## Prerequisites

- Working directory is the root of a `git` repository on a clean working tree (no uncommitted changes)
- A default branch to branch from (`main`, or the repo's detected default)
- A way to verify changes: a test suite, a linter/formatter, or a typechecker. The skill discovers these (see Discovery below). If none can be found, it runs in `--dry-run` only and asks the user to record commands in `AGENTS.md`.
- Read any files under `.sdlc/context/` for project conventions
- Network access to push the branch and open a PR (unless `--no-pr`)

## Safety Contract (Non-Negotiable)

These rules make the skill safe to run unattended on a schedule:

1. **Never touch the default branch.** All work happens on a short-lived branch.
2. **Never auto-fix anything rated higher than "low risk".** Security issues, dependency majors, complexity refactors, and public API changes become issues, not commits.
3. **Never skip verification.** Every change must be validated by the project's own checks. If verification fails, revert that change and continue with the next candidate.
4. **One concern per commit, one PR per run.** Reviewers see small atomic commits, not a wall of diff.
5. **Respect `.gitignore`, lint configs, and existing suppression comments** (`# noqa`, `//nolint`). Do not fight the project's stated preferences.
6. **Never force-push, never amend published commits, never bypass hooks.**
7. **Bounded output.** A run stops at the change budget so the PR stays reviewable.
8. **Never introduce new dependencies.** Only removes or patches existing ones.

## Improvement Categories

Each category has a risk rating. Only `auto` categories are applied directly. `issue` categories are written to the PR body as follow-up issues (or filed via `/create-issue` with `--create-issues`).

| Category | Risk | Action | Examples |
|---|---|---|---|
| `dead-code` | auto | remove | unused exports, zero-reference functions, unreachable code, orphaned config keys |
| `lint` | auto | fix | run the project's formatter/linter with its auto-fix flag (`ruff format`, `ruff check --fix`, `prettier --write`, `gofmt -w`, `goimports -w`) |
| `types` | auto | add | missing type annotations on untyped public functions (Python/TS) |
| `docs` | auto | add | missing docstrings on public APIs (only when trivially inferrable) |
| `deps-patch` | auto | update | patch/minor dependency bumps with no breaking changes |
| `deps-unused` | auto | remove | dependencies declared but never imported |
| `deps-major` | issue | report | major version bumps, unmaintained packages |
| `security` | issue | report | hardcoded secrets, injection risks, missing auth |
| `complexity` | issue | report | high cyclomatic complexity, deep nesting |
| `coverage` | issue | report | critical paths with no test coverage |

### What This Skill Will Never Auto-Change

- Public API signatures or exported names
- Database schemas, migrations, or persisted data formats
- Security-sensitive code (auth, crypto, secrets handling)
- Test logic or assertions
- Anything behind a feature flag still in use
- Anything in files touched in the last 7 days (too fresh to "improve")

## Scopes and Flags

`$1` controls which categories run. Defaults to `all` (all `auto` categories; `issue` categories are scanned for the PR body).

| Scope | Categories applied |
|---|---|
| `all` | every `auto` category (default) |
| `safety` | `dead-code`, `lint`, `deps-unused` |
| `types` | `types` |
| `deps` | `deps-patch`, `deps-unused` |
| `dead-code` | `dead-code` only |
| `lint` | `lint` only |
| `docs` | `docs` only |
| Comma-separated | specific categories, e.g. `dead-code,lint` |

Flags:

- `--budget N` — maximum number of changes per run (default `20`). The run stops once N changes are committed or no safe candidates remain.
- `--dry-run` — scan and produce the report, but make no commits and open no PR.
- `--no-pr` — commit to a branch but do not push or open a PR (for local review).
- `--label NAME` — PR label to use (default `codebase-improvement`). Also used for dedup.
- `--create-issues` — file GitHub issues for `issue`-rated findings, not just list them.

## Discovery: Finding The Project's Commands

Before changing anything, discover how this project verifies itself. Order of preference:

1. **`AGENTS.md` / `CLAUDE.md`** — read it for documented test, lint, typecheck, and format commands. These are authoritative.
2. **Language manifests:**
   - `package.json` → `scripts.test`, `scripts.lint`, `scripts.format`, `scripts.typecheck`
   - `pyproject.toml` → `[tool.pytest]`, ruff/mypy config; commands like `uv run pytest`, `uv run ruff`, `uv run mypy`
   - `Makefile` → `make test`, `make lint`, `make check`
   - `Cargo.toml` → `cargo test`, `cargo clippy`, `cargo fmt`
   - `go.mod` → `go test ./...`, `go vet ./...`, `gofmt -l`
3. **Fallback heuristics:** run `pytest`, `npm test`, `go test ./...` and keep whichever exits 0 from a clean tree.

Record the discovered commands at the top of the run report. If nothing is found, stop and ask the user to add them to `AGENTS.md`, then exit in `--dry-run` mode only.

## The Weekly Loop

```
1. Discover commands (test / lint / typecheck / format)
        |
        v
2. Baseline: confirm the clean tree passes all checks
   (if baseline fails, stop — fix the baseline first, do not build on red)
        |
        v
3. Dedup: list recently merged PRs labeled `codebase-improvement`
   skip any file they touched in the last 7 days
        |
        v
4. Scan: run find-* / audit-* skills as READ-ONLY scanners
   collect candidates per category
        |
        v
5. Rank: score each candidate (impact / effort / risk)
   select the top candidates within --budget
        |
        v
6. Apply + verify, per candidate:
      a. make the change
      b. run lint + typecheck + tests
      c. green?  -> commit (atomic, one concern)
      d. red?    -> git restore, record as "reverted", move on
        |
        v
7. Aggregate: build the PR body from committed changes
   + list issue-rated findings for follow-up
        |
        v
8. Ship: push branch, open PR (or report only for --dry-run / --no-pr)
```

## Steps

### 1. Parse arguments and discover commands

Resolve scope and flags from `$1`. Run Discovery above. Print the resolved command set. If no verification command exists and the user did not pass `--dry-run`, stop and ask them to record commands in `AGENTS.md`.

### 2. Confirm a green baseline

Require a clean working tree (`git status --porcelain` empty). Run the discovered test/lint/typecheck commands on the unmodified tree. **If the baseline is red, stop.** Never apply improvements on top of a failing tree, otherwise red-green ambiguity makes verification meaningless. Report the failing baseline and exit.

### 3. Dedup against recent runs

List recently merged PRs with the `codebase-improvement` label (default) or the `--label` value:

```bash
gh pr list --state merged --label "$LABEL" --limit 8 --json number,title,mergedAt,files
```

Collect the set of files touched in the last 7 days. Candidates inside those files are skipped this week (avoid churn on actively-developed code).

### 4. Scan for candidates

Invoke the scanner skills in read-only mode and collect their findings as candidates. Do not let them write anything.

| Category | Scanner skill | What it yields |
|---|---|---|
| `dead-code` | `/find-dead-code` | symbols safe to remove |
| `lint` | direct formatter/linter run | files needing format/auto-fix |
| `types` | `/find-type-gaps` | untyped public functions |
| `docs` | `/find-documentation-gaps` | undocumented public APIs |
| `deps-unused`, `deps-patch`, `deps-major` | `/audit-dependencies` | unused/outdated/unmaintained deps |
| `security` | `/audit-security` | secrets, injection, missing auth |
| `complexity` | `/find-complexity-hotspots` | complex functions |
| `coverage` | `/find-coverage-gaps` | untested critical paths |

Skip a scanner gracefully when its preconditions are not met (e.g., skip `/find-type-gaps` for non-Python/TS projects, skip dependency scanners when no manifest exists).

### 5. Rank and select

Score every candidate:

```
score = impact × confidence / (effort × risk)
```

- **impact:** how much does this clean up (bytes of dead code, number of untyped call sites, severity of the lint rule)
- **confidence:** scanner certainty (e.g., vulture `--min-confidence 80`)
- **effort:** estimated change size
- **risk:** auto=1, issue=high

Select the top candidates from `auto` categories until the budget is reached. Cap each category so one noisy scanner (for example, hundreds of lint fixes) cannot crowd out the others:

- `lint`: at most 40% of the budget
- `dead-code`, `types`: at most 30% each
- `deps-patch`, `deps-unused`: at most 10% each
- `docs`: at most 10%

### 6. Apply and verify each candidate

For each selected candidate, in ranked order:

1. Create the branch once (before the first commit), named `improve/<YYYY-MM-DD>` (or append `-2`, `-3` if it exists).
2. Make the single change.
3. Run lint, then typecheck, then the full test suite.
4. **Green** → commit with an atomic message (see Commit Style). Decrement the budget.
5. **Red** → `git restore` the change, log it under "Reverted (failed verification)", and continue. Never commit a change that fails verification.

If three consecutive candidates in the same category fail verification, stop pulling from that category for the rest of the run (likely a noisy/false-positive scanner).

### 7. Aggregate the PR body

Build the PR description from the committed changes plus the issue-rated findings (see Output Format). Group commits by category. Include verification evidence (which commands ran, green status).

### 8. Ship

Unless `--dry-run` or `--no-pr`:

1. Push the branch.
2. Open a PR with title `chore(codebase-improvement): <YYYY-MM-DD>` using `/create-pr` conventions, labeled `codebase-improvement` (and the `--label` value), targeting the default branch.
3. If `--create-issues` was passed, file one issue per `issue`-rated critical/high finding via `/create-issue`, and link them from the PR body.

For `--dry-run`, write the full report to `.sdlc/improvement-dryrun-<YYYY-MM-DD>.md` and print it. For `--no-pr`, leave the local branch in place and print instructions to review and push.

### 9. Exit posture

- If at least one change shipped: PR is open, ready for human review. Done.
- If nothing was safe to apply this week: report "no safe improvements found", still list the `issue`-rated findings so they are not lost, and suggest a manual `/audit-sdlc` if the list is large.
- If baseline was red: report it and stop (do not open a PR).

## Commit Style

Each commit is atomic and self-describing. Use conventional-commit prefixes scoped to the category:

```
refactor(dead-code): remove unused `parseLegacyConfig` export
style(lint): apply ruff format to src/payments/
chore(deps): patch requests 2.31.0 -> 2.31.2
chore(deps): remove unused `left-pad` dependency
feat(types): annotate `calculate_total` return type as Decimal
docs(api): add docstring to `UserStore.lookup`
```

Reference no issue number (these are proactive improvements, not issue-driven). Append the run's co-author trailer if the project convention requires it.

## Output Format (PR Body)

```markdown
---
date: "<YYYY-MM-DD>"
scope: "<scope run>"
budget: "<used / limit>"
baseline: green
verification: "<commands run, all green>"
status: complete
---

# Codebase improvement — <YYYY-MM-DD>

**Scope:** <categories>  **Changes:** N committed, M reverted  **Budget:** N/limit

## Summary

| Category | Committed | Reverted | Skipped (recent) |
|---|---|---|---|
| dead-code | N | N | N |
| lint | N | N | N |
| types | N | N | N |
| deps-patch | N | N | N |
| deps-unused | N | N | N |
| docs | N | N | N |

## Verification

All changes validated against the project's own suite:

- `uv run ruff check .` — green
- `uv run mypy src/` — green
- `uv run pytest -q` — green (N passed)

## Changes

### dead-code (N)
- `<file>:<line>` — removed unused `parseLegacyConfig` (0 references)
- ...

### lint (N)
- applied `ruff format` to 6 files in `src/payments/`
- ...

### types (N)
- `src/billing.py:42` — annotated `calculate_total() -> Decimal`
- ...

### deps (N)
- patched `requests` 2.31.0 -> 2.31.2 (patch, no breaking changes)
- removed unused `left-pad` dependency
- ...

## Reverted (failed verification)

- `src/cache.py` — removing `legacyKey` broke a test that asserts its presence; restored. Needs manual review.
- ...

## Follow-ups (not auto-applied)

These need a human. Filed as issues when `--create-issues` was passed.

| Severity | Category | Finding | Issue |
|---|---|---|---|
| high | security | SQL string concat in `search()` | <link or "not created"> |
| medium | complexity | `dispatch()` has CC 24 | <link or "not created"> |
| medium | coverage | no tests on `POST /refund` | <link or "not created"> |
| low | deps-major | `pydantic` 1 -> 2 (breaking) | <link or "not created"> |

## Dedup

Skipped N files touched by merged PRs in the last 7 days: `<list>`.
```

## Example Usage

**Scenario 1: Weekly routine (the default)**
```
/improve-codebase
```
Scans every `auto` category, applies up to 20 safe changes, opens one PR. Also reports 4 issue-rated findings (1 security, 2 complexity, 1 coverage) in the PR body for manual follow-up.

**Scenario 2: Conservative safety-only pass**
```
/improve-codebase safety --budget 10
```
Only dead-code removal, lint auto-fix, and unused-dependency removal. Caps at 10 changes. Good for the first few weekly runs while trust is being built.

**Scenario 3: Dry run before trusting it**
```
/improve-codebase --dry-run
```
Produces the full report and candidate list at `.sdlc/improvement-dryrun-2026-06-20.md` but commits nothing. Use this to audit what the skill would do before enabling the routine.

**Scenario 4: Types-only, no PR (local review)**
```
/improve-codebase types --no-pr
```
Adds missing type annotations on a local branch, leaves it unpushed for the developer to inspect and push themselves.

**Scenario 5: Full pass that also files issues**
```
/improve-codebase all --create-issues
```
Ships the safe PR and creates GitHub issues for each critical/high follow-up so nothing is lost.

## Scheduling (Weekly Cadence)

This skill is designed to be safe to run unattended on a schedule. Three options:

- **Paperclip routine (recommended for agents):** create a routine with a weekly cron trigger (for example `0 9 * * 1` for Monday 09:00) whose execution issue instructs the agent to run `/improve-codebase`. Each fire produces a PR for review. See the `paperclip` skill's Routines section.
- **GitHub Actions workflow:** a weekly schedule that invokes the agent CLI with `/improve-codebase --no-pr` on a self-hosted runner, or opens the PR via `gh`.
- **Manual:** run `/improve-codebase` each Friday as part of `/end-week`.

Because every run is bounded, verified, and labeled, it composes cleanly with the weekly review skills: the PR shows up in the end-of-week GitHub summary and is reviewed alongside normal work.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `audit-sdlc` | The scanner half of this skill. `improve-codebase` calls the same find-* / audit-* skills but acts on the safe subset instead of only reporting. |
| `sync-repository` | Broader consistency check (SDLC, docs, cross-layer drift). Use `sync-repository` to detect drift; use `improve-codebase` to incrementally pay down the code-quality debt it surfaces. |
| `find-dead-code`, `find-type-gaps`, `audit-dependencies`, `audit-security`, `find-complexity-hotspots`, `find-coverage-gaps`, `find-documentation-gaps` | Read-only scanners invoked by this skill. |
| `create-pr` | Used to open the review PR with the standard description format. |
| `create-issue` | Used to file follow-up issues for `issue`-rated findings when `--create-issues` is passed. |
| `session-review` | Per-session checklist. `improve-codebase` is the periodic (weekly) counterpart that pays down debt between sessions. |
| `end-week` | Natural home for a weekly `/improve-codebase` invocation before the Friday wrap-up. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `git status --porcelain` | Confirm clean tree before starting |
| `gh pr list --state merged --label codebase-improvement --limit 8 --json files` | Dedup: files touched by recent improvement PRs |
| `uv run ruff format . && uv run ruff check --fix .` | Python auto-fix (respect project config) |
| `npx prettier --write .` | JS/TS format |
| `gofmt -w . && goimports -w .` | Go format |
| `uv run pytest -q` / `npm test` / `go test ./...` | Verify (run the discovered test command) |
| `gh pr create --label codebase-improvement` | Open the weekly PR |
