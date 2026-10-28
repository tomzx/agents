---
name: adversarial-pr-review
description: Adversarially attack a GitHub pull request by finding the most likely ways the change breaks, then trying to make each one happen and reporting what was reproduced. Unlike static review it may execute throwaway probes outside the repo to reach L3 - Executed or L4 - Reproduced. Use when the user asks "how could this PR break", "red team this PR", "adversarial review this PR", "attack this change", "find failure modes", "verify this failure is possible", "what is the worst case for this PR", or wants adversarial evidence next to review-pr and verify-pr.
allowed-tools: Bash(gh:*, ghx:*, git:*, uv:*, python:*, python3:*, node:*, npm:*, npx:*, go:*, cargo:*, make:*, docker:*, curl:*, ~/.agents/scripts/get-env:*, ~/.agents/scripts/should-post-to-github:*, ~/.agents/scripts/review-progress:*), Read, Write, Glob, Grep
argument-hint: "<pr-number> [repository]"
---

# Adversarial PR Review

Answers the **adversarial** question: "what is the most likely way this change breaks, and can I make it break?"
It assumes the change is broken and works to prove it, instead of checking that it does what it claims.

It complements the other review steps and does not replace them:

| Skill | Question | Evidence ceiling |
|---|---|---|
| `/review-pr` | Is the code well built? | `L2 - Ruled out` (static) |
| `/verify-pr` | Does the accepted behavior work? | `L4 - Reproduced` |
| `/validate-pr` | Is this the right product? | `L2 - Ruled out` (static plus issue reading) |
| `/adversarial-pr-review` | Which plausible failure happens, and can I reproduce it? | `L4 - Reproduced` |

Its contribution is adversarial reproduction: a ranked list of failure scenarios where the decisive ones were actually executed against the PR's code.
A suspicion that was never tried is reported as unproven, never as a failure.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md` (PR Review Reports for report location and posting rules).
- Apply the shared evidence standard in [`../sdlc/references/evidence.md`](../sdlc/references/evidence.md): label every finding with an `L<n> - <Name>` level.
  A `breaks` verdict requires at least one decisive scenario at `L3 - Executed` or `L4 - Reproduced`.
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read access to the target repository.
- `git worktree` available, and a toolchain able to run the PR's code (or the willingness to report `unproven` when it cannot).
- A scratch directory outside the repository, by default `/tmp/adversarial-pr-review-$PR_NUMBER`.
- Read-only toward the PR and its repository: probes run against the worktree, write only under the scratch directory, and never modify, stage, or commit anything in the worktree.
- Self-contained evidence: the attack needs only the diff, the codebase, the PR description, and the linked issue. It never reads or waits for sibling reports (`assess-pr-risk`, `summarize-behavior-changes`, `analyze-test-coverage`, `validate-pr`, `verify-pr`, `review-pr`).
- Orchestrators (`review-pr-full`, `review-requested-prs`) dispatch this skill concurrently with the analyze-test-coverage -> validate -> verify -> review chain and provide `WORKTREE_DIR`; because it shares no evidence with the chain, the parallel dispatch never weakens it.

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `adversarial-pr-review`.

### Communication guidelines (outbound text)

Before composing any text posted or drafted on the user's behalf, apply [`communication-guidelines/SKILL.md`](../communication-guidelines/SKILL.md).

## Workflow

```
Fetch PR metadata + diff + linked issue ($1)
          |
          v
CLOSED or MERGED? --> note and stop
          |
          v
Create or reuse git worktree
          |
          v
Map the attack surface
(entry points, invariants, trust
 boundaries, state, contracts)
          |
          v
Enumerate candidate failure scenarios (8 classes)
          |
          v
Rank by likelihood x impact
Select 3 to 5
          |
          v
Try to reproduce each selected scenario
(scratch probe, time-boxed, non-mutating)
   /          |           \
L3/L4        L2           unproven
reproduced   ruled out    could not run
   \          |           /
          v
Write adversarial-pr-review.<sha>.md
Post if should-post-to-github allows
          |
          v
