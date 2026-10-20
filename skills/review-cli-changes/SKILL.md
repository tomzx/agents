---
name: review-cli-changes
description: "Review a change to a command-line interface (new or changed commands, options, arguments, output, exit codes) for compatibility, consistency, and usability. Use when a PR, branch, or diff touches a CLI surface and the user asks whether the CLI change is safe, whether it breaks callers, whether flags or output are consistent, or wants a CLI-focused change review."
allowed-tools: Bash(git:*, gh:*, ghx:*, rg:*, ~/.agents/scripts/should-post-to-github:*, ~/.agents/scripts/review-progress:*), Read, Write, Glob, Grep
argument-hint: "<pr-number> [repository] | <diff-ref | worktree-dir>"
---

# Review CLI Changes

Reviews a change to a command-line interface and reports findings.
It answers one question: **is this CLI change safe to ship?**
Covering compatibility with the existing surface, consistency across commands, option and argument handling, output behavior, exit codes, error handling, configuration precedence, and shell integration.

It is the change-time counterpart to [`/review-cli-design`](../review-cli-design/SKILL.md): that skill reviews a `cli-design.md` artifact before implementation, this one reviews the implemented diff.
General code craft stays with [`/review-pr`](../review-pr/SKILL.md); criteria conformance stays with [`/verify-pr`](../verify-pr/SKILL.md).
This review is static: it does not build or run the CLI, so a claim that needs the CLI executed is `/verify-pr`'s to prove.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md` (PR Review Reports for report location and posting rules).
- Apply the shared evidence standard in [`../sdlc/references/evidence.md`](../sdlc/references/evidence.md).
  Static claims carry `L1 - Cited` or `L2 - Ruled out`; a decisive claim proven by a read-only command can reach `L3 - Executed`.
  Behavior observed by running the CLI is `/verify-pr`'s `L4 - Reproduced`.
- The change to review, in one of these forms:
  - a PR number plus repository (`/review-cli-changes 42 acme/cli`),
  - a git diff ref (for example `origin/main..HEAD`),
  - a worktree directory, or a changeset already in context.
- The CLI's existing surface at the base revision, so the before/after can be compared (read with `git show <base>:<path>`).
- `.sdlc/features/N-<slug>/cli-design.md` when one exists (optional; used for surface-vs-design checks).
- Grep access to the codebase for the CLI framework, its option definitions, and its test suite.

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `review-cli-changes`.

### Communication guidelines (outbound text)

Before composing any text posted or drafted on the user's behalf, apply [`communication-guidelines/SKILL.md`](../communication-guidelines/SKILL.md).

## Workflow

```
Resolve the change ($1: PR / diff-ref / worktree)
          |
          v
Read the base revision's CLI surface
(so before/after can be compared)
          |
          v
Split the diff: CLI-surface hunks
vs internal hunks
          |
          v
Apply the Review Checklist to each
surface change (compat, consistency,
options, output, exit codes, errors,
config, shell, tests, docs)
          |
          v
Write review-cli-changes.<sha>.md
(marker + verdict)
Post if should-post-to-github allows
          |
          v
Clean up worktree (only if owned)
```

## Steps

### 1. Resolve the change

If a PR number is given, fetch its metadata and diff:

```bash
PR_NUMBER="$1"; REPO="$2"
ghx pr view $PR_NUMBER --repo "$REPO" --comments --refresh
gh pr view $PR_NUMBER --repo "$REPO" --json headRefOid,headRefName,headRepository,baseRefName,files,title,body
gh pr diff $PR_NUMBER --repo "$REPO"
```

Extract `HEAD_COMMIT` (`headRefOid`), `SHORT_SHA` (the first 7 characters of `HEAD_COMMIT`), `HEAD_REPO`, `HEAD_BRANCH`, `BASE_BRANCH`, `PR_AUTHOR`, and `PR_STATE`.
Set `BASE_REF="origin/$BASE_BRANCH"` so the base surface can be read in step 2.
If `PR_STATE` is `CLOSED` or `MERGED`, note it and stop.

Create a worktree on the PR branch so the changed files can be read in full, not only as diff hunks.
If `$WORKTREE_DIR` is already set (for example by an orchestrator), use it directly and skip creation and cleanup.

