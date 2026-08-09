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

2. **Resolve the agents version.**
   The canonical templates and skill definitions live in a git repository.
   Resolve the current version by running:
   ```
   git -C <skill-base-dir> rev-parse HEAD
   git -C <skill-base-dir> remote get-url origin
   ```
   where `<skill-base-dir>` is the parent directory containing the `sdlc/` templates (typically the agents repo root).
   Store the resulting SHA as `current_ref` and the remote URL as `current_remote`.

3. **Read sync metadata and generate a migration summary.**
   Read `.sdlc/sync-meta.yml` from the project root if it exists.
   - If it exists and `agents_ref` differs from `current_ref`:
     a. Run `git -C <skill-base-dir> log <stored-ref>..HEAD -- skills/sdlc/` to get the changelog of template and process changes.
     b. For each commit that changed a template or context file, read the diff to understand what was added, removed, or restructured.
     c. Produce a **migration summary** listing concrete actions needed to adapt the project's existing `.sdlc/` files (e.g. "remove Glossary section from project-overview.md", "add Observability section to specification template").
   - If it does not exist, this is a first sync, so no migration is needed.
   - If `agents_ref` matches `current_ref`, no migration is needed.

4. If `.sdlc/` does not exist, run `/initialize-sdlc-directory` (passing `$1` if provided) to create the directory tree and copy templates.
   If `.sdlc/` already exists, run `/update-sdlc-templates` to pull any upstream template improvements and merge them with user edits.
   In both cases, ensure the local-only workflow state files are gitignored: read `.sdlc/.gitignore` (create it if absent) and add any missing entries for `state.yml` and `features/*/progress.md`. These are regenerated per machine and per run and must never be committed or included in PRs.
   Also ensure the project root `.gitignore` excludes `status-report.html` (the generated output of `/sdlc-status`): read the root `.gitignore` if it exists and append `status-report.html` on its own line if the entry is missing, or create the file with that entry if it does not exist.
   Also ensure the **SDLC anchor** is present in the repo's primary agent-instruction file, per `sdlc/references/shared.md` (AGENTS.md SDLC anchor): a marker-delimited `## SDLC` section in `AGENTS.md` (falling back to `CLAUDE.md`, or creating `AGENTS.md` if neither exists) that tells future sessions `.sdlc/` exists and where to find context. On first sync `initialize-sdlc-directory` writes it; on later syncs this step re-ensures it (idempotent: create if absent, replace the delimited content if the markers exist, never touch content outside them). If the target file is read-only, skip and note it in the report.

