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
