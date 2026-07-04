---
name: sync-sdlc
description: Analyze the codebase and reconcile it with the .sdlc/ directory. Creates the .sdlc/ structure if absent, populates context files, creates missing features, updates stale artifacts, and flags drift between code and documentation. With --create-issues, promotes pending (p-prefixed) features to issue-driven ones by creating placeholder GitHub issues.
argument-hint: "[project-root] [--create-issues]"
---

# Sync SDLC

Reads the codebase and reconciles it with the `.sdlc/` directory.
On first run, creates the `.sdlc/` structure from scratch and populates everything.
On subsequent runs, compares the codebase against existing `.sdlc/` content to create missing features, update stale context files, and flag drift.
Works for both initial bootstrapping and periodic sync.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- Read access to the project root and its subdirectories
- Write access to create or update `.sdlc/`

## Flags

- `--create-issues`: After reconciliation, promote every pending (`p`-prefixed) feature to an issue-driven one by invoking `/create-placeholder-issue` for each. This creates placeholder GitHub issues and renames the feature directories to their issue numbers. Only acts on features whose `.sdlc/` resolves in the repository (a repo you own); it is skipped with a warning when the SDLC store is `SDLC_DIR`-only (a third-party repo where creating issues is inappropriate). Requires `gh` authenticated with write access. Without this flag, pending features are left as `p*`.

## Steps

1. Determine the project root: use `$1` if provided and it is not a flag (does not start with `--`), otherwise use the current working directory. Parse `--create-issues` out of the arguments; it is a flag, not the project root.

   **SDLC_DIR resolution:** Apply `sdlc/references/shared.md` (repo first, then `$SDLC_DIR/{owner}/{repository}/.sdlc/`; mirror writes when set). `sync-meta.yml` is written to the repo's `.sdlc/` only.

2. **Resolve the dot-claude version.**
   The canonical templates and skill definitions live in a git repository.
   Resolve the current version by running:
   ```
   git -C <skill-base-dir> rev-parse HEAD
   git -C <skill-base-dir> remote get-url origin
   ```
   where `<skill-base-dir>` is the parent directory containing the `sdlc/` templates (typically the dot-claude repo root).
   Store the resulting SHA as `current_ref` and the remote URL as `current_remote`.

3. **Read sync metadata and generate a migration summary.**
   Read `.sdlc/sync-meta.yml` from the project root if it exists.
   - If it exists and `dot_claude_ref` differs from `current_ref`:
     a. Run `git -C <skill-base-dir> log <stored-ref>..HEAD -- skills/sdlc/` to get the changelog of template and process changes.
     b. For each commit that changed a template or context file, read the diff to understand what was added, removed, or restructured.
     c. Produce a **migration summary** listing concrete actions needed to adapt the project's existing `.sdlc/` files (e.g. "remove Glossary section from project-overview.md", "add Observability section to specification template").
   - If it does not exist, this is a first sync, so no migration is needed.
   - If `dot_claude_ref` matches `current_ref`, no migration is needed.

4. If `.sdlc/` does not exist, run `/initialize-sdlc-directory` (passing `$1` if provided) to create the directory tree and copy templates.
   If `.sdlc/` already exists, run `/update-sdlc-templates` to pull any upstream template improvements and merge them with user edits.
   In both cases, ensure the local-only workflow state files are gitignored: read `.sdlc/.gitignore` (create it if absent) and add any missing entries for `state.yml` and `features/*/progress.md`. These are regenerated per machine and per run and must never be committed or included in PRs.

