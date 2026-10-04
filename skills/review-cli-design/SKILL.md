---
name: review-cli-design
description: Review a CLI design for command-surface completeness, cross-command consistency, usability, error handling, output behavior, and convention fit.
---

# Review CLI Design

Audits a `cli-design.md` artifact and reports findings across seven categories: requirements traceability, command surface, cross-command consistency, usability, error handling, output behavior, and convention fit.

This is the detailed review of the CLI interface design itself.
`/review-requirements` reviews `cli-design.md` alongside `requirements.md` at the requirements-alignment level and remains the gate in the SDLC pipeline.
Run this skill for a standalone or second-pass audit of the interface when the design is the primary artifact (a hand-authored design, or a re-audit after implementation feedback).

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/cli-design.md`, or a CLI design provided in context or as a file path
- `.sdlc/features/N-<slug>/requirements.md` (optional, required for the traceability checks)
- The template at `skills/sdlc/templates/features/cli-design.md` (to check section completeness)
- The repository's existing CLI framework and conventions, when one exists

## Steps

1. Read the CLI design from `.sdlc/features/N-<slug>/cli-design.md` if present, otherwise from context or as a file path. Read `requirements.md` too when available.
2. Identify issues in each of the applicable categories below.
3. Report findings using the output format. Omit any category that has no findings.
4. Write the findings to `.sdlc/features/N-<slug>/review-cli-design.md` with frontmatter `artifact: cli-design`, `verdict` (`approved` if there are no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, and the findings as the body, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body.

## Review Checklist

### Requirements Traceability
- Does every user-facing functional requirement map to at least one command, subcommand, or option in the traceability table?
- Does every command in the design trace back to a requirement or stated goal, with no unexplained surface?
- Does any interface choice conflict with a requirement or constraint?

### Command Surface
- Is the command tree discoverable and grouped by user goal rather than by implementation module?
- Are command and subcommand names verbs, and consistent in form across the tree?
- Does each command have a synopsis, positional arguments (name, required, description), and options (short and long form, type, default, env-var fallback)?
- Is each command at a consistent granularity, with no single command doing several unrelated jobs?

### Cross-Command Consistency
- Do options with the same name carry the same meaning on every command that has them?
- Are exit codes used consistently, with one meaning per code across the whole surface?
- Are global options, environment variables, and config precedence stated once and honored everywhere?
- Is machine-readable output (`--json`) available wherever scripts would need to consume it, and consistent in structure?

### Usability
- Are help text and usage examples present for the root command and for representative subcommands?
- Are defaults sensible enough that the common case needs no flags?
- Is the stdout/stderr split correct (data on stdout, diagnostics on stderr)?
- Is TTY-aware behavior defined (color, progress, and tables only on a TTY, honoring `NO_COLOR`)?
- Are long-running or destructive operations discoverable and safely interruptible?

### Error Handling
- Is the error message format actionable (`error: <message>` plus a hint)?
- Does every documented error case have a defined exit code and message?
- Are destructive actions protected by a confirmation prompt, with `--yes`/`--force` to skip it?
- Is `--dry-run` offered where an operation is hard to reverse?

### Output Behavior
- Are example sessions present, covering a happy path, at least one error path, and, where relevant, a confirmation exchange and a piping example?
- Do the transcripts faithfully reflect the documented commands, flags, and output?
- Is output that is meant to be parsed stable and script-friendly?

### Convention Fit
- Does the design follow the project's existing CLI framework, naming, and flag style, or state and justify its baseline conventions for a first CLI?
- Are deviations from house conventions deliberate and recorded under Design Principles?

## Output Format

```markdown
## Requirements Traceability

<Findings or "No issues found.">

## Command Surface

<Findings or "No issues found.">

## Cross-Command Consistency

<Findings or "No issues found.">

## Usability

<Findings or "No issues found.">

## Error Handling

<Findings or "No issues found.">

## Output Behavior

<Findings or "No issues found.">

## Convention Fit

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

In the same emission, list the findings file under `artifacts:` (`.sdlc/features/N-<slug>/review-cli-design.md`, plus `cli-design.md` when you amended the design to resolve a finding).

## Example Usage

**Scenario 1: Inconsistent flag meaning**
`--output` selects a file on `set` but a format on `get`.
Report under Cross-Command Consistency; rename one flag (for example `--format`).

**Scenario 2: Unprotected destructive command**
`secrets delete` runs immediately with no confirmation and no `--yes` skip.
Report under Error Handling.

**Scenario 3: No error transcript**
The example sessions show only the happy path.
Report under Output Behavior; require at least one error session.

**Scenario 4: Untraceable option**
A global `--profile` option appears in the design but maps to no requirement or stated goal.
Report under Requirements Traceability.

## Next Step

Once the findings verdict is `approved`, the CLI design is ready to drive implementation (or `/create-existing-solutions` when prior-art survey has not run yet).

## Useful Commands Reference

| Command | Description |
|---|---|
| `rg -n "argparse\|click\|typer\|cobra\|yargs\|commander" -g '*.{py,ts,js,go}' .` | Detect an existing CLI framework and its conventions |
