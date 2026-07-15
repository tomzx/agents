---
name: sync-documentation
description: Reconcile the docs/ directory with the codebase so documentation stays current. Detects and fixes drift between code and docs (stale references, missing docs, broken links, nav drift, outdated examples). Use when the user says /sync-documentation, "sync docs", "update docs", "docs are stale", or wants to ensure docs match the current code.
argument-hint: "[docs-path] [--fix] [--check-links]"
---

TODAY=!`date +%Y-%m-%d`

# Sync Documentation

Reads the codebase and reconciles the `docs/` directory against it.
On every run it detects drift between code and documentation, classifies each drift item, and (with `--fix`) applies the updates that are safe to make mechanically.
Unlike `sync-sdlc` (which reconciles `.sdlc/` artifacts), this skill reconciles the user-facing `docs/` tree: the prose people actually read.

## The Core Problem This Solves

Code changes constantly; documentation changes when someone remembers to update it. The result is docs that reference functions renamed three releases ago, CLI flags that no longer exist, code examples that fail to run, and nav entries pointing at deleted files.
`/find-documentation-gaps` reports *what is missing*. This skill goes further: it detects *every* flavor of drift (stale, missing, broken, outdated), fixes the mechanical ones automatically, and hands the rest to a human as a prioritized report.

## Prerequisites

- Working directory is the root of the repository
- A `docs/` directory exists (or the `$1` path points at one). If neither exists, report that there is nothing to sync and suggest `/setup-docs-site`.
- Read access to the source tree and `docs/`
- Optional: a docs build tool installed to verify the build (`mkdocs`, `sphinx-build`, `npm`)
- `git` repository with commit history (used to scope drift to recent changes when `--fix` is off)

## Drift Scenarios This Skill Detects

| Drift | Root Cause | Fixable With `--fix` |
|---|---|---|
| Doc references a function/class/symbol that no longer exists | Code renamed or removed | yes (rename or flag) |
| Code example uses a renamed or removed API | Example not updated with the code | yes |
| Doc references a CLI flag or subcommand that no longer exists | CLI changed | yes |
| Doc references a config key or env var that no longer exists | Config changed | yes |
| Public API, CLI command, or endpoint has no doc at all | New code added without docs | no (needs writing) |
| Function signature in code (params, defaults) differs from the doc | Signature changed | yes |
| `mkdocs.yml` `nav` lists a file that does not exist | Doc deleted, nav not updated | yes |
| Doc file exists but is not referenced in `nav` | Doc added, nav not updated | yes |
| Internal doc link points to a moved or deleted page | Refactor of doc structure | yes |
| External link is broken (404) | Upstream moved or vanished | no (report only) |
| Doc duplicates information now stale vs `README.md` / `CHANGELOG.md` | Single source of truth broken | no (report) |
| Docs build fails | Any of the above, or config error | no (report) |

## Mode

- **Report mode (default):** detect all drift, classify it, and print a prioritized report. No files change. Safe to run anytime.
- **Fix mode (`--fix`):** also apply the mechanical fixes listed above. Missing-documentation items are *never* auto-written (prose needs a human); they are reported so they can be written with `/create-documentation`.

## Steps

### 1. Parse arguments and locate the docs root

- `$1` (optional): path to the docs directory. Defaults to `docs/`.
- `--fix`: apply mechanical fixes after detecting drift.
- `--check-links`: validate external links via HTTP HEAD (slow; off by default).
- If the docs root does not exist, report "nothing to sync" and suggest `/setup-docs-site`, then stop.

### 2. Identify the docs tooling and structure

Detect the generator to know which files are authoritative:

```
ls mkdocs.yml mkdocs.yaml conf.py docusaurus.config.js .vitepress/config.* docs/ 2>/dev/null
```

Build a model of the doc tree:

| Signal | Meaning |
|---|---|
| `mkdocs.yml` | MkDocs; `nav:` is the source of truth for page ordering |
| `conf.py` | Sphinx; `toctree` directives and `index.rst` are authoritative |
| `docusaurus.config.js` / `sidebars.js` | Docusaurus; sidebar config lists pages |
| plain `docs/**/*.md` | No generator; every markdown file is a page |

### 3. Verify the docs build

Run the project's own build command if one exists:

```
mkdocs build --strict 2>&1 | tail -40
sphinx-build -W -b html docs docs/_build 2>&1 | tail -40
npm run build 2>&1 | tail -40
```

