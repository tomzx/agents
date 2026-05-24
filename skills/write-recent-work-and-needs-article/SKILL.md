---
name: write-recent-work-and-needs-article
description: Write a personal status article covering what you have been working on recently and what you currently need. Gathers information from the user through conversation, then produces a polished blog-ready piece.
---

# Write Recent Work and Needs Article

Produces a personal status article with two sections: what you have been working on recently, and what you see as your current needs. Useful for blog posts, manager syncs, team updates, or personal reflection.

## Steps

### 1. Gather Recent Work

Ask the user:

> "What have you been working on recently? List anything significant from the past few weeks: features shipped, problems solved, decisions made, investigations, collaborations."

Prompt for specifics if the response is vague:
- What was the outcome, not just the activity?
- What changed or was delivered?
- Anything that surprised you or turned out harder than expected?

### 2. Gather Current Needs

Ask the user:

> "What do you currently need? Think about: blockers waiting on someone else, decisions that haven't been made, resources or access you're missing, areas where the goal or approach is still unclear."

Prompt for specifics if the response is vague:
- Who needs to act for the blocker to clear?
- What exactly is ambiguous, and what would clarity enable?

### 3. Produce the Article

Using the information gathered, write the article according to the structure below.

- Open with the most significant or interesting recent work, not a chronological list
- Under current needs, be specific: name the blocker, the person whose input is needed, or the resource required
- Avoid vague language ("working on various things", "need more support") -- name the thing
- Omit the needs section entirely if the user has none

### 4. Confirm and Deliver

Present the draft to the user. Ask if anything should be added, removed, or reworded before finalizing.

Output the final article as clean markdown, ready to paste into a blog or document.

## Article Structure

```markdown
# [Title: personal, specific -- e.g. "Where I am: late May 2026"]

[Lead: 1-2 sentences framing the period and its defining theme. Skip if nothing stands out.]

## What I Have Been Working On

[Narrative or short list of recent work. Group related items. Lead with what is most significant.
Prefer concrete outputs over activities: "shipped X", "resolved Y", "decided Z".]

## What I Currently Need

[Specific needs, each with enough context to act on:
- Blocker from <person or system>: <what is needed and why>
- Clarity on <topic>: <what is ambiguous>
- Access to <resource>: <what it unlocks>
Omit this section entirely if there are no real needs right now.]
```

## Quality Criteria

- Every need should be specific enough that someone reading it knows what to do
- Recent work should show outputs and decisions, not just effort
- The article should be useful to someone who has not spoken to you in two weeks
- Open with the most interesting or important thing, not background
- Use concrete examples, numbers, or comparisons to anchor abstract points
- Avoid padding: no "In today's fast-paced world..." or "It's important to note that..."
- Avoid em-dash sentence structures; use commas or parentheses instead

## Example Usage

**Scenario 1: Manager sync**
User describes shipping a feature and one open blocker waiting on a team decision. Output: a focused article naming what shipped, what is in progress, and a specific ask for the decision.

**Scenario 2: Quiet period**
User reports mostly maintenance and no blockers. Output: honest brief summary of maintenance work done, no needs section.

**Scenario 3: Many open threads**
User lists five workstreams. Output: groups related items into two or three themes rather than listing all five separately.
