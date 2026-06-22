# General
* Be concise
* Do not use em-dashes, use commas or parentheses instead
* One sentence per line

# Python
* Use uv for package management
* When creating a project, always use the most recent Python LTS version
* Use type hints
* Use pytest for testing
* Use ruff for linting/formatting
* Run tests before committing
* Run linter/formatter before committing
* Create "green path" tests that cover the main functionality
* Use structlog for logging
* When adding dependencies, use `uv add ...` over adding the version directly to pyproject.toml
* Keep __init__.py files minimal/empty, only for package initialization
* Do NOT use/add __all__ in __init__.py files

# Per-repository instructions
* Before working in a git repository, check for per-repository overrides stored outside that repository.
* Find the skills library root by resolving the real path of this AGENTS.md (follow symlinks), then look in its `repositories/` directory, which is a sibling of `skills/`.
* Derive `{owner}/{repository}` from the current repository's GitHub remote URL.
* If `repositories/{owner}/{repository}/AGENTS.md` exists, read and apply it together with these base instructions.
* For forks, symlink `repositories/{fork-owner}/{repository}` to the upstream `repositories/{owner}/{repository}` so both resolve to the same instructions.

# SDLC skills
* The conventions shared across every SDLC skill live in a single file: `skills/sdlc/references/shared.md`, resolved relative to the skills library root (the same root as the `repositories/` directory above).
* Before running any skill that reads or writes under `.sdlc/`, read that file and apply its conventions — they are not repeated in each skill. This covers reading `.sdlc/context/` for artifact style rules and resolving all `.sdlc/` paths via the repo-first `SDLC_DIR` fallback.
