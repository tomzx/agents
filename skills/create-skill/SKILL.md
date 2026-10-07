---
name: create-skill
description: Author a new skill by discovering similar skills, studying their strengths and weaknesses, and synthesizing the best single skill from them. Use when the user says /create-skill, "create a skill", "build a skill", "make a skill for X", or wants a new skill grounded in the best existing examples rather than written from scratch.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
argument-hint: "<skill-name-or-concept>"
---

TODAY=!`date +%Y-%m-%d`

# Create Skill

Authors a new skill by first discovering existing skills that solve a similar problem, studying each one's strengths and weaknesses, then synthesizing the single best skill from what was learned.

The premise is that a skill written from scratch is usually weaker than one built by combining the best techniques already proven across several existing skills.
This skill automates that synthesis.

## Prerequisites

- Working directory is the root of the `tomzx/agents` repository (the skill library root)
- `$1`: the name or concept of the skill to create (e.g. `create-skill`, or "a skill that summarizes meetings")
- The Skills CLI available as `npx skills` for searching and fetching candidates into a temp directory, never installed into this library (its global scope resolves to `~/.agents/skills`)
- No skill with the chosen name already exists at `skills/$1/SKILL.md`

## How This Skill Relates to Others

| Skill | Relationship |
|-------|--------------|
| `find-skills` | Delegated to for discovery. Its search logic (local library scan plus `npx skills find`) is the input to this skill. |
| `compare-skills` | Borrows the evaluation dimensions (instruction quality, structure, completeness, safety) for scoring candidates. |
| `improve-skill` | Shares the definition of "high-value, low-risk" and the hard constraint of confining edits to one skill directory. |
| `review-skills` | The new skill is checked against its duplicate detector at the end so the synthesis does not collide with an existing skill. |

## What Counts as a Strong Synthesis

A good synthesis takes the strongest part from each candidate and combines them into one coherent skill, not a patchwork of copied sections.

| Quality | What to Look For |
|---------|------------------|
| Best-of-breed sections | Take the clearest prerequisites, the most specific steps, the best output template, and the strongest examples, even if each comes from a different candidate |
| Conflict resolution | When candidates disagree, pick the approach that is clearer, more specific, and better aligned with the rest of the library, and record why |
| Structural coherence | One consistent voice, one section ordering, one frontmatter style, matching the house conventions of neighboring skills |
| Coverage | The union of edge cases and error handling from all candidates, deduplicated and pruned to what is realistic |
| Conventions | Repo style applied throughout: one sentence per line, no em-dashes, concise prose, correct frontmatter |

## What Counts as Churn (Avoid)

| Anti-pattern | Why to Avoid |
|--------------|--------------|
| Wholesale copy of one candidate | Defeats the purpose of synthesis and imports the candidate's weaknesses wholesale |
| Pasting sections back to back | Produces a patchwork with duplicated instructions, shifting voice, and broken cross-references |
| Speculative features the candidates lacked | Makes the skill larger with unproven edge cases; add only what the candidates justify |
| Renaming the concept mid-flight | Breaks the filename, frontmatter name, and README entry in one go |
| Importing external dependencies | A skill only works if it relies on tools already available in this environment |
| Installing candidates into this library | `npx skills add` writes into the project's `.agents/skills/`, and its global scope (`-g`) resolves to `~/.agents/skills`, which on this machine is a symlink to this repository; a global install therefore lands in `skills/<name>/` and overwrites any skill of the same name. Fetch candidates into a temp directory instead |

## Steps

### 1. Resolve and name the target skill

```
SKILL=$1
```

If `$1` is empty, ask the user for the skill's purpose and propose a kebab-case name, then confirm.
If `$1` already exists as a directory under `skills/`, stop and tell the user to run `/improve-skill $1` instead.

Normalize the name to kebab-case if needed.
Confirm the name does not already exist:

```bash
test -e "skills/$SKILL" && echo "::error::skills/$SKILL already exists" || echo "target: skills/$SKILL"
```

### 2. Discover candidate skills

Run the discovery step in two places.

**Local library.** Find skills whose name or description overlaps the concept:

```bash
grep -rli -e "$SKILL" skills/*/SKILL.md
```

Read the `name` and `description` of every match and keep those whose purpose genuinely overlaps, not merely those that mention the word.

**External ecosystem.** Search the open skills registry:

```bash
npx skills find "$SKILL"
```

Also browse the [skills.sh leaderboard](https://skills.sh/) for well-known skills in the field.
Search only: never install candidates into this library (see Step 3).

Collect the top candidates (typically three to six).
Record for each: source, install count, GitHub stars, and a one-line summary of what it does.
Apply the `find-skills` quality bar: prefer official sources and 1K+ installs; be skeptical of repos under 100 stars.

### 3. Gather the candidate sources

For each candidate, obtain the full `SKILL.md`:

- **Local**: read `skills/<name>/SKILL.md` directly, plus any files in its `references/` subdirectory if present.
- **External**: fetch the skill with the skills CLI into a temp location outside this repository, or read it without installing at all.

To read just the `SKILL.md`, use the non-installing form, which prints it to stdout:

```bash
npx skills use <owner>/<repo>@<skill>
```

When you also need the candidate's `references/` files, install it into a throwaway directory so the project scope is that directory rather than this repo:

```bash
CANDIDATE_DIR="/tmp/opencode/create-skill-candidates/<owner>-<repo>-<skill>"
mkdir -p "$CANDIDATE_DIR" && cd "$CANDIDATE_DIR"
npx skills add <owner>/<repo> --skill <skill> -y --copy
# files land in ./.agents/skills/<skill>/, read SKILL.md and references/ from there
```

Never run `npx skills add` from the library root, never pass `-g`, and never run `npx skills update` here.
The global scope resolves to `~/.agents/skills`, which on this machine is a symlink to this repository, so a global install writes straight into `skills/<name>/` and overwrites any skill sharing the name.
The CLI is used here only to search and to read candidates into scratch space outside the repo.

If fewer than two usable candidates are found, say so and fall back to writing the skill from first principles using one or two neighboring skills as a style reference.
Note that no synthesis basis existed.

### 4. Analyze each candidate

Read every gathered source end to end.
For each candidate, score it along these dimensions (borrowed from `compare-skills`):

| Dimension | Question |
|-----------|----------|
| Frontmatter | Does it have `name`, `description`, `allowed-tools`, `argument-hint`? Is the description a good trigger for the skill? |
| Prerequisites | Are inputs, tools, and preconditions stated concretely? |
| Steps | Are steps numbered, specific, and ordered, with clear acceptance between steps? |
| Output format | Is there a concrete template the agent can fill in? |
| Examples | Are there scenario-based examples covering the common and the edge cases? |
| Error handling | Are failure modes and recovery documented? |
| Safety | Are guards present before destructive or external side effects? |
| Reusability | Does it parameterize via arguments and dynamic values instead of hardcoding? |

For each candidate, write two short lists: its strongest section (worth adopting) and its weakest section (worth replacing or dropping).

### 5. Plan the synthesis

Before writing, decide the structure of the new skill by selecting, per section, which candidate supplies the strongest version:

| New skill section | Adopted from | Adaptation needed |
|-------------------|--------------|-------------------|
| Frontmatter | `<candidate>` | rename, retrigger description |
| Prerequisites | `<candidate>` | match this repo's working directory and tools |
| Steps | `<candidate>` | merge in edge cases from others |
| Output format | `<candidate>` | retemplate for this repo's conventions |
| Examples | `<candidate>` | rewrite in this repo's voice |

Resolve every conflict between candidates by picking the clearer, more specific option and noting the reason.
The plan is a table, not the prose.
Do not start writing the skill until every section has a chosen source and every conflict has a resolution.

### 6. Write the skill

Create the directory and write `skills/$SKILL/SKILL.md` from the plan:

```bash
mkdir -p "skills/$SKILL"
```

Apply this repo's conventions exactly:

- Frontmatter with `name`, `description`, and `allowed-tools` (and `argument-hint` if the skill takes arguments).
- `TODAY=!`date +%Y-%m-%d`` line only if the skill references the current date.
- One sentence per line where applicable.
- No em-dashes, use commas or parentheses.
- No comments or decorative noise.
- Section order matching neighboring skills (typically: Prerequisites, Steps, Output Format, Example Usage).

Do not copy any candidate's prose verbatim unless it is a structural template (a table or a command).
Rewrite the instructions in this repo's voice so the skill is coherent rather than a patchwork.

### 7. Verify the result

Re-read the finished skill end to end and confirm:

- The frontmatter parses (name, description, allowed-tools are valid).
- The `description` is a strong trigger: it lists the phrases a user would actually say and when to use the skill.
- Every step is specific and actionable, not vague handwaving.
- The output format and examples are concrete and consistent with the steps.
- No broken cross-references to other skills.
- Every change is confined to the new skill directory and the README index, and no existing skill was overwritten:

```bash
# Anything modified or deleted under skills/ outside $SKILL means a candidate was installed over it.
git status --porcelain -- skills/ | grep -v "^?? skills/$SKILL/" | grep -v "^ M skills/$SKILL/" \
  | grep -v "^A  skills/$SKILL/" && echo "::error::Existing skill modified or deleted; a candidate may have been installed over it" \
  || echo "No existing skill overwritten"
```

### 8. Check for duplicates

Run the duplicate check from `review-skills` against the new skill: compare its name and description against every other skill in the library.
If a near-duplicate is found, stop and ask the user whether to merge, rename, or document an explicit scope boundary before continuing.

### 9. Register the skill

Update `README.md` so the skills index stays in sync (required by `AGENTS.md`).
Add one row to the most fitting thematic table:

```markdown
| `/$SKILL` | <one-line purpose matching the table's voice> |
```

Increment the skill-count badge in the README header (`skills-N`).

Do not edit `.github/llmaw/flows.yml`; this skill does not participate in an automated flow.

### 10. Summarize

Print a short summary of what was synthesized and from where:

```
## Create Skill: {SKILL} ({TODAY})

Candidates studied:
- <candidate> (<source>): adopted <section>; dropped <section>
- <candidate> (<source>): adopted <section>; dropped <section>

Conflicts resolved:
- <conflict>: chose <approach> because <reason>

Wrote skills/{SKILL}/SKILL.md and registered it in README.md.
```

If no candidates were found, state that the skill was written from first principles with a style reference to `<neighbor-skill>`.

## Output Format

The skill itself is the output.
It must conform to this skeleton:

```markdown
---
name: <skill-name>
description: <One or two sentences. State what the skill does and the trigger phrases a user would say. Start with a verb.>
allowed-tools: <comma-separated tools this skill needs>
argument-hint: "<signature>"
---

TODAY=!`date +%Y-%m-%d`   // only if the skill uses today's date

# <Skill Title>

<One-paragraph summary of what the skill does and why it exists.>

## Prerequisites

- <concrete inputs, tools, and preconditions>

## Steps

### 1. <step>
<specific instructions>

### 2. <step>
<specific instructions>

## Output Format

<concrete template or artifact the skill produces>

## Example Usage

**Scenario 1: <title>**
<walkthrough>
```

## Example Usage

**Scenario 1: Create a skill grounded in the ecosystem**
```
/create-skill summarize-meeting
```
Discovers three meeting-summary skills (two local, one on skills.sh with 12K installs), studies each, adopts the external skill's transcript-parsing steps and the local skill's output template, resolves a conflict on output format by choosing structured markdown, and writes `skills/summarize-meeting/SKILL.md`.

**Scenario 2: No good candidates exist**
```
/create-skill classify-emoji-sentiment
```
Finds no usable candidates in the library or the registry.
Falls back to writing the skill from first principles, using `triage-issue` as a style reference for its classification steps, and notes in the summary that no synthesis basis existed.

**Scenario 3: Candidate already exists locally**
```
/create-skill git-commit
```
Detects `skills/git-commit/` already exists and stops, suggesting `/improve-skill git-commit` instead of overwriting a working skill.

## Useful Commands Reference

| Command | Purpose |
|---------|---------|
| `npx skills find <query>` | Search the external skills registry for candidates |
| `npx skills use <owner>/<repo>@<skill>` | Print a candidate's `SKILL.md` to stdout without installing it |
| `npx skills add <owner>/<repo> --skill <skill> -y --copy` | Install a candidate into a temp directory (run there, never in the library root, never with `-g`) |
| `npx skills update` | Do NOT run: global scope resolves to this repo and can overwrite skills |
| `grep -rli -e "<term>" skills/*/SKILL.md` | Find local skills mentioning a term |
| `test -e skills/<name>` | Check whether a skill directory already exists |
| `git diff --name-only` | Confirm changes stayed inside the skill directory |
