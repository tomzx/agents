---
name: identify-feature-opportunities
description: Analyze the existing software surface and surrounding signals (code, issues, recent PRs, goals, roadmap) to generate and rank new feature opportunities that would add value. The bottom-up discovery counterpart to create-roadmap and create-goals, and the inverse of create-needs-assessment (which validates a given idea rather than proposing one). Use when the user says /identify-feature-opportunities, "what should we build next", "find feature ideas", "product opportunities", "feature gaps", "what's missing", or wants a periodic discovery pass. Designed to run safely on a monthly schedule or on demand.
argument-hint: "[repository] [--create-issues N] [--limit N] [--focus <area>] [--since <YYYY-MM-DD>]"
allowed-tools: Bash(gh:*, ghx:*), Read, Glob, Grep, Write
---

TODAY=!`date +%Y-%m-%d`
REPO=!`git remote get-url origin 2>/dev/null | sed -E 's#.*[:/]([^/]+/[^/]+)(\.git)?$#\1#'`

# Identify Feature Opportunities

Surfaces **new** feature opportunities by reading the software as it actually exists today and the signals around it, then synthesizing concrete, evidenced ideas ranked by value and strategic fit. This is discovery: it proposes work that does not yet exist, unlike `prioritize-issues` (ranks existing issues), `check-issues-status` (finds done work), or `create-needs-assessment` (validates one proposed idea).

## The Core Problem This Solves

Roadmaps and backlogs fill up from incoming requests, but they rarely get a bottom-up re-derivation from the software itself. Capabilities get 80% built and abandoned, adjacent expansion paths go unnoticed, repeated issue themes never get generalized into a feature, and stated goals sit with no corresponding code. This skill reads the codebase as evidence of what exists and proposes what is missing.

## Prerequisites

- Working directory is the root of a `git` repository
- `gh` CLI authenticated with read access to the target repository (for issue and PR signals)
- Read any files under `.sdlc/context/` (`project-overview.md`, `goals.md`, `roadmap.md`, `architecture.md`) for strategic context. These are optional but materially improve alignment scoring.
- If no argument is provided, operate on `$REPO` (derived from `origin`), then the current working directory.

## Inputs Synthesized

The skill reasons over five evidence sources. Each opportunity must cite at least one; strong opportunities cite two or more.

| Source | What it reveals |
|---|---|
| **Code surface** | CLI commands, API endpoints, UI screens, modules, config keys. What exists, what is stubbed, what is asymmetrically mature. |
| **`.sdlc/context/`** | Stated goals, roadmap initiatives, positioning. Used to score alignment and to find goals with no backing code. |
| **Open + recent issues** | User pain and requests. Clusters of same-theme issues signal unmet need, not random bugs. |
| **Merged PR history** | Recent themes and velocity. Momentum in one area hints at adjacent expansion. |
| **README / docs** | Stated capabilities vs. actual. Positioning reveals the product category and its expected feature set. |

## Opportunity Dimensions

Opportunities are derived from seven recurring patterns. Scan for each.

| Dimension | Signal in the code / signals | Example opportunity |
|---|---|---|
| **Surface gaps** | `TODO`/`FIXME`/`stub`/`NotImplemented`, feature flags wired but unused, config keys with no implementation, endpoints that error or return placeholder data | "The `/export` endpoint returns 501; implement CSV export." |
| **Usage asymmetry** | A rich subsystem next to a thin one. Create exists but no list/show; write but no read; sync but no async; one resource type fully built, a sibling resource half-built | "Orders have full CRUD; refunds support create only. Add list, show, update." |
| **Adjacent expansion** | Natural X→Y capability extensions: CRUD→bulk, API→webhooks, manual→automation, CLI→API, sync→async/streams, single-tenant→multi-tenant | "The API has no outbound webhooks; add event delivery so integrations react instead of poll." |
| **Issue theme clusters** | Three or more open issues around the same theme (exports, integrations, auth, performance) | "Four open issues ask for different export formats; generalize into an export framework." |
| **Roadmap/code gaps** | A roadmap initiative or goal with no corresponding feature directory or code | "Roadmap lists 'internationalization' for Q3; there is no i18n code yet. Start it." |
| **Adoption blockers** | Missing foundational capability that limits who can use the software: no auth, no rate limiting, no multi-tenancy, no offline mode, no audit log | "No authentication; every endpoint is public. Add auth to unlock enterprise use." |
| **Comparative gaps** | README positioning implies a category whose standard capabilities are absent here | "Positioned as a 'data pipeline tool' but has no scheduling or retry. Add a scheduler." |

