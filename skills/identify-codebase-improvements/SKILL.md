---
name: identify-codebase-improvements
description: Discover concrete gaps and improvements in an existing codebase, keep only the high-confidence ones, and use ghx to discard anything already tracked by a GitHub issue, searching for another candidate until nothing useful remains. Works bottom-up from the code (correctness, tests, maintainability, performance, dependencies, DX) rather than from the backlog. Use when the user says /identify-codebase-improvements, "find improvements", "what should we improve", "codebase gaps", "tech debt hunt", "untracked improvements", "what is worth fixing", or wants a periodic quality discovery pass that does not re-propose known issues.
allowed-tools: Bash(ghx:*, gh:*, git:*, rg:*), Read, Glob, Grep, Write
argument-hint: "[repository] [--focus <area>] [--limit N] [--create-issues N] [--since <YYYY-MM-DD>] [--quick|--deep]"
---

TODAY=!`date +%Y-%m-%d` REPO=!`git remote get-url origin 2>/dev/null | sed -E 's#.*[:/]([^/]+/[^/]+)(\.git)?$#\1#'`

# Identify Codebase Improvements

Reads an existing codebase as evidence and proposes concrete improvements that are worth doing and are not already tracked in the issue tracker.
Every recommendation must pass two gates: high confidence (the agent read the code and can cite it) and not already an existing GitHub issue.
Dedup is the goal: a pass that re-surfaces known work is noise, so the skill loads the existing issue history with `ghx` up front and re-checks each candidate against it.

This is a read-only discovery skill.
It does not modify code.
It produces a ranked recommendation report, and optionally files issues for the recommendations that survive dedup.

## The Core Problem This Solves

The issue tracker already holds the known work.
A generic audit re-reports it anyway (the same swallowed exception, the same complex function, the same untyped module), which teaches everyone to ignore the audit.
This skill inverts the default: it treats every existing issue as a known recommendation, excludes those, and spends its budget finding the improvements nobody has written down yet.
It is a loop, not a one-shot list: when a candidate turns out to be already tracked, it drops it and keeps looking, until the code surface stops yielding untracked, high-confidence candidates.

## How This Differs From Related Skills

| Skill | Direction | Issue-aware | Output |
|---|---|---|---|
| `identify-feature-opportunities` | New value to build (what the product could do) | partially | Ranked feature opportunities |
| **`identify-codebase-improvements`** | **Quality of what exists (what to fix or improve)** | **yes, ghx dedup is mandatory** | **Ranked, untracked improvements** |
| `audit-sdlc` / `audit-*` / `find-*` | Quality scanners, report findings | no | Findings report |
| `improve-codebase` | Applies the safe fixes automatically | reads recent PRs only | A PR with verified changes |
| `check-issues-status` | Finds issues already done (to close) | yes | Close candidates |

Use the `audit-*` / `find-*` family for breadth, `improve-codebase` to land the safe subset, and this skill to find what is missing from the tracker at a confidence high enough to act on.

## Prerequisites

- Working directory is the root of a `git` repository (or a path inside it)
- `ghx` installed and authenticated (falls back to `gh auth token`); run `ghx cache` once so list and search are served locally
- Read any files under `.sdlc/context/` (`goals.md`, `architecture.md`, `conventions.md`) for project intent
- Read design and decision docs if present (`.sdlc/decisions/`, `docs/adr/`, `docs/decisions/`, `CONTEXT.md`, `DESIGN.md`); a tradeoff recorded there is settled, not a finding
- If no repository argument is provided, operate on `$REPO` (derived from `origin`), then the current working directory

## What Counts as a Recommendation

A recommendation is a single, concrete change or investigation with a clear payoff.
The scan covers the same quality surface as the audit skills, but only findings that pass the confidence and usefulness gates survive.
Treat the categories as prompts, not a checklist to fill.

| Category | What to look for | Evidence that makes it high confidence |
|---|---|---|
| Correctness and safety | swallowed exceptions, empty catches, unawaited promises, missing validation, non-idempotent retries, unchecked nulls | the exact `file:line`, plus the code path that triggers it |
| Tests | critical paths with no coverage, tests that assert nothing, no one-command verification | the untested function and the important path (money, auth, or data) it affects |
| Maintainability | duplication, God modules, cycles, layering violations, inconsistent patterns | 2-5 `file:line` sites that should be one, or the measured metric |
| Dead weight | unused code, always-on flags, orphaned config keys, unused dependencies | zero references found by a search, with the search recorded |
| Performance | N+1 queries, repeated work in hot loops, unbounded lists, missing pagination | the loop plus the query it issues per iteration |
| Dependencies | major-version lag on a core runtime, abandoned packages on critical paths, duplicate libraries | the manifest line and the reason staying behind is costly |
| DX and tooling | missing typecheck/lint/format, undocumented required env vars, slow or absent CI feedback | the missing command and where the project clearly expects it |
| Docs | absent reference for a published surface, docs that are actively wrong | the surface and the concrete cost of the gap |

### High-Confidence Bar (both gates must pass)

