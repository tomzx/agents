---
name: arxiv-article
description: Downloads an arXiv HTML article, converts it to markdown with pandoc, archives it, and returns a structured summary. Use when processing a single arXiv paper given its HTML URL (e.g., https://arxiv.org/html/2504.12345). Called by the arxiv-catchup skill but can also be invoked directly.
---

# arXiv Article Processor

Downloads an arXiv HTML article, converts it to markdown via pandoc, archives it under `$ARXIV_DIRECTORY/{base_id}/`, and produces a structured summary.

## Prerequisites

`ARXIV_DIRECTORY` must be set to the directory where archived articles are stored (e.g., `~/arxiv-articles`). If the variable is unset, stop and ask the user to set it.

```bash
echo "${ARXIV_DIRECTORY:?ARXIV_DIRECTORY is not set}"
```

If pandoc is not available (`which pandoc` returns nothing), report the error and stop. Do not proceed without pandoc.

## Input

The URL of the arXiv HTML article. Expected format: `https://arxiv.org/html/{arxiv_id}` (with or without a version suffix such as `v1`).

## Steps

### 1. Resolve archive directory

```bash
ARCHIVE_DIR="${ARXIV_DIRECTORY}"
mkdir -p "$ARCHIVE_DIR"
```

### 2. Extract the arxiv ID

From the URL, take the path segment after `/html/`. Strip any version suffix for the archive filename:

- `https://arxiv.org/html/2504.12345v1` → base ID `2504.12345`, versioned ID `2504.12345v1`
- `https://arxiv.org/html/2504.12345` → base ID `2504.12345`

The article is stored under `$ARCHIVE_DIR/{base_id}/`.

### 3. Check archive

```bash
test -f "$ARCHIVE_DIR/{base_id}/article.md" && echo "EXISTS" || echo "MISSING"
```

If the file exists, skip to step 5 (summarize from the cached file).

### 4. Download and convert with pandoc

Pass the URL directly to pandoc so it can resolve relative image URLs. Images are saved into `$ARCHIVE_DIR/{base_id}/` alongside the article.

```bash
mkdir -p "$ARCHIVE_DIR/{base_id}"
pandoc -f html -t markdown \
  --wrap=none \
  --strip-comments \
  --extract-media="$ARCHIVE_DIR/{base_id}" \
  -o "$ARCHIVE_DIR/{base_id}/article.md" \
  "{URL}"
```

If the command fails, report the error and stop.

### 5. Summarize

Read the full `$ARCHIVE_DIR/{base_id}/article.md` and produce this structured summary:

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

Write the summary to `$ARCHIVE_DIR/{base_id}/summary.md`, overwriting if it already exists.
