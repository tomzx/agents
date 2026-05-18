---
name: initialize-sdlc-directory
description: Bootstrap the .sdlc/ directory structure in a project, creating subdirectories and populating templates.
argument-hint: "[project-root]"
---

# Initialize SDLC Directory

Creates the `.sdlc/` directory structure in the project root (or `$1` if provided) and populates it with default templates.
Already-existing files are never overwritten — this is safe to run on a project that has partially adopted the structure.

## Prerequisites

- Write access to the project root
- The canonical templates at `../sdlc/templates/` relative to this skill file (i.e. `skills/sdlc/templates/`)

## Steps

1. Determine the project root: use `$1` if provided, otherwise use the current working directory.

2. For each directory below, create it if it does not already exist:
   ```
   .sdlc/
   .sdlc/context/
   .sdlc/features/
   .sdlc/templates/
   .sdlc/templates/context/
   .sdlc/templates/features/
   .sdlc/templates/knowledge/
   .sdlc/knowledge/
   .sdlc/knowledge/assumptions/
   .sdlc/knowledge/decisions/
   .sdlc/knowledge/learnings/
   ```

3. For each canonical template file (read from `../sdlc/templates/` relative to this skill), copy it to the corresponding path under `.sdlc/templates/` — **only if the destination file does not already exist**:

   | Canonical source | Destination |
   |---|---|
   | `../sdlc/templates/context/project-overview.md` | `.sdlc/templates/context/project-overview.md` |
   | `../sdlc/templates/context/architecture.md` | `.sdlc/templates/context/architecture.md` |
   | `../sdlc/templates/context/conventions.md` | `.sdlc/templates/context/conventions.md` |
   | `../sdlc/templates/features/requirements.md` | `.sdlc/templates/features/requirements.md` |
   | `../sdlc/templates/features/specification.md` | `.sdlc/templates/features/specification.md` |
   | `../sdlc/templates/features/plan.md` | `.sdlc/templates/features/plan.md` |
   | `../sdlc/templates/features/task.md` | `.sdlc/templates/features/task.md` |
   | `../sdlc/templates/features/tests.md` | `.sdlc/templates/features/tests.md` |
   | `../sdlc/templates/features/questions.md` | `.sdlc/templates/features/questions.md` |
   | `../sdlc/templates/knowledge/assumption.md` | `.sdlc/templates/knowledge/assumption.md` |
   | `../sdlc/templates/knowledge/decision.md` | `.sdlc/templates/knowledge/decision.md` |
   | `../sdlc/templates/knowledge/learning.md` | `.sdlc/templates/knowledge/learning.md` |

4. For each context file below, create it under `.sdlc/context/` — **only if the destination file does not already exist** — using the corresponding template as starting content:
   - `project-overview.md`
   - `architecture.md`
   - `conventions.md`

5. Report what was created and what was skipped (already existed).

## Output Format

```
## SDLC directory initialized

### Created
- .sdlc/context/project-overview.md
- .sdlc/templates/features/requirements.md
...

### Skipped (already exist)
- .sdlc/context/conventions.md
...

Next steps:
1. Fill in `.sdlc/context/project-overview.md` with your project's goals, stakeholders, and scope.
2. Fill in `.sdlc/context/architecture.md` with the system topology.
3. Fill in `.sdlc/context/conventions.md` with naming, structure, and coding conventions.
4. Edit templates under `.sdlc/templates/` to match your project's preferred artifact formats.
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