1. **Confidence is HIGH.** The agent opened the cited files and can point at the code.
   A signal that needs verification is MED and belongs only in the "needs verification" appendix, never in the main ranked list.
   Anything weaker is not reported.
2. **Useful.** There is a concrete impact (a bug that can happen, time spent on every change, a user-visible failure), not a preference.
   If the payoff is a style opinion or a micro-optimization with no measured cost, drop it.
3. **Not settled.** It is not a documented decision, a standard platform convention, or a tradeoff recorded in an ADR.
   If the code has drifted from a documented decision, the drift is the finding, not the decision.
4. **Evidence is specific.** No "probably has an N+1 somewhere".
   Name the file, line, and behavior.

## The Dedup Contract (ghx)

This is mandatory, and it is what separates a useful pass from a noisy one.

### Load the known set once, up front

Warm the cache and pull the issue history.
Existing issues, open or closed, are the already-identified recommendations.

```bash
ghx cache --repo "$REPO"
ghx issue list --repo "$REPO" --state all --limit 200 --json
```

Build a known set from issue number, title, state, and labels.
Also read every prior report at `.sdlc/codebase-improvements-*.md` and carry forward its recommendations and its "already tracked" and "considered and rejected" ledgers, so a re-run does not redo settled work.

### Re-check every candidate before it is kept

For each candidate, extract 2 to 4 keyword combinations from its most distinctive signals: identifiers, file paths, error strings, endpoint names, domain nouns.
Search, then read the top matches rather than trusting titles.

```bash
ghx issue list --repo "$REPO" --search "<keywords>" --state all --limit 10
ghx issue view <number> --repo "$REPO" --comments
```

Pass a number, not a URL: `ghx issue view` rejects URL arguments.

### The loop

1. Generate a candidate from the code.
2. Search the known set and the tracker for it.
3. If any issue tracks it, discard it, record `already tracked: #<n> (<state>)`, and go back to step 1 for another candidate.
4. If no issue tracks it and it clears the high-confidence bar, keep it.
5. Repeat until the requested count is reached or a full sweep of the surface yields no new untracked candidate.

Only then is the pass done.
State the exhaustion evidence in the report: what areas were swept, roughly how many raw candidates were dropped as already tracked, and which categories were not covered.

## Steps

### 1. Resolve scope and read context

Resolve the repository from `$1`, then `$REPO`, then the current directory.
Apply `--focus` if given.
Read `.sdlc/context/` and any decision or design docs.
Record settled decisions so they are not reported later.

### 2. Load the known set with ghx

Run the load commands above.
Record the count of existing issues and the prior report IDs.
This set is consulted for every candidate in step 4.

### 3. Map the code surface

Identify the languages, package manager, and the exact commands the project uses to build, test, lint, typecheck, and format.
Enumerate the full surface: CLI commands, API routes, UI screens, modules, config keys, dependencies.
Use the `find-*` and `audit-*` skills as read-only lead generators when helpful, but treat their output as candidates to vet, never as finished findings.
Sketch the critical paths (money, auth, data mutation) because untested critical code outranks untested utility code.

### 4. Generate, vet, and dedup candidates

For each candidate:

1. Open the cited files and confirm the finding is present and correctly attributed.
2. Reject by-design behavior, documented decisions, and standard conventions.
3. Apply the high-confidence bar.
   Downgrade to "needs verification" or drop.
4. Run the dedup search.
   If tracked, discard and continue the loop.
5. Keep it, capture the evidence (`file:line`), impact, effort estimate (S/M/L), confidence, and a 1-3 sentence fix sketch.

Continue until the `--limit` count is reached or the surface is exhausted.

### 5. Rank by leverage

Order kept recommendations by leverage, discounted by fix risk:

```
leverage = impact / effort, discounted by confidence and by the risk of the fix itself
```

Tiebreakers: anything that unblocks other recommendations (a verification baseline, characterization tests) moves up; security findings with HIGH confidence rank above equivalent-leverage non-security findings; prefer fixes with a clean verification story.

### 6. Write the report

Write to `.sdlc/codebase-improvements-<TODAY>.md` (repo only).
Continue the recommendation ID sequence from the previous report.
Use the Output Format below.
The report is the deliverable and must work on its own; do not reference the live conversation.

### 7. Optional issue creation

Only when `--create-issues N` is passed, file the top N via `/create-issue`.
Label them `codebase-improvement` (create the label only if the repository already supports label creation; otherwise skip labels).
Each issue body cites the evidence and links back to the report.
Before filing, check repository visibility: if the repository is public, confirm before publishing any recommendation that names a security weakness or a credential location.

## Flags

- `--focus <area>` restricts the scan to one area (a module path, `api`, `cli`, `ui`, or a category such as `tests`).
- `--limit N` caps the number of kept recommendations (default `10`).
  The loop still runs to exhaustion or until N is reached.
- `--create-issues N` files the top N as GitHub issues (off by default; report-only).
- `--since <YYYY-MM-DD>` restricts issue dedup and git signal to issues and commits since this date (default: all issues).
- `--quick` scans hotspots only (recent churn, critical paths).
  `--deep` sweeps every package.
  Default is a hotspot-weighted standard pass.

## Output Format

