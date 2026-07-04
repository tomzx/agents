---
name: supersede-decision
description: Mark an existing decision as superseded by a newer one, updating status in both records and validating the relationship.
argument-hint: "[old-decision new-decision]"
---

# Supersede Decision

Records that one decision replaces another.
Updates the old decision to `Superseded by [N]`, annotates the new decision with the reverse link, and validates that the relationship is sound (no cycles, no re-superseding an already-terminal decision).
Use this instead of editing decision files by hand when a replacement ADR is adopted.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- Two existing decisions under `.sdlc/knowledge/decisions/`: the one being replaced (`old-decision`) and its replacement (`new-decision`).

## Arguments

| Position | Name | Required | Description |
|---|---|---|---|
| 1 | `old-decision` | yes | The decision being replaced. |
| 2 | `new-decision` | yes | The decision that replaces it. |

Both arguments accept a bare number (e.g. `7`) or a filename/path (e.g. `7-use-redis.md`); leading zeros are tolerated when matching (`0007` resolves the same as `7`).
A number resolves to the file `N-<slug>.md` in the decisions directory.

## Steps

1. Resolve both arguments to files under `.sdlc/knowledge/decisions/` (or the project's existing ADR directory, same resolution as `create-decision`), applying the `SDLC_DIR` read fallback in `shared.md` when the repo path is absent.
2. Validate the relationship against the Rules below. Stop and report on any violation; change no files.
3. In the **old** decision, set frontmatter `status: Superseded by [N]` and update the body `**Status:**` line to match. The frontmatter remains the source of truth; the body line is kept in sync for readers.
4. In the **new** decision, add frontmatter `supersedes: N` (only if absent) and a `**Supersedes:** N-<slug>` line directly beneath `**Status:**`.
5. Report the result and emit the outcome.

## Rules

- Refuse if `old-decision` is already `Deprecated` or `Superseded by [...]`. Terminal states cannot be re-superseded; point the caller at the live decision at the head of the chain instead.
- Refuse if `new-decision` is `Deprecated` or `Superseded by [...]`. A retired decision cannot replace a live one.
- Refuse if the two resolve to the same file.
- Refuse a cycle: follow the `supersedes` links from `new-decision` and refuse if any reaches `old-decision` (i.e. the replacement already transitively supersedes the target).
- Edit only status fields. Supersession is a lifecycle transition, not a content revision; do not rewrite context, options, or consequences.

## Output Format

On success:

```markdown
## Superseded

- **3-use-memcached** -> Superseded by 9
- **9-use-redis** -> added reverse link (Supersedes 3)
```

On refusal:

```markdown
## Not superseded

- **3-use-memcached** is already `Superseded by 7`. Re-run against the live decision (7) or its successor.
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `superseded` | Both records updated and the relationship recorded |
| `rejected` | A validation rule failed; no files were changed |
| `unknown` | A decision could not be resolved, or an error occurred |

This skill records lifecycle state, not artifact quality.
It does not gate on review and is safe to run independently of the `create-decision` / `review-decision` pair.

## Example Usage

**Scenario 1: Number arguments**
`/supersede-decision 3 9` marks decision 3 as superseded by 9 and records the reverse link on 9.

**Scenario 2: Filename arguments**
`/supersede-decision 3-use-memcached.md 9-use-redis.md` resolves by filename and behaves identically.

**Scenario 3: Already superseded**
`/supersede-decision 3 9` where 3 already reads `Superseded by 7`. Refused: report the live decision (7) and suggest re-running against it or its successor.

**Scenario 4: Reverse relationship exists**
`/supersede-decision 3 9` where 9 already supersedes 3. Refused as a cycle; the relationship is already recorded in the opposite direction.

**Scenario 5: Pure deprecation, no replacement**
Out of scope. A decision that should retire with no successor is set to `Deprecated` by `/review-decision`.

## Useful Commands Reference

No CLI commands required. This skill edits two Markdown files in place.
