---
name: compare-skills
description: Compare skills between two directories (mine and theirs) to identify best practices from "theirs" that can be adopted into "mine". Produces a prioritized list of improvements with concrete suggestions.
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "<mine-dir> <theirs-dir>"
---

TODAY=!`date +%Y-%m-%d`

# Compare Skills

Compares the skill libraries in two directories, identifies best practices present in "theirs" but missing or weaker in "mine", and produces a prioritized adoption plan.

## Prerequisites

- Two directories containing skill libraries, each with `SKILL.md` files in subdirectories
- `<mine-dir>` — your skill directory (the one to improve)
- `<theirs-dir>` — the reference skill directory (the one to learn from)

## What Counts as a Best Practice

| Category | What to Look For |
|----------|-----------------|
| Structural patterns | Consistent frontmatter fields, section ordering, standard sections (Prerequisites, Steps, Output Format, Examples) |
| Instruction quality | Specificity of steps, use of code blocks, error handling guidance, edge case coverage |
| Reusability | Parameterization via arguments or environment variables, `!` template syntax for dynamic values |
| Completeness | Prerequisites section, example usage scenarios, useful commands reference, next steps |
| Safety | Guardrails, validation steps, rollback guidance, confirmation prompts before destructive actions |
| Observability | Logging guidance, output formatting, status reporting |
| Tool usage | `allowed-tools` frontmatter, appropriate tool constraints, tool-specific tips |

## What Counts as a Removal Candidate

Patterns in "mine" that "theirs" has evolved away from or that are demonstrably harmful:

| Category | Signals |
|----------|---------|
| Over-constraint | Instructions that micromanage the agent (e.g., prescribing exact phrasing, mandating specific library versions in prose) where theirs delegates judgement |
| Redundancy | Instructions duplicated across sections, or content repeated in multiple skills that theirs consolidates |
| Stale assumptions | Hardcoded paths, version pins, or tool names that may be outdated; theirs uses dynamic values or omits them |
| Vague handwaving | Steps like "handle errors appropriately" or "do the right thing" with no specificity; theirs either removes these or makes them concrete |
| Boilderplate noise | Large copy-pasted blocks that add no instructional value (license headers, repeated disclaimers, decorative formatting) |
| Premature optimization | Instructions that optimize for edge cases the agent handles naturally, bloating the skill without benefit |
| Anti-patterns from theirs | Patterns present in mine that theirs explicitly avoids (e.g., mine uses `cd &&` chains, theirs uses `workdir`; mine hardcodes values, theirs uses `!` syntax) |

## What Counts as a Disagreement

Conflicting instructions that pull the agent in different directions. These are higher priority than removal candidates because they actively cause wrong behavior.

| Scope | What to Detect | Example |
|-------|---------------|---------|
| Intra-skill (within one skill) | A step says one thing, a later step or output format template says the opposite | Step 3 says "always ask before committing" but Output Format shows auto-commit |
| Inter-skill (across mine) | Two skills in mine give incompatible instructions for overlapping scenarios | Skill A says "use conventional commits"; Skill B says "write one-line commit messages" |
| Cross-library (mine vs theirs) | For the same skill, mine and theirs prescribe different approaches with no clear reason for the divergence | Mine: "use `find` for file discovery"; Theirs: "use `Glob` tool, never `find`" |
| Tone / style conflicts | One section demands brevity, another demands exhaustive detail | Preamble says "be concise" but Steps say "document every edge case exhaustively" |
| Tool conflicts | Skill tells the agent to use one tool, but the code examples use a different one | Prose says "use `uv`" but code blocks show `pip install` |

## Steps

### 1. Parse Arguments

```
MINE_DIR=$1
THEIRS_DIR=$2
```

Validate both directories exist and contain at least one `SKILL.md`. If arguments are missing or directories are invalid, report the error and stop.

### 2. Inventory Skills

List all skills in both directories:

```
find $MINE_DIR -name "SKILL.md" -type f | sort
find $THEIRS_DIR -name "SKILL.md" -type f | sort
```

### 3. Build Skill Maps

