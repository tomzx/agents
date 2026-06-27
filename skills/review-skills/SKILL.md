---
name: review-skills
description: Audit a skill directory for duplicates, broken references, circular dependencies, orphaned skills, composability issues, and skill gaps. Use when the user says /review-skills or wants to audit their skill library.
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "[skills-directory]"
---

# Review Skills

Audits a directory of skills for structural and semantic issues across seven categories: duplicates, broken references, circular dependencies, orphaned skills, composability, re-run safety, and skill gaps.
Produces a prioritized report with concrete remediation steps.

## Prerequisites

- A directory containing skill subdirectories, each with a `SKILL.md` file
- If no directory is provided, infer the active skill directory from the current agent/harness configuration (see Step 1)

## What Gets Checked

| Category | Description |
|----------|-------------|
| Duplicates | Skills with overlapping or identical purpose, name, or description |
| Broken references | Cross-references to skills, files, or tools that do not exist |
| Circular dependencies | Chains of skill invocations that form a cycle |
| Orphaned skills | Skills never referenced or invoked by any other skill |
| Composability | Skills that cannot be composed because of conflicting interfaces, missing prerequisites, or incompatible tool constraints |
| Re-run safety | Skills that may behave incorrectly or destructively when invoked multiple times on the same inputs |
| Skill gaps | Common agent workflows that lack a corresponding skill |

## Steps

### 1. Determine the skills directory

If `$1` is provided, use it.
Otherwise, locate the active skill directory by checking in order:

1. `.opencode/skills/` in the current repository root
2. `~/.opencode/skills/`
3. `.claude/skills/` in the current repository root
4. `~/.claude/skills/`

If none exist, report the error and stop.

Validate that the chosen directory contains at least one `SKILL.md`:

```bash
find "$SKILLS_DIR" -mindepth 2 -name "SKILL.md" -type f | head -1
```

### 2. Build the skill index

For every `SKILL.md` in the directory, extract:

- **name** from frontmatter `name` field
- **description** from frontmatter `description` field
- **allowed-tools** from frontmatter (if present)
- **argument-hint** from frontmatter (if present)
- **directory name** (the folder containing the SKILL.md)
- **section headers** (all `##` and `###` headings)
- **line count**
- **references to other skills** (see extraction rules below)
- **referenced by** (populated by cross-referencing in step 3)

Reference extraction: scan each SKILL.md for these patterns:

1. **Slash-invocations**: `/skill-name` in prose, code blocks, or workflow diagrams
2. **Relative file links**: `../skill-name/SKILL.md` or `./skill-name/SKILL.md`
3. **Prose mentions**: "invoke `skill-name`", "delegates to `skill-name`", "run `skill-name`"
4. **Invocation by description**: "the reproduce-issue skill", "arxiv-article for each URL"

For each reference, record the target skill name and whether the reference is a call (the invoking skill delegates work) or a mention (the invoking skill just names the other skill for context).

### 3. Check for duplicates

Compare every pair of skills:

1. **Exact name collision**: two skills with the same `name` in frontmatter
2. **Near-duplicate names**: names that differ only by hyphen/underscore, singular/plural, or a common suffix (e.g., `create-pr` vs `create-pr-description`)
3. **Overlapping descriptions**: descriptions that describe the same workflow or purpose, even with different names
4. **Near-identical content**: skills whose section headers and step descriptions overlap substantially (>60% of sections in common and same general purpose)

For each duplicate found, classify:

| Type | Condition | Recommendation |
|------|-----------|----------------|
| **Exact duplicate** | Same name, same purpose | Merge into one |
| **Name collision** | Same name, different purpose | Rename one |
| **Near-duplicate** | Different name, same purpose | Merge or clarify scope boundaries |
| **Sibling** | Different name, overlapping purpose with clear scope split | Document the boundary explicitly |

### 4. Check for broken references

For every skill-to-skill reference found in Step 2:

1. Resolve the target name against the skill index
2. Flag as **broken** if no skill with that name exists
3. Flag as **ambiguous** if the name matches multiple skills (partial match)
4. For relative file references (`../foo/SKILL.md`), verify the file actually exists at that path

Also check:

- Tool references in `allowed-tools` that do not exist or are misformatted
- Environment variable references (`${VAR}`, `$VAR`) that are not explained in a Prerequisites section
- Script references (`scripts/get-env`, etc.) where the script path is not documented or verified
- External URLs that appear malformed (basic syntax check only, do not fetch)