## Scoring

Each opportunity is scored so the output is ranked, not just listed. Reuse the RICE framing from `prioritize-issues`, extended with an alignment multiplier.

```
score = (Reach × Impact × Confidence × Alignment) / Effort
```

| Factor | Scale | Meaning |
|---|---|---|
| Reach | 1–10 | How many users / callsites are affected per period |
| Impact | 1–5 | Effect on the product goal (1=minimal, 5=massive) |
| Confidence | 0.5–1.0 | Strength of the evidence cited (code signal > issue cluster > inference) |
| Alignment | 0.5–1.5 | Fit with `.sdlc/context/goals.md` and `roadmap.md` (1.0 = neutral, 1.5 = directly on a stated initiative, 0.5 = off-strategy) |
| Effort | 0.5–5 | Person-weeks of work required |

When `.sdlc/context/` is absent, Alignment defaults to 1.0 for all opportunities and a note is added to the report.

## Flags

- `--create-issues N` — file GitHub issues for the top N opportunities via `/create-issue`. Off by default (report-only). Each issue links back to this report.
- `--limit N` — maximum opportunities to surface (default 20). The report shows the top N by score.
- `--focus <area>` — restrict the scan to one area (e.g., `api`, `ui`, `cli`, a module path or a roadmap initiative slug). narrows the code surface scanned.
- `--since <YYYY-MM-DD>` — only consider issues and PRs from this date forward when reading signals (default: last 90 days). Useful for a focused recent-signal pass.

## Dedup (makes re-runs idempotent and safe to schedule)

Before surfacing an opportunity, check it is not already tracked:

1. Read the most recent prior report at `.sdlc/feature-opportunities-*.md`. Opportunities carried over keep their original ID and are marked `recurring` with the first-seen date, not re-proposed as new.
2. Search open issues for overlapping requests:
   ```
   gh search issues --repo <repo> --state open --limit 50 "<keyword>"
   ```
   If an open issue already requests the capability, link it and mark the opportunity `requested: #N` rather than proposing it fresh.
3. Carry forward the opportunity ID sequence from the prior report so numbering is stable across runs.

This makes monthly scheduled runs low-noise: only genuinely new opportunities appear as new rows.

## Steps

### 1. Resolve scope and read context

Resolve the repository from `$1`, then `$REPO`, then the current directory. Read `.sdlc/context/` files that exist. Record whether goals/roadmap are present (they govern Alignment scoring). Apply `--focus` if given.

### 2. Map the code surface

Enumerate the actual capability surface. Use the language-appropriate discovery:

- **CLI**: commands and subcommands, flags, `--help` output
- **API**: routes/endpoints (grep for route decorators: `@app.route`, `@router`, `app.get`, handlers), request/response schemas
- **UI**: screens, pages, routes (if a frontend is present)
- **Modules**: top-level packages and their public exports
- **Config**: keys, feature flags, environment variables

```
grep -rEn "TODO|FIXME|stub|NotImplemented|not implemented|501|placeholder" --include="*.py" --include="*.ts" --include="*.go" --include="*.js" .
```

Record each capability and its maturity (full / partial / stub).

### 3. Read issue and PR signals

Pull the last 90 days (or `--since`) of issues and merged PRs:

```
gh search issues --repo <repo> --state open --limit 100 --json number,title,labels,createdAt
gh search prs --repo <repo> --state closed --merged --limit 100 --json number,title,mergedAt
```

Group open issues by theme (label, keyword, or inferred topic). Any cluster of 3+ same-theme issues becomes an "issue theme cluster" opportunity candidate.

### 4. Derive opportunities

Apply the seven Opportunity Dimensions to the evidence collected. For each candidate opportunity, record:

- The dimension it came from
- The concrete evidence (file:line, issue numbers, roadmap initiative)
- A one-sentence opportunity statement (the value to the user, not the implementation)
- RICE + Alignment scores

### 5. Dedup against prior reports and open issues

Run the Dedup checks. Drop or annotate candidates already tracked. Assign stable IDs continuing the sequence from the prior report.

### 6. Rank and select

Sort by score descending. Apply `--limit`. Group by dimension in the output for readability, but order groups by their top opportunity's score.

### 7. Write the report

Write to `.sdlc/feature-opportunities-<TODAY>.md` (repo only; never mirrored to `SDLC_DIR`). Use the Output Format below.

### 8. Optional issue creation

If `--create-issues N` was passed, file the top N via `/create-issue`. Each issue body cites the evidence and links back to this report. Use a `feature-opportunity` label (create it if absent). Do not file issues without the flag.

## Output Format