`--strict` / `-W` turn warnings (broken references, missing files) into errors, which surfaces nav and link drift directly.
Record pass/fail and capture the warnings for the report. Do not fail the whole skill on a broken build; a broken build is itself a finding.

### 4. Check nav / sidebar consistency

For MkDocs, parse `mkdocs.yml` `nav:` and compare against `docs/**/*.md`:

- **Missing files (nav drift):** entries in `nav` whose target file does not exist. With `--fix`, remove the entry (and note it).
- **Orphaned pages:** markdown files under `docs/` not reachable from `nav`. With `--fix`, add them under a sensible section or flag them.

For Sphinx, walk `toctree` directives in `.rst` files the same way.
For Docusaurus, parse `sidebars.js`.
For a plain docs dir, every top-level `.md` is considered "in nav"; skip this check.

### 5. Detect stale symbol references

Extract symbols referenced from docs (inline code and fenced blocks) and check they still exist in the source.

```
# Symbols in backticks within docs
grep -roh --include="*.md" --include="*.rst" '`[A-Za-z_][A-Za-z0-9_.]*`' docs/ 2>/dev/null \
  | sed 's/`//g' | sort -u
```

For each referenced symbol, confirm it exists in the source tree (use `grep -r` over `--include="*.py" --include="*.ts" --include="*.go"` etc., or an AST-based lookup for precision).
A symbol that appears in docs but nowhere in source is **stale**. With `--fix`, attempt a rename resolution (see step 7); otherwise flag it.

### 6. Detect missing documentation

Run the read-only scan from `/find-documentation-gaps` (conceptually, or by invoking it) to find public APIs, CLI commands, endpoints, and config keys that have no corresponding doc. These are reported but never auto-written.

### 7. Detect outdated code examples and signatures

For each fenced code block and signature shown in docs that maps to a real symbol, compare against the live definition:

- Function/method: do the parameter names, order, and defaults in the doc match the source signature?
- CLI: do the flags and subcommands shown still exist (check `--help` output or the command definitions)?
- Config: do the keys and their default values match the current config schema / `.env.example`?

A mismatch is an **outdated example**. With `--fix`, regenerate the snippet from the current source (signatures, `--help` output, config dump) where it can be done losslessly. If the example has surrounding prose that would be invalidated, flag it instead of rewriting.

### 8. Check internal links

Resolve every relative link and `[[wikilink]]` in the docs against the current file tree:

```
grep -rn --include="*.md" -E '\]\([^)]+\)|\[\[[^]]+\]\]' docs/ 2>/dev/null
```

- A link to a path that does not resolve (accounting for `mkdocs` extensionless conventions) is **broken**.
- With `--fix`, attempt to resolve via the rename map built in step 5/7 (e.g., a moved file); otherwise flag.

### 9. Check external links (only with `--check-links`)

For each `http(s)://` link in docs, issue a HEAD request. Report any non-2xx/3xx as a broken external link. Never auto-edit external links (a redirect may be intentional).

### 10. Apply fixes (only with `--fix`)

Apply, in order, the mechanical fixes identified above:

1. Remove/repair broken nav entries.
2. Add discoverable orphaned pages to the nav.
3. Rename stale symbols using the rename map (commit history `git log --follow` / `git log -p` reveals renames).
4. Regenerate outdated signature/CLI/config snippets from source.
5. Repair internal links using the rename map.

After applying, **re-run the docs build** (step 3) to confirm the fixes did not introduce new errors. If the build regresses, revert the offending fix and report it as needing manual review.

### 11. Write the sync report

Produce the report (see Output Format). If `--fix` was used, summarize what changed and what still needs a human.

## Output Format

