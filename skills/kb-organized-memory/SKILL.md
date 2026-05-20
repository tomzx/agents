---
name: kb-organized-memory
description: >-
  Builds theme-organized Slack channel knowledge from temporal monthly memory
  files. Use when merging notes across months for a given channel, deduplicating
  by topic, or maintaining the non-temporal “by theme” KB for that channel.
---

# Slack channel knowledge base — organized by theme

Use when creating or updating **cross-month, theme-centric** documentation for **any Slack channel** you maintain in this repo, derived from **temporal** monthly files.

**Per channel, fix a stable `<channel-slug>`** (short kebab-case id, same string as in [`slack-kb-channel`](../slack-kb-channel/SKILL.md) temporal filenames). Know the **Slack channel id** (`C…`) when you need to align with ingestion or disambiguate threads.

## Inputs (read-only)

- **Source of truth (temporal):** `memory/temporal/<channel-slug>-YYYY-MM.md` — one file per month; time-sliced channel digest.
- Optionally use **`thread-fetch-YYYY-MM-<CHANNEL_ID>.jsonl`** or **`extracted-thread-ts-YYYY-MM-<CHANNEL_ID>-valid.txt`** under `memory/temporal/` only for maintainer validation; do **not** paste thread indexes into organized output.

Do **not** treat raw Slack export folders or per-thread dumps as inputs for the organized KB.

## Outputs (canonical for “by theme”)

Write **one markdown file per theme** under **`memory/organized/<channel-slug>/`** — not a single monolithic file. Use **kebab-case** filenames and **meaningful** theme names.

**Theme index:** The authoritative map of which files exist and what each covers is **`memory/organized/<channel-slug>/README.md`** (table of themes + links). **Read it** before merging or restructuring; **update it** whenever you add, remove, rename, or split files. Do not duplicate that catalog in this skill — keep it in memory only.

**New files:** Add a **`.md` file** when a genuinely new theme appears, when an existing file is **overloaded** (hard to scan or mixed concerns), or when a topic deserves a **dedicated** home. Prefer **one clear theme per file** over stuffing unrelated bullets into the nearest match.

**Restructuring and moves:** You are not limited to **appending** to existing files. When appropriate:

- **Split** a file into two (or more) theme files; leave a short pointer in the original if readers might still look there, or **rename** the original and add redirects in `README.md` only (avoid broken links in other repos).
- **Move** bullets between theme files when the **better** home is obvious (e.g. vendor A batch auth notes belong under vendor A even if they were first filed under inference).
- **Rename** a file only when the theme boundary changed (use **kebab-case**; update **`README.md`** and any **in-repo** links to the old path).

**Stability vs clarity:** Prefer **stable filenames** once external links exist, but **clarity wins** over leaving a misfit file unchanged. When splitting or renaming, update **`README.md`** and fix links under `memory/organized/<channel-slug>/`.

**Conventions**

- **Themes** are coherent topics. Merge facts from **all** relevant months into the appropriate theme file(s); prefer the clearest or most recent wording when duplicates appear. If a theme file has grown too broad, **split** or **re-scope** per **Restructuring and moves** rather than only stacking more bullets.
- **Dates in prose:** Prefer **ISO-style slashes** — **`YYYY/MM/DD`** when a specific day matters, and **`YYYY/MM`** when only the month matters (e.g. `2026/03` for March 2026). Do **not** use English month names or abbreviations in running text (`Feb`, `Feb 2026`, `March 2026`, …); they sort poorly and read inconsistently next to `thread_ts`.
- **Temporal provenance:** where useful, tag freshness with **`YYYY/MM`** or **`YYYY/MM/DD`** (not “last month” or month names alone).
- **No thread tables:** same rule as temporal memory — findings inline with `thread_ts`, not exhaustive lists.
- **Cross-links:** point to **`memory/temporal/`** for month-specific digests; use **`memory/organized/<channel-slug>/README.md`** as the entry point for “by theme,” not a calendar.

## Workflow

1. Choose **`<channel-slug>`** (and confirm **`<CHANNEL_ID>`** if you touch ingestion artifacts).
2. List `memory/temporal/<channel-slug>-*.md` and read the months you are folding in (often all available months).
3. Extract themes, incidents, and pointers; collapse duplicates across months.
4. **Choose structure:** Decide whether existing theme files under `memory/organized/<channel-slug>/` still fit. If a file is too large, mixes unrelated concerns, or a new recurring topic appears, **split**, **move**, or **add** files (see **Restructuring and moves** above).
5. Update the relevant **`memory/organized/<channel-slug>/<theme>.md`** file(s) — including content **moved from** other theme files when you restructure.
6. Update **`memory/organized/<channel-slug>/README.md`**: theme index table, **Sources folded in** line, and links whenever you add, remove, or rename theme files. Optionally note **channel id** and human-readable channel name there for consistency with [`slack-kb-channel`](../slack-kb-channel/SKILL.md).

## Relationship to the temporal KB

| Location | Question it answers |
|----------|---------------------|
| `memory/temporal/<channel-slug>-*.md` | What happened **when** (monthly slice, Slack-era context) |
| `memory/organized/<channel-slug>/` | What matters **by topic** (stable reference across time; **one file per theme**) |

After a heavy update to temporal months, **reconcile** the organized theme files for that channel so they stay current.

## Legacy single-channel layouts

If this repo already keeps theme files at **`memory/organized/README.md`** and **`memory/organized/<theme>.md`** with **no** `<channel-slug>` directory, treat that as one channel’s layout until you migrate: same rules apply, with paths as they exist. Prefer **`memory/organized/<channel-slug>/`** for new work or when adding a second channel.