5. Read existing `.sdlc/` content to establish the current state. Resolve each path via SDLC_DIR resolution (repo first, then `$SDLC_DIR/{owner}/{repository}/.sdlc/`); treat the union of both locations as the current state, with the repo copy winning on conflict:
   - List all directories under `.sdlc/features/` (and the mirror's `features/` if set) to identify tracked features.
   - Read each existing feature's `requirements.md`, `specification.md`, and `lifecycle.md` if present (from whichever location holds them).
    - Read `.sdlc/context/project-overview.md`, `architecture.md`, `conventions.md`, `vocabulary.md`, `infrastructure.md`, `schema.dbml`, `observability.md`, and `telemetry.md` if they exist (from whichever location holds them).
   - Note which context files and feature artifacts are present vs. missing.

6. Analyze the codebase to gather the information needed to fill in context files and identify features.
   Read enough of the project to confidently answer:
   - What does this project do and what problem does it solve?
   - Who are the likely stakeholders?
   - What is in scope and explicitly out of scope?
   - What are the key technical and business constraints?
   - What major components exist and how do they relate?
   - What are the core domain entities and their relationships?
   - Does the project use a database, and if so, what is the schema (tables, columns, types, constraints, indexes, relationships)?
   - How does data flow through the system?
    - What infrastructure is in use (CI, hosting, observability)?
    - What is the technology stack (languages, runtimes, frameworks, versions)?
    - What development tooling is configured (package manager, linter, formatter, type checker, build system, test runner, and how to invoke each)?
    - What environments exist (dev, staging, production, preview) and how do they map to branches?
    - What CI/CD pipelines are defined, what triggers them, and what do they run?
    - What are the deployment and rollback procedures?
    - What health check endpoints and smoke tests exist?
    - What observability infrastructure is in place (metrics, logging, tracing, alerting systems and their SDKs/libraries)?
    - What analytics or telemetry platform is used (if any), what SDK is installed, and what is the existing event taxonomy?
    - What naming, directory, coding, commit, and branching conventions are followed?
   - What domain terms, technical terms, and acronyms are used in the codebase?
   - What are the distinct features or subsystems present in the codebase?
   - What test files exist, and which features or modules do they cover?
   - What documentation exists (README sections, `docs/` pages, API docs, inline docstrings), and which features does it cover?

   Useful signals to look at (read what exists; skip what does not):
   - `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`
   - `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `Gemfile`, or equivalent manifest
   - CI configuration files (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, etc.)
   - Top-level directory structure (`ls -1`)
   - Entry-point files (e.g., `main.py`, `src/index.ts`, `cmd/`, `app/`)
   - Test directories and files (`tests/`, `test/`, `*_test.*`, `*.spec.*`, `*_spec.*`)
   - Database signals: migration files or directories (`migrations/`, `alembic/`, `db/migrate/`, `prisma/migrations/`), ORM model definitions (SQLAlchemy models, Django models, Prisma schema, ActiveRecord models, GORM definitions, TypeORM entities, Drizzle schemas), SQL schema files (`schema.sql`, `init.sql`, `*.sql` in a migrations directory), or database configuration files (`database.yml`, `prisma/schema.prisma`, `alembic.ini`, `drizzle.config.ts`)
   - Existing documentation under `docs/` if present
   - `CLAUDE.md` or `.claude/` for project-specific conventions already captured
    - Open or recently closed GitHub issues (`gh issue list --limit 20`) if the project has a remote

    **Parallelize context file reconciliation.** Steps 7–14 below each reconcile an independent context file and share no dependencies. Dispatch one subagent per file using the `Task` tool (`subagent_type: "general"`), passing the codebase analysis from step 6, the migration summary from step 3, the existing file content (if any), and the template structure. Each subagent starts with a fresh context, so its prompt must be fully self-contained. Collect all results for the sync report. If the `Task` tool is unavailable, process the files sequentially as written.

7. Reconcile and write `.sdlc/context/project-overview.md`.
   - If the file does not exist: create it using the project-overview template, populate with real content derived from the codebase.
   - If the file exists: read it, compare its content with the codebase analysis, and update sections that have drifted. **Also apply the migration summary**: if a section was removed from the template since the last sync, remove the corresponding section from the file. If a section was added, add it. Preserve any manual additions that are still accurate. Flag sections that changed in the report.
   - Do not leave any `<…>` placeholders.
   - If a section genuinely cannot be determined from the code (e.g., named stakeholders), write a concise note explaining what is unknown rather than a filler placeholder.

8. Reconcile and write `.sdlc/context/architecture.md` using the same compare-and-update approach, applying the migration summary where relevant.
   - Include a component table and describe the data flow based on what you read.
   - Include an **Entity Relationship Diagram** section using a Mermaid `erDiagram` block. Identify the core domain entities from the codebase (data models, database tables, key abstractions, config schemas) and their relationships. Include key attributes for each entity.
   - Use Mermaid diagrams for the system overview and data flow if the topology is non-trivial.

9. **Reconcile and write `.sdlc/context/schema.dbml`** (database schema, if the project uses a database).
   - **Detect whether the project has a database** using the signals gathered in step 6 (migration files, ORM models, SQL schema files, database configuration). If no database signals are found, skip this step. If `.sdlc/context/schema.dbml` exists from a previous sync but no database is detected now, flag it in the report as a stale artifact for manual review.
   - **If the project has a database**, derive the full schema from the codebase: ORM model definitions, migration files, SQL schema files, or schema introspection. Write `.sdlc/context/schema.dbml` in [DBML](https://dbml.dbdiagram.io/docs) format. Include all tables, columns with their data types, primary keys, foreign keys, unique constraints, indexes, and table relationships (`Ref` declarations). Add a header comment noting the file is generated by `/sync-sdlc` and the date.
   - Use the same compare-and-update approach as the other context files: if the file exists, compare its content with the current schema and update drifted tables, columns, or relationships. Preserve any manual annotations or notes added outside the generated content. If it does not exist, create it. Do not leave any placeholder content.
   - This file complements the Mermaid `erDiagram` in `architecture.md`: the ER diagram gives a high-level visual overview, while the DBML file provides the complete, detailed schema with types, constraints, and indexes.

10. Reconcile and write `.sdlc/context/conventions.md` using the same compare-and-update approach, applying the migration summary where relevant.
   - Derive naming conventions from existing file names, variable names, function names, and class names.
   - Derive commit-message conventions from `git log --oneline -20` if the project has a git history.
   - Derive branching conventions from visible branch names or documented workflow.

11. Reconcile and write `.sdlc/context/vocabulary.md` using the same compare-and-update approach, applying the migration summary where relevant.
    - Extract domain-specific terms, technical terms, and acronyms from the codebase.
    - Look at class names, function names, variable names, config keys, API routes, comments, and documentation for term candidates.
    - Sort terms alphabetically by the first column within each table (Domain Terms, Technical Terms, Acronyms and Abbreviations).
    - If you cannot determine enough terms, add a note that the vocabulary needs manual completion.

12. Reconcile and write `.sdlc/context/infrastructure.md` using the same compare-and-update approach, applying the migration summary where relevant.
    - Derive the technology stack from project manifests (`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, etc.): languages, runtimes, frameworks, and versions.
    - Derive development tooling from config files and scripts: package manager, linter, formatter, type checker, build system, test runner, and the commands to invoke each.
    - Derive environments from CI/CD config, deployment scripts, and branch naming: what environments exist, their branch mappings, and URLs.
    - Derive CI/CD pipeline definitions from workflow files (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`): workflow names, triggers, and what they run.
    - Derive deployment and rollback procedures from deployment scripts, workflow files, and documentation.
    - Derive health check endpoints from the codebase (search for `/health`, `/ready`, `/healthz`).
    - Derive smoke test locations from test directories or deployment scripts.
    - Derive hosting platform from config files, deployment scripts, and documentation.
    - Derive secrets management approach from config files and environment variable usage.

13. Reconcile and write `.sdlc/context/observability.md` (optional, only when the project has observability infrastructure) using the same compare-and-update approach.
    - Detect observability infrastructure by searching for instrumentation libraries (`prometheus`, `datadog`, `opentelemetry`, `otel`, `jaeger`, `zipkin`, `sentry`, `structlog`, `logging`, `logrus`, `zap`, etc.) in project manifests and imports.
    - If no observability signals are found, skip this step. If `.sdlc/context/observability.md` exists from a previous sync but no observability is detected now, flag it in the report as a stale artifact for manual review.
    - Populate monitoring pillars, instrumentation libraries, log aggregation, tracing, alerting, and dashboards from the codebase analysis.
    - Reference `service-levels.md` in the SLO Reference section if it exists.

14. Reconcile and write `.sdlc/context/telemetry.md` (optional, only when the project has an analytics or product telemetry platform) using the same compare-and-update approach.
    - Detect analytics/telemetry infrastructure by searching for analytics SDKs (`amplitude`, `mixpanel`, `posthog`, `google-analytics`, `segment`, `@analytics/*`, etc.) in project manifests and imports.
    - If no analytics signals are found, skip this step. If `.sdlc/context/telemetry.md` exists from a previous sync but no analytics is detected now, flag it in the report as a stale artifact for manual review.
    - Populate analytics platform, event naming conventions, existing event taxonomy, identity resolution, privacy and compliance constraints, and funnels from the codebase analysis.

15. Identify the major features or subsystems of the project.
    A feature is a coherent unit of functionality visible to users or operators, not an internal module or utility.
    Aim for 3–10 features; fewer for small projects, more for large ones.
    Good signals: top-level CLI commands, API route groups, major UI sections, distinct background jobs, named services.
    For each feature, record the source files that implement it, the test files that cover it, and any documentation that describes it. This implementation, test, and documentation evidence drives artifact status and progress tracking in steps 17–18.

16. Match identified features against existing `.sdlc/features/` directories.
    Build three lists:
    - **New features**: identified in the codebase but not present in `.sdlc/features/`.
    - **Existing features**: identified in the codebase and present in `.sdlc/features/`.
    - **Orphaned features**: present in `.sdlc/features/` but not identified in the codebase scan.

    **Process features in parallel.** Steps 17–18 below process new and existing features independently with no cross-feature dependencies. Dispatch one subagent per feature using the `Task` tool (`subagent_type: "general"`), passing the feature's type (new or existing), its source files, test files, and documentation evidence from step 15, the codebase analysis from step 6, and the existing artifacts (for existing features). Each subagent starts with a fresh context, so its prompt must be fully self-contained. Collect all results and merge into the sync report. Process orphaned features (step 19) inline since they require only flagging, no file writes. If the `Task` tool is unavailable, process all features sequentially as written.

17. For each **new feature**:
    a. Create a directory `.sdlc/features/p<seq>-<slug>/` following the Feature Directory Naming convention in `skills/sdlc/references/shared.md`. Features discovered from the codebase during reconciliation have no associated issue, so they are created as **pending** features with a `p`-prefixed sequence id (the next unused `p<seq>`, e.g. `p1`, `p2`), to be promoted to placeholder issues later. `<slug>` is a kebab-case name derived from the feature name.
    b. Create `requirements.md` and `specification.md` in the new directory using the corresponding templates from `.sdlc/templates/features/` as the structure. Since these features were reverse-engineered from existing code, set frontmatter `status: done` on both — they document already-implemented functionality, not work yet to be done.
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
           e. **Identify test coverage.** Using the evidence gathered in step 15, determine which test files cover this feature's functionality. Match by naming conventions, import paths, module structure, or test descriptions. Record the specific test files and test cases found.
    f. **Create `tests.md`** if test coverage was found. Use the tests template from `.sdlc/templates/features/` with frontmatter `status: done`. Populate it from the actual test code: list the test files, summarize what each covers, categorize into unit/integration/end-to-end as appropriate, note edge cases already tested, and build a coverage matrix mapping functional requirements (from `requirements.md`) to test cases. If no tests were found for this feature, skip this step and note the gap in the sync report.
     g. **Create `progress.md`** reflecting that implementation already exists. Use the progress template from `.sdlc/templates/features/`. Set frontmatter `current_phase` to `complete`, `re_entry_point` to the first missing artifact (`create-tests` if no tests found, `create-documentation` if tests exist but no documentation was found, or `none` if both exist), and `last_updated` to today's date. In the Pipeline Status table, mark `create-requirements`, `create-specifications`, and `create-implementation` as `done`; mark `create-tests` and `review-tests` as `done` if tests were found, otherwise leave as `—`; mark `create-documentation` and `review-documentation` as `done` if documentation was found, otherwise leave as `—`; mark all review, planning, and feasibility phases that were not formally conducted as `skipped`; leave PR, deployment, and learnings phases as `—`. Write a Summary noting the feature was reverse-engineered from existing code during sync. Leave the Task Progress table empty since tasks were not formally decomposed.

18. For each **existing feature**:
    a. Read the current `requirements.md` and `specification.md`.
    b. Generate a fresh analysis of the feature from the codebase.
    c. Compare the fresh analysis with the existing files.
    d. If the existing `requirements.md` is missing functional requirements that the code clearly implements, or contains requirements that no longer match the code, produce a drift report entry listing the discrepancies. Do **not** overwrite the existing file; instead, if `review-requirements.md` exists with `verdict: approved`, regress it to `verdict: changes-requested` and append a `## Sync drift: <date>` section to its body describing the discrepancies, so the forward pipeline resyncs and re-reviews it.
    e. If the existing `specification.md` has drifted from the code, regress `review-specification.md` the same way and add a drift report entry.
    f. If the existing `lifecycle.md` has drifted from the code (states or transitions no longer match what the code implements), regress `review-lifecycle.md` the same way and add a drift report entry.
    g. If the existing files match the codebase analysis, note it as "in sync" in the report.
     h. Reconcile `progress.md`. If it does not exist, create it following the same logic as step 17g. If it exists but `current_phase` predates implementation (e.g., `specification`, `plan`, or earlier) while the code is already implemented, update `current_phase` to `complete` and adjust the Pipeline Status table accordingly. Never downgrade a `current_phase` that already reflects completion or a later stage.
     i. Reconcile `tests.md`. If test files covering this feature exist in the codebase but `tests.md` does not, create it following step 17f. If `tests.md` already exists, compare its documented test cases against the actual test code and, for any discrepancies, regress `review-tests.md` to `changes-requested` with a `## Sync drift: <date>` body the same way.
    j. If `requirements.md`, `specification.md`, or `lifecycle.md` have frontmatter `status: draft` but the feature is already implemented, update `status` to `done`.

19. For each **orphaned feature**:
    a. Do not delete or modify any files.
    b. Flag it in the report as potentially removed from the codebase.
    c. The user should review and either update the feature's scope or remove the `.sdlc/features/` directory manually.

20. **Promote pending features** (only when `--create-issues` is set). This step remains sequential: each promotion renames a feature directory and rewrites `FEAT-p<seq>` cross-references across all feature directories, so each must complete before the next begins.
    a. If the SDLC store resolves to `SDLC_DIR`-only (no in-repo `.sdlc/`), skip promotion and record a warning: the repo appears to be third-party, so creating issues there is inappropriate.
    b. Otherwise, list every `p`-prefixed directory under `.sdlc/features/` (pending features with no GitHub issue yet).
    c. For each, invoke `/create-placeholder-issue <feature>` (pass the feature id, e.g. `FEAT-p1`). That skill creates a placeholder issue, renames the directory to the issue number, and rewrites every `FEAT-p<seq>` cross-reference.
    d. Collect each verdict. Re-runs are safe: `create-placeholder-issue` no-ops on features that are already issue-driven and deduplicates against existing placeholder issues.

    If `--create-issues` was not set, skip this step entirely; pending features remain `p*` until promoted manually or on a later sync with the flag.

21. **Write sync metadata.**
    Write `.sdlc/sync-meta.yml` with:
    ```yaml
    agents_ref: <current_ref>
    agents_remote: <current_remote>
    last_synced: <today's date in ISO 8601>
    ```
    This file should be committed alongside the other `.sdlc/` changes so that the next sync can detect version drift.

22. Produce the sync report.

## Output Format

```
## SDLC sync report

### Migration summary (agents changes since last sync)
| Change | Affected files | Action taken |
|---|---|---|
| <e.g. "Removed Glossary section from project-overview template"> | .sdlc/context/project-overview.md | Removed Glossary section |
| <e.g. "Added Observability template"> | .sdlc/templates/features/ | Created new template |

(If this is a first sync, this section shows "Initial sync, no migration needed.")

### Directory structure
(output from /initialize-sdlc-directory or /update-sdlc-templates)

### Agent instructions
- AGENTS.md: SDLC anchor created / updated / unchanged / skipped: read-only

### Sync metadata
- agents_ref: <SHA>
- agents_remote: <URL>
- last_synced: <date>

### Context files
| File | Status | Changes |
|---|---|---|
| .sdlc/context/project-overview.md | created / updated / unchanged | <summary of changes> |
| .sdlc/context/architecture.md | created / updated / unchanged | <summary of changes> |
| .sdlc/context/schema.dbml | created / updated / unchanged / not applicable (no database) | <summary of changes> |
| .sdlc/context/conventions.md | created / updated / unchanged | <summary of changes> |
| .sdlc/context/vocabulary.md | created / updated / unchanged | <summary of changes> |
| .sdlc/context/infrastructure.md | created / updated / unchanged | <summary of changes> |
| .sdlc/context/observability.md | created / updated / unchanged / not applicable (no observability infra) | <summary of changes> |
| .sdlc/context/telemetry.md | created / updated / unchanged / not applicable (no analytics platform) | <summary of changes> |

### Feature reconciliation

#### New features (created)
- N-<slug>: <Feature Name>
  - requirements.md: populated (N functional requirements, M non-functional), status: done
  - specification.md: populated, status: done
  - tests.md: created (N test cases documented) / not created (no tests found)
  - progress.md: created (current_phase: complete, re_entry_point: <phase or none>)
  - documentation: found (<paths>) / not found

#### Existing features (checked)
- N-<slug>: <Feature Name>
  - requirements.md: in sync / drift detected (<count> items, see review-requirements.md)
  - specification.md: in sync / drift detected (<count> items, see review-specification.md)
  - tests.md: created / in sync / drift detected / not created (no tests found)
  - progress.md: created / updated / in sync
  - documentation: found (<paths>) / not found

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
3. Address drift items in the regressed `review-<artifact>.md` files for existing features.
4. Decide the fate of orphaned features (update scope or remove).
5. Commit changes to `.sdlc/` to version control.
```

## Example Usage

**Scenario 1: First-time setup (no .sdlc/ exists)**
```
/sync-sdlc
```
Creates `.sdlc/` with templates, populates all context files fresh, creates feature directories with requirements, specifications, tests, and progress reflecting existing implementation.

**Scenario 2: Periodic sync on an established project**
```
/sync-sdlc
```
Updates templates, compares and updates context files, creates new features, checks existing features for drift, reconciles progress and test artifacts, flags orphaned features.

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
