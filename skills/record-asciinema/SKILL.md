---
name: record-asciinema
description: Record a terminal/CLI demonstration with asciinema, render it to an embeddable GIF (or SVG), and return the asset path. Reusable recording primitive used by validate-pr and create-pr.
allowed-tools: Bash(asciinema:*, agg:*, asciicast2gif:*, svg-term:*, scripts/get-env:*), Read, Write, Glob
argument-hint: "[<slug>] [-- <command...>]"
---

# Record CLI Demo (asciinema)

Record a terminal demonstration with `asciinema`, render the `.cast` to a GIF (or SVG fallback) so it can be embedded inline in a GitHub PR or comment, and return the path to the rendered asset.

This is the recording primitive for CLI changes. For web UI changes, use `/record-playwright`.

## Prerequisites

- `asciinema` installed
- One of `agg`, `asciicast2gif`, or `svg-term-cli` installed (for rendering). `agg` is preferred (fastest, best quality).
- If none are installed, the skill still returns the raw `.cast` with playback instructions.

## Inputs

The skill is driven by the following inputs. Set them from context, or accept them from the command line.

| Input | Meaning | Default |
|-------|---------|---------|
| `$RECORD_SLUG` (`$1`) | Filename slug for the recording, e.g. `verbose-flag` | `demo` |
| `$RECORD_TITLE` | Human-readable title shown in the asciinema player | `CLI demo` |
| `$RECORD_DIR` | Output directory for `.cast` / `.gif` | `/tmp/record-asciinema` |
| `$RECORD_COMMAND` (`$2..`) | A single command to record non-interactively (single-shot demos) | *(none; interactive mode)* |

If `$RECORD_COMMAND` is provided, the demo runs that one command and exits. If not, the skill drops into an interactive asciinema shell where the agent types the relevant commands and exits.

## Workflow

```
Inputs resolved (slug, title, dir, command?)
          |
          v
asciinema available?
   /            \
 Yes             No
  |               |
  v               v
Record .cast   Return nothing,
               caller falls back to text
  |
  v
Render to GIF (agg -> asciicast2gif -> svg-term)
   |
   v
Return rendered asset path (+ raw .cast)
```

## Steps

### 1. Resolve inputs

```bash
RECORD_SLUG="${1:-demo}"
RECORD_DIR="${RECORD_DIR:-/tmp/record-asciinema}"
RECORD_TITLE="${RECORD_TITLE:-CLI demo}"
mkdir -p "$RECORD_DIR"
```

If `$2` onward forms a command (i.e. the caller passed `-- <command...>` or a bare command string), capture it into `RECORD_COMMAND`.

### 2. Verify asciinema is available

```bash
command -v asciinema >/dev/null 2>&1 || { echo "asciinema not installed"; exit 0; }
```

If absent, stop and signal the caller to fall back to capturing stdout/stderr as text. Do not error out.

### 3. Record the demonstration

For a single-shot command:

```bash
asciinema rec "$RECORD_DIR/${RECORD_SLUG}.cast" \
  --overwrite \
  --command="$RECORD_COMMAND" \
  --title="$RECORD_TITLE"
```

For a multi-step interactive demo:

```bash
asciinema rec "$RECORD_DIR/${RECORD_SLUG}.cast" \
  --overwrite \
  --title="$RECORD_TITLE"
# Run the relevant CLI commands inside the recorder.
# Type `exit` or Ctrl-D when done.
```

### 4. Verify the recording matches the intent

```bash
asciinema cat "$RECORD_DIR/${RECORD_SLUG}.cast"
```

Confirm the captured output demonstrates the claim. If it is empty or wrong, re-record with `--overwrite`.

### 5. Render to an embeddable asset

Try renderers in quality order. Stop at the first that succeeds.

```bash
CAST="$RECORD_DIR/${RECORD_SLUG}.cast"

if command -v agg >/dev/null 2>&1; then
  agg "$CAST" "$RECORD_DIR/${RECORD_SLUG}.gif"

elif command -v asciicast2gif >/dev/null 2>&1; then
  asciicast2gif "$CAST" "$RECORD_DIR/${RECORD_SLUG}.gif"

elif command -v svg-term >/dev/null 2>&1; then
  svg-term --in "$CAST" --out "$RECORD_DIR/${RECORD_SLUG}.svg" --window
fi
```

### 6. Return the asset

Report the path to the rendered asset so the caller can upload and embed it:

- GIF: `$RECORD_DIR/${RECORD_SLUG}.gif`
- SVG: `$RECORD_DIR/${RECORD_SLUG}.svg`
- Neither renderer available: `$RECORD_DIR/${RECORD_SLUG}.cast` (raw), with a note to upload the `.cast` and link the asciinema player.

## Failure Modes

| Mode | Response |
|------|----------|
| **asciinema not installed** | Stop cleanly; signal caller to capture stdout/stderr as text |
| **Recording is empty/wrong** | Re-record with `--overwrite` after fixing the command |
| **No renderer installed** | Return the raw `.cast` path; caller uploads it with playback instructions |
| **Render fails** | Keep the `.cast`, report the renderer error, return the `.cast` path |

## Example Usage

**Scenario 1: Single-shot demo (called by validate-pr)**
```
/record-asciinema verbose-flag -- my-tool --verbose
```
Records `my-tool --verbose`, renders `verbose-flag.gif`, returns its path for upload to the PR branch.

**Scenario 2: Interactive multi-step demo**
```
/record-asciinema export-flow
```
Opens an asciinema shell; the agent runs `my-tool export --format csv` then `cat output.csv`, exits, and renders `export-flow.gif`.

**Scenario 3: Renderer missing**
```
/record-asciinema help-text -- my-tool --help
```
`agg`/`asciicast2gif`/`svg-term` all absent. Returns `help-text.cast`; the caller uploads the raw cast and links `https://asciinema.org` playback.