```markdown
---
date: "<TODAY>"
repository: "<repo>"
scope: "<focus or whole project>"
effort_level: "<quick|standard|deep>"
status: complete
---

# Codebase Improvements: <repo>

**Date:** <TODAY>
**Scope:** <whole project | focus area>
**Effort level:** <level>  **Recommendations:** N  **Already tracked (skipped):** M

## Summary

- High-confidence recommendations: N
- Raw candidates dropped as already tracked: M
- Deferred to "needs verification": K
- Not covered: <areas deliberately left out>

## Ranked Recommendations

| Rank | ID | Improvement | Category | Evidence | Impact | Effort | Confidence | Next step |
|---|---|---|---|---|---|---|---|---|
| 1 | CI-3 | <imperative title> | <category> | `src/x.py:42` | <concrete impact> | S | HIGH | `/create-issue` |

## Recommendation Detail

### CI-3: <imperative title>

- **Category:** <category>
- **Evidence:** `src/x.py:42`: <what is there>. <repeat for 2-5 sites>
- **Impact:** <what goes wrong, or what is paid, concretely>
- **Effort:** S | M | L
- **Confidence:** HIGH
- **Fix sketch:** <1-3 sentences>
- **Suggested next step:** `/create-issue` | `/create-needs-assessment` | `/improve-codebase` | `/audit-sdlc <scope>`

## Already Tracked (not re-proposed)

| Candidate | Tracked by | State |
|---|---|---|
| <title> | #<n> | open |

## Considered and Rejected

| Candidate | Reason |
|---|---|
| <title> | documented decision in `<doc>`; standard convention; not worth the change |

## Needs Verification (medium confidence, not recommended yet)

| Candidate | Signal | What to check |
|---|---|---|
| <title> | <the signal found> | <the read or run that would settle it> |

## Coverage and Exhaustion

- Swept: <categories and areas actually read>
- Skipped: <areas not scanned and why>
- Exhaustion: a full sweep of `<areas>` yielded no new untracked high-confidence candidate.
```

## Example Usage

**Scenario 1: First pass on an existing repo**
```
/identify-codebase-improvements
```
Loads all issues with `ghx`, maps the surface, and reads the code.
Finds a swallowed exception on the payment path, a duplicated retry helper in three modules, and an untested auth boundary.
Two other candidates were dropped because issues already track them.
Writes `.sdlc/codebase-improvements-2026-10-02.md` with 3 recommendations.
Files nothing.

**Scenario 2: Exhaustive deep pass**
```
/identify-codebase-improvements --deep --limit 20
```
Sweeps every package.
Discards 14 candidates that match existing issues, keeps 11 untracked high-confidence improvements, and reports that no further untracked candidate remained after the final sweep.

**Scenario 3: Focused on tests**
```
/identify-codebase-improvements --focus tests
```
Reads only the test surface and critical paths.
Surfaces untested money and auth code, and notes that a single valuable candidate was already tracked by issue #88.

**Scenario 4: File the top findings**
```
/identify-codebase-improvements --create-issues 3
```
Same pass, then files the top 3 untracked improvements via `/create-issue`, labeled `codebase-improvement`, each linking back to the report.

## Scheduling

This skill is designed to run safely on a schedule.
It is read-only by default (no commits, no PRs), idempotent (the known set and the prior report keep it from re-proposing), and bounded (`--limit`).
Recommended cadence: monthly, or weekly alongside `/improve-codebase`.
Pair with `/start-month` (discovery feeds planning) and `/improve-codebase` (lands the safe subset).

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `identify-feature-opportunities` | Proposes new value to build. This proposes quality improvements to what exists. Complementary; both feed planning. |
| `improve-codebase` | Applies the safe subset automatically. This reports the full high-confidence set, including items too risky to auto-apply. |
| `audit-sdlc`, `audit-*`, `find-*` | Breadth scanners without issue dedup. This skill consumes them as lead generators, vets their output, and filters out what is already tracked. |
| `check-issues-status` | Finds already-implemented issues to close. The inverse direction: this finds not-yet-tracked improvements to open. |
| `search-existing-issues` | The dedup primitive this skill applies per candidate. |
| `create-issue` | Consumed by `--create-issues` to file surviving recommendations. |
| `session-review` | Per-session checklist. This is the periodic discovery counterpart. |
| `review-skills` | Audits the skill library itself; unrelated to this skill's codebase target. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `ghx cache --repo <repo>` | Warm the local issue/PR cache for fast, rate-limit-friendly reads |
| `ghx issue list --repo <repo> --state all --limit 200 --json` | Load the known set of existing recommendations |
| `ghx issue list --repo <repo> --search "<keywords>" --state all --limit 10` | Per-candidate dedup search |
| `ghx issue view <number> --repo <repo> --comments` | Read a candidate match in full (pass a number, not a URL) |
| `git remote get-url origin` | Resolve the target repository |
| `git log --since="1 month ago" --name-only --pretty=format: \| sort \| uniq -c \| sort -rn` | Churn hotspots to weight the scan |
| `rg -n "TODO\|FIXME\|NotImplemented\|stub" .` | Surface-gap signals to seed candidates |
