---
name: what-to-demo
description: Review notes from the past two weeks to determine what could be demoed.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=`date +%Y-%m-%d`
YEAR=`date +%Y`
MONTH=`date +%m`
DAY=`date +%d`

# Identify What to Demo

Scans two weeks of daily notes to surface completed features, notable improvements, and interesting work that would make good demonstration material.

## Prerequisites

- `NOTES_DIR` environment variable set, containing daily note files
- `scripts/get-env` utility available
- At least one week of daily notes present in `{BASE_DIR}`

## Steps

1. Resolve the notes directory:
   ```
   scripts/get-env NOTES_DIR
   ```
2. Identify daily note files from the past two weeks within `{BASE_DIR}`.
3. Read each file and extract: completed features, notable changes, and improvements with visible results.
4. Rank items by demo-worthiness: prefer work with visible outputs, user impact, or technical novelty.
5. Write the output to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.what-to-demo.md`.

## Example Usage

**Scenario 1: Sprint demo preparation**
```
/what-to-demo
```
Reviews 10 days of notes, finds 4 completed features. Output lists them ranked by impact with a one-line description of what to show for each.

**Scenario 2: Light two weeks**
Few notes with mostly maintenance work. Output notes that demo material is limited, highlighting the one user-visible improvement found.

**Scenario 3: Multiple significant features**
Notes reference a new API endpoint, a UI redesign, and a performance optimization. All three appear in the output with brief suggested demo scripts.

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `date +%Y-%m-%d` | Get today's date for output filename |
