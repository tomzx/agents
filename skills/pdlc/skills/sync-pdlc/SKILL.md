---
name: sync-pdlc
description: Reconcile the .pdlc/ directory with current product reality — create the structure if absent, detect drift, and ensure the anchor exists. The PDLC counterpart of sync-sdlc.
argument-hint: "[project-root]"
---

# Sync PDLC

Analyzes the current state of the product/project against `.pdlc/` and reconciles it: creates the structure if absent (via `initialize-pdlc-directory`), detects drift between artifacts and reality, and ensures the PDLC anchor and context files are present and current. Read-mostly; it reports drift and only writes to heal structure, not to rewrite initiative content.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- Write access to the project root.

## Steps

1. If `.pdlc/` does not exist, run `initialize-pdlc-directory` and then continue.
2. Verify the directory tree matches the canonical structure (context, initiatives, decisions, learnings, templates). Create any missing subdirectories.
3. Ensure `.pdlc/.gitignore` excludes local-only state (`state.yml`, `initiatives/*/progress.md`); create or repair it if missing or stale.
4. Ensure the PDLC anchor exists in the repo's primary agent-instruction file (per `references/shared.md`); create or refresh it if missing.
5. Ensure context files exist (`product-overview.md`, `vision.md`, `goals.md`, `roadmap.md`, `vocabulary.md`); seed any missing ones from templates without overwriting existing content.
6. Detect drift:
   - **Orphaned initiatives:** directories whose artifacts reference phases that have moved on, or that have no decision records.
   - **Stale decisions:** gate decisions whose verdict no longer matches the artifacts (e.g., a `proceed` to Define with no `prd.md`).
   - **Missing artifacts:** initiatives whose current phase implies an artifact that is absent.
   - **Unmirrored writes:** when `PDLC_DIR` is set, context/initiative artifacts missing from the mirror.
7. Write a reconciliation report to `.pdlc/sync-meta.yml` (repo-only) plus a human-readable summary. Regress stale gate decisions to `pivot` where the artifacts no longer support `proceed`, so the forward loop resyncs them.

## Output Format

```
## PDLC sync

Structure: ok / repaired (<list>)
Anchor: present / created / refreshed
Context files: <missing ones seeded>

### Drift
| Initiative | Finding | Action |
|---|---|---|
| INIT-3 | stale: validate:proceed but no experiment-result.md | regressed to pivot |

### Mirror (PDLC_DIR)
<paths written to repo / mirror / both>
```

## Outcome

If `$OUTCOME_YAML` is set:

| Verdict | When |
|---|---|
| `aligned` | No drift detected |
| `drift-detected` | Drift found and gates regressed; resync needed |
| `initialized` | `.pdlc/` was absent and has been created |

## Next Step

Address regressed gates by re-running the relevant phase skill in revision mode, or run `audit-outcomes` for a full chain trace.