```bash
_WORKTREE_OWNER=false
if [ -z "${WORKTREE_DIR:-}" ]; then
  git fetch "https://github.com/$HEAD_REPO.git" "$HEAD_BRANCH"
  WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
  mkdir -p /tmp/sdlc/$REPO
  git worktree add "$WORKTREE_DIR" FETCH_HEAD
  _WORKTREE_OWNER=true
fi
cd "$WORKTREE_DIR" || exit 1
```

If worktree creation fails, stop.

If a diff ref or worktree directory is given instead of a PR number, use it directly and derive the commit identity:

```bash
DIFF_REF="${1:-origin/main..HEAD}"
BASE_REF="${DIFF_REF%%..*}"   # the part before ..
[ -n "${WORKTREE_DIR:-}" ] && cd "$WORKTREE_DIR"
HEAD_COMMIT=$(git rev-parse HEAD)
SHORT_SHA="${HEAD_COMMIT:0:7}"
HEAD_TREE=$(git rev-parse "$HEAD_COMMIT^{tree}")
git diff --name-only "$DIFF_REF"
git diff "$DIFF_REF"
```

Define the report directory once: `PR_REVIEW_DIR="$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER"`, then `mkdir -p "$PR_REVIEW_DIR"`.
For a non-PR run, write to `/tmp/sdlc/${REPO:-review}/review-cli-changes.$SHORT_SHA.md` (create that directory first) and skip posting.
Set `HEAD_TREE=$(git rev-parse "$HEAD_COMMIT^{tree}")` when it is not already set.

### 2. Read the base revision's CLI surface

Compatibility only means something against the previous surface.
Before reading the diff, read how the CLI was defined at the base revision: the command tree, the option and argument declarations, the output and exit-code paths, and the environment/config keys.

```bash
# The CLI's entry point and option definitions at the base revision
git ls-tree -r --name-only "$BASE_REF" | grep -E '(cli|cmd|commands?)[/.]' || true
git show "$BASE_REF:path/to/cli.py"   # or the framework's command module
```

Detect the CLI framework so option and error conventions can be checked against it:

```bash
rg -n "argparse|click|typer|cyclopts|cobra|urfave|clap|yargs|commander|oclif" -g '*.{py,ts,js,go,rs}' .
```

### 3. Split the diff into CLI-surface and internal hunks

A CLI change can hide in an internal hunk (a default constant, a formatter, an exit-code map) and a surface-looking hunk can be internal plumbing.
Mark a hunk as CLI-surface when it changes any of:

- the command tree: commands, subcommands, aliases, grouping, or their help strings;
- option and argument declarations: names, short/long forms, types, defaults, required/optional, mutual exclusion, `--` handling;
- output: stdout/stderr routing, table/JSON/quiet formats, color and TTY handling, progress output;
- exit codes, or the mapping from an error condition to an exit code;
- user-facing error messages and usage text;
- environment variables, config file keys, or their precedence;
- the behavior of destructive or long-running commands (confirmation prompts, `--yes`, `--force`, `--dry-run`).

Only surface hunks feed the checklist; internal hunks stay with `/review-pr`.

### 4. Apply the Review Checklist to each surface change

Publish the in-progress marker before walking the checklist when this is a PR run (skip it for a bare diff ref), and remove it before returning (see `sdlc/references/shared.md`, In-progress marker):

```bash
~/.agents/scripts/review-progress start --step review-cli-changes --repo "$REPO" --pr "$PR_NUMBER" --sha "$HEAD_COMMIT"
```

Walk the categories below for every surface change.
Skip a category only when the diff cannot touch it, and say so.

### 5. Report findings

Give each finding:
- a severity: 🔴 MUST, 🟡 SHOULD, or 🟢 MAY;
- the category it maps to;
- an evidence level in the form `L<n> - <Name>` plus a `file:line`;
- a concrete, actionable fix.

Prefer compatibility findings first: a renamed flag or a changed output format breaks scripts that never appeared in the diff.

### 6. Write the report and post it

Start the file with the marker so an orchestrator can detect which commit was reviewed:

```markdown
<!-- {"step":"review-cli-changes","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"MARKER_VERDICT"} -->
```

Replace `HEAD_COMMIT`, `HEAD_TREE`, and `SHORT_SHA` with the resolved values (`SHORT_SHA` is the first 7 characters of `HEAD_COMMIT`).
`MARKER_VERDICT` is `pass` for `approved`, and `fail` for `changes-requested` or `rejected`.

Write the report to `$PR_REVIEW_DIR/review-cli-changes.$SHORT_SHA.md` and point the stable symlink at it:

