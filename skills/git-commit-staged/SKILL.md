---
name: git-commit-staged
description: Generate a git commit message based on the staged changes in the repository.
---

Generate a git commit based on the staged changes in this repository.

Follow these guidelines for the commit message:
- Use the imperative mood in the subject line (e.g., "Add feature" not "Added feature")
- Keep the subject line under 72 characters
- Use [Conventional Commits](https://www.conventionalcommits.org/) format: `type(scope): description`
  - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Separate the subject from the body with a blank line when a body is needed
- Use the body to explain *what* and *why*, not *how*
