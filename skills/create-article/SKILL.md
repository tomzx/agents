---
name: create-article
description: Write a high-quality article given a target audience and relevant sources. Produces a structured, well-researched article tailored to the audience's knowledge level and interests.
---

# Write Article

Produces a high-quality article from a target audience definition and a set of relevant sources. Adapts tone, depth, and structure to fit the audience.

## Prerequisites

- **Target audience**: Who will read this article (e.g., "senior backend engineers", "product managers unfamiliar with ML", "general tech enthusiasts")
- **Relevant sources**: URLs, file paths, or inline content to draw from (research papers, blog posts, docs, notes, etc.)
- **Topic** (optional): If not inferable from sources, state the article topic explicitly

If sources are not yet gathered, run `/research-article` first to discover the state of the art and produce a research brief whose key sources feed this skill.

## Steps

1. Read all provided sources thoroughly.
2. Identify the core insight or argument the article should convey.
3. Calibrate tone and depth to the target audience.
4. Draft the article using the structure below, following the formatting rules.
5. Verify all links: curl every URL in the article and replace any that return 4xx, 5xx, or connection errors.
6. Discover related articles in the same repository (see "Finding Related Articles" below) and add a "See also" section.
7. Revise for clarity, flow, and conciseness.

## Formatting Rules

- **One sentence per line**: Each sentence occupies its own line in the markdown source.
  This produces cleaner git diffs since changes to one sentence don't affect adjacent lines.
  Paragraphs are separated by a blank line, with sentences within a paragraph on consecutive lines
  (not separated by blank lines).
- **Link all sources**: Every source referenced in the article body must include a verified hyperlink,
  not just a textual citation (e.g., `[Author, "Title"](https://...)` not just `Author, "Title"`).
- **Verify links**: After drafting, curl every hyperlink and replace any that return 4xx or connection
  errors before finalizing the article.
- **Bold important statements**: Highlight the most important statements, key claims, and takeaways
  in **bold** so readers scanning the article still capture the core message. Be selective: bold
  sentences or phrases that carry the argument, not routine sentences. Avoid bolding more than one
  statement per paragraph on average.
- **Plain vocabulary**: Prefer common, everyday words over less frequent synonyms, so the article is
  easy to read (for example, "use" over "utilize", "help" over "facilitate", "show" over "elucidate").
  Keep technical terms where they are the precise and expected choice; the goal is to avoid uncommon
  or showy words, not to lose precision. Calibrate this to the audience: write simpler for general
  readers, and allow more domain terms for expert readers.

## Audience Calibration

| Audience type | Tone | Depth | Jargon |
|---|---|---|---|
| Technical experts | Peer-to-peer, direct | Deep, assume fundamentals | Domain terms fine |
| Practitioners (non-expert) | Instructional, approachable | Moderate, explain non-obvious concepts | Define on first use |
| General / non-technical | Accessible, engaging | Conceptual, avoid implementation details | Avoid or translate |
| Decision-makers | Business-focused, outcome-oriented | High-level, emphasize impact | Minimal |

## Article Structure

```markdown
---
audience_notes: >
  [one line on any assumptions made about the audience's prior knowledge]
---

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

## See also

- [Title of related article](relative/path/to/article.md) - [one-line note on the connection]
- [Title of related article](relative/path/to/article.md) - [one-line note on the connection]
```

Adjust section count and naming to fit the content. Not every article needs all four sections.

## Finding Related Articles

The "See also" section links readers to other articles in the same repository that provide useful context, background, or contrasting perspective. A good "See also" section saves the reader a search and surfaces adjacent reading.

**Discovery steps:**
1. Determine the output location of the new article (ask the user if not specified).
2. Search the repository for other article files near that location. Common patterns: `*.md` under `articles/`, `posts/`, `blog/`, `docs/`, or a content directory indicated by the user.
3. Match candidates by topic overlap: shared keywords, referenced technologies, same problem domain, or citations to the same primary sources.
4. Prefer linking to 2-5 high-relevance articles over listing many loosely related ones. Quality over quantity.
5. Use repository-relative paths (e.g. `../foo/bar.md` or `articles/xyz.md`) so links work in any clone or rendered preview of the repo.

If no related articles exist in the repository, omit the "See also" section entirely rather than padding it.

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
- Reaching for uncommon words when a simpler word means the same thing, while keeping technical terms where they fit

## Output Format

Produce the article as clean markdown starting with YAML frontmatter containing `audience_notes`. After the article, include a brief sources section:

```markdown
---
audience_notes: >
  [one line on any assumptions made about the audience's prior knowledge]
---

[...article body...]

## References

- [Source Title](https://...) - [one-line note on what it contributed]
- [Source Title](https://...) - [one-line note on what it contributed]
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
