---
name: initialize-sdlc-directory
description: Bootstrap the .sdlc/ directory structure in a project, creating subdirectories and populating templates.
argument-hint: "[project-root]"
---

# Initialize SDLC Directory

Creates the `.sdlc/` directory structure in the project root (or `$1` if provided) and populates it with default templates.
Already-existing files are never overwritten — this is safe to run on a project that has partially adopted the structure.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- Write access to the project root
- The canonical templates at `../sdlc/templates/` relative to this skill file (i.e. `skills/sdlc/templates/`)

## Steps

1. Determine the project root: use `$1` if provided, otherwise use the current working directory.

2. **Resolve the SDLC write location** per `sdlc/references/shared.md`: default `<project-root>/.sdlc/`; if it cannot be created and `SDLC_DIR` is set, use `$SDLC_DIR/{owner}/{repository}/.sdlc/`; mirror created files to the external store when set. Record which location was used in the report.

3. For each directory below, create it (under the resolved write location) if it does not already exist:
   ```
   .sdlc/
   .sdlc/context/
   .sdlc/features/
   .sdlc/templates/
   .sdlc/templates/features/
   .sdlc/templates/knowledge/
   .sdlc/knowledge/
   .sdlc/knowledge/assumptions/
   .sdlc/knowledge/decisions/
   .sdlc/knowledge/learnings/
   ```

4. Create `.sdlc/.gitignore` — **only if it does not already exist** — with the following content to keep local-only workflow state out of version control:
   ```gitignore
   # Local-only workflow state — do not commit
   # Orchestrator run state
   state.yml
   # Per-feature progress tracking and session logs
   features/*/progress.md
   ```
   `state.yml` (the orchestrator run state) and each feature's `progress.md` (progress tracking + session log) are regenerated per machine and per run, so they must never be committed or included in PRs. The `features/*/progress.md` pattern ignores only the per-feature files, not the template at `templates/features/progress.md`. Only the repo's `.sdlc/.gitignore` is meaningful; do not create a `.gitignore` under the `SDLC_DIR` mirror.

5. For each canonical template file (read from `../sdlc/templates/` relative to this skill), copy it to the corresponding path under `.sdlc/templates/` — **only if the destination file does not already exist**:

   | Canonical source | Destination |
   |---|---|
   | `../sdlc/templates/features/needs-assessment.md` | `.sdlc/templates/features/needs-assessment.md` |
   | `../sdlc/templates/features/requirements.md` | `.sdlc/templates/features/requirements.md` |
   | `../sdlc/templates/features/existing-solutions.md` | `.sdlc/templates/features/existing-solutions.md` |
   | `../sdlc/templates/features/codebase-analysis.md` | `.sdlc/templates/features/codebase-analysis.md` |
   | `../sdlc/templates/features/feasibility.md` | `.sdlc/templates/features/feasibility.md` |
   | `../sdlc/templates/features/specification.md` | `.sdlc/templates/features/specification.md` |
   | `../sdlc/templates/features/mockups.md` | `.sdlc/templates/features/mockups.md` |
   | `../sdlc/templates/features/telemetry.md` | `.sdlc/templates/features/telemetry.md` |
   | `../sdlc/templates/features/observability.md` | `.sdlc/templates/features/observability.md` |
   | `../sdlc/templates/features/plan.md` | `.sdlc/templates/features/plan.md` |
   | `../sdlc/templates/features/task.md` | `.sdlc/templates/features/task.md` |
   | `../sdlc/templates/features/tests.md` | `.sdlc/templates/features/tests.md` |
   | `../sdlc/templates/features/documentation.md` | `.sdlc/templates/features/documentation.md` |
   | `../sdlc/templates/knowledge/assumption.md` | `.sdlc/templates/knowledge/assumption.md` |
   | `../sdlc/templates/knowledge/decision.md` | `.sdlc/templates/knowledge/decision.md` |
   | `../sdlc/templates/knowledge/learning.md` | `.sdlc/templates/knowledge/learning.md` |

6. For each context file below, create it under `.sdlc/context/` — **only if the destination file does not already exist** — using the corresponding canonical template (from `../sdlc/templates/context/`) as starting content:
   - `project-overview.md`
   - `goals.md`
   - `architecture.md`
   - `conventions.md`
   - `vocabulary.md`

7. Report what was created and what was skipped (already existed). When `SDLC_DIR` is set, the report notes whether each path was written to the repo, the mirror, or both.

## Output Format

```
## SDLC directory initialized

### Created
- .sdlc/.gitignore
- .sdlc/context/project-overview.md
- .sdlc/templates/features/requirements.md
...

### Skipped (already exist)
- .sdlc/context/conventions.md
...

Next steps:
1. Fill in `.sdlc/context/project-overview.md` with your project's goals, stakeholders, and scope.
2. Fill in `.sdlc/context/goals.md` with your objectives, key results, and KPIs (or run `/create-goals`).
3. Fill in `.sdlc/context/architecture.md` with the system topology.
4. Fill in `.sdlc/context/conventions.md` with naming, structure, and coding conventions.
5. Fill in `.sdlc/context/vocabulary.md` with domain terms, technical terms, and abbreviations used across the project.
6. Edit templates under `.sdlc/templates/features/` and `.sdlc/templates/knowledge/` to match your project's preferred artifact formats.
   Run `/update-sdlc-templates` later to pull in upstream improvements while preserving your edits.
```

## Example Usage

**Scenario 1: New project**
```
/initialize-sdlc-directory
```
Creates all directories and templates from scratch. All context files are created as stubs.

**Scenario 2: Existing project with partial structure**
```
/initialize-sdlc-directory /path/to/project
```
Creates only the missing directories and files. Existing files are untouched.
