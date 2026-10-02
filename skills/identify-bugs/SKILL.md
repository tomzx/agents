---
name: identify-bugs
description: Proactively discover latent bugs in an existing codebase (correctness, error handling, null and boundary handling, async, concurrency, state, resource management), keep only high-confidence ones, verify each where a seam exists, and use ghx to discard anything already tracked by a GitHub issue, searching for another candidate until nothing useful remains. Use when the user says /identify-bugs, "find bugs", "hunt for bugs", "look for latent bugs", "bug sweep", "what is broken", or wants a periodic bug-discovery pass that does not re-report known defects. Distinct from reproduce-issue (a known bug) and review-pr (a diff).
allowed-tools: Bash(ghx:*, gh:*, git:*, rg:*, uv:*, python:*, python3:*, pytest:*, node:*, npx:*, go:*), Read, Glob, Grep, Write
argument-hint: "[repository] [--focus <area>] [--limit N] [--create-issues N] [--since <YYYY-MM-DD>] [--no-verify] [--quick|--deep]"
---

TODAY=!`date +%Y-%m-%d`
REPO=!`git remote get-url origin 2>/dev/null | sed -E 's#.*[:/]([^/]+/[^/]+)(\.git)?$#\1#'`

# Identify Bugs

Reads an existing codebase and surfaces latent defects that are worth fixing and are not already tracked in the issue tracker.
Every candidate must clear three gates: high confidence (the code path exists and is reachable), verification where possible (a failing test or runnable repro), and not already an existing GitHub issue.
The dedup is what keeps the pass useful: the skill loads the issue history with `ghx` up front and re-checks each candidate, dropping anything tracked and continuing until no untracked bug remains.

This is a proactive, whole-codebase hunt.
It does not modify or commit source code.
It produces a ranked bug report, and optionally files issues for the bugs that survive dedup.

## The Core Problem This Solves

Bugs are usually found by accident, from a stack trace or a user report.
A static scan in the other direction produces a pile of "probably a bug" claims, most of which are defensively handled elsewhere, by design, or already known.
Both directions waste effort.
This skill walks the code deliberately, states the exact input and state that produces wrong behavior, verifies the claim where a test seam exists, and excludes anything already tracked, so what it reports is worth acting on.

## How This Differs From Related Skills

| Skill | Direction | Input | Output |
|---|---|---|---|
| `identify-bugs` | Proactive hunt for unknown defects | Whole codebase | Ranked, verified, untracked bugs |
| `reproduce-issue` | Confirm one known bug | A GitHub issue | A reproduction comment |
| `diagnosing-bugs` / `systematic-debugging` | Diagnose one known symptom | A failure | A root cause |
| `review-pr` / `identify`-style diff review | Bugs introduced by a change | A diff | Review findings |
| `audit-functional-suitability` | Does the code meet requirements | Requirements corpus | Completeness and correctness signals |
| `identify-codebase-improvements` | Make correct code better | Whole codebase | Improvement recommendations |
| `audit-security` | Security vulnerabilities | Whole codebase | Security findings |

The seam with `identify-codebase-improvements`: a bug is behavior that is wrong (it produces an incorrect result or crashes); an improvement is behavior that is correct but could be better.
A missing validation that lets bad data through is a bug; a missing validation that only costs style points is an improvement.
When a candidate is security-relevant, defer the deep analysis to `audit-security` and note it, rather than duplicating it here.

## Prerequisites

- Working directory is the root of a `git` repository (or a path inside it)
- `ghx` installed and authenticated (falls back to `gh auth token`); run `ghx cache` once so list and search are served locally
- The project's build, test, and run commands are known (read `AGENTS.md`, the language manifest, or the CI config)
- Read `.sdlc/context/` and any decision or design docs; a documented decision or standard convention is not a bug
- If no repository argument is provided, operate on `$REPO` (derived from `origin`), then the current working directory

## What Counts as a Bug

Treat these as prompts, not a checklist to fill. Read the code paths they point to and judge.

