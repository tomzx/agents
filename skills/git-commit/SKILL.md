---
name: git-commit
description: Generate a git commit message based on the changes in the repository.
---

# Generate Git Commit

Generates a Conventional Commits-formatted commit message from all changes in the repository and creates the commit.

## Prerequisites

- `git` repository with uncommitted changes (staged or unstaged)
- Working directory is the root of the repository

## Steps

1. Review all changes:
   ```
   git diff HEAD
   ```
2. Draft a commit message following the format below.
3. Stage and commit:
   ```
   git add <files>
   git commit -m "<type>(<scope>): <description>"
   ```

## Commit Message Format

```
<type>(<scope>): <short description under 72 chars>

<optional body explaining what and why, not how>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Rules:**
- Use imperative mood: "Add feature" not "Added feature"
- Keep subject line under 72 characters
- Separate subject from body with a blank line when a body is included
- Body explains *what* and *why*, not *how*

## Example Usage

**Scenario 1: New feature**
Changes add a user authentication endpoint.
Commit: `feat(auth): add JWT login endpoint`

**Scenario 2: Bug fix with explanation**
Changes fix a null pointer in the order processor.
```
fix(orders): prevent null pointer when cart is empty

Cart can be null for guest users before session is initialized.
```

**Scenario 3: Documentation update**
Changes update README with new setup instructions.
Commit: `docs: update setup instructions for uv`

**Scenario 4: Refactor across multiple files**
Changes restructure the database layer without changing behavior.
Commit: `refactor(db): extract connection pool into separate module`

## Useful Commands Reference

| Command | Description |
|---|---|
| `git diff HEAD` | Show all uncommitted changes |
| `git diff --staged` | Show only staged changes |
| `git add <files>` | Stage specific files |
| `git commit -m "<message>"` | Create a commit with a message |
| `git log --oneline -10` | Show recent commits for style reference |
