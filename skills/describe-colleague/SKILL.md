---
name: describe-colleague
description: Generate a profile for a colleague based on their Slack and GitHub activity, covering strengths, weaknesses, interests, avoids, and other relevant information.
argument-hint: "[colleague]"
---

BASE_DIR=!`scripts/get-env NOTES_DIR`

# Describe Colleague

Generates a structured profile for a colleague by synthesizing their Slack and GitHub activity, capturing strengths, weaknesses, interests, and avoidances.

## Prerequisites

- Slack MCP server connected and authenticated
- `gh` CLI authenticated
- `NOTES_DIR` environment variable set (resolved via `scripts/get-env NOTES_DIR`)
- Colleague identifier (`{COLLEAGUE}`) provided as argument or from context

## Steps

1. Retrieve `NOTES_DIR` from environment:
   ```
   scripts/get-env NOTES_DIR
   ```
2. Search GitHub for the colleague's contributions using `gh`:
   ```
   gh search commits --author={COLLEAGUE} --limit 50
   gh search prs --author={COLLEAGUE} --limit 50
   ```
3. Review their Slack messages and threads via the Slack MCP server. Do not read local files.
4. Synthesize observations into the profile format below.
5. Write the profile to `{BASE_DIR}/colleagues/{COLLEAGUE}.md`.

## Output Format

```markdown
# Strengths

- <strength>

# Weaknesses

- <weakness>

# Interests

- <topic>

# Avoids

- <topic>

# Other relevant information

- <item>
```

## Example Usage

**Scenario 1: Profile a specific colleague**
```
/describe-colleague alice
```
Searches GitHub for alice's commits and PRs, reviews her Slack messages, then writes a profile to `{NOTES_DIR}/colleagues/alice.md`.

**Scenario 2: Update an existing profile**
```
/describe-colleague bob
```
If `{NOTES_DIR}/colleagues/bob.md` already exists, overwrite it with a refreshed profile incorporating recent activity.

**Scenario 3: Colleague with limited GitHub activity**
```
/describe-colleague carol
```
Carol's contributions are primarily via Slack. Profile is weighted toward Slack observations, with a note that GitHub data is sparse.

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `gh search commits --author=<user> --limit 50` | Fetch recent commits by a user |
| `gh search prs --author=<user> --limit 50` | Fetch recent PRs authored by a user |