```markdown
---
date: "<TODAY>"
repository: "<repo>"
scope: "<focus or whole project>"
since: "<signal window>"
goals_present: <true|false>
status: complete
---

# Feature Opportunities — <repo>

**Date:** <TODAY>
**Scope:** <whole project | focus area>
**Signals window:** issues/PRs since <date>
**Strategic context:** goals.md <present|absent>, roadmap.md <present|absent>

## Summary

- Opportunities surfaced: N (M new, K recurring, L already requested)
- Top dimension: <dimension>
- Top score: <score> — <opportunity title>

## Ranked Opportunities

| Rank | ID | Opportunity | Dimension | Evidence | R | I | C | A | Effort | Score | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FO-7 | Add outbound webhooks for order events | Adjacent expansion | `src/api/orders/*`; PR #88 momentum | 8 | 5 | 0.9 | 1.5 | 3 | 18.0 | new |
| 2 | FO-3 | Implement CSV/JSON export (endpoint 501) | Surface gap | `src/api/export.py:42` returns 501; issues #12 #31 #44 | 7 | 4 | 1.0 | 1.0 | 2 | 14.0 | requested: #12 |
| 3 | FO-8 | Start i18n work (roadmap Q3) | Roadmap/code gap | roadmap.md "internationalization"; no i18n code | 6 | 4 | 0.8 | 1.5 | 4 | 7.2 | new |

## By Dimension

### Adjacent expansion (N)
- **FO-7 — Add outbound webhooks for order events**
  - **Value:** Integrations react to events instead of polling.
  - **Evidence:** `src/api/orders/*` is the most active subsystem (PR #88, #91); no webhook delivery code exists.
  - **Alignment:** Directly serves roadmap initiative "platform integrations".
  - **Suggested next step:** `/create-needs-assessment` (validate delivery semantics before building).

### Surface gaps (N)
...

## Recurring (carried over from prior runs)

| ID | Opportunity | First seen | Status |
|---|---|---|---|
| FO-2 | Add bulk operations to refunds API | 2026-06-03 | recurring (still open) |

## Already requested (not re-proposed)

| Opportunity | Open issue |
|---|---|
| Dark mode | #15 |
| SSO login | #22 |

## Recommended Next Steps

| Rank | Opportunity | Next step |
|---|---|---|
| 1 | FO-7 | `/create-needs-assessment` then `/create-issue` |
| 2 | FO-3 | `/create-issue` (evidence is strong, skip needs-assessment) |
| 3 | FO-8 | `/create-roadmap` (strategic, not immediate) |
```

## Scheduling (Monthly Cadence)

This skill is designed to run safely unattended on a schedule. Properties that make this safe:

- **Read-only by default.** No commits, no PRs, no pushes unless `--create-issues` is passed.
- **Idempotent.** Stable opportunity IDs, dedup against prior reports and open issues, so monthly runs only surface genuinely new opportunities.
- **Bounded output.** `--limit` caps the report size.
- **No side effects on the codebase.** Writes only to `.sdlc/feature-opportunities-<date>.md`.

Recommended cadence: **monthly**. Feature discovery does not need to be weekly; the surface and signals shift on a sprint-to-month timescale.

Scheduling options (same as `improve-codebase`):

- **Paperclip routine:** create a routine with a monthly cron trigger (e.g., `0 9 1 * *` for the 1st of each month at 09:00) whose execution instructs the agent to run `/identify-feature-opportunities`.
- **GitHub Actions:** a monthly schedule that invokes the agent CLI with `/identify-feature-opportunities` (report-only) and commits the report, or opens issues with `--create-issues 3`.
- **Manual:** run `/identify-feature-opportunities` at the start of each month as input to `/create-roadmap` or `/start-month`.

Pair naturally with `/start-month` (discovery feeds monthly planning) and `/create-roadmap` (opportunities become roadmap candidates).

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `create-needs-assessment` | Validates one proposed idea. This skill *generates* the ideas to validate. Pipeline: identify-feature-opportunities → create-needs-assessment → create-requirements. |
| `create-roadmap` / `create-goals` | Top-down strategy. This is the bottom-up discovery that feeds them. |
| `prioritize-issues` | Ranks existing issues. This proposes *new* work not yet in the backlog. |
| `check-issues-status` | Finds already-implemented issues to close. This finds unbuilt capabilities to open. Opposite directions of backlog hygiene. |
| `create-issue` | Consumed by `--create-issues` to file the top opportunities. |
| `select-issue` | Operates on the prioritized backlog this skill helps populate. |
| `customer-research` | Gathers external (customer) signals. This synthesizes internal (code + issue) signals. Complementary. |
| `audit-sdlc` | Looks *inward* at code and architecture quality (organized by the ISO/IEC 25010 model). This looks *outward* at new value to add. |

## Example Usage

**Scenario 1: Monthly discovery pass (the default)**
```
/identify-feature-opportunities
```
Reads the whole codebase, last 90 days of issues/PRs, and `.sdlc/context/`. Surfaces 12 opportunities ranked by score. Writes `.sdlc/feature-opportunities-2026-08-03.md`. No issues filed.

**Scenario 2: Discovery that files the top 3**
```
/identify-feature-opportunities --create-issues 3
```
Same scan, then files the top 3 as GitHub issues labeled `feature-opportunity`, each linking back to the report.

**Scenario 3: Focused API pass**
```
/identify-feature-opportunities --focus api
```
Restricts the surface scan to the API layer. Useful when the API is the product's growth surface.

**Scenario 4: First run, no .sdlc context yet**
```
/identify-feature-opportunities
```
Goals and roadmap absent, so Alignment defaults to 1.0 for all. Report notes that strategic context was missing and recommends running `/create-goals` and `/create-roadmap` to improve future scoring.

**Scenario 5: Quarterly signal window**
```
/identify-feature-opportunities --since 2026-04-01
```
Only considers issues and PRs from Q2. Useful for a quarterly planning review.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh search issues --repo <repo> --state open --limit 100 --json number,title,labels,createdAt` | Open issue signals |
| `gh search prs --repo <repo> --state closed --merged --limit 100 --json number,title,mergedAt` | Recent merged PR themes |
| `gh search issues --repo <repo> --state open "<keyword>"` | Dedup: is this already requested? |
| `grep -rEn "TODO\|FIXME\|NotImplemented\|501\|stub" --include="*.py" .` | Surface-gap scan |
| `grep -rEn "@(app\|router)\.(get\|post\|put\|delete\|patch)" --include="*.py" .` | API surface enumeration |