Clean up probes and worktree
```

## Steps

### 1. Fetch PR metadata, diff, and intent

```bash
ghx pr view $PR_NUMBER --repo "$REPO" --comments --refresh
gh pr view $PR_NUMBER --repo "$REPO" --json title,body,state,headRefName,headRefOid,headRepository,author,files,additions,deletions,changedFiles,closingIssuesReferences
gh pr diff $PR_NUMBER --repo "$REPO"
```

Extract:
- `HEAD_COMMIT`: `headRefOid` (full SHA)
- `SHORT_SHA`: first 7 characters of `HEAD_COMMIT`
- `PR_AUTHOR`: `author.login`
- `HEAD_REPO`: `headRepository.nameWithOwner`
- `HEAD_BRANCH`: `headRefName`
- `HEAD_TREE`: `git fetch "https://github.com/$HEAD_REPO.git" "$HEAD_BRANCH" >/dev/null 2>&1 || true; git rev-parse "$HEAD_COMMIT^{tree}"`
- `ISSUE_NUMBER`: the first linked issue number from `closingIssuesReferences` (or empty)
- `PR_STATE`: `OPEN`, `CLOSED`, or `MERGED`
- The changed files, diff stats, PR description, and linked issue body

The PR description and issue state the intended behavior.
The attack targets that behavior: how does the change fail when a user, caller, or operator uses it as advertised, or when the world is not the happy path the author assumed.

If `PR_STATE` is `CLOSED` or `MERGED`, note it and stop.

Define the report directory once: `PR_REVIEW_DIR="$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER"` (see `sdlc/references/shared.md`, PR Review Reports).

Publish the in-progress marker before analyzing, and remove it before returning on every path (see `sdlc/references/shared.md`, In-progress marker).
From this point on, every return path runs the cleanup in step 10, including an early stop:

```bash
mkdir -p "$PR_REVIEW_DIR"
~/.agents/scripts/review-progress start --step adversarial-pr-review --repo "$REPO" --pr "$PR_NUMBER" --sha "$HEAD_COMMIT"
```

### 2. Create or reuse the worktree

If `$WORKTREE_DIR` is already set (e.g. by an orchestrator), use that directory directly and skip creation and cleanup.

```bash
_WORKTREE_OWNER=false
if [ -z "${WORKTREE_DIR:-}" ]; then
  git fetch "https://github.com/$HEAD_REPO.git" $HEAD_BRANCH
  WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
  mkdir -p /tmp/sdlc/$REPO
  git worktree add $WORKTREE_DIR FETCH_HEAD
  _WORKTREE_OWNER=true