| Category | What to look for |
|---|---|
| Error handling | swallowed exceptions, empty catches, catch-and-continue on critical paths, errors logged but never surfaced, missing rollback |
| Null and empty handling | unchecked indexing, non-null assertion on a possibly-null value, missing empty-collection branch, presence assumed from a lookup that can fail |
| Boundaries | off-by-one in loops and slices, integer overflow, timezone and locale assumptions, encoding mismatches, inclusive versus exclusive ranges |
| Async and concurrency | unawaited promises, shared mutable state without synchronization, check-then-act races, missing transaction around a multi-write, non-idempotent retries |
| State and control flow | unhandled enum or status branches, a `default` that silently no-ops, impossible states made representable, switched conditions, assignment where comparison was meant |
| Resource management | unclosed handles, connections, or subscriptions, missing `finally`, migration without cleanup, accumulated listeners |
| Input and data integrity | missing schema validation at a trust boundary, mass assignment, unsafe deserialization, silent truncation, lossy conversions |
| Copy-paste and logic errors | the same-variable mistake, precedence assumptions, wrong operator, inverted condition, stale constant |

## The High-Confidence Bar

A candidate is reported only when all of these hold:

1. **Concrete wrong behavior.** State the input and state that produce an incorrect result, a crash, or data loss. "This could be a problem" is not a bug report.
2. **Reachable.** The path can actually execute in production. Exclude dead code, test-only paths, and code behind a flag that is always off. If reachability is uncertain, say so and treat it as suspected, not confirmed.
3. **Evidence read first-hand.** Cite `file:line` for every location involved and open each one. A finding inherited from a scanner or a subagent is a lead, not a fact.
4. **False positives rejected.** Before keeping, rule out the common classes below.
5. **Verified where possible.** Run the failing test or repro (see Verification). A bug that is statically certain but not run-verified is reported with `verification: static`.

### Common False Positives to Reject

- Behavior that is intentional, documented in an ADR or design doc, or a standard platform convention.
- The bug is already guarded by a caller, an upstream validation, a framework behavior, or an existing test.
- Generated code, vendored dependencies, or migrations not meant to be read.
- A performance concern with no incorrect result (that is an improvement, not a bug).
- An error path that is correctly handled, just not the way the reader expected.

## Verification

Verification is what separates a bug report from a guess. Where a seam exists, confirm the bug before keeping it.

Follow the seam discipline from `diagnosing-bugs`:

- Build the smallest pass/fail signal that goes red on this exact bug: an existing test, a one-off script, a CLI invocation with a fixture, an HTTP call, or a headless browser check.
- Prefer the tightest seam that exercises the actual bug pattern at its call site. A shallow unit test that cannot replicate the chain that triggers the bug gives false confidence.
- Run the repro once and show the command and its output. Redact secrets first, and never write a secret into the report.
- **If no correct seam exists, that itself is a finding.** Note that the architecture prevents the bug from being locked down by a test.

Verification must leave the working tree unchanged. Use an existing test, a throwaway file under `/tmp`, or a disposable `git worktree`, and delete it afterward. Never commit, and never edit source as part of this skill.

When `--no-verify` is passed, or the bug is a static certainty with no runnable seam, record `verification: static` and move on. Do not overstate a static finding as confirmed.

## The Dedup Contract (ghx)

This is mandatory.

### Load the known set once, up front

Warm the cache and pull the issue history. Existing issues, open or closed, are the already-known defects.

```bash
ghx cache --repo "$REPO"
ghx issue list --repo "$REPO" --state all --limit 200 --json
```

Build a known set from issue number, title, state, and labels.
Also read every prior report at `.sdlc/bugs-*.md` and carry forward its entries and its "already tracked" and "rejected" ledgers, so a re-run does not redo settled work.

### Re-check every candidate before it is kept

Extract 2 to 4 keyword combinations from the most distinctive signals: error strings, function and file names, the symptom, the affected endpoint.
Search, then read the top matches rather than trusting titles.

```bash
ghx issue list --repo "$REPO" --search "<keywords>" --state all --limit 10
ghx issue view <number> --repo "$REPO" --comments
```

Pass a number, not a URL: `ghx issue view` rejects URL arguments.

### The loop

1. Generate a candidate bug from the code.
2. Vet it against the high-confidence bar and verify it where a seam exists.
3. Search the known set and the tracker for it.
4. If any issue tracks it, discard it, record `already tracked: #<n> (<state>)`, and go back to step 1 for another candidate.
5. If no issue tracks it, keep it.
6. Repeat until the requested count is reached or a full sweep of the surface yields no new untracked bug.

