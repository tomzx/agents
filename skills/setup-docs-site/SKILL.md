---
name: setup-docs-site
description: Scaffold a MkDocs documentation site with Material theme, initial content structure, and a GitHub Actions workflow to publish to GitHub Pages. Use when the user says /setup-docs-site, "set up docs", "create docs site", "mkdocs setup", or wants to bootstrap a documentation website.
argument-hint: "[project-root]"
---

TODAY=!`date +%Y-%m-%d`

# Setup Docs Site

Scaffolds a MkDocs documentation site with the Material theme, creates the initial content structure under `docs/`, and adds a GitHub Actions workflow to build and deploy to GitHub Pages.

Does not overwrite existing files. If `mkdocs.yml` or `docs/` already exist, reports what is present and skips or offers to update.

## Prerequisites

- Python project with `pyproject.toml` (for `uv add`), or willingness to install MkDocs via pip
- Git repository with a GitHub remote (for the GHA workflow)
- `uv` available in PATH (preferred) or `pip`
- Read any files present under `.sdlc/context/` for project-level context to populate docs content

## Steps

### 1. Determine the project root

Use `$1` if provided, otherwise use the current working directory.
Verify it is a git repository:

```
git rev-parse --is-inside-work-tree
```

Check for a GitHub remote:

```
gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null
```

If no GitHub remote, skip the GHA workflow creation and report the limitation.

### 2. Check existing documentation infrastructure

Check for existing files:

```
ls mkdocs.yml docs/ README.md .github/workflows/pages*.yml .github/workflows/pages*.yaml 2>/dev/null
```

If `mkdocs.yml` exists, report it and skip to Step 5 (content structure).
If `docs/` exists, report it and merge content rather than overwrite.

### 3. Install MkDocs dependencies

Detect the package manager and install:

For `uv` projects (preferred):

```bash
uv add --dev mkdocs mkdocs-material
```

For pip projects:

```bash
pip install mkdocs mkdocs-material
```

Record what was installed.

### 4. Create mkdocs.yml

Create `mkdocs.yml` in the project root with the following structure.
Derive `site_name`, `site_description`, and `repo_url` from the codebase:

```yaml
site_name: <project name>
site_description: <one sentence from README or pyproject.toml>
site_url: ""
repo_url: <github remote url>
repo_name: <owner/repo>

theme:
  name: material
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - search.suggest
    - search.highlight
    - content.code.copy

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Reference: reference/
  - Changelog: changelog.md

markdown_extensions:
  - admonition
  - attr_list
  - footnotes
  - pymdownx.details
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences
  - tables
  - toc:
      permalink: true

plugins:
  - search
```

Adapt the `nav` section based on what exists:
- If `.sdlc/context/` exists, include a "Architecture" entry pointing to architecture docs.
- If the project has a CLI, include a "CLI Reference" entry.
- If the project has an API, include an "API Reference" entry.
- If `CHANGELOG.md` exists, include a "Changelog" entry.

### 5. Create docs/ directory structure

Create the following structure under `docs/`:

```
docs/
  index.md
  getting-started.md
  reference/
    index.md
  changelog.md (if CHANGELOG.md exists at root)
```

Do NOT overwrite existing files. For each file:

**`docs/index.md`**: Derive content from `README.md` if it exists, otherwise from `.sdlc/context/project-overview.md`, otherwise write a placeholder.

**`docs/getting-started.md`**: Extract installation and quickstart steps from README, pyproject.toml, or Makefile. Include:
- Prerequisites
- Installation
- Quick start example
- Next steps

**`docs/reference/index.md`**: Create a stub that lists the reference sections that will be populated (CLI, API, configuration).

**`docs/changelog.md`**: If `CHANGELOG.md` exists at the project root, copy its content. Otherwise create a stub with the standard Keep a Changelog format.

If `.sdlc/context/architecture.md` exists, create `docs/architecture.md` with its content.

### 6. Create GitHub Actions workflow

