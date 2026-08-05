---
name: pdlc
description: Run the full product development lifecycle loop, from discovery through launch and measurement, with proceed/pivot/kill gates at every phase.
argument-hint: "[phase-name]"
---

# Product Development Lifecycle

Orchestrates the full PDLC loop by invoking phase skills in sequence.
Each phase consumes the previous phase's artifact and ends in a gate (`make-decision`) with verdict `proceed` / `pivot` / `kill`.
Pass an optional phase name to enter the loop at a specific stage.

PDLC wraps SDLC: it decides *whether* and *what* to build, hands the *how* off to SDLC at `define-acceptance`, then closes the loop with launch and measurement.

## When to Use `/pdlc` vs Individual Skills

- Use **`/pdlc`** (with an optional phase name) when you want the orchestrator to run multiple phases, manage gates and backtracking, and maintain run state.
The PDLC phase skills are **internal sub-skills** bundled under this `pdlc` skill at `skills/pdlc/skills/<name>/SKILL.md`. They are not individually discovered as slash commands, so only `/pdlc` is directly invocable; the orchestrator loads each phase by reading its file (see *Load Each Phase Sub-Skill* below).

## Load Each Phase Sub-Skill (mandatory)

Before performing any work that belongs to a phase, read that phase's sub-skill file at `skills/pdlc/skills/<name>/SKILL.md` (use the Read tool) so its workflow, gates, and commit rules are in context.
Never execute a phase's actions from memory or general knowledge.
This applies at every phase transition, on every entry point and fast path.
If you reach a phase that commits, pushes, or opens a PR and its sub-skill is not yet read, read it before doing anything else, then follow its workflow.

## Loop Overview

```
The PDLC loop — 6 phases (entry: problem → measure)

  Phase 1 — Discover (divergent: find problems worth solving)
  discover-problems     Synthesize JTBD, interviews, and problem statements
  research-market       Size the market, map trends and segments
  analyze-competition    Map the competitive landscape and positioning gaps
  frame-opportunities    Build an opportunity-solution tree, scored
          │
          ▼  GATE (make-decision: proceed / pivot / kill)
  Phase 2 — Validate (converge or kill, before any build)
  map-assumptions        List hypotheses, beliefs, and risks ranked by leverage
  design-experiment      Design the cheapest decisive test (fake-door, concierge, prototype, survey)
  run-experiment         Execute, collect data, record a verdict
          │
          ▼  GATE (make-decision: proceed / pivot / kill)
  Phase 3 — Strategy (decide where to focus)
  define-vision          Product vision, target customer, positioning
  set-goals              OKRs, success metrics + guardrail metrics
  build-roadmap          Now/Next/Later, outcome-based
  prioritize             Rank the backlog (RICE / WSJF)
          │
          ▼  GATE (make-decision: proceed / pivot / kill)
  Phase 4 — Define (turn outcome into buildable scope)
  write-prd              Problem, outcomes, success criteria, non-goals
  define-acceptance      Acceptance contract: testable criteria (HANDOFF TO SDLC)
  prototype-ux           Wireframes/prototype + usability findings
          │
          ▼  GATE (make-decision: proceed / pivot / kill)  ──►  SDLC owns the build
  Phase 5 — Launch (go-to-market)
  plan-launch            Readiness checklist, timeline, channels
  craft-messaging        Value prop, messaging house, narratives
  enable-teams           Sales playbook, support runbook
  set-pricing            Pricing model, packaging, tiers
          │
          ▼  GATE (make-decision: proceed / pivot / kill)
  Phase 6 — Measure (close the loop)
  spec-analytics         Events, funnels, dashboards, guardrails
  review-metrics         Actuals vs goals, anomalies, health report
  synthesize-feedback    Aggregate support, sales, NPS, reviews
  run-retrospective      Keep / stop / start
  sunset-product         End-of-life plan (when an initiative is net-negative)
          │
          ▼  GATE (make-decision: double-down / iterate / sunset)  ──► feeds back into Discover

Cross-cutting (invoke at any point)

  make-decision          The gate mechanism — one decision record, reused at every transition
  kill-initiative        Explicit sunset-or-pivot: reallocate capacity, notify stakeholders
  brief-stakeholders     Exec summary, status update, stakeholder map
  audit-outcomes         Trace shipped outcomes back to the original problem and metrics (PDLC backpropagation)
  manage-portfolio       Health across multiple initiatives/products

Setup (run once per project, no dependencies on the loop)

  initialize-pdlc-directory   Bootstrap .pdlc/ structure and populate templates
  sync-pdlc                   Reconcile .pdlc/ with current product reality (calls initialize if absent)
```

## Directory Structure

All PDLC artifacts live under `.pdlc/` in the repository root.
When `PDLC_DIR` is set, the same tree can also live (or be mirrored) outside the repo under `$PDLC_DIR/{owner}/{repository}/.pdlc/`; see `references/shared.md` for the full rules.

