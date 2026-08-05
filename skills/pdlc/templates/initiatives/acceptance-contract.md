---
initiative: INIT-N
title: "<topic>"
status: draft
phase: define
spawns_features: []   # FEAT-N ids this initiative decomposes into
---

# Acceptance Contract: <title>

This is the seam between PDLC and SDLC. SDLC's create-requirements consumes it.

## Acceptance Criteria

| ID | Requirement | Criterion (Given/When/Then or measurable) | Bound metric | Proof type |
|---|---|---|---|---|
| AC-1 | FR-1 | <criterion> | SM-N / GM-N / — | functional / analytics |

## Success-Metric Gates (must reach target within window)

| Metric | Target | Window | Acceptance criterion |
|---|---|---|---|
| SM-N | <target> | <window> | AC-_: accepted only if SM-N reaches target |

## Guardrail Lines (must hold post-launch)

| Metric | Floor | Acceptance criterion |
|---|---|---|
| GM-N | <floor> | AC-_: must not regress below floor |

## Acceptance Boundary

- **In scope (must pass):** <list>
- **Out of scope (non-goals):** <list, from PRD>

## SDLC Decomposition

- **Spawns features:** <FEAT-N list>
- **Needs runtime/analytics proof:** <AC ids> → feeds /spec-analytics
- **Needs functional proof:** <AC ids> → feeds SDLC tests (TC-N)
