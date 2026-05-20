---
name: gws-pull-transcripts
description: Pull Google Meet transcripts and Gemini notes from Google Drive and save them as markdown files locally. Use when the user says "pull transcripts", "download transcripts", "sync transcripts", "get meeting notes", or wants to fetch Google Meet transcript or Gemini meeting notes from Drive.
metadata:
  openclaw:
    requires:
      bins:
        - jq
---

# Pull Google Meet Transcripts from Google Drive

Run the automation script (do not reimplement the pipeline by hand unless the script is missing or broken):

```bash
./scripts/gws-pull-transcripts.sh
```

The script downloads Google Meet transcripts and Gemini meeting notes from Google Drive (including shared drives) and saves them as markdown under `{NOTES_DIR}/transcripts/`.

## gws binary

Default: `/Users/tom.rochette/.local/share/pnpm/gws`

Override for other machines or installs:

```bash
GWS=/path/to/gws ./scripts/gws-pull-transcripts.sh
```

## Prerequisites

- `gws` CLI installed and authenticated (see `skills/gws-drive/SKILL.md`)
- `jq` installed
- `NOTES_DIR` set in `.env` (resolved via `scripts/get-env NOTES_DIR` from the repo root)
- Google Drive API enabled for your GCP project

## Behavior (reference)

- Resolves `TRANSCRIPTS_DIR` as `{NOTES_DIR}/transcripts/`
- Loads or creates `{TRANSCRIPTS_DIR}/manifest.json` keyed by Drive file id
- Searches Drive for Google Docs whose names contain `Notes by Gemini` or `Transcript`, merges and dedupes by id
- Skips ids already in the manifest
- Exports each new doc as `text/markdown`, falls back to `text/plain` if needed
- Writes filenames from the doc title (date prefix when the title has no `YYYY-MM-DD`), slug, collision suffixes `-2`, `-3`, etc.
- Prints a short summary (new count, skipped count, totals, new filenames)

For full pipeline details and manifest schema, read `scripts/gws-pull-transcripts.sh`.
