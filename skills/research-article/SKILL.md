---
name: research-article
description: Research a topic to map the state of the art, gathering and triaging sources before writing an article. Produces a research brief with organized sources, key findings, and identified gaps that feeds into create-article.
---

# Research Article

Given a topic, discovers what the state of the art is by searching broadly, triaging sources, deep-reading the strongest ones, and synthesizing the landscape.
The output is a research brief that becomes the input to `/create-article`, so the writing step can focus on craft rather than discovery.

## Prerequisites

- **Topic**: The subject to investigate (e.g., "vector databases", "test-time compute in LLMs", "CRDTs for collaborative editing")
- **Scope** (optional but recommended): The specific angle or question, time bounds (e.g., "last 2 years"), and what "state of the art" means here (best accuracy, fastest, most adopted, most recent breakthrough)
- **Intended audience** (optional): Helps calibrate which sources and framing are relevant
- **Seed sources** (optional): Any URLs, papers, or files the user already knows matter

## Steps

1. Clarify the topic and scope.
   State the specific research question in one sentence.
   Define what "state of the art" means for this topic (top benchmark score, dominant method, industry standard, latest breakthrough).
   Note any time bounds or constraints.
2. Cast a wide net.
   Search multiple source types (see Search Strategy below).
   Start with surveys, review papers, and benchmark leaderboards to map the terrain quickly before going deep.
3. Build a candidate source list.
   For each result, capture title, URL, type, year, and a one-line relevance note.
   Prioritize primary sources (papers, official docs, benchmarks) over secondary commentary, but keep influential blog posts and talks that shape practice.
4. Triage.
   Rank candidates by relevance, credibility, and recency.
   Keep the strongest 8-15 to deep-read.
   Drop outdated or low-quality sources, but record why so the exclusion is deliberate.
5. Deep-read the top sources.
   Fetch and read each one.
   Extract: the problem it tackles, its approach, its key results and numbers, and how it compares to prior work.
   Verify claims against the source rather than paraphrasing from memory or a summary.
6. Map the landscape.
   Group the sources into the main approaches or camps.
   Identify what currently defines the state of the art (top scores, dominant technique, widely adopted standard).
   Note where the field agrees and where it actively disagrees.
7. Surface gaps and open questions.
   What is unsolved, contested, or just emerging?
   These tensions are what make an article worth reading.
8. Synthesize.
   Write the state-of-the-art summary.
   Recommend an angle for the article: the single core insight or argument the research best supports.
9. Produce the research brief using the output format below.

## Search Strategy

Cover several source types so the picture is not skewed by one medium.

| Source type | What to look for | Where |
|---|---|---|
| Surveys / reviews | Existing maps of the field, taxonomy of approaches | arXiv, Google Scholar, Semantic Scholar |
| Primary papers | New methods, benchmark results | arXiv, conference proceedings |
| Benchmark leaderboards | Current best scores, what "SOTA" means concretely | Papers With Code, leaderboard sites |
| Engineering blogs | What works in production, real-world trade-offs | Company tech blogs, personal blogs |
| Documentation / specs | How mature tools actually behave | Official docs, RFCs, standards |
| Community discussion | Controversies, pitfalls, emerging work | HN, Reddit, forum threads |

Prefer recency for a fast-moving field, but anchor to the seminal works that everyone cites.

## When to Stop Researching

Research converges when:
- New searches mostly surface sources already in the candidate list.
- The main approaches are stable and you can name them without checking notes.
- The top benchmark numbers and the dominant method are clear.

If after reasonable effort the field is too large to map fully, narrow the scope and say so explicitly in the brief rather than producing a shallow survey.

## Output Format

Write the research brief as markdown with this structure:

```markdown
---
topic: "<topic>"
audience: "<intended audience, or omit if unknown>"
status: draft
---

# Research Brief: <Topic>

## Scope

<One paragraph: the specific question investigated, what is in and out of scope, time bounds, and how "state of the art" is defined here.>

## Search Strategy

| Source type | Searched | Queries / notes |
|---|---|---|
| Surveys / reviews | Yes / No | <queries> |
| Primary papers | Yes / No | ... |
| Benchmark leaderboards | Yes / No | ... |
| Engineering blogs | Yes / No | ... |
| Documentation / specs | Yes / No | ... |
| Community discussion | Yes / No | ... |

## State of the Art

### Main Approaches

| Approach | Key idea | Representative work | Strengths | Limitations |
|---|---|---|---|---|
| <name> | <one line> | [Title](https://...) | <one line> | <one line> |

### Current Best Results

<Benchmarks, leaderboards, or numbers that define the state of the art today. Cite each.>

### Consensus and Disagreement

<Where the field agrees, and where it actively debates.>

## Key Sources

| Source | Type | Year | Why it matters |
|---|---|---|---|
| [Title](https://...) | Paper / Blog / Docs / Standard | <year> | <one line> |

## Open Questions / Gaps

1. <What is unsolved, contested, or just emerging.>
2. ...

## Recommendation for the Article

**Core insight:** <The single argument the research best supports.>
**Angle:** <How to frame the article given the state of the art.>
**Sources to lead with:** <2-4 sources that should anchor the article.>
```

## Quality Criteria

**Strong research briefs:**
- Answer "what is the state of the art?" with specific names, numbers, and dates, not vague generalities
- Distinguish what is established from what is contested or emerging
- Trace claims to primary sources with verifiable links
- Name the main approaches and how they compare
- Recommend a concrete angle the article can take

**Avoid:**
- Listing sources without explaining what each contributes
- Treating every source as equally important (triage ruthlessly)
- Stating opinions or impressions as if they were sourced facts
- Stopping at the first page of search results without triangulating
- Em-dash sentence structures, use commas or parentheses instead

## Example Usage

**Scenario 1: Fast-moving research field**
Topic: "test-time compute in LLMs", scope: "last 18 months, accuracy on math reasoning".
Search arXiv and Papers With Code, find the dominant scaling approach and the top benchmark scores, note the open question of cost at inference.
Recommend an article framing test-time compute as the new scaling axis.

**Scenario 2: Established engineering topic**
Topic: "vector databases", scope: "what to choose in 2025, latency and recall trade-offs".
Search engineering blogs and docs, compare the main products and libraries on benchmarks, note the consensus on approximate nearest neighbor and the disagreement on indexing strategy.
Recommend a practical selection-guide article.

**Scenario 3: Conceptual explainer**
Topic: "CRDTs for collaborative editing", scope: "how they work and where they struggle".
Anchor on the seminal papers and a key survey, map the main algorithms, surface the gap around complexity and memory overhead.
Recommend an article that explains CRDTs and honestly covers their limitations.

## Next Step

Run `/create-article`, passing the key sources from this brief and the recommended core insight and angle.
The research brief is the "relevant sources" prerequisite for `/create-article`, so the writing step can focus on structure, tone, and audience calibration rather than on finding material.

After the article is drafted, run `/review-article` to audit it for accuracy, sourcing, and clarity.

## Useful Commands Reference

| Command | Description |
|---|---|
| `WebSearch` | Cast the wide net across the web, blogs, and docs |
| `WebFetch` | Deep-read a candidate source and extract its claims |
| `/arxiv-article <url>` | Download, archive, and summarize a single arXiv paper |
| `grep` / codebase search | Find how the topic is handled in the local repository, if relevant |
| `gh-cached search ...` | Search the organization's repositories for prior art or related work |
