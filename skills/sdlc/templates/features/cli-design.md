---
title: "<Feature Name>"
status: draft
---

# CLI Design: <Feature Name>

## Design Principles

- <Convention baseline, e.g., GNU-style long options, kebab-case command names, verb-first commands, or "extends the existing `<binary>` CLI conventions">

## Command Tree

```
<binary>
├── <command>          <one-line purpose>
│   └── <subcommand>   <one-line purpose>
└── <command>          <one-line purpose>
```

## Commands

### `<binary> <command>`

**Description:** <what it does and which requirements it serves>

**Synopsis:**

```
<binary> <command> [options] <arg> [...]
```

**Positional arguments:**

| Argument | Required | Description |
|---|---|---|
| <name> | Yes / No | <description> |

**Options:**

| Short | Long | Value | Default | Description |
|---|---|---|---|---|
| -h | --help | | | Show help and exit |

**Examples:**

```bash
<binary> <command> --flag value <arg>
```

**Errors:** <command-specific error conditions and their messages>

### <Next command>

...

## Global Options

| Short | Long | Value | Default | Description |
|---|---|---|---|---|
| -h | --help | | | Show help and exit |

## Environment Variables

| Variable | Used by | Default | Description |
|---|---|---|---|---|
| <NAME> | <command or all> | <value> | <what it configures> |

## Configuration

- <Config file path and format, when the CLI reads one>
- Precedence: CLI flags > environment variables > config file > defaults

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Runtime failure |
| 2 | Usage error |

## Output Behavior

- **stdout:** <the data or results; what a pipe consumer receives>
- **stderr:** <diagnostics, progress, and errors>
- **Machine-readable:** <the `--json` output shape, when scripts must consume the output>
- **TTY behavior:** <color, progress bars, and tables only when stdout is a TTY; honors `NO_COLOR`>

## Help Text

```
<the `--help` output for the root command>
```

## Error Messages

- Format: `error: <message>` followed by an actionable hint when one exists
- <Representative examples>

## Interactive Behavior

- **Prompts:** <when the CLI prompts for missing input instead of failing>
- **Destructive actions:** <confirmation prompt; `--yes` / `--force` to skip>
- **Dry run:** <`--dry-run` behavior, when meaningful>

## Example Sessions

Transcripts of the intended experience.
A reader should understand what using the CLI feels like from these alone.
Cover a happy path, at least one error path, and (when relevant) a confirmation exchange and a piping example.

### <Session name, e.g., first run>

```console
$ <binary> <command> <args>
<output>
```

### <Session name, e.g., error path>

```console
$ <binary> <command> <bad args>
error: <message>
hint: <how to fix it>
$ echo $?
2
```

## Requirements Traceability

| Requirement | Command(s) / Option(s) | Notes |
|---|---|---|
| FR-1 | `<binary> <command>` | <how the command satisfies the requirement> |

## Out of Scope

- <What is explicitly not designed here and why>

## Open Questions

1. <Question about the interface that needs an answer before implementation>
