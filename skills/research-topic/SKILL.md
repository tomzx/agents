---
name: research-topic
description: "Research any topic by running a comprehensive web search, snapshotting each visited page's raw HTML and converting it to clean markdown, then synthesizing a structured research document. Use when the user says /research-topic, 'research a topic', 'investigate a subject', 'gather sources', 'background research', 'build a research dossier', 'find information on', or wants a topic researched with sources saved on disk. Persists snapshots of every source so findings are auditable and re-usable. For mapping the state of the art of a research field to feed article writing, see research-article."
---

# Research Topic

Given any topic, runs a comprehensive web search across multiple angles and source types, snapshots every page it visits (raw HTML plus a clean markdown conversion), and synthesizes a structured research document.
The snapshots stay on disk so every claim in the final document can be traced back to the exact content that was read, and the material can be re-used later without re-fetching.

## Prerequisites

- **Topic**: The subject to investigate (e.g., "how WebRTC handles NAT traversal", "React Server Components vs. Remix", "the 2024 SQLite virtual table changes")
- **Scope** (optional but recommended): The specific question or angle, time bounds (e.g., "last 2 years"), and how many sources to deep-read (default 8-12)
- **Seed sources** (optional): Any URLs the user already knows matter
- **Output directory** (optional): Defaults to `./research/<topic-slug>/` relative to the current working directory

### Tools

This skill does its fetching, image handling, and conversion through one script: `scripts/snapshot.py` (next to this file).
The script owns every deterministic decision so the skill steps stay focused on research judgment, not tool mechanics.
Run it with `uv run`; the `# /// script` preamble declares its Python dependencies (trafilatura, structlog), so `uv` installs them into an ephemeral environment on first use, no project setup required.

```bash
uv run <skill_dir>/scripts/snapshot.py --help
```

Resolve `<skill_dir>` to this skill's directory (the directory containing this `SKILL.md`).

### What the script does

For each URL it:

1. Fetches the exact served bytes with a browser User-Agent and writes them to `raw.html` (the canonical archive).
2. Converts to clean markdown through a cascade, recording which converter won in `meta.json`:
   - **trafilatura** (preferred), a content extractor: it strips navigation, sidebars, footers, and boilerplate, then emits the article as markdown, and captures title, author, and date.
     It is a Python package ([adbar/trafilatura](https://github.com/adbar/trafilatura), Apache-2.0), benchmark-validated and used by HuggingFace, IBM, and Microsoft Research.
     In an empirical comparison on chrome-heavy pages (Wikipedia, GitHub), trafilatura produced 3-13x smaller markdown with near-zero nav/footer noise, versus the pure converters below.
   - **html2markdown** (first fallback), a pure converter ([JohannesKaufmann/html-to-markdown](https://github.com/JohannesKaufmann/html-to-markdown)) that keeps nav/footer but respects local image links.
   - **pandoc** (last resort), a pure converter, present on most systems.
3. Optionally downloads images: with `--with-images`, it mirrors the page with `wget -p -k` so images are saved and `<img src>` is rewritten to local relative paths, then trafilatura emits markdown whose image links point at those local files. Images wget cannot fetch stay as remote URLs.

External tools the script shells out to when needed: `wget` (only for `--with-images`), `html2markdown` and `pandoc` (only as fallbacks). Only one of the three converters needs to be available for the script to produce output; trafilatura comes via the preamble, so a fresh machine needs nothing installed to get clean text.

If every converter returns empty (e.g. a page with no body), the script records `converter: "failed"` in `meta.json`, exits non-zero, and leaves only `raw.html` plus `meta.json`. Do not invent content for a page that failed to snapshot.

## Directory Layout

All output lives under one directory per topic so the research is self-contained and portable.

```
research/<topic-slug>/
├── research.md          # the final synthesized research document
├── sources.md           # manifest of every page visited (kept and excluded)
└── snapshots/
    └── <source-slug>/
        ├── raw.html      # raw HTML snapshot, exactly as fetched
        ├── content.md    # trafilatura (or html2markdown / pandoc) conversion
        ├── meta.json     # url, fetched_at, http_status, converter, title, images, ...
        └── media/        # wget mirror of page requisites (only with --with-images)
```

Rules:

- `<topic-slug>` and `<source-slug>` are lowercase, hyphenated, ASCII only.
- The script derives `<source-slug>` from the URL automatically (registrable domain plus path, non-alphanumeric runs collapse to a single hyphen, truncated to 60 characters), or you can pass `--slug` to override.
  If two URLs collapse to the same slug, pass distinct `--slug` values.
- The script always writes `raw.html` before converting, so a converter failure still leaves a usable archive.
- Never overwrite a prior run's snapshots silently.
  If `<topic-slug>` already exists, ask whether to overwrite, extend (add new sources only), or pick a new directory.

## Steps

### 1. Clarify scope

State the research question in one sentence.
List the specific sub-questions to answer and any time bounds.
Note what is explicitly out of scope so the search stays focused.
If the topic is ambiguous, ask the user one clarifying question before searching.

### 2. Compute paths

```bash
TOPIC_SLUG="<topic-slug>"
BASE="research/$TOPIC_SLUG"
mkdir -p "$BASE/snapshots"
```

### 3. Cast a wide net

Search multiple query angles and several source types so the picture is not skewed by one medium.

| Source type | What to look for | Where |
|---|---|---|
| Primary / official | Specs, docs, RFCs, changelogs, reference manuals | Official sites, standards bodies |
| Long-form analysis | Explanations, comparisons, post-mortems | Engineering blogs, personal blogs |
| Community discussion | Controversies, pitfalls, emerging work, corrections | HN, Reddit, forum threads, Stack Overflow |
| Academic / papers | Formal methods, benchmarks, citations | arXiv, Google Scholar, Semantic Scholar |
| Reference data | Numbers, tables, version histories | Wikipedia, leaderboards, databases |

Run at least 3 distinct query phrasings, including one the target audience would use and one a skeptic would use.
Record every query you ran in `sources.md` (see step 6) so the search itself is auditable.

### 4. Build a candidate list

For each result, capture: title, URL, source type, and a one-line relevance note.
Deduplicate by final URL (resolve redirects).
Prefer primary sources over secondary commentary, but keep influential posts that shape practice.

### 5. Triage

Rank candidates by relevance, credibility, and recency.
Keep the strongest `N` to deep-read (default 8-12; more for a deep dive, fewer for a quick scan).
Drop low-quality or off-topic sources, but record each exclusion with a one-line reason in `sources.md` so the cut is deliberate, not accidental.

### 6. Snapshot and convert each kept source

For every source that survives triage, run the snapshot script once.
It fetches and archives the raw HTML, converts to clean markdown via the cascade, and writes `meta.json` with the result, all in one step.

Snapshot one source (replace `{url}`, `{source-slug}`, `<skill_dir>`):

```bash
uv run <skill_dir>/scripts/snapshot.py "{url}" \
  --output-dir "$BASE/snapshots/{source-slug}" \
  --slug "{source-slug}"
```

Add `--with-images` when a source's figures matter (docs, tutorials, data visualizations).
The script then mirrors the page with `wget` so images download and the markdown's image links point at those local files, and records `images_downloaded` in `meta.json`.

```bash
uv run <skill_dir>/scripts/snapshot.py "{url}" \
  --output-dir "$BASE/snapshots/{source-slug}" \
  --slug "{source-slug}" \
  --with-images
```

The script prints a one-line summary per source (`url <tab> converter <tab> status <tab> bytes <tab> images`) and exits non-zero on failure, which makes it easy to fan out across sources with parallel subagents and collect results.

Extraction notes:

- Read the resulting `content.md` and synthesize findings from it.
- `meta.json` already records `converter`, `http_status`, `title`, `author`, `date`, `fetched_at`, and (with `--with-images`) `images_downloaded`, so reuse those fields in `sources.md` rather than re-deriving them.
  Use the date portion of `fetched_at` (when the page was snapshotted) for the **Snapshotted** column, not `date` (which is the source's own publication date from its metadata).
- If `meta.json` shows `converter: "failed"`, or `http_status` is 4xx/5xx, record the failure in `sources.md` and fall back to `WebFetch` for that URL.
  Do not fabricate content for a page that failed to snapshot.
- `converter` is one of `trafilatura`, `html2markdown`, `pandoc`, or `failed`.
  trafilatura runs against the archived `raw.html` (or the wget-rewritten HTML when `--with-images` is set), so the markdown provably derives from the snapshot rather than a re-fetch.
- For PDFs, the script does not convert them; save the file as `raw.pdf` and run `pandoc -f pdf -o content.md raw.pdf` (or the `docx` reader), then set `converter` in `meta.json` manually.

### 7. Build the sources manifest

Write `sources.md` listing every page considered, kept and excluded.

```markdown
# Sources: <Topic>

**Research question:** <one sentence>
**Generated:** <YYYY-MM-DD>
**Searches run:**
- "<query 1>"
- "<query 2>"
- "<query 3>"

## Kept

| # | Source | Type | Snapshot | Snapshotted | Why it matters |
|---|---|---|---|---|---|
| 1 | [Title](https://...) | Docs | `snapshots/<slug>/content.md` | 2026-07-06 | <one line> |

## Excluded

| Source | Reason |
|---|---|
| [Title](https://...) | <one line: outdated, off-topic, duplicate, low quality> |
```

### 8. Deep-read and extract

Read each `content.md` snapshot and extract:

- The question or problem the source addresses.
- Its key claims, numbers, or definitions, with the exact wording that matters.
- How it relates to the other sources (agreement, contrast, correction, deeper detail).
- Direct quotes for any claim you will cite verbatim, with the snapshot path so it is traceable.

Verify claims against the snapshot rather than paraphrasing from memory.

### 9. Synthesize

Group the sources into the main viewpoints, approaches, or themes.
Identify where the material agrees and where it actively disagrees.
Surface what is unsolved, contested, or emerging.
Draw out the single most important takeaway the research supports.

### 10. Write the research document

Write `research.md` using the output format below.

## Output Format

```markdown
---
topic: "<topic>"
question: "<one-sentence research question>"
generated: "<YYYY-MM-DD>"
sources_dir: "research/<topic-slug>/snapshots"
status: draft
---

# Research: <Topic>

## Question

<One paragraph: the specific question investigated, what is in and out of scope, and any time bounds.>

## Summary

<2-4 sentences: the most important finding or takeaway, in plain language.>

## Key Findings

1. **<Finding>.** <One or two sentences of support, with a source link.>
   [Source Title](https://...) ([snapshot](snapshots/<slug>/content.md))
2. **<Finding>.** ...

## Themes

### <Theme 1>

<What the sources collectively say here, citing each.>

### <Theme 2>

...

## Points of Disagreement

<Where credible sources conflict, stated neutrally with each side cited. Omit the section if there is none.>

## Open Questions

1. <What is unsolved, contested, or just emerging.>
2. ...

## References

- [Source Title](https://...) - <one-line note on what it contributed> ([snapshot](snapshots/<slug>/content.md))
- ...
```

Snapshot links use paths relative to `research.md` (i.e. `snapshots/<slug>/content.md`) so they resolve from the topic directory.

## Quality Criteria

**Strong research documents:**

- Answer the stated question with specific facts, names, numbers, and dates, not vague generalities.
- Distinguish what is established from what is contested or emerging.
- Trace every cited claim to a saved snapshot on disk, not just a URL.
- Name the main themes and how the sources relate (agreement, contrast, correction).
- Reveal gaps and open questions rather than papering over them.

**Avoid:**

- Listing sources without explaining what each contributes.
- Treating every source as equally important (triage ruthlessly).
- Stating opinions or impressions as if they were sourced facts.
- Stopping at the first page of search results without triangulating.
- Fabricating content for pages that failed to snapshot.
- Em-dash sentence structures; use commas or parentheses instead.

## When to Stop Researching

Research converges when:

- New searches mostly surface sources already in the candidate list.
- The main themes are stable and you can name them without checking notes.
- The key numbers and definitions are clear and cited.

If the topic is too large to map fully, narrow the scope and say so explicitly in `research.md` rather than producing a shallow survey.

## Example Usage

**Scenario 1: Technical explainer with primary sources**
Topic: "how WebRTC handles NAT traversal", scope: "STUN, TURN, ICE, last 3 years".
Search official specs (RFC 8445, RFC 8489) and engineering blogs, snapshot each, map STUN vs. TURN vs. ICE, surface the open question of TURN server cost.
Output a research document anchored to the spec snapshots.

**Scenario 2: Comparative landscape**
Topic: "React Server Components vs. Remix", scope: "data loading and bundling trade-offs, 2024-2025".
Search both projects' docs plus independent analyses, snapshot all, contrast on data flow and bundle strategy, note where the community disagrees on mental model.
Output a side-by-side themes section.

**Scenario 3: Quick background scan**
Topic: "the 2024 SQLite virtual table changes", scope: "what changed and what breaks".
Search the SQLite changelog and release notes, snapshot 4-6 sources, summarize the changes and migration impact.
Output an abbreviated research document with a single themes section.

## Next Step

- Run `/research-article` to turn this material into a state-of-the-art brief, or `/create-article` with `research/<topic-slug>/` as a source directory to write a polished article from the snapshots.
- Run `/review-article` after drafting to audit accuracy, sourcing, and clarity.

## Useful Commands Reference

| Command | Description |
|---|---|
| `WebSearch` | Cast the wide net across the web, blogs, and docs |
| `WebFetch` | Fallback reader for a URL whose snapshot failed |
| `uv run <skill_dir>/scripts/snapshot.py "{url}" --output-dir ... [--with-images]` | Fetch, archive, and convert one source in a single step (preferred) |
| `uv run <skill_dir>/scripts/snapshot.py --help` | Inspect the script's flags and defaults |