```
.pdlc/
├── .gitignore                     # Excludes state.yml and initiatives/*/progress.md (local-only)
├── context/
│   ├── product-overview.md        # Product, ICP, scope, stakeholders
│   ├── vision.md                  # Product vision and positioning
│   ├── goals.md                   # OKRs, success metrics, guardrail metrics
│   ├── roadmap.md                 # Now/Next/Later
│   ├── pricing.md                 # Pricing model (optional)
│   └── vocabulary.md              # Product and domain terms
├── state.yml                      # Orchestrator run state (local-only, gitignored)
├── initiatives/
│   └── N-<slug>/                  # One per initiative (INIT-N)
│       ├── progress.md            # Initiative progress + session log (local-only, gitignored)
│       ├── problems.md            # Discover
│       ├── market.md              # Discover
│       ├── competitors.md         # Discover
│       ├── opportunity-tree.md    # Discover (feeds the first gate)
│       ├── assumptions.md         # Validate
│       ├── experiment-plan.md     # Validate
│       ├── experiment-result.md   # Validate (feeds the gate)
│       ├── prd.md                 # Define
│       ├── acceptance-contract.md # Define — the SDLC handoff seam
│       ├── prototype.md           # Define
│       ├── launch-plan.md         # Launch
│       ├── messaging.md           # Launch
│       ├── enablement-kit.md      # Launch
│       ├── pricing.md             # Launch
│       ├── analytics-spec.md      # Measure
│       ├── health-report.md       # Measure
│       ├── feedback-loop.md       # Measure (feeds the double-down/iterate/sunset gate)
│       └── eol-plan.md            # Measure (sunset)
├── decisions/
│   └── N-<slug>.md                # Gate decisions and other product decisions (DEC-N)
├── learnings/
│   └── N-<slug>.md                # Retrospectives (run-retrospective)
└── templates/                     # Editable defaults used by phase skills
    ├── initiatives/...            # One template per artifact above
    ├── decision.md
    ├── learning.md
    └── context/...
```

**Initiative directory naming:** directories under `initiatives/` are named `N-<slug>` (issue number verbatim when tied to an issue, otherwise `p1-<slug>`, `p2-<slug>`, ... for pending initiatives). The **initiative ID** `INIT-N` is used in cross-references. Full rules live in `references/shared.md`.

## Entry Points

| Phase | Start here when you have... |
|---|---|
| `status` | Want to see initiative progress or pick up where you left off (delegates to `pdlc-status`, no side effects) |
| `setup` | A new product/project that needs the `.pdlc/` structure bootstrapped (runs `initialize-pdlc-directory`) |
| `sync` | An existing `.pdlc/` that needs reconciling with current reality (runs `sync-pdlc`) |
| `discover` | A vague problem area, signal, or metric regression to turn into structured problems and opportunities |
| `validate` | A framed opportunity ready to test before building |
| `strategy` | A validated opportunity ready to turn into vision, goals, and a roadmap |
| `define` | A prioritized opportunity ready to become a PRD and acceptance contract (handoff to SDLC) |
| `launch` | A built/shipped change ready for go-to-market planning |
| `measure` | A launched initiative whose outcomes need to be read and closed |
| `sunset` | An initiative that is net-negative and ready for an end-of-life plan |
| `decision` | A decision to record at any phase (runs `make-decision`) |
| `kill` | An initiative to stop (runs `kill-initiative`) |
| `audit` | Want to trace shipped outcomes back to problems and metrics (runs `audit-outcomes`) |
| `continue` | Resume an in-progress initiative (runs Automatic Resume) |

## State File

The orchestrator maintains `.pdlc/state.yml` to track the current run.
Read it at the start of every invocation; write it after every phase transition.
It is local-only workflow state and is never read from or mirrored to `PDLC_DIR`.

```yaml
current_phase: null             # the next phase to run (entry point name)
github_ref: null                # GitHub issue or PR number, e.g. "#42"
initiative: null                # N-<slug> directory name if one has been created
last_gate: null                 # verdict of the most recent gate (proceed/pivot/kill)
```

- **On first entry**: create `.pdlc/state.yml`, populating `current_phase` with the entry point and `github_ref` if known.
- **After each phase completes**: update `current_phase` to the next phase. This is the single rule: `current_phase` always holds what comes next.
- **When an initiative directory is created**: populate `initiative`.
- **After each gate**: set `last_gate` to the verdict.
- **On loop completion**: set `current_phase` to `complete`.

### Local-only files (never commit)

`state.yml` and each initiative's `progress.md` are local workflow state.
They must never be committed. `initialize-pdlc-directory` creates a `.pdlc/.gitignore` that excludes them:

```gitignore
# Local-only workflow state — do not commit
# Orchestrator run state
state.yml
# Per-initiative progress tracking and session logs
initiatives/*/progress.md
```

## Steps