fi
SCRATCH_DIR=/tmp/adversarial-pr-review-$PR_NUMBER
mkdir -p "$SCRATCH_DIR"
```

All code reading and every probe run against `$WORKTREE_DIR`.
Nothing is written inside it.

If worktree creation fails, clear the in-progress marker and stop:

```bash
~/.agents/scripts/review-progress stop --step adversarial-pr-review --repo "$REPO" --pr "$PR_NUMBER"
```

### 3. Map the attack surface

Read the diff and the code immediately around it, then record:

- **Entry points** the change adds or alters: functions, CLI commands, HTTP routes, jobs, migrations, hooks, config keys.
- **Invariants** the change relies on: an input is non-empty, a row exists, a lock is held, the caller checked authorization, the old and new code never run at once.
- **Trust boundaries** crossed: untrusted input to a sink, user input to a filesystem or query, tenant A to tenant B data, secret to log.
- **State and ordering** the change assumes: writes commit together, retries are idempotent, events arrive once, the process stays up between steps.
- **Contracts** the change touches: public API, wire format, CLI flags, config defaults, database schema, error types and status codes.
- **Callers** of every changed exported symbol: `Grep` the symbol, check sibling modules, packages, and tests.

Record the map in the report.
A scenario that does not name the entry point and the invariant it violates is a guess, not an attack.

### 4. Enumerate candidate failure scenarios

Walk the eight classes below against the attack surface.
For each class, write every candidate the diff plausibly enables.
Only keep a candidate that names a concrete mechanism in the changed code (`file:line`), not a generic worry.

| Class | Look for | Typical probe |
|---|---|---|
| **Input boundary** | Empty, null, zero, negative, maximum, malformed, unicode, oversized, or wrong-typed input reaching the changed parsing, validation, or arithmetic | Call the function or command with the boundary value |
| **Trust boundary** | Untrusted input reaching a sink (query, shell, path, template, deserializer), authorization checked on one path but not another, tenant or user scope missing, secret written to a log or error | Send the payload or call the unguarded path |
| **State, ordering, concurrency** | Partial write, non-idempotent retry, duplicate delivery, interleaved requests, crash between two steps, cache and source disagreeing | Run the operation twice, concurrently, or after a forced failure |
| **Persistence and migration** | Existing rows that do not match the new structure, backfill that misses rows, old and new code running together, rollback that cannot restore, lock taken on a large table | Seed a throwaway database with old-format data and run the migration |
| **Contract and compatibility** | Existing consumer of a changed signature, response field, status code, exit code, flag, or config default; version skew during rollout; error type changed | Call the old contract against the new code |
| **Error paths and recovery** | Swallowed exception, cleanup skipped on failure, wrong error mapped to the user, retry storm, misleading message, resource left open | Force the dependency to fail and inspect what the caller sees |
| **Resources and limits** | Unbounded growth, missing timeout, N+1, large payload held in memory, connection or file descriptor leak, work proportional to untrusted input | Drive the path with a large or repeated input |
| **Deployment and operational state** | Feature flag defaulting on, startup order, shutdown mid-write, missing permission, health check that passes while the feature is broken, rollback that needs a manual step | Trace the deploy and rollback path statically; run only if locally possible |

### 5. Rank and select

Score each candidate on two axes, citing evidence:

| Likelihood | Criteria |
|---|---|
| High | The diff directly implements the path, an existing caller reaches it, and no test exercises the case |
| Medium | Reachable only through a specific state, config, or input, or a test exists but misses the case |
| Low | No caller in the repo, or a guard already rules the state out |

| Impact | Criteria |
|---|---|
| High | Data loss or corruption, authorization bypass, outage, wrong money or access decision, irreversible change |
| Medium | Wrong result on a user-facing path, degraded performance, failure that needs manual repair |
| Low | Misleading message, cosmetic defect, easy workaround |

Select the 3 to 5 highest likelihood x impact scenarios, always including at least one High-impact scenario even when its likelihood is Medium.
Cap at 5: more than that cannot be reproduced in the time budget.
List the candidates you did not select as deferred in the report, so the next reviewer knows what was considered and skipped.

### 6. Try to reproduce each selected scenario

For each selected scenario, find the narrowest seam that reaches the changed code and execute a scratch probe against it.
Prefer the repo's own test runner, fixtures, and fakes so the probe exercises the actual code with controlled inputs.

| Surface | Probe | Level |
|---|---|---|
| Library or pure function | Scratch script that imports the checkout (`PYTHONPATH="$WORKTREE_DIR" uv run "$SCRATCH_DIR/probe.py"`), asserts the bad behavior | `L3 - Executed` |
| CLI | Run the worktree's CLI entry point with the adversarial input, capture exit code, stdout, and stderr | `L4 - Reproduced` |
| HTTP handler | Start the app from the worktree on a free port, send the request, capture the response, tear it down | `L4 - Reproduced` |
| Background job or worker | Invoke the job function directly, or run one worker iteration with a scratch queue or database | `L3 - Executed` |
| Database migration | Create a throwaway database, seed old-format rows, run the migration, inspect the schema and rows | `L3 - Executed` |
| Concurrency | Drive the operation from N concurrent callers against the scratch instance, assert the invariant | `L3 - Executed` |
| Deploy or config | Static trace of defaults, startup order, and rollback; runtime only when a local run is possible | `L2 - Ruled out` at best |

Rules for a probe:

- **Non-mutating.** Write only under `$SCRATCH_DIR`.
  Never edit, stage, or commit in the worktree, and never touch the PR branch.
- **Disposable state.** Use a temporary database file or a throwaway container (`docker run --rm --network none` unless the probe needs a local port), never a live database, bucket, or queue.
- **No live credentials, no production, no network writes.** A probe that needs them is not run; mark the scenario unproven and name what it needed.
  Any HTTP request goes to `localhost` only, and no package is installed from a registry for a probe.
- **No destructive operation**, no matter how confident the outcome. A migration that drops data is reviewed statically, never executed against anything live.
- **Time-boxed.** Ten minutes per scenario and 25 minutes total for all probes.
  Stop when the budget is spent, keep what was learned, and mark the rest unproven.
- **Minimal.** The probe should be the smallest call that demonstrates the behavior.
  Paste it into the report so the author can rerun it.
- **Deterministic check.** Assert the specific observable difference (exit code, exception type, response body, row count, log line), not "it looked wrong".

A scenario ends in one of three states:

| State | Meaning |
|---|---|
| **Reproduced** | The probe ran and the failure was observed: `L3 - Executed` or `L4 - Reproduced` |
| **Ruled out** | The failure path was walked and cannot be reached (`L2 - Ruled out`), or the probe ran and the code behaved correctly (`L3`) |
| **Unproven** | The decisive probe could not run; name the runtime evidence it needed and why that was infeasible |

Delete the scratch directory when the probes are done.

### 7. Judge the findings

Each reproduced scenario is a finding with:

- **Severity**: `MUST` when it loses or corrupts data, bypasses a trust boundary, causes an outage, or gives a wrong money or access decision; `SHOULD` when it gives a wrong result on a user-facing path or needs manual repair; `MAY` otherwise.
- **Evidence level** with the probe and its output on the same line.
- **Impact**: who hits it, when, and what they see.

Rank reproduced findings by severity, then by impact.
A `MUST` finding requires `L3 - Executed` or `L4 - Reproduced`; a MUST that could not be executed is reported as unproven, not as a blocker.

Do not convert a ruled-out scenario into a passing claim about the whole change.
State it as what was tested: one failure path, ruled out.

### 8. Decide the verdict

| Verdict | Light | Condition |
|---|---|---|
| `breaks` | 🔴 No-go | At least one scenario reproduced with an observable failure a user, caller, or operator can hit |
| `unproven` | 🟡 Caution | No failure reproduced, and at least one decisive scenario was not executed (including a run where no probe could execute) |
| `holds` | 🟢 Go | At least one probe executed and passed, every other selected scenario was ruled out, and no decisive scenario is unproven |

`L2 - Ruled out` alone never carries `holds`: a scenario walked and shown impossible can complete the list, but at least one scenario must reach `L3 - Executed`.
The one exception is a diff with no executable surface (documentation or comments only): there is nothing to probe, so report `holds` and say the green means "nothing executable changed", not "the code is safe".
A decisive execution that could not run makes the verdict `unproven`, never `holds`, because the evidence floor in `evidence.md` does not allow a pass on reading alone.

`holds` does not mean the change is correct or well built; it means the attacks that were tried did not land.
Say that in one sentence.

### 9. Write the report and post it

Write the report to `$PR_REVIEW_DIR/adversarial-pr-review.<SHORT_SHA>.md` and point the stable symlink at it (`ln -sf "adversarial-pr-review.<SHORT_SHA>.md" "adversarial-pr-review.report.md"`).
Start the file with the marker, then the traffic-light header from `sdlc/references/shared.md` (Report header (traffic light)).

```
<!-- {"step":"adversarial-pr-review","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"VERDICT_TOKEN","reproduced_count":N,"unproven_count":N} -->
```

Posting as a PR comment is decided by `should-post-to-github`.
Run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`; if it exits 1, skip posting (the report is saved locally).
If it exits 0, set `REPORT` to the report file's contents and `FOOTER` to the attribution footer per `../github-post-attribution/SKILL.md`, then post with the **Posting a review report** recipe in `skills/sdlc/references/shared.md` (`STEP="adversarial-pr-review"`).
The recipe updates this step's existing comment on the PR (append or replace per `PR_REVIEW_POST_MODE`, default `replace`) instead of adding a new comment on every run.

### 10. Clean up

```bash
rm -rf /tmp/adversarial-pr-review-$PR_NUMBER
~/.agents/scripts/review-progress stop --step adversarial-pr-review --repo "$REPO" --pr "$PR_NUMBER"
if [ "$_WORKTREE_OWNER" = true ]; then
  git worktree remove $WORKTREE_DIR
fi
```

## Output Format

````markdown
<!-- {"step":"adversarial-pr-review","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"VERDICT_TOKEN","reproduced_count":N,"unproven_count":N} -->
# Adversarial PR Review: PR #<PR_NUMBER> <title>

**🔴 / 🟡 / 🟢 <Breaks / Unproven / Holds>**: <one sentence: the highest-impact reproduced failure, or what was attacked and held>

- 🟢 / 🟡 / 🔴 Attack surface mapped
- 🟢 / 🟡 / 🔴 Scenarios ranked
- 🟢 / 🟡 / 🔴 Probes executed: <n> of <m> selected
- 🟢 / 🟡 / 🔴 Decisive evidence: <r> reproduced, <u> unproven

Reviewed commit: `SHORT_SHA`
**Verdict: <breaks | unproven | holds>** · **Reproduced: <r>** · **Ruled out: <o>** · **Unproven: <u>**

## Reproduced failures

### RT-1: <scenario name>: <MUST | SHOULD | MAY>, `L3 - Executed` / `L4 - Reproduced`

- **Trigger:** <the input, state, or sequence>
- **Mechanism:** `<file>:<line>` <how the changed code reaches the failure>
- **Probe:**
  ```bash
  <exact command, with the scratch file inlined above it or shown here>
  ```
- **Observed:** <the actual output, exit code, exception, or rows>
- **Expected:** <what the code promises>
- **Impact:** <who hits it, when, and what they see>

## Ruled out

| ID | Scenario | Why it cannot happen | Evidence |
|---|---|---|---|
| RT-<n> | <scenario> | <the walked failure path, or the probe that passed> | `L2 - Ruled out` / `L3 - Executed`, <artifact> |

## Unproven

| ID | Scenario | What would prove it | Why it was not run |
|---|---|---|---|
| RT-<n> | <scenario> | <runtime evidence needed> | <missing toolchain, needs production, needs a live credential, over budget> |

## Attack surface

| Element | What the change adds or assumes | Where |
|---|---|---|
| Entry point | <function, CLI command, route, job, migration> | `<file>:<line>` |
| Invariant | <assumption the code relies on> | `<file>:<line>` |
| Trust boundary | <input or identity crossing a boundary> | `<file>:<line>` |
| Contract | <public API, wire format, schema, flag, config default> | `<file>:<line>` |

## Deferred candidates

<Scenarios that ranked below the cut, one line each: the candidate and why it was deferred. Omit the section when nothing was deferred.>

## Time spent

<Minutes on reading, per-probe minutes, total. Note when the budget cut the run short, and what was left unproven because of it.>

---
<Attribution footer per github-post-attribution>
````

## Failure Modes

| Mode | Response |
|---|---|
| **Worktree creation fails** | Stop |
| **PR is CLOSED or MERGED** | Note it and stop |
| **No scenario survives the ranking** | If the diff has executable code, report `unproven` and say why no probe was warranted; if it has no executable surface, report `holds` and say nothing executable changed |
| **Toolchain missing or the build exceeds the budget** | Mark the affected scenarios unproven, name the missing tool, and report `unproven` when one of them was decisive |
| **A probe would touch live data or production** | Do not run it; mark the scenario unproven and say which environment it needed |
| **Probe leaves the worktree dirty** | Stop, remove the probe files you created, report the probe as invalid, and list the dirty paths; never run `git checkout`, `git reset`, or `git clean` in a worktree the orchestrator shares |
| **Diff is 1000 lines or more** | Sample entry points and public surface, say what was not attacked, and cap confidence in the report |

## Example Usage

**Scenario 1: Small parser change with a reproduced boundary failure**
```
/adversarial-pr-review 42 acme/api
```
The diff adds a new `parse_window` helper with no test for an empty input.
Candidate: `parse_window("")` raises an unhandled `IndexError` on a user-supplied header.
Probe imports the module from the worktree and calls it: reproduced at `L3 - Executed`.
Two other candidates (retry ordering, migration backfill) are ruled out by walking the code.
Verdict `breaks`, one MUST finding.

**Scenario 2: Auth change, no way to execute**
```
/adversarial-pr-review 88 acme/api
```
The diff narrows session validation.
Candidate: a revoked token still passes on the refresh path.
The probe needs a running identity provider that is not available locally, so the scenario is unproven and the report names the missing fixture.
Verdict `unproven`, with the exact seam and input the author should test.

**Scenario 3: Refactor that holds**
```
/adversarial-pr-review 55 acme/web
```
Candidates: partial write on cancel, stale cache after rename, old client sending the removed field.
The first two run against a scratch database and the repo's test fixtures and pass; the third is ruled out by tracing the deserializer's default.
Verdict `holds`, with the three attacks and their evidence listed.

**Scenario 4: Adversarial input on a CLI**
```
/adversarial-pr-review 77 acme/cli
```
The diff adds `--format` to a command.
A probe runs the command with `--format ../../etc/passwd` and a two-gigabyte value.
The path traversal is rejected; the oversized value is buffered whole and the process is killed, reproduced at `L4 - Reproduced`.
Verdict `breaks`, one SHOULD finding with the command and output pasted.

## Next Step

Route the verdict: `breaks` → the reproduced findings go to the author with the probes, and the reviewer treats them as blockers; `unproven` → ask the author or CI for the runtime evidence named in the report; `holds` → record what was attacked and do not re-run the same attacks on the next review of an unchanged diff.
