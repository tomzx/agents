---
name: update-sdlc-templates
description: Update .sdlc/templates/ with the latest canonical best practices, merging intelligently with any user customizations.
argument-hint: "[project-root]"
---

# Update SDLC Templates

Compares each file in `.sdlc/templates/` against the corresponding canonical template in `../sdlc/templates/` (relative to this skill).
Templates that the user has not modified are updated automatically.
Templates with user customizations are merged intelligently, preserving the user's additions while incorporating upstream structural improvements.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/templates/` directory exists (run `/initialize-sdlc-directory` first if not)
- The canonical templates at `../sdlc/templates/` relative to this skill file

## Steps

1. Determine the project root: use `$1` if provided, otherwise use the current working directory.

   **SDLC_DIR resolution:** Apply `sdlc/references/shared.md` for `.sdlc/templates/` paths (repo first, then `$SDLC_DIR/{owner}/{repository}/.sdlc/templates/`; mirror writes when set).

2. For each canonical template, read both versions:
   - **Canonical:** `../templates/<path>` (the upstream default)
   - **Installed:** `.sdlc/templates/<path>` (the project's copy, resolved via SDLC_DIR)

3. Classify each template into one of three states:

   | State | Condition | Action |
   |---|---|---|
   | **Up to date** | Installed matches canonical exactly | No action needed |
   | **Unmodified** | Installed differs from canonical but contains only placeholder text (no real content has been filled in) | Overwrite with canonical |
   | **Customized** | Installed has real content that differs from canonical | Merge (see below) |

4. For **customized** templates, perform an intelligent merge:
   - Preserve sections the user has written or renamed
   - Add new sections present in the canonical that are absent in the installed version
   - Update structural improvements (column renames, reordered frontmatter fields) without disturbing user content
   - If a merge would lose content or is ambiguous, report the conflict and leave the file unchanged

5. If any new canonical templates do not exist in `.sdlc/templates/` at all, create them (same as step 3 of `/initialize-sdlc-directory`).

6. Report the outcome for every template.

## Output Format

```
## SDLC templates updated

### Up to date (no changes)
- features/requirements.md

### Updated automatically (unmodified)
- features/tests.md  — added "Edge Cases" section

### Merged (customizations preserved)
- features/specification.md  — added "Constraints" section; kept your "API Contracts" section

### Conflicts (manual resolution required)
- features/plan.md  — upstream removed "Timeline" table; your version has content there. Resolve manually.

### New templates added
- features/questions.md
```

## Merge Principles

- **Additive first:** only add; never remove a section the user has filled in.
- **Structural changes are safe:** renaming an empty column header, adding a new frontmatter field, or reordering empty sections can be applied without risk.
- **Content changes require judgement:** if canonical changed a section's purpose (not just its structure), surface it as a conflict rather than silently overwriting.
- **When in doubt, conflict:** a false conflict is easy to resolve; a silent data loss is not.

## Example Usage

**Scenario 1: Routine upgrade**
```
/update-sdlc-templates
```
Pulls in structural improvements from the latest canonical templates. User's project-specific content (filled-in sections, renamed columns) is preserved.

**Scenario 2: After cloning a new version of agents**
The canonical templates may have new sections or revised frontmatter.
Run `/update-sdlc-templates` to propagate changes to the project's `.sdlc/templates/` without discarding earlier customizations.
