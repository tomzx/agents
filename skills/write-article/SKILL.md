---
name: write-article
description: Write a high-quality article given a target audience and relevant sources. Produces a structured, well-researched article tailored to the audience's knowledge level and interests.
---

# Write Article

Produces a high-quality article from a target audience definition and a set of relevant sources. Adapts tone, depth, and structure to fit the audience.

## Prerequisites

- **Target audience**: Who will read this article (e.g., "senior backend engineers", "product managers unfamiliar with ML", "general tech enthusiasts")
- **Relevant sources**: URLs, file paths, or inline content to draw from (research papers, blog posts, docs, notes, etc.)
- **Topic** (optional): If not inferable from sources, state the article topic explicitly

## Steps

1. Read all provided sources thoroughly.
2. Identify the core insight or argument the article should convey.
3. Calibrate tone and depth to the target audience.
4. Draft the article using the structure below, following the formatting rules.
5. Verify all links: curl every URL in the article and replace any that return 4xx, 5xx, or connection errors.
6. Revise for clarity, flow, and conciseness.

## Formatting Rules

- **One sentence per line**: Each sentence occupies its own line in the markdown source.
  This produces cleaner git diffs since changes to one sentence don't affect adjacent lines.
  Paragraphs are separated by a blank line, with sentences within a paragraph on consecutive lines
  (not separated by blank lines).
- **Link all sources**: Every source referenced in the article body must include a verified hyperlink,
  not just a textual citation (e.g., `[Author, "Title"](https://...)` not just `Author, "Title"`).
- **Verify links**: After drafting, curl every hyperlink and replace any that return 4xx or connection
  errors before finalizing the article.

## Audience Calibration

| Audience type | Tone | Depth | Jargon |
|---|---|---|---|
| Technical experts | Peer-to-peer, direct | Deep, assume fundamentals | Domain terms fine |
| Practitioners (non-expert) | Instructional, approachable | Moderate, explain non-obvious concepts | Define on first use |
| General / non-technical | Accessible, engaging | Conceptual, avoid implementation details | Avoid or translate |
| Decision-makers | Business-focused, outcome-oriented | High-level, emphasize impact | Minimal |

## Article Structure

```markdown
# [Title: specific and descriptive, not clickbait]

[Lead: 1-3 sentences that state the core insight or frame the problem.]
[No throat-clearing.]
[Each sentence on its own line.]

## [Section 1: Context or Background]

[What the reader needs to understand before the main argument.]
[Only include what is necessary.]
[Each sentence on its own line, separated by newlines within a paragraph.]

## [Section 2: Main Argument or Explanation]

[The substance of the article.]
[Can be split into multiple sections if needed.]
[All source references include hyperlinks, e.g. [Author, "Title"](https://...).]

## [Section 3: Implications, Applications, or Next Steps]

[What the reader should think or do differently after reading.]

## Conclusion (optional)

[Only include if it adds something beyond a summary.]
[A strong final line beats a weak conclusion section.]
```

Adjust section count and naming to fit the content. Not every article needs all four sections.

## Quality Criteria

**Strong articles:**
- Open with the most interesting or important thing, not background
- Make a specific claim or argument, not a survey of possibilities
- Use concrete examples, numbers, or comparisons to anchor abstract points
- Attribute claims to sources with hyperlinks; don't state opinions as facts
- End with something the reader can take away or act on
- Each sentence sits on its own line in the markdown source

**Avoid:**
- Padding: filler phrases like "In today's fast-paced world..." or "It's important to note that..."
- Hedging everything: take a position where the sources support one
- Restating the same point in multiple sections
- Ending with "In conclusion, we have seen that..."
- Em-dash sentence structures; use commas or parentheses instead

## Output Format

Produce the article as clean markdown. After the article, include a brief section:

```markdown
---
**Sources used:**
- [Source Title](https://...) -- [one-line note on what it contributed]
- [Source Title](https://...) -- [one-line note on what it contributed]
**Audience notes:** [one line on any assumptions made about the audience's prior knowledge]
```

## Example Usage

**Scenario 1: Technical deep-dive**
Target audience: "experienced Go developers", sources: Go memory model spec + blog post on goroutine scheduling.
Produce a peer-level article explaining a non-obvious behavior, with code examples, assuming the reader knows Go basics.

**Scenario 2: Explainer for non-technical readers**
Target audience: "product managers at a SaaS company", sources: two research papers on LLM hallucination.
Produce a business-oriented piece explaining what hallucination is, why it matters for product decisions, and how to mitigate it, without implementation details.

**Scenario 3: Opinion/perspective piece**
Target audience: "software architects", sources: three blog posts arguing for and against microservices.
Synthesize the arguments, take a defensible position, and advise on when to use vs. avoid microservices.

## Useful Commands Reference

No CLI commands required. This skill operates on content provided in context.
