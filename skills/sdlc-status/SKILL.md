---
name: sdlc-status
description: Display a progress dashboard for SDLC features from .sdlc/ directory data, without modifying any artifacts. Use when the user says /sdlc-status, wants a status report, wants to see feature progress, or asks "where am I" in the SDLC pipeline.
argument-hint: "[feature-id | .sdlc-path]"
---

# SDLC Status Report

Produces a progress dashboard for all SDLC features in a repository.
This is a read-only operation that does not modify any artifacts.

## When to Use

- The user wants to see current progress on one or all features.
- The user wants to pick up where they left off and needs a summary.
- The user asks "where am I?" or "what's the status?" about the SDLC pipeline.
- The `/sdlc` orchestrator enters at the `status` entry point.

## Inputs

- `$1` (optional): A specific feature directory name (e.g., `FEAT-0001-notification-system`) or path to `.sdlc/`.
- If not provided, defaults to `.sdlc/` in the current repository.

## Outputs

A formatted status report displayed to the user, containing:

1. A summary table of all features (if multiple exist).
2. Per-feature detail: pipeline progress, task status, blockers, session log.
3. A prompt asking which feature to work on and at which phase to resume.

## Steps

1. Locate the `.sdlc/` directory. Use `$1` if it specifies a path, otherwise use `.sdlc/` in the current repository root.
2. Scan `.sdlc/features/` for all feature directories (excluding `templates/`).
3. If `$1` specifies a feature ID (e.g., `FEAT-0001`), filter to that feature only.
4. For each feature, read `progress.md` if it exists. Otherwise scan the directory for artifacts and task files.
5. Read all task files in `.sdlc/features/FEAT-NNNN-<slug>/tasks/` and collect their frontmatter.
6. Render the status report.

### Preferred: Use the bundled script

`scripts/sdlc-status.py` renders a self-contained HTML dashboard (one tabbed panel per feature, with pipeline status, task progress, blockers, and session log) directly from the `.sdlc/` directory. Prefer it over hand-building a report, especially when the user asks for HTML.

```bash
# The script carries PEP 723 inline metadata, so uv provisions PyYAML on the fly.
uv run <skill_dir>/scripts/sdlc-status.py <path-to-.sdlc> -o status-report.html
# Omit -o (or pass "-") to write the HTML to stdout instead of a file.
```

The script reads each feature's `progress.md` frontmatter and sections. Features without a `progress.md` render with limited detail, so for the richest dashboard ensure `progress.md` exists. If the script cannot run (no uv available) or the user wants a plain-text summary, fall back to the manual steps below.

### Manual text-based report

If the script is unavailable or the user prefers text, produce the report manually:

For each feature, output:

```markdown
## <Feature Name> -- <current_phase>

**Pipeline:** <furthest completed phase> -> <current phase> (<status>)
**Tasks:** <done> / <total> (<percentage>%)
**Blockers:** <current blocker, or "None">
**Last session:** <date> -- <summary>
**Re-enter at:** <phase name>

### Task Status

| ID | Title | Size | Status | Blocker |
|---|---|---|---|---|
| 0001 | ... | S | done | -- |
| 0002 | ... | M | in-progress | -- |
| 0003 | ... | S | blocked | Waiting on API access |

**Critical path progress:** 0001 done -> 0002 in-progress -> 0005 pending -> 0008 pending
```

If multiple features are found, show a brief summary table first:

```markdown
| Feature | Phase | Tasks | Last Updated |
|---|---|---|---|
| FEAT-0001 | implementation | 3/7 | 2025-06-03 |
| FEAT-0002 | requirements | 0/3 | 2025-06-01 |
```

7. After the report, ask the user which feature to work on and at which phase to resume.

## Progress Tracking Reference

The `progress.md` file in each feature directory is the single source of truth for feature status. It contains:

- **Frontmatter:** `issue`, `title`, `current_phase`, `re_entry_point`, `last_updated`.
- **Summary section:** One paragraph status of the feature.
- **Pipeline Status table:** Each SDLC phase and its status.
- **Task Progress table:** ID, title, size, status, completed date, blocker.
- **Current Blocker section:** Active blocker description, or "None".
- **Session Log table:** Date, summary, next step.

### Task status values

| Status | Meaning |
|---|---|
| `draft` | Initial state, created by decomposition |
| `pending` | Reviewed and approved, ready to start |
| `in-progress` | Actively being worked on |
| `blocked` | Cannot proceed, waiting on external dependency |
| `done` | All acceptance criteria met, tests passing |
| `cancelled` | No longer needed (superseded or descoped) |

### Pipeline status values

`--` (not started), `done`, `skipped`, `blocked`, or the current status from the artifact frontmatter (`draft`, `in-review`, `approved`).

## Automatic Resume

When invoked without arguments and `.sdlc/features/` contains in-progress features:

1. Scan `.sdlc/features/*/progress.md` for features where `current_phase` is not `complete` and `re_entry_point` is set.
2. If exactly one in-progress feature is found, present its status report and ask: "Resume at `<re_entry_point>` for `<feature>`?"
3. If multiple in-progress features are found, show the summary table and ask which one to resume.
4. If no in-progress features are found, list all features with their status.

## Relationship to Other Skills

- **`sdlc`**: The orchestrator invokes this skill at the `status` entry point and for automatic resume detection.
- **`create-tasks-decomposition`**: Initializes `progress.md` when creating tasks.
- **`review-tasks-decomposition`**: Populates the Task Progress table in `progress.md`.
- **`create-implementation`**: Updates task status and `progress.md` as work proceeds.
