---
name: create-cli-design
description: Design the CLI interface for a feature during requirements creation, covering the command tree, commands, options, arguments, exit codes, output behavior, and example terminal sessions that demonstrate the intended experience. Use when a feature adds or changes CLI commands or options, when requirements mention a CLI, or when /create-requirements delegates its CLI surface.
argument-hint: "[requirements-doc or feature-brief]"
---

# Create CLI Design

Designs the command-line interface for a feature as a companion artifact to the requirements document, settling the commands, subcommands, options, arguments, exit codes, output behavior, help text, and example sessions before implementation begins.

For a CLI, the interface is the product: the user experiences the feature entirely through command syntax, help text, output, and errors.
This skill is the terminal counterpart of `/create-mockups`, which serves features with a graphical interface.

Without this step, CLI work starts with no shared picture of the command surface, so naming, flags, and output are improvised during implementation and reworked in review.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/requirements.md` (a draft is acceptable; this skill typically runs delegated from `/create-requirements`), or a feature brief provided in context or as a file path (`$1`)
- The repository's existing CLI conventions, when one exists: detect the framework and match its command naming, flag style, and output conventions instead of inventing new ones

## Steps

1. Detect revision mode: if `review-requirements.md` exists beside `requirements.md` with `verdict: changes-requested` and its findings concern `cli-design.md`, read the design and the findings together, amend the design minimally to resolve each finding (preserving content the findings did not challenge), and set frontmatter `status: in-review`. Skip the fresh drafting below.
2. Read the requirements (or brief) and apply any style rules in `.sdlc/context/conventions.md`.
3. Survey the existing CLI, if any: framework, command naming, flag style, output conventions, exit code usage. When the project has no CLI yet, fix the baseline conventions explicitly (e.g., GNU-style long options, kebab-case names, verb-first commands) and record them as the design principles.
4. Determine whether the feature has a CLI surface: does it add or change commands, options, or command output? If not, emit `verdict: skipped` and write no artifact.
5. Derive the command tree from the functional requirements: every user-facing FR maps to at least one command, subcommand, or option; one command per user goal; group related operations under noun subcommands.
6. For each command, specify: a synopsis, a description, positional arguments (name, required, description), options (short and long form, value type, default, env-var fallback), at least one usage example, and its specific error cases.
7. Define the cross-command surface: global options, environment variables, config file and precedence (flags over env over config over defaults), exit codes, the stdout/stderr split, machine-readable output (`--json`) when scripts must consume the output, and TTY-aware behavior (color, progress, and tables only on a TTY, honoring `NO_COLOR`).
8. Design user error protection: an actionable error message format (`error: <message>` plus a hint), confirmation prompts on destructive actions with `--yes`/`--force` to skip, and `--dry-run` where meaningful.
9. Write the help text for the root command and one representative subcommand.
10. Write example sessions as fenced `console` transcripts demonstrating the intended experience: a happy path, at least one error path, and (for destructive or interactive CLIs) a confirmation exchange plus a piping example. These transcripts are the artifact's centerpiece: a reader should be able to feel what using the CLI will be like before it exists.
11. Feed implied changes back: options or commands that surface a missing requirement go into `requirements.md` as open questions or new FRs, and unresolved interface decisions become open questions here.
12. Write the output to `.sdlc/features/N-<slug>/cli-design.md`, creating the directory if it does not exist, with frontmatter `status: draft`.

## Output Format

Use the template at `skills/sdlc/templates/features/cli-design.md` (copied to `.sdlc/templates/features/cli-design.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

The template's sections, in order: Design Principles, Command Tree, Commands (one subsection per command with synopsis, arguments, options, examples, errors), Global Options, Environment Variables, Configuration, Exit Codes, Output Behavior, Help Text, Error Messages, Interactive Behavior, Example Sessions, Requirements Traceability, Out of Scope, Open Questions.

Keep command and option names in running backticks so they are greppable against the implemented code later.

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | The CLI design was produced (or revised) with `status: draft`, ready for `/review-requirements` |
| `skipped` | The feature has no CLI surface; no artifact is written |

If the artifact could not be produced for any other reason, omit the file.
When invoked directly, list the artifact under `artifacts:` (`.sdlc/features/N-<slug>/cli-design.md`); omit the key when emitting `skipped` (no file was written).
When delegated from `/create-requirements`, do not emit a separate outcome: the delegating skill's emission lists both artifacts, and it emits last.

## Example Usage

**Scenario 1: Delegated from /create-requirements**
Requirements for a secrets tool define FRs for storing, retrieving, and rotating entries.
The skill designs `secrets set|get|rotate` with a global `--vault` option, exit codes for auth vs usage failures, and console transcripts of a happy `get` and a failed `rotate`.
`/create-requirements` records both `requirements.md` and `cli-design.md` and proceeds to `/review-requirements`.

**Scenario 2: First CLI in the project**
A library gains its first CLI.
The skill fixes the conventions explicitly (GNU long options, kebab-case, verb-first), designs the command tree from the FRs, and records the convention choice under Design Principles so later features extend it.

**Scenario 3: API-only feature**
The requirements describe a webhook receiver with no user-facing commands.
The skill writes nothing and emits `verdict: skipped` so the pipeline proceeds without a CLI review.

**Scenario 4: Revision after review**
`review-requirements.md` carries `verdict: changes-requested` with findings that `--output` means different things on two commands.
The skill renames one flag to `--format`, updates the affected transcript, and sets `status: in-review` instead of regenerating the artifact.

## Completion Checklist

Before handing off to review, confirm:

- [ ] Every user-facing functional requirement maps to at least one command, subcommand, or option in the traceability table
- [ ] Every command has a synopsis, options with types and defaults, and at least one example
- [ ] Exit codes, the stdout/stderr split, and machine-readable output are defined and consistent across commands
- [ ] Example sessions demonstrate a happy path and at least one error path

Self-check the draft against the CLI Design section of the [`review-requirements` checklist](../review-requirements/SKILL.md) and fix what you can, so review finds less to flag.

## Next Step

Run `/review-requirements`, which audits `requirements.md` and `cli-design.md` together when the design is present.
Once approved, continue with `/create-existing-solutions` to survey prior art.

## Useful Commands Reference

| Command | Description |
|---|---|
| `rg -n "argparse\|click\|typer\|cobra\|yargs\|commander" -g '*.{py,ts,js,go}' .` | Detect an existing CLI framework and its conventions |
