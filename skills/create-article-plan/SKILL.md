---
name: create-article-plan
description: Plan a long-form article before writing it, defining the core insight, audience, section outline with supporting sources and planned visualizations, and non-goals, and writing plan.md next to the target article. Use when a long-form article's argument and structure should be settled and checked before drafting, after research-article and before create-article.
---

# Plan Article

Settles a long-form article's argument and structure before any prose is written, so the core insight, section order, and evidence can be checked while they are still cheap to change.
The output is a `plan.md` next to the target article, and it becomes the input to `/create-article`.

## Prerequisites

- **Target article**: the intended topic and the file path the article will be written to (or at least its directory)
- **Audience**: who will read the article
- **Sources**: the research brief from `/research-article`, or a set of sources (URLs, file paths, inline content)
- **Format** (optional): long-form essay, tracker, or another structure. Infer it when not stated.

If sources are not yet gathered, run `/research-article` first and plan from its brief.
The brief's "Recommendation for the Article" already proposes a core insight and angle, which the plan turns into a concrete structure.
If you decide not to run it, say so and give your reasoning before proceeding, so the user can course-correct.

## When to Plan

Plan a **long-form article** (roughly four or more sections, or any article whose structure is not fixed by a template).
Skip the plan for a **short templated piece** (for example a research note on a fixed skeleton, roughly one screen): the template is the plan, so a `plan.md` would only duplicate it.
When revising an existing article, plan only when the revision changes the argument or the section structure; otherwise edit the article in place.

## Plan Structure

Write `plan.md` next to the target article file.
Keep it to about one screen: it records the argument and structure, not the prose.

```markdown
---
artifact: article-plan
audience: <target audience>
status: draft
---

# Article Plan: <working title>

## Core insight

<One sentence: the single thesis the article argues.>

## Audience and calibration

<Who reads it, the prior knowledge assumed, and the tone and depth to use.>

## Format and length

<Long-form essay / research note / tracker, and the target length.>

## Section outline

### <Section title>

- Claim: <what this section establishes.>
- Evidence: <the sources that support the claim, with links.>
- Visualization: <the planned figure, or "none".>

### <Section title>

- Claim: ...
- Evidence: ...
- Visualization: ...

## Opening and takeaway

- Hook: <how the article opens, leading with the most important point.>
- Takeaway: <what the reader should think or do after reading.>

## Non-goals

- <What to leave out, to prevent scope creep.>
```

## Self-Check

Before handing off, check the plan against the **Structure** and **Sourcing** checks in [`../review-article/SKILL.md`](../review-article/SKILL.md):

- Structure: the sections form a logical progression to the takeaway, each section carries one idea, and a through-line connects them.
- Sourcing: every section's claim has at least one credible source with a hyperlink, and opinions are distinguished from sourced facts.

Fix what the self-check surfaces in the plan before handing it to `/create-article`.

## Steps

1. Confirm the article is one that warrants a plan (see When to Plan); if not, say so and stop.
2. Read the research brief and its sources, or the sources provided.
3. State the core insight in one sentence: the single thesis the article argues.
   Every section must serve it.
4. Calibrate the audience: the prior knowledge assumed, and the tone and depth to use.
5. Choose the format and the target length.
6. Outline the sections in order, and for each record the claim it establishes, the sources that support the claim, and any planned visualization.
   Keep each section to one idea.
7. Decide the opening hook and the takeaway.
8. List the non-goals: what the article deliberately leaves out.
9. Write `plan.md` next to the target article file.
10. Run the self-check and fix what it surfaces.

## Quality Criteria

Strong article plans:

- State a single specific thesis, not a survey of the topic
- Give every section a claim and at least one source that supports it
- Order the sections so the argument builds toward the takeaway
- Mark opinions as opinions and attribute facts to sources
- Stay short: the plan decides the argument, the article supplies the prose

Avoid:

- A plan that restates the research brief instead of committing to an article angle
- Sections with a topic label but no claim
- Claims with no supporting source
- More than one idea per section
- Pulling in material beyond the stated scope
- Em-dash sentence structures; use commas or parentheses instead
- The banned terms listed in `banned-terms.txt` at the skills library root (one per line), unless one is genuinely the most appropriate term

## Example Usage

**Scenario 1: Long-form essay**
Topic: "why agent memory is hard", audience: senior engineers.
Read the research brief, commit to one thesis (memory systems fail on retrieval, not storage), outline four sections each with evidence, and set non-goals (no product reviews).

**Scenario 2: Tracker**
Topic: coding-agent benchmarks, audience: practitioners.
Plan a tracker: the thesis (throughput is improving faster than reliability), the leaderboard sections, the source for each, and what to exclude.

**Scenario 3: Short research note**
Topic: a single tool.
The template already fixes the structure, so skip the plan and run `/create-article` directly.

## Output Format

Produce `plan.md` next to the target article file, in the structure above.
List the plan file in any handoff, and pass it to `/create-article`, which drafts from it.

## Next Step

Run `/create-article` to draft the article from `plan.md`, then `/review-article` to audit the article and check it against the plan (plan fidelity).