1. Read `.pdlc/state.yml` if it exists. Use its values as defaults unless the user provides explicit arguments.
2. Determine the entry point: normalize `$1` to lowercase and match against the supported entry points. If `$1` does not match, do not infer from text; inform the user and ask for a valid entry point. If `continue`, run Automatic Resume.
3. If the entry point is `status`, invoke the `pdlc-status` skill. Do not advance the loop or modify any artifacts.
4. If the entry point is `setup`, invoke `initialize-pdlc-directory`. If `sync`, invoke `sync-pdlc`. These are standalone and do not advance the loop.
5. If the entry point is `decision`, invoke `make-decision` directly. If `kill`, invoke `kill-initiative`. If `audit`, invoke `audit-outcomes`.
6. Read `.pdlc/context/` (`product-overview.md`, `vision.md`, `goals.md`) for product context before invoking any sub-skill, and apply the style rules found there to every document produced. The shared conventions (context reading and `.pdlc/` path resolution via `PDLC_DIR`) are defined in `references/shared.md` and are not repeated per sub-skill.
7. Confirm the artifacts available for the current phase (previous phase output under `.pdlc/initiatives/N-<slug>/`, existing files, or context).
8. **Before executing each sub-skill, read it** at `skills/pdlc/skills/<name>/SKILL.md` (Read tool). This is mandatory. Read first, then perform the sub-skill's steps. Never run a phase's commit/push/PR actions without reading the governing sub-skill first.
9. After each phase skill completes its artifact, **run the gate**: invoke `make-decision` for the phase just completed. The gate decides `proceed` / `pivot` / `kill`.
   - `proceed` → advance to the next phase.
   - `pivot` → return to the phase named in the decision body and re-run that skill in revision mode.
   - `kill` → invoke `kill-initiative` and stop the loop.
10. After the gate resolves to `proceed`, update `.pdlc/state.yml` (`current_phase`, `initiative`, `last_gate`) and update the initiative's `progress.md`.
11. At the SDLC seam (`define-acceptance`): the acceptance contract is the handoff. Note that SDLC owns the build; PDLC resumes at `launch` once the change is shipped. Do not run SDLC skills from within PDLC; point the user to `/sdlc requirements` with the acceptance contract as input.
12. At the end of Measure, the gate is `double-down` / `iterate` / `sunset`. `iterate` routes back to Discover with the feedback artifact as input (the loop closes). `sunset` invokes `sunset-product`.
13. When the session ends, write a session boundary marker to `progress.md`.

### Automatic Resume (entry: `continue`)

1. Scan `.pdlc/initiatives/*/progress.md` for initiatives where `current_phase` is not `complete` and `re_entry_point` is set.
2. If exactly one is found, present its status and ask: "Resume at `<re_entry_point>` for `<initiative>`?"
3. If multiple are found, show the summary table and ask which to resume.
4. If none are found, inform the user and ask for an entry point.
5. The user can always override by specifying an explicit entry point.

### Progress Tracking

The `progress.md` file in each initiative directory is the single source of truth for initiative status, updated after each phase and gate.

**Session Boundary Markers:** at the start and end of every session, write a brief entry to the Session Log in `progress.md` (date, what was accomplished / planned, where to pick up next). Update `re_entry_point` on session end so the next session resumes cleanly.

## Backtracking and Failure Recovery

| Mode | Example | Response |
|---|---|---|
| **Gate pivot** | `make-decision` returns `pivot` with a named phase | Return to that phase, re-run its skill in revision mode, re-gate. |
| **Scope change** | A PRD reveals the initiative is far larger than discovery suggested | Pivot back to `frame-opportunities`, re-scope, re-derive downstream artifacts. |
| **Experiment kills it** | `run-experiment` verdict is negative | Gate returns `kill`; run `kill-initiative`; record the learning. |
| **External blocker** | A dependency (API, partner, budget) is unavailable | Record as an assumption with a validation plan. Stop after the current phase if unresolved. |
| **Build handoff stall** | SDLC never ships the change | PDLC pauses at `define-acceptance`; resume `launch` only once shipped. |

Backtracking rules:
1. Pivot to the nearest phase that owns the root cause.
2. Re-derive downstream artifacts after revising.
3. Record why you pivoted via `make-decision`.
4. Do not silently skip a failed phase; state why and either pivot or stop.

When stopping, leave the loop resumable: update `progress.md` with the re-entry point, save artifacts produced so far, and set `current_phase`.

## Skipping Gates

Gates may be skipped in low-risk or exploratory contexts (a quick prototype, a tiny iteration).
State the skip explicitly: "Skipping the discover gate — prototype context."
Never skip gates for commitments that consume significant engineering capacity, pricing changes, or anything that touches guardrail metrics.

## Commit / Push / PR Gate (mandatory)

Never commit, push, or open a PR without an explicit request from the user, even when a phase would normally include these actions (posting a launch plan, filing a placeholder issue, sending enablement comms). Complete non-destructive work, stop, report, and wait for explicit confirmation.
