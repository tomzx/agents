---
name: improve-skill
description: Inspect a single skill in the library, reason about high-value low-risk improvements, and apply them directly. Used by the Skill Refresher workflow and invocable directly as /improve-skill <skill-name>.
allowed-tools: Bash, Read, Glob, Grep, Edit, Write
argument-hint: "<skill-name>"
---

TODAY=!`date +%Y-%m-%d`

# Improve Skill

Inspects one skill end to end, reasons about concrete improvements, and applies them in place. Designed for the Skill Refresher workflow that improves a random skill every day, but also useful when a human points it at a specific skill that feels weak.

## Prerequisites

- Working directory is the root of the `tomzx/agents` repository (the skill library root)
- `$1` — the name of the skill directory under `skills/` to improve (e.g. `git-commit`)
- The target skill exists at `skills/$1/SKILL.md`

## What Counts as an Improvement

Keep only improvements that are high-value and low-risk. Prefer concrete, surgical edits over rewrites.

| Category | What to Look For |
|----------|-----------------|
| Clarity and precision | Steps that are ambiguous, easy to get wrong, or could be misread by an agent |
| Completeness | Missing prerequisites, steps, edge cases, error handling, or acceptance checks |
| Correctness | Examples, commands, or file paths that are wrong, outdated, or would fail if followed literally |
| Examples and templates | Missing, vague, or broken example usage, output format templates, or code blocks |
| Structure | Poor section ordering, redundant sections, verbosity, or content that should be split or merged |
| Frontmatter | Description that does not match the body, missing `allowed-tools` or `argument-hint`, broken `argument-hint` signature |
| References | Broken cross-references to other skills, files, scripts, or environment variables |
| Safety | Missing guards before destructive actions, re-run safety concerns, rollback guidance |

## What Counts as Churn (Avoid)

Do not change things for the sake of change. These are not improvements:

| Anti-pattern | Why to Avoid |
|--------------|--------------|
| Rewriting working prose into different working prose | Adds review burden with no functional gain |
| Introducing new dependencies or tools not used in the project | Bloats the skill with unavailable tools |
| Adding speculative edge cases the skill will never hit | Inflates length without value |
| Restyling or reformatting that does not fix a real problem | Noise in the diff |
| Splitting or renaming sections that are already clear | Breaks muscle memory and references |

## Steps

### 1. Resolve and validate the target skill

```
SKILL=$1
```

If `$1` is empty, report the error and stop. Confirm the skill exists:

```bash
test -f "skills/$SKILL/SKILL.md" && echo "target: skills/$SKILL"
```

### 2. Understand the skill

Read every file in `skills/$SKILL/`, starting with `SKILL.md`. Read `AGENTS.md` at the repository root for repo conventions (concise, no em-dashes, one sentence per line). Skim one or two neighboring skills under `skills/` to calibrate house style and section conventions.

### 3. Reason about improvements

Evaluate the target skill against every category in "What Counts as an Improvement" above. For each candidate improvement, ask:

1. Does it fix a real problem a reader or the agent would actually hit?
2. Is it low-risk (small, localized, no new dependencies)?
3. Does it respect repo conventions?

Discard anything that fails any of these checks. Prioritize correctness fixes (broken commands, wrong paths) over clarity and style.

### 4. Apply changes

Edit only what passed the checks in Step 3. Follow repo conventions exactly:
- Concise, one sentence per line where applicable
- No em-dashes, use commas or parentheses instead
- No comment noise
- Match the existing section style and frontmatter of neighboring skills

### 5. Hard constraint

Modify ONLY files inside `skills/$SKILL/`. Do not create, move, rename, or edit any file outside that directory. Do not change `AGENTS.md`, other skills, workflows, or configuration.

### 6. Verify the result

Re-read the edited skill end to end and confirm:

- The frontmatter is still valid (name, description, and any `allowed-tools`/`argument-hint` parse correctly)
- No broken references were introduced
- Code blocks and commands are syntactically valid
- The diff is entirely contained within `skills/$SKILL/`

```bash
git diff --name-only | grep -v "^skills/$SKILL/" && echo "::error::Edit escaped the skill directory" || echo "All changes confined to skills/$SKILL/"
```

If any change escaped the skill directory, revert it.

### 7. Summarize

Print a short summary of what changed and why, or state clearly that the skill needed no changes:

```
## Improve Skill — {SKILL} ({TODAY})

- <change>: <why>
- <change>: <why>

Or: No changes needed. The skill is already clear, correct, and complete.
```

## Example Usage

**Scenario 1: Improve a specific skill**
```
/improve-skill git-commit
```
Reads `skills/git-commit/`, finds that the commit message format example uses a deprecated scope syntax and that the "Types" list omits `perf`, and applies both fixes.

**Scenario 2: Called by the Skill Refresher workflow**
```
/improve-skill review-tests
```
The workflow picked `review-tests` at random. The skill adds a missing acceptance-checks section and fixes a code block that references a nonexistent script.

**Scenario 3: No changes needed**
```
/improve-skill find-dead-code
```
After review, the skill is already clear, correct, and complete. Reports "No changes needed" and exits without editing.