Create `.github/workflows/docs.yml`:

```yaml
name: Deploy Docs

on:
  push:
    branches: [main]
    paths:
      - "docs/**"
      - "mkdocs.yml"
      - "pyproject.toml"
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --dev
      - run: uv run mkdocs build
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

If the project does not use `uv`, replace the `uv` steps with:

```yaml
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - run: pip install mkdocs mkdocs-material
      - run: mkdocs build
```

Only create this file if a GitHub remote exists.
Check for existing workflow files first:

```
ls .github/workflows/docs*.yml .github/workflows/pages*.yml 2>/dev/null
```

If one exists, report it and skip.

### 7. Add .gitignore entries

Check if `site/` is in `.gitignore`. MkDocs outputs to `site/` by default.

```bash
grep -q "^site/" .gitignore 2>/dev/null || echo "site/" >> .gitignore
```

### 8. Verify the build

Run a local build to confirm everything works:

```bash
uv run mkdocs build
```

If it fails, fix the issue and retry.
Report success or the error.

### 9. Report

Present the summary to the user.

## Output Format

```markdown
## Docs Site Setup — {TODAY}

### Dependencies Installed
- mkdocs: <version>
- mkdocs-material: <version>

### Files Created
| File | Status |
|---|---|
| mkdocs.yml | created / already existed |
| docs/index.md | created / already existed |
| docs/getting-started.md | created / already existed |
| docs/reference/index.md | created / already existed |
| docs/changelog.md | created / skipped (no CHANGELOG.md) |
| docs/architecture.md | created / skipped (no .sdlc/context/architecture.md) |
| .github/workflows/docs.yml | created / already existed / skipped (no GitHub remote) |
| .gitignore | updated / already had site/ |

### Local Build
- mkdocs build: passed / failed (<error>)

### Next Steps
1. Run `uv run mkdocs serve` to preview locally at http://localhost:8000
2. Commit and push to trigger the GitHub Pages deployment
3. In GitHub repo Settings > Pages, set Source to "GitHub Actions"
4. Run `/create-documentation` to write substantive content for each section
5. Run `/find-documentation-gaps` to identify missing API docs
```

## Example Usage

**Scenario 1: New Python project**
```
/setup-docs-site
```
Installs mkdocs and mkdocs-material, creates mkdocs.yml with Material theme, scaffolds docs/ with index, getting-started, reference stubs, creates .github/workflows/docs.yml for GitHub Pages, adds site/ to .gitignore, verifies the build.

**Scenario 2: Project already has docs/ directory**
```
/setup-docs-site
```
Detects existing docs/, creates mkdocs.yml, preserves existing markdown files, only adds missing files (getting-started.md, reference/index.md), creates the GHA workflow.

**Scenario 3: No GitHub remote**
```
/setup-docs-site
```
Sets up MkDocs and docs/ content but skips the GHA workflow. Reports that Pages deployment requires a GitHub remote.

**Scenario 4: Everything already exists**
```
/setup-docs-site
```
Reports that mkdocs.yml, docs/, and the workflow already exist. Offers to update mkdocs.yml with any missing extensions or plugins.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `create-documentation` | Writes documentation content (tutorials, how-tos, reference, explanation) for features. Use after setup-docs-site scaffolds the infrastructure. |
| `find-documentation-gaps` | Finds undocumented public APIs. Run after setup-docs-site to identify what reference docs are missing. |
| `sync-repository` | Can invoke setup-docs-site as an optional phase when no docs infrastructure exists. |
| `write-readme` | Generates README.md. setup-docs-site derives docs/index.md from README content. |
| `divio-documentation` | Provides the documentation framework guidelines that create-documentation follows. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `uv run mkdocs serve` | Local preview at http://localhost:8000 with live reload |
| `uv run mkdocs build` | Build static site to site/ directory |
| `uv add --dev mkdocs mkdocs-material` | Add MkDocs dependencies |