For each skill in both directories, extract:
- **Name** (from frontmatter `name` field)
- **Description** (from frontmatter `description` field)
- **Frontmatter fields** present (name, description, allowed-tools, argument-hint, etc.)
- **Section headers** present (Prerequisites, Steps, Output Format, Examples, etc.)
- **Line count** (proxy for thoroughness)
- **Uses dynamic values** (`!` syntax)
- **Has code blocks** (fenced blocks with language hints)
- **Has examples** (scenario-based example usage sections)

### 4. Categorize Relationships

For each skill, determine its relationship across the two directories:

| Relationship | Condition |
|-------------|-----------|
| **Match** | Same skill name exists in both directories |
| **Unique to mine** | Skill exists only in `<mine-dir>` |
| **Unique to theirs** | Skill exists only in `<theirs-dir>` |
| **Similar** | Different name but semantically overlapping purpose (manual judgement based on description comparison) |

### 5. Compare Matched Skills

For each matched pair, compare along these dimensions:

**Frontmatter completeness:**
- Does theirs have `allowed-tools` that mine lacks?
- Does theirs have `argument-hint` that mine lacks?
- Does theirs use additional frontmatter fields?

**Section structure:**
- Sections present in theirs but missing in mine
- Order and flow of sections

**Instruction quality:**
- Specificity and actionability of steps (numbered steps vs vague guidance)
- Use of concrete code examples and commands
- Error handling and edge case coverage
- Validation and verification steps

**Parameterization:**
- Dynamic value usage (`!` syntax)
- Argument handling
- Environment variable usage

**Examples and reference:**
- Example usage scenarios
- Useful commands reference tables
- Output format templates

### 6. Identify Removal Candidates in Mine

For each skill in `<mine-dir>`, check for the removal candidate signals above. Cross-reference with "theirs" where a matched skill exists:

- If theirs omits a section mine has, determine if the omission is intentional (the section adds no value) or a gap in theirs
- If theirs has a cleaner version of the same instruction, flag mine's version as a simplification target
- If mine has content theirs does not, assess whether it is project-specific (keep) or boilerplate noise (remove)
- Flag any instructions in mine that contradict patterns observed as standard in theirs

### 7. Detect Disagreements

Check for conflicting instructions at every scope:

**Intra-skill (within a single skill):**
- Read each skill in mine end to end
- Look for assertions in one section that are violated by code blocks, output templates, or later steps in the same skill
- Common signals: "always X" in prose but output format shows not-X; "never Y" in prerequisites but Step N does Y; argument-hint says one signature but steps describe a different one

**Inter-skill (across skills in mine):**
- Build a topic map: for each skill, extract the key topics it governs (e.g., commit messages, PR descriptions, test structure)
- Where two skills share a topic, compare their instructions for conflicts
- Common signals: different naming conventions, different tool preferences, different required sections

**Cross-library (mine vs theirs on matched skills):**
- For matched pairs, compare the actual instructions not just the structure
- Flag cases where mine and theirs prescribe different approaches to the same step
- Assess which approach is better (clearer, more specific, more aligned with the rest of the library) and recommend which to keep

**Tone/style and tool conflicts:**
- Check if a skill's preamble (or AGENTS.md conventions) sets a tone that the steps violate
- Check if prose mentions a tool by name but code blocks use a different one

For each disagreement found, record: the two conflicting assertions, their locations (file + section), the scope (intra/inter/cross), and a recommendation for which to keep.

### 8. Extract Cross-Cutting Best Practices

Analyze all skills in `<theirs-dir>` for patterns not tied to a single skill:

- **Consistent conventions** used across all their skills (e.g., every skill has an Examples section)
- **Novel frontmatter fields** not used in mine
- **Common structural patterns** (e.g., Prerequisites always listed first, Output Format always before Examples)
- **Reusable techniques** (e.g., confirmation prompts, dry-run modes, progressive disclosure)

### 9. Analyze Unique-to-Theirs Skills

For skills that exist only in `<theirs-dir>`:
- Summarize what the skill does
- Assess whether it fills a gap in `<mine-dir>` or represents a workflow worth adding
- Note any novel patterns or techniques it introduces

### 10. Prioritize Findings

Rank each finding by impact and effort:

| Priority | Criteria |
|----------|----------|
| High | Applies to many skills in mine, easy to adopt, clear benefit |
| Medium | Applies to several skills, moderate effort, notable benefit |
| Low | Applies to few skills, high effort, or marginal benefit |

### 11. Print the Report

```
# Skill Comparison Report — {TODAY}

## Summary

- Mine: N skills in `<mine-dir>`
- Theirs: N skills in `<theirs-dir>`
- Matched skills: N
- Unique to mine: N
- Unique to theirs: N
- Similar skills: N
- Total findings: N (N high, N medium, N low)

## Cross-Cutting Best Practices

### [HIGH] <Practice Name>

**Observation:** What theirs does differently.
**Impact:** Why this matters (which of my skills benefit).
**Suggestion:** Concrete change to make in mine.

<repeat for each cross-cutting finding>

## Matched Skill Comparisons

### <skill-name>

**Dimension where theirs is stronger:**
- <Specific difference>
- <What mine is missing>

**Suggested changes:**
- <Concrete improvement for mine>

<repeat for each matched skill with findings>

## Unique-to-Theirs Skills

| Skill | Description | Gap Filled? | Adoption Priority |
|-------|-------------|-------------|-------------------|
| `<name>` | <one-line summary> | Yes/No | High/Medium/Low |

## Similar Skills (Potential Deduplication or Merge)

| Mine | Theirs | Overlap |
|------|--------|---------|
| `<my-skill>` | `<their-skill>` | <what overlaps> |

## Adoption Checklist

Prioritized list of changes to apply:

1. [HIGH] <change> — affects N skills
2. [HIGH] <change> — affects N skills
3. [MEDIUM] <change> — affects N skills
...

## Removal Candidates

Sections, instructions, or patterns in mine to consider removing or simplifying:

| Skill | Section/Content | Reason | Confidence |
|-------|----------------|--------|------------|
| `<skill-name>` | <what to remove> | <over-constraint / redundancy / stale / boilerplate / vague / anti-pattern> | High/Medium/Low |

Confidence levels:
- **High** — Theirs has the same skill without this content and works well
- **Medium** — The content appears to be noise but no direct evidence from theirs
- **Low** — May be project-specific; needs human judgement

## Disagreements

Conflicting instructions found, sorted by scope and severity:

### Intra-Skill Conflicts

| Skill | Assertion A | Assertion B | Resolution |
|-------|------------|------------|------------|
| `<skill-name>` | Step 2: "always ask before committing" | Output Format: auto-commit shown | <keep A / keep B / clarify conditions> |

### Inter-Skill Conflicts (Across Mine)

| Skill A | Skill B | Topic | A says | B says | Resolution |
|---------|---------|-------|--------|--------|------------|
| `<skill-a>` | `<skill-b>` | commit messages | conventional commits | one-line summaries | <pick one / scope each> |

### Cross-Library Conflicts (Mine vs Theirs)

| Skill | Mine approach | Theirs approach | Recommendation |
|-------|--------------|----------------|----------------|
| `<skill-name>` | <what mine says> | <what theirs says> | <adopt theirs / keep mine / merge> |

## Statistics

| Metric | Mine | Theirs |
|--------|------|--------|
| Total skills | N | N |
| Avg lines per skill | N | N |
| Skills with examples | N | N |
| Skills with output format | N | N |
| Skills with prerequisites | N | N |
| Skills using dynamic values | N | N |
| Skills with allowed-tools | N | N |
```

## Example Usage

**Scenario 1: Compare your skills against a reference repo**
```
/compare-skills ~/.opencode/skills /path/to/reference-repo/skills
```
Finds that the reference repo consistently includes `allowed-tools` frontmatter and Example sections, while yours lacks them on 12 skills. Produces a checklist to add these to each affected skill.

**Scenario 2: Compare two team members' skill sets**
```
/compare-skills ~/my-skills ~/teammate-skills
```
Discovers 5 unique skills in teammate's directory that cover workflows you also perform. Recommends adopting them.

**Scenario 3: Upgrade your skills after pulling upstream changes**
```
/compare-skills ~/.claude/skills ~/.opencode/skills
```
Finds that the upstream `.opencode/skills` has improved output formatting and added error handling sections. Prioritizes which improvements to backport.
