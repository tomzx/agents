# Evidence Levels

One evidence standard shared by the audit and review skills.
Each of those skills cites this file instead of restating it.
It defines how a claim gets an evidence level and what a verdict must reach.

## The ladder

Levels run from a claim with no support (L0) to the behavior observed in the running product (L4).
Always write the level in the form `L<n> - <Name>`, so a reader who does not know the numbering still reads the level name.

| Level | What must exist |
|---|---|
| `L0 - Asserted` | The claim alone. No pointer. |
| `L1 - Cited` | A `file:line`, or the library source at its pinned version. |
| `L2 - Ruled out` | For a safety claim that something cannot happen: the walked failure path, step by step, showing the bad case cannot be reached. |
| `L3 - Executed` | A script or test that calls the code, run, with its output pasted. |
| `L4 - Reproduced` | The behavior observed in the running product (CLI run, browser, live service). |

`L2 - Ruled out` is for a claim that something cannot happen.
For a claim that something does happen, use `L3 - Executed` or `L4 - Reproduced`.

## Rules

1. **Label every finding.** Each finding or acceptance criterion carries an evidence level in the form `L<n> - <Name>`, plus an artifact on the same line: a command, a path, a SHA, or pasted output. A level with no artifact is an `L0 - Asserted` claim.
2. **Promote the decisive claims.** A claim the verdict depends on must reach `L3 - Executed` or `L4 - Reproduced`. Do not try to execute every claim. Spend the effort on the one or two that decide the result.
3. **Declare `unproven` when execution is not possible.** When a decisive claim cannot reach `L3 - Executed`, write `unproven`, name the runtime evidence it needed, and say why that was infeasible. An `unproven` result is valid and must be declared, not hidden.
4. **A verdict has a floor.** A pass, an approval, or a `conforms` result requires every decisive claim at `L3 - Executed` or `L4 - Reproduced`. An `L0 - Asserted`, `L1 - Cited`, or `L2 - Ruled out` claim never carries a pass on its own.

## Non-mutating execution

A read-only audit still runs code to reach `L3 - Executed`.
Write scratch scripts and tests under a temp directory such as `/tmp`, never into the repository.
Leave no artifacts behind.
The run must not modify the subject under audit.

## Where each skill stops

| Skill | Ceiling | Why |
|---|---|---|
| `audit-*` | `L3 - Executed` for the decisive findings, `L1 - Cited` or `L2 - Ruled out` for the rest | Static scans find candidates; a scratch script confirms the ones that decide the report. |
| `review-implementation` | `L3 - Executed` for a 🔴 MUST finding | A blocking finding cannot rest on an assertion. |
| `review-pr` | `L2 - Ruled out` | The review is static and does not build or run the code. A claim that needs execution routes to `verify-pr`. |
| `verify-pr` | `L4 - Reproduced` | It builds the PR and runs each criterion. |