Only then is the pass done.
State the exhaustion evidence in the report: what areas were swept, how many candidates were dropped as already tracked, and which categories were not covered.

## Steps

### 1. Resolve scope and read context

Resolve the repository from `$1`, then `$REPO`, then the current directory. Apply `--focus` if given.
Read `.sdlc/context/` and any decision or design docs. Record settled decisions and standard conventions so they are not reported as bugs.
Discover and record the exact build, test, and run commands; they are needed for verification.

### 2. Load the known set with ghx

Run the load commands above. Record the count of existing issues and the prior report IDs. This set is consulted for every candidate in step 4.

### 3. Map the code surface and the risky paths

Identify languages, entry points, and the critical paths (money, auth, data mutation, the feature the project exists for).
Weight the hunt toward high-churn and high-criticality code, and toward boundaries where data crosses into the system.

### 4. Generate, vet, verify, and dedup candidates

For each candidate:

1. State the exact input and state that produce wrong behavior, and cite the `file:line` of every path involved.
2. Open the cited code and reject false positives (guards, by-design behavior, dead code, generated code).
3. Verify where a seam exists. Record `verified` with the command and outcome, or `static`.
4. Run the dedup search. If tracked, discard and continue the loop.
5. Keep it, capturing severity, evidence, trigger, impact, verification status, and a 1-3 sentence fix sketch.

Continue until the `--limit` count is reached or the surface is exhausted.

### 5. Rank

Order by severity first, then by confidence, reachability, and reach:

| Severity | Criteria |
|---|---|
| Critical | Data loss or corruption, auth bypass, a crash on a core path, incorrect money or security-critical math |
| High | User-visible incorrect behavior on a common path, or an intermittent failure from a race |
| Medium | Wrong behavior on an edge case, or a swallowed error on a non-critical path |
| Low | Latent bug in a rarely-hit path, or a defensive gap |

Prefer confirmed bugs over static ones at the same severity.

### 6. Write the report

Write to `.sdlc/bugs-<TODAY>.md` (repo only).
Continue the bug ID sequence from the previous report. Use the Output Format below.
The report is the deliverable and must stand alone; do not reference the live conversation.

### 7. Optional issue creation

Only when `--create-issues N` is passed, file the top N via `/create-issue`.
Label them `bug` (and the relevant area label if one exists).
Each issue body cites the evidence and the verification, and links back to the report.
Before filing, check repository visibility: if the repository is public, confirm before publishing any bug that describes a security weakness or a credential location.

## Flags

- `--focus <area>` restricts the hunt to one area (a module path, `api`, `cli`, `ui`, or a category such as `async`).
- `--limit N` caps the number of kept bugs (default `10`). The loop still runs to exhaustion or until N is reached.
- `--create-issues N` files the top N as GitHub issues (off by default; report-only).
- `--since <YYYY-MM-DD>` restricts issue dedup and git signal to issues and commits since this date (default: all issues).
- `--no-verify` skips runtime verification and reports static findings only.
- `--quick` scans hotspots only (recent churn, critical paths). `--deep` sweeps every package. Default is a hotspot-weighted standard pass.

## Output Format

```markdown
---
date: "<TODAY>"
repository: "<repo>"
scope: "<focus or whole project>"
effort_level: "<quick|standard|deep>"
status: complete
---

# Bugs Found: <repo>

**Date:** <TODAY>
**Scope:** <whole project | focus area>
**Confirmed:** N  **Static:** N  **Already tracked (skipped):** M

## Summary

- Bugs kept: N (N confirmed, N static)
- Raw candidates dropped as already tracked: M
- Deferred to "suspected": K
- Not covered: <areas deliberately left out>

## Ranked Bugs

| Rank | ID | Bug | Category | Severity | Evidence | Verification | Confidence |
|---|---|---|---|---|---|---|---|
| 1 | BUG-3 | <imperative title> | <category> | High | `src/x.py:42` | verified | HIGH |

## Bug Detail

### BUG-3: <imperative title>

- **Category:** <category>
- **Severity:** Critical | High | Medium | Low
- **Evidence:** `src/x.py:42`: <what is there>. <repeat for 2-5 sites>
- **Trigger:** <the exact input and state that produce wrong behavior>
- **Impact:** <what goes wrong, concretely>
- **Reachability:** <how the path is reached in production>
- **Verification:** verified | static. <command and outcome when verified>
- **Confidence:** HIGH | MED
- **Fix sketch:** <1-3 sentences>
- **Suggested next step:** `/create-issue` then `/fix-issue` | `/reproduce-issue` (no seam)

## Already Tracked (not re-reported)

| Bug | Tracked by | State |
|---|---|---|
| <title> | #<n> | open |

## Rejected (considered, not a bug)

| Candidate | Reason |
|---|---|
| <title> | handled by caller; documented decision; standard convention; improvement not bug |

## Suspected (could not verify, medium confidence)

| Bug | Signal | What would confirm it |
|---|---|---|
| <title> | <the signal found> | <the test or run that would settle it> |

## Coverage and Exhaustion

- Swept: <categories and areas actually read>
- Skipped: <areas not scanned and why>
- Exhaustion: a full sweep of `<areas>` yielded no new untracked bug.
```

