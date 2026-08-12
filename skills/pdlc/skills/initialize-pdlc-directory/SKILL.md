---
name: initialize-pdlc-directory
description: Bootstrap the .pdlc/ directory structure in a project, creating subdirectories and populating templates.
argument-hint: "[project-root]"
---

# Initialize PDLC Directory

Creates the `.pdlc/` directory structure in the project root (or `$1` if provided) and populates it with default templates.
Already-existing files are never overwritten — safe to run on a project that has partially adopted the structure.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- Write access to the project root.
- The canonical templates at `../../templates/` relative to this skill file (i.e. `skills/pdlc/templates/`).

## Steps

1. Determine the project root: use `$1` if provided, otherwise the current working directory.
2. **Resolve the PDLC write location** per `pdlc/references/shared.md`: default `<project-root>/.pdlc/`; if it cannot be created and `PDLC_DIR` is set, use `$PDLC_DIR/{owner}/{repository}/.pdlc/`; mirror created files when set. Record which location was used.
3. Create each directory below (under the resolved write location) if it does not already exist:
   ```
   .pdlc/
   .pdlc/context/
   .pdlc/initiatives/
   .pdlc/decisions/
   .pdlc/learnings/
   .pdlc/templates/
   .pdlc/templates/initiatives/
   .pdlc/templates/context/
   ```
4. Create `.pdlc/.gitignore` — **only if it does not already exist** — to keep local-only workflow state out of version control:
   ```gitignore
   # Local-only workflow state — do not commit
   # Orchestrator run state
   state.yml
   # Per-initiative progress tracking and session logs
   initiatives/*/progress.md
   ```
   `state.yml` and each initiative's `progress.md` are regenerated per machine and per run, so they must never be committed. The `initiatives/*/progress.md` pattern ignores only the per-initiative files, not the template. Only the repo's `.pdlc/.gitignore` is meaningful; do not create one under the `PDLC_DIR` mirror.
5. For each canonical template file (read from `../../templates/` relative to this skill), copy it to the corresponding path under `.pdlc/templates/` — **only if the destination file does not already exist**. The templates are the initiative artifacts (under `initiatives/`), the decision and learning templates, and the context templates (under `context/`).
6. For each context file below, create it under `.pdlc/context/` — **only if it does not already exist** — using the corresponding canonical template (from `../../templates/context/`) as starting content:
   - `product-overview.md`
   - `vision.md`
   - `goals.md`
   - `roadmap.md`
   - `vocabulary.md`
7. **Write the PDLC anchor** to the repo's primary agent-instruction file, per `pdlc/references/shared.md` (AGENTS.md PDLC anchor). This injects a short, marker-delimited `## PDLC` section into `AGENTS.md` (creating `AGENTS.md` if it doesn't exist). The block is idempotent: create if absent, replace its delimited content if the markers exist, never touch content outside the markers. Note the target file and whether it was created, updated, or skipped in the report.
8. Report what was created and what was skipped (already existed). When `PDLC_DIR` is set, note whether each path was written to the repo, the mirror, or both.

## Output Format

```
## PDLC directory initialized

### Created
- .pdlc/.gitignore
- .pdlc/context/product-overview.md
- .pdlc/templates/initiatives/prd.md
...

### Agent instructions
- AGENTS.md: PDLC anchor created (or updated / skipped: read-only)

### Skipped (already exist)
- .pdlc/context/goals.md
...

Next steps:
1. Fill in `.pdlc/context/product-overview.md` with your product, ICP, and stakeholders.
2. Run `/pdlc discover` to start the first initiative.
3. Edit templates under `.pdlc/templates/` to match your preferred artifact formats.
```