```bash
ln -sf "review-cli-changes.$SHORT_SHA.md" "$PR_REVIEW_DIR/review-cli-changes.report.md"
```

Posting as a PR comment is decided by `should-post-to-github`.
Run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`; if it exits 1, skip posting (the report is saved locally).
If it exits 0, set `REPORT` to the report file's contents and `FOOTER` to the attribution footer, then post with the **Posting a review report** recipe in `skills/sdlc/references/shared.md` (`STEP="review-cli-changes"`).

### 7. Clean up

For a PR run, remove the in-progress marker:

```bash
~/.agents/scripts/review-progress stop --step review-cli-changes --repo "$REPO" --pr "$PR_NUMBER"
```

If this skill created a worktree (no `$WORKTREE_DIR` was provided), remove it.

## Review Checklist

### Breaking Compatibility

- Is any command, subcommand, or alias removed or renamed, with a deprecation path for callers?
- Is any option renamed, removed, or given a different short form, or does an option that used to take a value now act as a flag (or the reverse)?
- Has a default changed in a way a caller would observe (a default output format, a default target, a default timeout)?
- Has the meaning of an option changed on one command but not on its siblings (a name reused for a different purpose)?
- Has machine-readable output changed structure or field names, breaking scripts that parse it?
- Have exit codes changed for a condition that already had a code?
- Are removed environment variables or config keys still documented, or is their removal called out?

### Command Surface

- Are new command and subcommand names verbs, and consistent in form with the existing tree?
- Is each new command at the same granularity as its siblings, doing one job?
- Does every new command appear in `--help`, in the parent's command list, and in the docs?
- Is the command grouped where a user would look for it, rather than under an implementation module name?

### Options & Arguments

- Does every new option have a long form, and a short form only when a short form is free and conventional?
- Are required versus optional arguments correct, with sensible defaults for the common case?
- Is boolean negation provided where an option needs it (`--no-color` for `--color`)?
- Are options mutually exclusive or dependent, and are those constraints enforced with a clear error rather than silently ignored?
- Are repeated options and values handled the way the framework and sibling commands handle them?
- Is `--` honored to stop option parsing before positional arguments?
- Do option names and semantics match the same options on other commands?

### Output Behavior

- Is data written to stdout and diagnostics to stderr, so piping output is safe?
- Is a stable machine-readable format offered (`--json`) wherever a script would consume the result, and is it stable across runs?
- Is color disabled on a non-TTY and when `NO_COLOR` is set?
- Are progress indicators, spinners, and tables suppressed when stdout is not a TTY?
- Is quiet and verbose behavior defined, and does `--quiet` suppress only diagnostics, not the requested data?
- Is unbounded output streamed or paginated rather than buffered whole?

### Exit Codes

- Is `0` reserved for success and a distinct non-zero class used for usage errors, not-found, and operational failure?
- Is each code consistent with the same condition on other commands?
- Is the documented exit code the one the code actually returns on each error path?
- Is a usage error distinguished from a runtime error, so callers can tell them apart?

### Error Handling & Destructive Actions

- Is the error message actionable, in the form `error: <message>` plus a hint to fix it?
- Does a usage error print usage to stderr and exit non-zero, rather than printing help to stdout and exiting `0`?
- Does every destructive or irreversible command prompt for confirmation, with `--yes` or `--force` to skip it?
- Is `--dry-run` offered where an operation is hard to reverse?
- Is `SIGINT` handled so an interrupted command stops cleanly and reports what happened (including partial work)?

### Configuration & Environment

- Is the precedence flags > environment > config file > default applied consistently and documented?
- Does a new environment variable or config key appear in `--help`, the docs, and the project's example config?
- Is a secret kept out of process arguments (where `ps` can read it) and out of logs?
- Is a config file location overridable, and is its absence handled without an error when defaults suffice?

### Shell Integration

- Do commands behave under piping and redirection (no TTY-only assumptions, no `SIGPIPE` stack trace on `| head`)?
- Are paths, line endings, and separators handled cross-platform where the CLI is cross-platform?
- Are completion scripts updated when the command tree changes, if the project ships them?
- Do the `--help` examples run as written against the current commands and flags?

### Tests & Documentation

- Are there tests for the new flag parsing (each new option and its error cases), not only for the command's happy path?
- Is there a test for each changed exit code and each new error message?
- Is there an error-path or confirmation-path test, not only the happy path?
- Are `--help` text, README usage, man pages, and the changelog updated for the changed surface?

### Convention Fit

- Does the change follow the project's existing CLI framework, naming, and flag style?
- Is a deviation from house conventions deliberate and recorded, rather than incidental?
- Does the change avoid adding a second flag style or a second output format alongside an existing one?

## Output Format

```markdown
<!-- {"step":"review-cli-changes","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"MARKER_VERDICT"} -->
# CLI Change Review: #<PR_NUMBER> <title> (or <diff-ref>)

🔴 / 🟢 <Overall assessment in one sentence.>

Reviewed commit: `SHORT_SHA`
Base: `<BASE_BRANCH or base ref>`

## Summary

<What the CLI change does, and the headline compatibility or usability risk.>

## Surface changes

| Area / entry point | Before | After | Breaking? | Consumer affected |
|---|---|---|---|---|
| `--timeout` (`src/cli.py:40`) | 10s | 30s | Conditional | scripts relying on a fast failure |
| `set --output` (`src/cli.py:112`) | file path | format name | Yes | scripts parsing `--output` |

## Findings

### 🔴 MUST / Breaking Compatibility / <title>

<What breaks, the concrete fix, and the evidence pointer.>

`Evidence: L2 - Ruled out` (`src/cli.py:40`; base `<BASE_REF>:src/cli.py:38`).

### 🟡 SHOULD / <Category> / <title>

<...>

## Checklist

| Category | Status | Notes |
|---|---|---|
| Breaking Compatibility | 🔴 / 🟡 / 🟢 | <terse note> |
| Command Surface | 🟢 | <terse note> |
| Options & Arguments | 🟢 | <terse note> |
| Output Behavior | 🟢 | <terse note> |
| Exit Codes | 🟢 | <terse note> |
| Error Handling & Destructive Actions | 🟢 | <terse note> |
| Configuration & Environment | 🟢 | <terse note> |
| Shell Integration | 🟢 | <terse note> |
| Tests & Documentation | 🟢 | <terse note> |
| Convention Fit | 🟢 | <terse note> |

## Outcome

<One sentence: what must change before the CLI change ships.>
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When | Marker verdict |
|---|---|---|
| `approved` | No blocking findings; the CLI change passes review | `pass` |
| `changes-requested` | Findings the author must address before it passes | `fail` |
| `rejected` | Fundamental flaw requiring rework or stopping | `fail` |

In the same emission, list the findings file under `artifacts:` (the report path written in step 6).

## Failure Modes

| Mode | Response |
|---|---|
| **Worktree creation fails** | Stop |
| **PR is CLOSED or MERGED** | Note it and stop |
| **No CLI surface in the diff** | Say so plainly and stop; the change belongs to `/review-pr` |
| **Base revision unavailable** | Review the surface on its own and mark compatibility findings `unproven`, naming the base comparison that was missing |
| **Diff is very large (>1000 lines)** | Review every surface hunk exhaustively, sample internal hunks, and say which areas were sampled |
| **`ghx` unavailable** | Fall back to `gh pr view` for PR context |

## Example Usage

**Scenario 1: Renamed flag**
```
/review-cli-changes 42 acme/cli
```
The diff renames `--format` to `--output` on `export` with no alias and no deprecation note.
Report a 🔴 MUST under Breaking Compatibility: scripts calling `--format` now fail with an unknown-option error.

**Scenario 2: New flag, wrong stream**
```
/review-cli-changes origin/main..HEAD
```
A new `--json` flag prints the payload to stderr.
Report a 🟡 SHOULD under Output Behavior: data belongs on stdout so it can be piped.

**Scenario 3: Destructive command with no guard**
```
/review-cli-changes 88 acme/cli
```
`secrets delete` gains a `--all` option with no confirmation and no `--dry-run`.
Report a 🔴 MUST under Error Handling & Destructive Actions.

**Scenario 4: Clean additive change**
```
/review-cli-changes 55 acme/cli
```
The diff adds a `--profile` option with a sensible default, a long form, help text, and parsing tests.
Report 🟢 approved with no findings.

## Related Skills

| Skill | Relationship |
|---|---|
| `review-cli-design` | Reviews the `cli-design.md` artifact before implementation; this skill reviews the implemented CLI change |
| `review-pr` | General code-craft review; this skill is the CLI-surface specialization and defers internal hunks to it |
| `verify-pr` | Proves criteria by building and running the CLI; this review is static |
| `audit-usability` | Repo-wide CLI/API/UI usability audit; this skill is diff-focused |