## Example Usage

**Scenario 1: First pass on a service**
```
/identify-bugs
```
Loads all issues with `ghx`, maps the critical paths, and reads the code. Confirms an unawaited promise in the request handler with a failing test, and a swallowed exception on the payment path statically. Two other candidates were dropped because issues already track them. Writes `.sdlc/bugs-2026-10-02.md` with 3 bugs. Files nothing.

**Scenario 2: Exhaustive deep pass**
```
/identify-bugs --deep --limit 20
```
Sweeps every package. Discards 9 candidates that match existing issues, keeps 7 untracked bugs, and reports that no further untracked bug remained after the final sweep.

**Scenario 3: Focused on async**
```
/identify-bugs --focus async
```
Reads only asynchronous code paths. Surfaces a check-then-act race in a shared cache and a listener that is never removed, and notes that a third candidate was already tracked by issue #141.

**Scenario 4: File the top findings**
```
/identify-bugs --create-issues 3
```
Same pass, then files the top 3 untracked bugs via `/create-issue`, labeled `bug`, each linking back to the report.

## Scheduling

This skill is designed to run safely on a schedule.
It is read-only (no commits, no PRs), idempotent (the known set and the prior report keep it from re-reporting), and bounded (`--limit`).
Recommended cadence: monthly, or weekly for high-churn repositories.
Pair with `/fix-issue` (fixes what it finds) and `/identify-codebase-improvements` (the improvement counterpart).

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `reproduce-issue` | Reproduces a known bug from an issue. This finds unknown bugs and verifies them at a seam; if it cannot, it hands to `reproduce-issue`. |
| `diagnosing-bugs`, `systematic-debugging` | Symptom-driven diagnosis for a known failure. Their seam and root-cause discipline is adopted here for verification. |
| `identify-codebase-improvements` | The sibling pass for code that works but could be better. A bug is wrong behavior; an improvement is correct behavior that could be improved. |
| `audit-functional-suitability` | Checks the code against requirements. This hunts defects independent of any requirement. |
| `audit-security` | Deep security analysis. Security-relevant candidates found here are noted and handed off, not fully analyzed. |
| `review-pr` | Reviews a diff. This hunts the whole existing codebase. |
| `find-*` | Quality scanners used as lead generators; their output is vetted here, never reported raw. |
| `create-issue`, `fix-issue` | Consumed by `--create-issues` and the recommended next step. |
| `check-issue-status` | Determines whether a tracked bug is already fixed. The inverse check for a candidate that turns out to be tracked. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `ghx cache --repo <repo>` | Warm the local issue/PR cache for fast, rate-limit-friendly reads |
| `ghx issue list --repo <repo> --state all --limit 200 --json` | Load the known set of existing defects |
| `ghx issue list --repo <repo> --search "<keywords>" --state all --limit 10` | Per-candidate dedup search |
| `ghx issue view <number> --repo <repo> --comments` | Read a candidate match in full (pass a number, not a URL) |
| `git log --since="1 month ago" --name-only --pretty=format: \| sort \| uniq -c \| sort -rn` | Churn hotspots to weight the hunt |
| `rg -n -U -B1 "except[^:]*:\s*\n\s*(pass\|continue\|\.\.\.)" -g '*.py' .` | Swallowed exceptions (Python) |
| `rg -n "catch\s*\([^)]*\)\s*\{\s*\}" -g '*.{js,ts}' .` | Empty catch blocks (JS/TS) |