```markdown
---
date: "{TODAY}"
mode: "report | fix"
docs_root: "<docs path>"
build: "pass | fail"
status: complete
---

# Documentation sync report - <Project Name>

**Date:** {TODAY}
**Mode:** report / fix
**Docs root:** docs/
**Build:** pass / fail (<error count> warnings)

## Summary

| Category | Stale | Missing | Broken | Outdated | Total |
|---|---|---|---|---|---|
| Symbols & APIs | N | N | - | N | N |
| CLI & config | N | N | - | N | N |
| Navigation | N | - | N | - | N |
| Links (internal) | - | - | N | - | N |
| Links (external) | - | - | N | - | N |
| Code examples | - | - | - | N | N |
| **Total** | N | N | N | N | N |

## Build Warnings

| File | Warning |
|---|---|
| docs/api.md | <warning text from mkdocs/sphinx> |

## Stale References (doc mentions, code no longer has)

| Doc file | Line | Symbol | Likely rename |
|---|---|---|---|
| docs/usage.md | 42 | `oldFuncName` | `newFuncName` |

## Missing Documentation (code has, doc does not)

| Symbol / surface | Type | Location | Visibility |
|---|---|---|---|
| `Client.connect` | method | src/client.py:88 | high |
| `--retries` | CLI flag | cli.py:120 | high |

## Outdated Examples

| Doc file | Line | What changed |
|---|---|---|
| docs/getting-started.md | 18 | `connect(timeout=30)` default is now `60` |

## Navigation Drift

| Entry | Status |
|---|---|
| nav -> Reference -> legacy.md | missing file |
| docs/advanced.md | not in nav (orphaned) |

## Broken Links

| Doc file | Line | Target |
|---|---|---|
| docs/guide.md | 7 | ./old-path.md |

## Fixes Applied

(Only present in fix mode.)

| Fix | Files changed |
|---|---|
| Renamed `oldFuncName` -> `newFuncName` | docs/usage.md |
| Removed dead nav entry `legacy.md` | mkdocs.yml |
| Regenerated CLI flags table from `--help` | docs/cli.md |

## Reverted (fix broke the build)

| Fix | Reason |
|---|---|
| <description> | build failed after applying; reverted |

## Next Steps

1. Write the missing docs (highest visibility first) with `/create-documentation`.
2. Review items needing manual review.
3. Rebuild and preview: `mkdocs serve` / `sphinx-build` / `npm run dev`.
4. Commit docs changes.
```

## Example Usage

**Scenario 1: Routine drift check**
```
/sync-documentation
```
Reports that `docs/api.md` references `Client.fetch` (renamed to `Client.get`), two new CLI flags are undocumented, and `nav` points at a deleted `legacy.md`. No files change.

**Scenario 2: After a refactor, apply safe fixes**
```
/sync-documentation docs --fix
```
Renames `Client.fetch` -> `Client.get` across docs, removes the dead `legacy.md` nav entry, regenerates the CLI flags table from current `--help` output, and re-runs `mkdocs build --strict` to confirm green. Reports the 3 missing-docs items it could not auto-write.

**Scenario 3: Catch broken external links before a release**
```
/sync-documentation --check-links
```
Same drift checks plus an HTTP HEAD sweep of every external link. Reports two 404s pointing at upstream docs that moved.

**Scenario 4: Sphinx project**
```
/sync-documentation
```
Detects `conf.py`, walks `toctree` directives, runs `sphinx-build -W`, and flags a `.rst` file that references a removed module.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `sync-sdlc` | Reconciles `.sdlc/` artifacts with code. This skill is the docs counterpart, reconciling the `docs/` tree with code. |
| `sync-repository` | Orchestrator that runs the full consistency pipeline; its Document phase calls `/find-documentation-gaps`. This skill is a deeper, write-capable docs reconciliation that can be run standalone or used inside that phase. |
| `find-documentation-gaps` | Read-only scanner that finds *missing* docs. This skill reuses that detection and adds stale, broken, outdated, and nav drift, plus fixes. |
| `setup-docs-site` | Scaffolds the docs infrastructure (mkdocs.yml, workflow). Run this first if no `docs/` exists; run `sync-documentation` afterward to keep it current. |
| `create-documentation` | Writes new doc content following Divio. Use it to address the missing-documentation items this skill reports. |
| `review-documentation` | Reviews doc *quality* (clarity, accuracy, structure). This skill reconciles doc *correctness* against code. |
| `divio-documentation` | Reference for which doc type to write when this skill reports a gap. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `mkdocs build --strict` | Build MkDocs; warnings become errors (surfaces broken refs/nav) |
| `sphinx-build -W -b html docs docs/_build` | Build Sphinx with warnings as errors |
| `grep -rn --include="*.md" '\]\(' docs/` | Find all markdown links for internal-link checks |
| `grep -roh --include="*.md" '\`[A-Za-z_][A-Za-z0-9_.]*\`' docs/` | Extract backticked symbols referenced in docs |
| `git log --follow -p -- <file>` | Trace a renamed/removed symbol back to its current name |
