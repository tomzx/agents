---
name: sync-agent-machine
description: Refresh the indexes of an agent machine context by rebuilding stale or missing index files and indexing directories that appeared under /* manifest paths. Use when the user says /sync-agent-machine, "sync agent machine", "refresh agent indexes", "re-index my directories", or wants agent machine indexes brought up to date.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*, date:*, find:*)
argument-hint: "[manifest-path] [directory ...]"
---

# Sync Agent Machine

Brings an agent machine context back in sync with reality: every directory listed in `agent-machine.yaml` ends up with an accurate, current index file, and directories that vanished are reported.

This skill owns freshness; `setup-agent-machine` owns bootstrapping; `index-directory` owns the format of a single index.

## Prerequisites

- An agent machine context with `agent-machine.yaml` in the current working directory (or the manifest path given as `$1`).
- If no manifest exists, stop and point the user to `/setup-agent-machine` instead of creating one.
- Optional `$2`, `$3`, ...: directories whose indexes are refreshed regardless of staleness.
- Reuse the stale rules from `setup-agent-machine`: an index is stale if its `Last indexed` date is older than 30 days, or its directory changed since it was written.

## Steps

### 1. Load and expand the manifest

Read `agent-machine.yaml` and expand every `/*` entry into the concrete child directories it currently contains.
Record the manifest's own comments (the per-path one-line descriptions) so they can be handed to `index-directory`.

### 2. Classify each directory

For every expanded directory, compare it against `indexes/` and place it in exactly one class:

| Class | Test |
|-------|------|
| Missing | No index file with its sanitized name exists |
| Stale | `Last indexed` older than 30 days, or top-level content is newer than the index file (`find <dir> -maxdepth 1 -newer <index>`), or listed in the arguments |
| Current | Index exists and neither stale test fires |
| Vanished | Directory no longer exists on disk |

### 3. Handle vanished directories

Report every vanished directory and ask the user, per directory, whether to remove its manifest entry and delete its index file.
Never delete either without confirmation.
If a vanished path was a `/*` entry itself, keep the entry (its children may return) and only remove the index file.

### 4. Rebuild the indexes

For every missing and stale directory, delegate to `skills/index-directory/SKILL.md`, passing the directory as `$1` and `indexes/<name>.md` as `$2`.
Rebuild indexes one directory at a time and keep going past individual failures, reporting them at the end.

### 5. Check the context files

- If `AGENTS.md` is missing or lacks the `Agent machine context` marker, suggest running `/setup-agent-machine`.
- If the manifest references directories that were pruned, confirm the YAML is still valid after your edits.

### 6. Verify and report

1. Confirm every non-vanished manifest directory has an index with today's `Last indexed` date (for the ones you rebuilt).
2. Report using the output format below.

## Output Format

```markdown
## Agent machine sync (<date>)

Manifest: <path> (N paths, N directories after expansion)

### Indexes
- Created: N
- Refreshed: N
- Still current: N
- Vanished: N

| Action | Index file | Directory |
|--------|------------|-----------|
| created / refreshed / current / removed | indexes/<name>.md | <path> |

### Failures
- <directory>: <reason> (or "none")

### Next steps
1. Run /setup-agent-machine to add new paths to the manifest.
2. Re-run /sync-agent-machine whenever directories change significantly or after 30 days.
```

## Example Usage

**Scenario 1: Routine refresh**
```
/sync-agent-machine
```
Expands 5 manifest paths into 19 directories, finds 3 stale indexes (older than 30 days), rebuilds those three, reports 16 still current.

**Scenario 2: New directories under a glob path**
```
/sync-agent-machine
```
A new project appeared under `~/src/*`. It has no index, so it is classified missing and indexed, while everything current is left untouched.

**Scenario 3: Force refresh specific directories**
```
/sync-agent-machine ~/notes/journal
```
Rebuilds only the journal index even though it is not stale, because the user reorganized it and wants the index to reflect the new layout.
