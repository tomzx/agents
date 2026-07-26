---
name: validate-implementation
description: Visually validate the implemented feature on the current branch BEFORE opening a PR, so the user can confirm the feature works as intended. Captures a CLI demo (via record-asciinema) or a web screenshot/video (via record-playwright) and presents it for human confirmation. For bug fixes, replays the reproduce-issue before-command on the fixed code to produce a comparable after recording. Writes a proof manifest that create-pr consumes, so the recording happens prior to PR creation rather than during it. Use when the user says /validate-implementation, "record a demo before the PR", "visually verify the feature", "show me it works before opening a PR", or wants pre-PR visual proof.
allowed-tools: Bash(git:*, asciinema:*, agg:*, asciicast2gif:*, svg-term:*, npx:*, npm:*, node:*, uv:*, python:*, python3:*, curl:*, scripts/get-env:*), Read, Write, Glob, Grep
argument-hint: "[repository] [issue-number]"
---

# Validate Implementation

Captures visual proof that the implemented feature works, on the current working branch, **before** a pull request is opened. Presents the captured asset to the user for visual confirmation so problems are caught before review begins.

This is the pre-PR producer of visual proof. It pairs with [`create-pr`](../create-pr/SKILL.md), which is a pure consumer: `create-pr` detects the proof this skill writes and embeds it, but no longer captures recordings itself. Recording happens here, at human-review time, not inside PR creation.

`/validate-pr` is a different, later step: it validates the claims of an **already-open** PR claim-by-claim. This skill validates the **implementation** on the branch with a single representative asset, before the PR exists.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, use `$REPO` and link `$ISSUE_NUMBER`.
- Implementation is complete on the current branch and tests pass (run `/create-implementation` and `/review-implementation` first).
- The branch has commits ahead of the base branch.
- For visual proof (best-effort): `asciinema` + renderer for CLI changes (via [`/record-asciinema`](../record-asciinema/SKILL.md)), or Playwright for web UI changes (via [`/record-playwright`](../record-playwright/SKILL.md)). If unavailable, the step is skipped with a clear note (it is never silently swallowed, because the whole point of this skill is to produce proof).

## Workflow

```
Resolve surface (from diff) + proof dir
            |
            v
Bug-fix manifest present? ($PROOF_DIR/proof-manifest.txt)
   /              \
  Yes              No
   |                |
   v                v
Replay manifest   Classify diff
command/URL on    (CLI or web UI?)
fixed code          /          \
   |             Yes           No
   |              |            |
   |              v            v
   |        Capture single    Skip proof
   |        (record-asciinema /  (non-visual change;
   |         record-playwright)   report + stop)
   |              |
   +------+-------+
          |
          v
   Write captured-proof.json
          |
          v
   Present asset(s) to user
          |
          v
   User confirms feature works?
      /         \
    Yes          No
     |            |
     v            v
   Done         Report what is wrong,
   (ready for   stop (do NOT open a PR)
   create-pr)
```

## Steps

### 1. Resolve the proof directory and surface

Resolve the per-repo, per-issue proof directory (same location `reproduce-issue` and `create-pr` use, so assets never collide with other work):

```bash
REPO="${1:-$REPO}"
ISSUE_NUMBER="${2:-$ISSUE_NUMBER}"
PROOF_DIR="/tmp/$REPO/${ISSUE_NUMBER:-housekeeping}"   # /tmp/<owner>/<repo>/<issue-id>
mkdir -p "$PROOF_DIR" 2>/dev/null || true
```

Compute the diff against the base branch to classify the change surface:

```bash
git diff $(git merge-base HEAD origin/main)..HEAD
```

Classify from the diff:

- **CLI changes** (entry points, `cli/`, `cmd/`, argument parsing, `--help`): surface = `cli`.
- **Web UI changes** (`src/pages`, routes, components, templates, CSS): surface = `web`.
- **Neither / not determinable**: surface = `none`.

### 2. Capture the proof

#### Bug-fix fast path (before/after pair)

Check for a before-recording manifest written by `reproduce-issue`:

```bash
test -f "$PROOF_DIR/proof-manifest.txt"
```

If present, read it to recover the surface and the demonstration command/URL used to capture the bug:

```bash
cat "$PROOF_DIR/proof-manifest.txt"
```

Then capture the matching **after** recording on the now-fixed code using the exact same command/URL, so the pair is directly comparable:

- `surface: cli` → read [`../record-asciinema/SKILL.md`](../record-asciinema/SKILL.md) and invoke it with `RECORD_SLUG` = `after-fix`, `RECORD_DIR` = `$PROOF_DIR`, `RECORD_COMMAND` = the manifest's command.
- `surface: web` → read [`../record-playwright/SKILL.md`](../record-playwright/SKILL.md) and invoke it with `RECORD_SLUG` = `after-fix`, `RECORD_DIR` = `$PROOF_DIR`, `RECORD_URL` = the manifest's url, `RECORD_VIEWPORTS` = `1280x720`, `RECORD_SERVER_CMD` = the manifest's server_cmd.

The before asset is the existing `$PROOF_DIR/before-bug.*`; the after asset is the freshly captured `$PROOF_DIR/after-fix.*`. Record both paths. If the after capture fails, keep the before asset alone so the bug is still visible, and record `mode: bugfix-before-only`.

#### Default (single representative asset)

With no manifest present, capture one representative asset for the classified surface:

- **CLI** → identify the CLI entry point from the codebase and pick one representative command that exercises the change. Read [`../record-asciinema/SKILL.md`](../record-asciinema/SKILL.md) and invoke it with `RECORD_SLUG` = `pr-demo`, `RECORD_DIR` = `$PROOF_DIR`, `RECORD_COMMAND` = the representative command.
- **Web UI** → identify the dev server command (e.g. `npm run dev`) and the changed route. Read [`../record-playwright/SKILL.md`](../record-playwright/SKILL.md) and invoke it with `RECORD_SLUG` = `pr-demo`, `RECORD_DIR` = `$PROOF_DIR`, `RECORD_URL` = the changed route, `RECORD_VIEWPORTS` = `1280x720`, `RECORD_SERVER_CMD` = the dev server command.
- **none** → skip capture. Report that the change has no CLI or web surface to record and stop. This is not an error; it signals `create-pr` to omit the Visual proof section.

This is a representative proof, not a claim-by-claim demonstration (that is `/validate-pr`'s job).

### 3. Write the proof manifest

Write `$PROOF_DIR/captured-proof.json` so `create-pr` can detect and embed the proof without re-capturing:

```bash
cat > "$PROOF_DIR/captured-proof.json" <<EOF
{
  "captured_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "surface": "cli" | "web" | "none",
  "mode": "single" | "bugfix-pair" | "bugfix-before-only",
  "assets": ["pr-demo.gif"] | ["before-bug.gif", "after-fix.gif"]
}
EOF
```

`assets` lists the exact filenames present in `$PROOF_DIR` that should be embedded. `create-pr` trusts this list.

### 4. Present the proof and get confirmation

Report to the user, for each captured asset:

- Its absolute path
- The surface and mode (single, bugfix-pair, etc.)
- For a pair: which is before and which is after

Then **pause and ask the user to open the asset and confirm the feature behaves correctly**. Do not assume success from a non-empty file. Specifically:

- For a GIF/SVG: give the path and ask the user to open it.
- For a PNG: give the path (and viewport) and ask the user to view it.
- For a bug-fix pair: ask the user to compare before vs after and confirm the defect is gone and nothing regressed.

Under automation (no interactive user; `$OUTCOME_YAML` set or a non-interactive flag), skip the pause and proceed: capture + write manifest, then emit the verdict. Interactive use must wait for an explicit human "looks good" before signaling readiness for `create-pr`.

If the user says the feature is wrong, incomplete, or regressed: do **not** proceed toward `create-pr`. Report what they observed and suggest revisiting `create-implementation`. Leave `captured-proof.json` in place only if the asset is still an accurate record; otherwise delete it so a later re-run re-captures.

## Re-runs

Re-running `/validate-implementation` re-captures (the recording skills overwrite), then rewrites `captured-proof.json`. To force a clean re-capture, delete `$PROOF_DIR/captured-proof.json` first.

## Failure Modes

| Mode | Response |
|------|----------|
| **No CLI or web surface** | Report `surface: none`; write no manifest; tell the user there is nothing to record and `create-pr` will omit proof |
| **asciinema / Playwright unavailable** | Report which tool is missing; do not write a manifest; tell the user proof cannot be captured until it is installed |
| **Recording is empty or wrong** | Re-record with `--overwrite` after fixing the command; only write the manifest once the take demonstrates the change |
| **Dev server won't start** | Report the URL/command; skip web capture; do not write a web manifest |
| **After capture fails (bug-fix pair)** | Keep the before asset; write `mode: bugfix-before-only` so `create-pr` embeds the before alone with a note |
| **User rejects the proof** | Do not signal readiness for `create-pr`; report the observed problem; route back to `create-implementation` |

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `validated` | Proof captured and (under automation) the take demonstrates the change |
| `no-surface` | Change has no CLI or web surface to record |
| `tools-missing` | Recording tools unavailable; proof could not be captured |
| `rejected` | Interactive user reviewed the proof and reported the feature is wrong |

## Example Usage

**Scenario 1: CLI feature, validate before PR**
```
/validate-implementation owner/myrepo 42
```
Diff touches `cmd/export.go`. Records `mytool export --format csv` via `/record-asciinema` into `/tmp/<owner>/<repo>/42/pr-demo.gif`, writes `captured-proof.json`, and asks the user to open the GIF and confirm. On "looks good", signals readiness for `/create-pr`.

**Scenario 2: Web UI feature**
```
/validate-implementation owner/myrepo 130
```
Diff touches `src/pages/dashboard.tsx`. Starts `npm run dev`, captures a desktop screenshot of `/dashboard` via `/record-playwright`, writes the manifest, presents the PNG path. The user confirms the layout, then runs `/create-pr`, which embeds the screenshot without re-capturing.

**Scenario 3: Bug fix with paired before/after**
```
/validate-implementation owner/myrepo 42
```
`/tmp/<owner>/<repo>/42/proof-manifest.txt` exists (written by `/reproduce-issue`), recording `surface: cli`. Replays that same command on the fixed code via `/record-asciinema` into `after-fix.gif`, writes `captured-proof.json` with `mode: bugfix-pair` and both filenames, and asks the user to compare before vs after.

**Scenario 4: Non-visual change**
```
/validate-implementation owner/myrepo 7
```
Diff is internal refactoring with no CLI or web surface. Reports `surface: none`, writes no manifest, tells the user there is nothing to record. `/create-pr` will omit the Visual proof section.

**Scenario 5: User catches a regression**
```
/validate-implementation owner/myrepo 42
```
GIF is captured, but on review the user notices the export omits the header row. The skill does **not** proceed to `create-pr`; it reports the observation and routes back to `create-implementation`. Deletes the stale `captured-proof.json` so the next run re-captures.

## Next Step

Once the user confirms the proof, run `/create-pr`. `create-pr` detects `$PROOF_DIR/captured-proof.json`, uploads the listed assets to the branch, and embeds them in a Visual proof section. It does not capture anything itself.

After the PR is open, run `/validate-pr` for claim-by-claim runtime validation with per-claim recordings, then `/verify-pr` for static code inspection.