### 5. Check for circular dependencies

Build a directed graph where edge A -> B means "skill A invokes/calls skill B".
Detect cycles using standard graph traversal (DFS with back-edge detection).

For each cycle found:

1. List the full cycle chain
2. Determine if the cycle is **intentional** (e.g., a retry loop like `handle-pr-ci` -> `handle-pr-ci`) or **unintentional**
3. For unintentional cycles, suggest where to break the cycle (usually the weakest dependency)

Also check for **excessively long chains**: a path of more than 5 skill invocations without reaching a leaf skill. Flag these as a maintainability concern.

### 6. Check for orphaned skills

A skill is **orphaned** if:

1. No other skill references it (by slash-invocation, prose mention, or relative link)
2. It is not listed as a sub-skill in any orchestrator skill (like `sdlc` or `fix-issue`)
3. It is not referenced in any configuration file that maps skill names to triggers (e.g., the agent's available skills list)

**Not all orphans are problems.** A skill that is meant to be invoked directly by the user (not composed into a pipeline) is not orphaned, it is a top-level entry point.
To distinguish, check if the skill's description suggests direct user invocation (contains phrases like "Use when the user says", "triggered when", or lists a `/command` in its description).

Classify orphans:

| Type | Condition | Action |
|------|-----------|--------|
| **True orphan** | Never referenced, not a user-facing entry point | Consider removing or integrating |
| **Undiscovered entry point** | Not referenced but designed for direct invocation | Document in an orchestrator or index |
| **Deprecated** | Not referenced and description mentions deprecation | Remove |

### 7. Check composability

For each pair of skills that reference each other (A calls B), verify:

1. **Interface compatibility**: If A passes arguments to B, does B's `argument-hint` accept those arguments?
2. **Prerequisite compatibility**: If A requires tool X and B requires tool Y, are both available when A calls B? Check `allowed-tools` for conflicts.
3. **Output compatibility**: If A consumes B's output, does B actually produce that output? Check B's output format section against what A expects.
4. **Side effect conflicts**: Do A and B both modify the same files or resources in incompatible ways (e.g., both write to the same output file with different formats)?
5. **Environment compatibility**: Do A and B require different environment variables or working directory states?

Flag any pair where composability is broken or uncertain.

### 8. Check re-run safety

For each skill, determine whether it is safe to invoke multiple times with the same arguments. A skill is re-run safe if repeating it produces the same result without data loss, duplication, or corruption.

Check for these signals in the skill's steps and output format:

1. **Idempotent writes**: Does the skill overwrite its output file unconditionally, or does it append? Overwrite is safe; append on re-run produces duplicates.
2. **State mutation**: Does the skill create git branches, push commits, open PRs, or create issues? If so, does it check whether the resource already exists before creating it? (e.g., `git rev-parse --verify <branch>` before `git checkout -b`)
3. **External side effects**: Does the skill post comments, send messages, or make API calls? Does it check for existing comments/messages before posting?
4. **Cleanup on failure**: If the skill fails partway through, does it leave behind partial state (branches, temp files, draft PRs)? Does it document rollback or cleanup steps?
5. **Convergence**: If the skill is run again after a previous successful run, does it converge to the same end state, or does it produce new artifacts each time?

Classify each skill:

| Rating | Condition |
|--------|-----------|
| **Safe** | Overwrites output, checks before mutating external state, or has no side effects |
| **Caution** | May duplicate output or create redundant artifacts on re-run, but no data loss |
| **Unsafe** | Will create duplicate PRs, duplicate comments, or corrupt state on re-run |

For skills rated Caution or Unsafe, suggest a specific fix (e.g., "check for existing branch before creating", "use overwrite instead of append", "add existence check before `gh issue create`").

### 9. Check for skill gaps

Analyze the skill library holistically:

1. **Workflow coverage**: Identify common agent workflows that have no corresponding skill:
   - Every `create-X` should have a matching `review-X` (and vice versa)
   - Every major phase in the SDLC (or similar pipeline) should have a skill
   - Common operations (commit, push, merge, deploy) should be covered
   - Cross-cutting concerns (logging, error handling, security) should have skills
2. **Missing review pairs**: List `create-*` skills with no corresponding `review-*` (and the reverse)
3. **Missing orchestration**: If there are many granular skills but no orchestrator that chains them, note the gap
4. **Missing documentation**: Skills without an Example Usage section or without an output format template
5. **Missing prerequisites**: Skills that reference tools, scripts, or environment variables without listing them in Prerequisites

### 10. Prioritize findings

Rank each finding using this priority scheme:

| Priority | Criteria |
|----------|----------|
| **Critical** | Broken reference that will cause a skill to fail at runtime; circular dependency that causes infinite loops |
| **High** | Duplicate that confuses the agent; composability issue between frequently composed skills; missing prerequisites |
| **Medium** | Orphaned skill; near-duplicate that adds maintenance burden; missing review pair; skill gap in a common workflow; re-run safety concern without data loss |
| **Low** | Missing documentation; stylistic inconsistency; long chain that could be simplified; re-run creates minor duplicates |

### 11. Print the report

```
## Skill Library Review — {SKILLS_DIR}

### Summary

- Total skills: N
- Skills with references to other skills: N
- Skills referenced by others: N
- Orphaned skills: N
- Total findings: N (N critical, N high, N medium, N low)

### Duplicates

| Skill A | Skill B | Type | Recommendation | Priority |
|---------|---------|------|----------------|----------|
| `<name-a>` | `<name-b>` | exact/near/sibling | <merge/rename/document> | critical/high/medium/low |

<Or "No duplicates found.">

### Broken References

| Source Skill | Reference | Target | Issue | Priority |
|-------------|-----------|--------|-------|----------|
| `<skill-name>` | `<what was referenced>` | `<resolved target or NOT FOUND>` | <not found / ambiguous / file missing> | critical/high/medium/low |

<Or "No broken references found.">

### Circular Dependencies

| Cycle | Intentional? | Break At | Priority |
|-------|-------------|----------|----------|
| `A → B → C → A` | yes/no | `<suggested skill>` | critical/high/medium/low |

<Or "No circular dependencies found.">

### Orphaned Skills

| Skill | Type | Action | Priority |
|-------|------|--------|----------|
| `<name>` | true orphan / undiscovered entry point / deprecated | <remove / document / keep> | medium/low |

<Or "No orphaned skills found.">

### Composability Issues

| Skill A | Skill B | Issue | Priority |
|---------|---------|-------|----------|
| `<name-a>` | `<name-b>` | <interface mismatch / prerequisite conflict / output mismatch / side effect conflict> | high/medium/low |

<Or "No composability issues found.">

### Re-run Safety

| Skill | Rating | Risk | Suggested Fix | Priority |
|-------|--------|------|---------------|----------|
| `<name>` | safe / caution / unsafe | <what happens on re-run> | <specific fix> | critical/high/medium/low |

<Or "All skills are re-run safe.">

### Skill Gaps

| Gap | Description | Suggested Name | Priority |
|-----|-------------|----------------|----------|
| Missing review pair | `create-X` has no `review-X` | `review-X` | medium |
| Missing orchestration | <workflow without an orchestrator> | `<suggested-name>` | medium |
| Missing documentation | `<skill>` has no examples | n/a | low |
| Uncovered workflow | <description of workflow> | `<suggested-name>` | medium |

<Or "No skill gaps found.">

### Statistics

| Metric | Value |
|--------|-------|
| Total skills | N |
| Avg lines per skill | N |
| Skills with examples | N |
| Skills with prerequisites | N |
| Skills with allowed-tools | N |
| Skills with argument-hint | N |
| Skills referencing others | N |
| Max dependency depth | N |
| Skills with review pairs | N / N create skills |
| Skills re-run safe | N safe, N caution, N unsafe |

### Adoption Checklist

Prioritized list of actions to take:

1. [CRITICAL] <action>
2. [HIGH] <action>
3. [MEDIUM] <action>
...
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

## Example Usage

**Scenario 1: Audit the default skills directory**
```
/review-skills
```
Scans `.opencode/skills/`, finds 3 broken references where skills were renamed, 1 circular dependency between `handle-pr-ci` and itself (intentional retry), and 2 skills missing review pairs.

**Scenario 2: Audit a specific directory**
```
/review-skills ~/.claude/skills
```
Scans the user's Claude skills directory, finds a near-duplicate pair (`start-day` vs `start-morning`) and an orphaned skill `old-deploy` that is no longer referenced.

**Scenario 3: Compare skill library health over time**
```
/review-skills
```
Run periodically to track the health of the skill library. The statistics section provides metrics to compare across runs.
