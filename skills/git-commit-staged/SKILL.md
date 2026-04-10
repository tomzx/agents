---
name: git-commit-staged
description: Generate a git commit message based on the staged changes in the repository.
---

# Generate Git Commit from Staged Changes

Generates a Conventional Commits-formatted commit message from only the staged changes, leaving unstaged changes untouched.

## Prerequisites

- `git` repository with at least one staged change (`git add` already run)
- Working directory is the root of the repository

## Steps

1. Review staged changes only:
   ```
   git diff --staged
   ```
2. Draft a commit message following the format below.
3. Commit the staged changes:
   ```
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

**Scenario 1: Partial commit - only test changes staged**
Staged: `tests/test_auth.py`. Unstaged: `src/auth.py`.
Commit: `test(auth): add unit tests for JWT validation`

**Scenario 2: Config change staged**
Staged: `pyproject.toml` adding a new dependency.
Commit: `chore(deps): add structlog dependency`

**Scenario 3: Multi-file feature staged**
Staged: `src/payments.py` and `migrations/0042_payments.sql`.
```
feat(payments): add Stripe payment processing

Introduces PaymentService class and corresponding DB migration
for the payments table.
```

## Useful Commands Reference

| Command | Description |
|---|---|
| `git diff --staged` | Show only staged changes |
| `git status` | Show staged vs unstaged file status |
| `git commit -m "<message>"` | Commit staged changes with a message |
| `git log --oneline -10` | Show recent commits for style reference |
