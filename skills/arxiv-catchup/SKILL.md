---
name: arxiv-catchup
description: Fetches new arXiv cs.AI papers published since the last processed date, processes each paper's HTML version via the arxiv-article skill, and advances the date checkpoint. Use when the user says /arxiv-catchup, catch up on arXiv, or wants to read recent AI papers.
---

# arXiv Catchup

Fetches cs.AI papers from arXiv published since the last checkpoint date, calls **arxiv-article** for each, then advances the checkpoint to today.

## State file

`~/.claude/memory/arxiv/state.json`

```json
{"last_date": "2026-04-21"}
```

- If the file does not exist, use `2026-04-21` as the default start date.
- The date is always in `YYYY-MM-DD` format.
- After all articles are processed, update the file with today's date.

## Steps

### 1. Read the last-processed date

```bash
mkdir -p ~/.claude/memory/arxiv
cat ~/.claude/memory/arxiv/state.json 2>/dev/null || echo '{"last_date": "2026-04-21"}'
```

Extract the value of `last_date`.

### 2. Fetch the catchup page

```bash
curl -L --silent --max-time 60 \
  -A "Mozilla/5.0 (compatible; research-bot/1.0)" \
  "https://arxiv.org/catchup/cs.AI/{last_date}"
```

Save the response to `/tmp/arxiv_catchup.html`.

If the response is empty or the status is non-200, report the error and stop without updating state.

### 3. Extract HTML article links

Parse the downloaded HTML to find all links to the HTML version of articles. The links follow the pattern `/html/{arxiv_id}`:

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

Collect the deduplicated list of HTML URLs. If the list is still empty after both attempts, report that no HTML-version links were found on the page and stop.

### 4. Report what was found

Print a brief header before processing:

```
Found {N} articles to process (since {last_date}).
```

### 5. Process each article

For each HTML URL, invoke the **arxiv-article** skill. Work through them one at a time and print each summary as it completes so the user sees progress.

If there are more than 30 articles, ask the user whether to continue or limit to the first 30.

### 6. Clean up

```bash
rm -f /tmp/arxiv_catchup.html
```

### 7. Update state

After all articles are processed (or if the user confirms partial processing is acceptable), write today's date:

```bash
echo "{\"last_date\": \"$(date +%Y-%m-%d)\"}" > ~/.claude/memory/arxiv/state.json
```

### 8. Final report

```
Processed {N} articles ({M} newly archived, {K} already cached).
Checkpoint advanced: {last_date} → {today}.
Archives: ~/.claude/memory/arxiv/articles/
```
