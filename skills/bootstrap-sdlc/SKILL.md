---
name: bootstrap-sdlc
description: Bootstrap the .sdlc/ directory for an existing project by running initialize-sdlc-directory and then populating the context files with real content derived from the codebase.
argument-hint: "[project-root]"
---

# Bootstrap SDLC

Runs `/initialize-sdlc-directory` to create the `.sdlc/` structure, then reads the existing codebase to populate the context files with real content instead of leaving them as blank templates.

## Prerequisites

- Read access to the project root and its subdirectories
- Write access to create `.sdlc/`

## Steps

1. Determine the project root: use `$1` if provided, otherwise use the current working directory.

2. Run `/initialize-sdlc-directory` (passing `$1` if provided) to create the directory tree and copy templates.

3. Analyze the codebase to gather the information needed to fill in the context files and identify features.
   Read enough of the project to confidently answer:
   - What does this project do and what problem does it solve?
   - Who are the likely stakeholders?
   - What is in scope and explicitly out of scope?
   - What are the key technical and business constraints?
   - What major components exist and how do they relate?
   - How does data flow through the system?
   - What infrastructure is in use (CI, hosting, observability)?
   - What naming, directory, coding, commit, and branching conventions are followed?
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

4. Write `.sdlc/context/project-overview.md` using the project-overview template as the structure.
   Replace every placeholder with real content derived from the codebase.
   Do not leave any `<…>` placeholders in the file.
   If a section genuinely cannot be determined from the code (e.g., named stakeholders), write a concise note explaining what is unknown rather than a filler placeholder.

5. Write `.sdlc/context/architecture.md` using the architecture template as the structure.
   Replace every placeholder with real content.
   Include a component table and describe the data flow based on what you read.
   Use a simple ASCII diagram if the topology is non-trivial.

6. Write `.sdlc/context/conventions.md` using the conventions template as the structure.
   Derive naming conventions from existing file names, variable names, function names, and class names.
   Derive commit-message conventions from `git log --oneline -20` if the project has a git history.
   Derive branching conventions from visible branch names or documented workflow.
   Replace every placeholder with real content.

7. Identify the major features or subsystems of the project.
   A feature is a coherent unit of functionality visible to users or operators — not an internal module or utility.
   Aim for 3–10 features; fewer for small projects, more for large ones.
   Good signals: top-level CLI commands, API route groups, major UI sections, distinct background jobs, named services.

   For each identified feature:
   a. Create a directory `.sdlc/features/FEAT-NNNN-<slug>/` where `NNNN` is a zero-padded sequence number (0001, 0002, …) and `<slug>` is a kebab-case name derived from the feature name.
   b. Create `requirements.md` and `specification.md` in the new directory using the corresponding templates from `.sdlc/templates/features/` as the structure. Do not create any other files — plan.md, tests.md, questions.md, and tasks/ are created when there is real content to put in them.
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

8. Report what was created and what was populated.

## Output Format

```
## SDLC bootstrapped

### Directory structure
(output from /initialize-sdlc-directory)

### Context files populated
- .sdlc/context/project-overview.md  — derived from README and pyproject.toml
- .sdlc/context/architecture.md      — derived from src/ layout and CI config
- .sdlc/context/conventions.md       — derived from file naming, git log, and CONTRIBUTING.md

### Features created
- .sdlc/features/FEAT-0001-<slug>/  — <Feature Name>: requirements.md and specification.md populated
- .sdlc/features/FEAT-0002-<slug>/  — <Feature Name>: requirements.md and specification.md populated
...

### Items requiring manual review
- Stakeholder table in project-overview.md: named individuals could not be determined from code alone
- Hosting infrastructure in architecture.md: no deployment config found
- plan.md, tests.md, questions.md not created — add them when there is real content to populate

Next steps:
1. Review each context file and correct anything that was inferred incorrectly.
2. Review each feature's requirements.md and specification.md; correct any misidentified behaviour.
3. Fill in the "requiring manual review" items above.
4. Commit `.sdlc/` to version control.
5. Run `/update-sdlc-templates` after pulling new versions of dot-claude to keep templates current.
```

## Example Usage

**Scenario 1: New project, run from its root**
```
/bootstrap-sdlc
```
Initializes `.sdlc/` and populates context files from the code in the current directory.

**Scenario 2: Bootstrapping a project from a different directory**
```
/bootstrap-sdlc /path/to/my-project
```
Same as above but targets the specified project root.
