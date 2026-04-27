---
name: arxiv-article
description: Downloads an arXiv HTML article, converts it to markdown with pandoc, archives it, and returns a structured summary. Use when processing a single arXiv paper given its HTML URL (e.g., https://arxiv.org/html/2504.12345). Called by the arxiv-catchup skill but can also be invoked directly.
---

# arXiv Article Processor

Downloads an arXiv HTML article, converts it to markdown via pandoc, archives it under `~/.claude/memory/arxiv/articles/`, and produces a structured summary.

## Input

The URL of the arXiv HTML article. Expected format: `https://arxiv.org/html/{arxiv_id}` (with or without a version suffix such as `v1`).

## Steps

### 1. Extract the arxiv ID

From the URL, take the path segment after `/html/`. Strip any version suffix for the archive filename:

- `https://arxiv.org/html/2504.12345v1` → base ID `2504.12345`, versioned ID `2504.12345v1`
- `https://arxiv.org/html/2504.12345` → base ID `2504.12345`

Use the base ID as the archive filename: `~/.claude/memory/arxiv/articles/{base_id}.md`.

### 2. Check archive

```bash
test -f ~/.claude/memory/arxiv/articles/{base_id}.md && echo "EXISTS" || echo "MISSING"
```

If the file exists, skip to step 6 (summarize from the cached file).

### 3. Download HTML

```bash
mkdir -p ~/.claude/memory/arxiv/articles
curl -L --silent --max-time 60 \
  -A "Mozilla/5.0 (compatible; research-bot/1.0)" \
  -o /tmp/arxiv_{base_id}.html \
  "{URL}"
```

If the download fails (non-zero exit or empty file), report the error and stop.

### 4. Convert to markdown with pandoc

```bash
pandoc -f html -t markdown \
  --wrap=none \
  --strip-comments \
  -o ~/.claude/memory/arxiv/articles/{base_id}.md \
  /tmp/arxiv_{base_id}.html
```

If pandoc is not available (`which pandoc` returns nothing), fall back to saving the raw HTML:

```bash
cp /tmp/arxiv_{base_id}.html ~/.claude/memory/arxiv/articles/{base_id}.html
```

and note in the summary that pandoc was unavailable.

### 5. Clean up temp file

```bash
rm -f /tmp/arxiv_{base_id}.html
```

### 6. Summarize

Read the archived file. Because converted papers can be long, read the first 300 lines to locate the title, authors, abstract, and introduction, then skim section headings and the conclusion. Produce this structured summary:

```markdown
## {Title}

**ID:** {base_id}
**URL:** https://arxiv.org/abs/{base_id}
**Authors:** {comma-separated author list}

### Problem
{1-2 sentences: what problem or gap does the paper address?}

### Approach
{2-3 sentences: what method, architecture, or technique do the authors use?}

### Key Results
- {finding or contribution 1}
- {finding or contribution 2}
- {finding or contribution 3 if present}

### Takeaway
{1 sentence: why this work matters or what it enables.}
```

If the archive is the raw HTML fallback, parse title and abstract from the HTML tags before summarizing.