5. Read existing `.sdlc/` content to establish the current state. Resolve each path via SDLC_DIR resolution (repo first, then `$SDLC_DIR/{owner}/{repository}/.sdlc/`); treat the union of both locations as the current state, with the repo copy winning on conflict:
   - List all directories under `.sdlc/features/` (and the mirror's `features/` if set) to identify tracked features.
   - Read each existing feature's `requirements.md` and `specification.md` if present (from whichever location holds them).
   - Read `.sdlc/context/project-overview.md`, `architecture.md`, `conventions.md`, and `vocabulary.md` if they exist (from whichever location holds them).
   - Note which context files and feature artifacts are present vs. missing.

6. Analyze the codebase to gather the information needed to fill in context files and identify features.
   Read enough of the project to confidently answer:
   - What does this project do and what problem does it solve?
   - Who are the likely stakeholders?
   - What is in scope and explicitly out of scope?
   - What are the key technical and business constraints?
   - What major components exist and how do they relate?
   - How does data flow through the system?
   - What infrastructure is in use (CI, hosting, observability)?
   - What naming, directory, coding, commit, and branching conventions are followed?
   - What domain terms, technical terms, and acronyms are used in the codebase?
   - What are the distinct features or subsystems present in the codebase?

   Useful signals to look at (read what exists; skip what does not):
   - `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`
   - `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `Gemfile`, or equivalent manifest
   - CI configuration files (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, etc.)
   - Top-level directory structure (`ls -1`)
   - Entry-point files (e.g., `main.py`, `src/index.ts`, `cmd/`, `app/`)
   - Existing documentation under `docs/` if present
   - `CLAUDE.md` or `.claude/` for project-specific conventions already captured
   - Open or recently closed GitHub issues (`gh issue list --limit 20`) if the project has a remote

7. Reconcile and write `.sdlc/context/project-overview.md`.
   - If the file does not exist: create it using the project-overview template, populate with real content derived from the codebase.
   - If the file exists: read it, compare its content with the codebase analysis, and update sections that have drifted. **Also apply the migration summary**: if a section was removed from the template since the last sync, remove the corresponding section from the file. If a section was added, add it. Preserve any manual additions that are still accurate. Flag sections that changed in the report.
   - Do not leave any `<…>` placeholders.
   - If a section genuinely cannot be determined from the code (e.g., named stakeholders), write a concise note explaining what is unknown rather than a filler placeholder.

8. Reconcile and write `.sdlc/context/architecture.md` using the same compare-and-update approach, applying the migration summary where relevant.
   - Include a component table and describe the data flow based on what you read.
   - Use a simple ASCII diagram if the topology is non-trivial.

9. Reconcile and write `.sdlc/context/conventions.md` using the same compare-and-update approach, applying the migration summary where relevant.
   - Derive naming conventions from existing file names, variable names, function names, and class names.
   - Derive commit-message conventions from `git log --oneline -20` if the project has a git history.
   - Derive branching conventions from visible branch names or documented workflow.

10. Reconcile and write `.sdlc/context/vocabulary.md` using the same compare-and-update approach, applying the migration summary where relevant.
   - Extract domain-specific terms, technical terms, and acronyms from the codebase.
   - Look at class names, function names, variable names, config keys, API routes, comments, and documentation for term candidates.
   - If you cannot determine enough terms, add a note that the vocabulary needs manual completion.

11. Identify the major features or subsystems of the project.
    A feature is a coherent unit of functionality visible to users or operators, not an internal module or utility.
    Aim for 3–10 features; fewer for small projects, more for large ones.
    Good signals: top-level CLI commands, API route groups, major UI sections, distinct background jobs, named services.

12. Match identified features against existing `.sdlc/features/` directories.
    Build three lists:
    - **New features**: identified in the codebase but not present in `.sdlc/features/`.
    - **Existing features**: identified in the codebase and present in `.sdlc/features/`.
    - **Orphaned features**: present in `.sdlc/features/` but not identified in the codebase scan.

13. For each **new feature**:
    a. Create a directory `.sdlc/features/p<seq>-<slug>/` following the Feature Directory Naming convention in `skills/sdlc/references/shared.md`. Features discovered from the codebase during reconciliation have no associated issue, so they are created as **pending** features with a `p`-prefixed sequence id (the next unused `p<seq>`, e.g. `p1`, `p2`), to be promoted to placeholder issues later. `<slug>` is a kebab-case name derived from the feature name.
    b. Create `requirements.md` and `specification.md` in the new directory using the corresponding templates from `.sdlc/templates/features/` as the structure. Do not create any other files; `plan.md`, `tests.md`, `questions.md`, and `tasks/` are created when there is real content to put in them.
    c. Populate `requirements.md` with:
       - A real overview paragraph describing the feature's purpose.
       - Functional requirements derived from the code (what the system does).
       - Non-functional requirements if inferable (performance targets, security constraints, etc.).
       - Acceptance criteria mapped to the functional requirements.
       - Any open questions that cannot be answered from the code alone.
    d. Populate `specification.md` with:
       - The technical approach for this feature.
       - Relevant data models or schemas (inferred from the code).
       - API contracts if the feature exposes endpoints.
       - Key sequence flows if non-trivial.
       - Technical decisions already made (libraries chosen, patterns used).
       - Known risks or open unknowns.

14. For each **existing feature**:
    a. Read the current `requirements.md` and `specification.md`.
    b. Generate a fresh analysis of the feature from the codebase.
    c. Compare the fresh analysis with the existing files.
    d. If the existing `requirements.md` is missing functional requirements that the code clearly implements, or contains requirements that no longer match the code, produce a drift report entry listing the discrepancies. Do **not** overwrite the existing file; instead append findings to the feature's `questions.md` (create it if it does not exist) as "Sync drift" items.
    e. If the existing `specification.md` has drifted from the code, produce a drift report entry the same way.
    f. If the existing files match the codebase analysis, note it as "in sync" in the report.

15. For each **orphaned feature**:
    a. Do not delete or modify any files.
    b. Flag it in the report as potentially removed from the codebase.
    c. The user should review and either update the feature's scope or remove the `.sdlc/features/` directory manually.

16. **Promote pending features** (only when `--create-issues` is set).
    a. If the SDLC store resolves to `SDLC_DIR`-only (no in-repo `.sdlc/`), skip promotion and record a warning: the repo appears to be third-party, so creating issues there is inappropriate.
    b. Otherwise, list every `p`-prefixed directory under `.sdlc/features/` (pending features with no GitHub issue yet).
    c. For each, invoke `/create-placeholder-issue <feature>` (pass the feature id, e.g. `FEAT-p1`). That skill creates a placeholder issue, renames the directory to the issue number, and rewrites every `FEAT-p<seq>` cross-reference.
    d. Collect each verdict. Re-runs are safe: `create-placeholder-issue` no-ops on features that are already issue-driven and deduplicates against existing placeholder issues.

    If `--create-issues` was not set, skip this step entirely; pending features remain `p*` until promoted manually or on a later sync with the flag.

17. **Write sync metadata.**
    Write `.sdlc/sync-meta.yml` with:
    ```yaml
    dot_claude_ref: <current_ref>
    dot_claude_remote: <current_remote>
    last_synced: <today's date in ISO 8601>
    ```
    This file should be committed alongside the other `.sdlc/` changes so that the next sync can detect version drift.

18. Produce the sync report.

## Output Format

```
## SDLC sync report

### Migration summary (dot-claude changes since last sync)
| Change | Affected files | Action taken |
|---|---|---|
| <e.g. "Removed Glossary section from project-overview template"> | .sdlc/context/project-overview.md | Removed Glossary section |
| <e.g. "Added Observability template"> | .sdlc/templates/features/ | Created new template |

(If this is a first sync, this section shows "Initial sync, no migration needed.")

### Directory structure
(output from /initialize-sdlc-directory or /update-sdlc-templates)

### Sync metadata
- dot_claude_ref: <SHA>
- dot_claude_remote: <URL>
- last_synced: <date>

### Context files
| File | Status | Changes |
|---|---|---|
| .sdlc/context/project-overview.md | created / updated / unchanged | <summary of changes> |
| .sdlc/context/architecture.md | created / updated / unchanged | <summary of changes> |
| .sdlc/context/conventions.md | created / updated / unchanged | <summary of changes> |
| .sdlc/context/vocabulary.md | created / updated / unchanged | <summary of changes> |

### Feature reconciliation

#### New features (created)
- N-<slug>: <Feature Name>
  - requirements.md: populated (N functional requirements, M non-functional)
  - specification.md: populated

#### Existing features (checked)
- N-<slug>: <Feature Name>
  - requirements.md: in sync / drift detected (<count> items, see questions.md)
  - specification.md: in sync / drift detected (<count> items, see questions.md)

#### Orphaned features (no matching code)
- N-<slug>: <Feature Name> — review and update scope or remove manually

#### Promoted features (--create-issues)
- p<seq>-<slug> -> M-<slug>: <Feature Name> (issue #M, <url>) [promoted | skipped: third-party | failed: <reason>]
(Omit this subsection when `--create-issues` was not set. When it was set but there are no pending features, show "No pending features to promote.")

### Items requiring manual review
- <any context file sections that could not be determined>
- <any orphaned features>

### Next steps
1. Review context file changes and correct anything that was inferred incorrectly.
2. Review each new feature's requirements.md and specification.md.
3. Address drift items in questions.md for existing features.
4. Decide the fate of orphaned features (update scope or remove).
5. Commit changes to `.sdlc/` to version control.
```

## Example Usage

**Scenario 1: First-time setup (no .sdlc/ exists)**
```
/sync-sdlc
```
Creates `.sdlc/` with templates, populates all context files fresh, creates feature directories with requirements and specifications.

**Scenario 2: Periodic sync on an established project**
```
/sync-sdlc
```
Updates templates, compares and updates context files, creates new features, checks existing features for drift, flags orphaned features.

**Scenario 3: Sync a project from a different directory**
```
/sync-sdlc /path/to/my-project
```
Same as above but targets the specified project root.

**Scenario 4: Sync and back pending features with GitHub issues**
```
/sync-sdlc --create-issues
```
Same as a normal sync, then promotes every `p`-prefixed feature: creates a placeholder issue for each, renames the directory to the issue number, and rewrites cross-references. Skipped automatically when the SDLC store is `SDLC_DIR`-only (third-party repo).
