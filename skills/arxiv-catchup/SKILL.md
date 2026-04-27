---
name: arxiv-catchup
description: Fetches new arXiv cs.AI papers published since the last processed date, processes each paper's HTML version via the arxiv-article skill, and advances the date checkpoint. Use when the user says /arxiv-catchup, catch up on arXiv, or wants to read recent AI papers.
---

# arXiv Catchup

Fetches cs.AI papers from arXiv published since the last checkpoint date, calls **arxiv-article** for each (via parallel subagents), then advances the checkpoint to today.

## Prerequisites

`ARXIV_DIRECTORY` must be set to the directory where archived articles are stored (e.g., `~/arxiv-articles`). If the variable is unset, stop and ask the user to set it.

```bash
echo "${ARXIV_DIRECTORY:?ARXIV_DIRECTORY is not set}"
```

## State file

`~/.arxiv-catchup/state.json`

```json
{"last_date": "YYYY-MM-DD"}
```

- If the file does not exist, ask the user what start date to use before proceeding.
- The date is always in `YYYY-MM-DD` format.
- After all articles are processed, update the file with today's date.

## Steps

### 1. Read the last-processed date

```bash
mkdir -p ~/.arxiv-catchup
cat ~/.arxiv-catchup/state.json 2>/dev/null
```

If the file does not exist or is empty, ask the user:

> "No catchup state found. From what date should I start? (YYYY-MM-DD)"

Wait for the user's answer, then use it as `last_date`.

### 2. Fetch the catchup page

```bash
curl -L --silent --max-time 60 \
  -A "Mozilla/5.0 (compatible; research-bot/1.0)" \
  -o /tmp/arxiv_catchup.html \
  "https://arxiv.org/catchup/cs.AI/{last_date}"
```

If the response is empty or the status is non-200, report the error and stop without updating state.

### 3. Extract HTML article links

The catchup page contains three sections: **New submissions**, **Cross-lists**, and **Replacements**. Ignore all articles under the Replacements section.

Parse the HTML to collect links from New submissions and Cross-lists only. In the page source, replacement entries appear after a heading such as `Replacements` or `replaced`. Discard any `/html/` links that appear after that heading.

Extract links following the pattern `/html/{arxiv_id}`:

```bash
grep -oP '(?<=href=")[^"]*' /tmp/arxiv_catchup.html \
  | grep '^/html/' \
  | sed 's|^/html/|https://arxiv.org/html/|' \
  | sort -u
```

If that yields nothing, also try the absolute-URL form:

```bash
grep -oP 'https://arxiv\.org/html/[^\s"<>]+' /tmp/arxiv_catchup.html | sort -u
```

Collect the deduplicated list. If the list is still empty after both attempts, report that no HTML-version links were found and stop.

### 4. Report what was found

Print a brief header before processing:

```
Found {N} articles to process (since {last_date}): {new} new, {cross} cross-lists.
```

### 5. Process each article in parallel

Dispatch one subagent per article URL, all in parallel. Each subagent runs the **arxiv-article** skill for its assigned URL. Collect all summaries and print them as they arrive.

### 6. Clean up

```bash
rm -f /tmp/arxiv_catchup.html
```

### 7. Update state

After all subagents complete, write today's date:

```bash
echo "{\"last_date\": \"$(date +%Y-%m-%d)\"}" > ~/.arxiv-catchup/state.json
```

### 8. Final report

```
Processed {N} articles ({M} newly archived, {K} already cached).
Checkpoint advanced: {last_date} → {today}.
Archives: $ARXIV_DIRECTORY
```
