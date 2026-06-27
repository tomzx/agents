---
name: create-codebase-analysis
description: Analyze the existing internal code and architecture a feature will touch, extend, or replace, and assess each part's changeability (reuse, extend, refactor, replace) with rationale, risk, and migration impact.
argument-hint: "[requirements-doc]"
---

# Create Codebase Analysis

Analyzes the existing internal code and architecture that a feature will rely on, change, or replace, and assesses each relevant part's changeability before the design is committed.
The goal is to know the terrain before specifying how to change it: what exists today, how it is coupled, what can be touched safely, and what must stay stable.

This is the internal counterpart to `create-existing-solutions`.
`create-existing-solutions` surveys external prior art (libraries, OSS, products) and checks for cheap internal reuse.
This skill goes deeper into the internal architecture you are about to modify: it maps components, coupling, and blast radius, and decides a change disposition for each part (reuse as-is, extend, refactor, or replace).

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/FEAT-NNNN-<slug>/requirements.md` (must have `status: approved`), or a requirements document provided in context or as a file path (`$1`)
- `.sdlc/features/FEAT-NNNN-<slug>/existing-solutions.md` (optional): carry forward any internal reuse candidates it already identified so they are not re-discovered
- Read any files present under `.sdlc/context/` (`project-overview.md`, `architecture.md`, `conventions.md`, `vocabulary.md`) for project-level context
- Apply any artifact style rules found in `conventions.md` to the produced document

## Steps

1. Read the requirements document and extract the functional and non-functional requirements that imply changes to existing code.
2. Read `.sdlc/context/architecture.md` (if present) to ground the analysis in the documented system topology, and read the existing solutions survey if one was produced.
3. Determine the **analysis scope**: which parts of the codebase this feature will touch, integrate with, or replace. Trace inward from the requirements to concrete modules, services, data stores, and interfaces.
4. Locate the relevant code by searching the codebase. Record the entry points used (queries, paths) so the search is auditable.
5. For each relevant component, capture its name, location (file or module path), current responsibility, and how the feature interacts with it (reads, writes, extends, replaces).
6. Map **dependencies and coupling** between the relevant components and any external systems. Call out shared state, synchronous vs. asynchronous boundaries, and the blast radius of changing each part.
7. For each component, decide a **change disposition** and justify it:
   - **Reuse as-is** — the component already does what is needed; do not modify it.
   - **Extend** — add to the component along its existing seams (new method, new config, new consumer) without altering current behavior.
   - **Refactor** — restructure the component's internals to accept the change, while preserving its observable behavior.
   - **Replace** — supersede the component (or a path through it) with a new implementation.
8. For every **Refactor** or **Replace** disposition, outline migration and impact: the path from current to target behavior, backward compatibility, rollout strategy, what else breaks, and how to de-risk (feature flag, dual-run, shadow comparison).
9. Record **assumptions about existing behavior** that the analysis relies on but has not fully verified. Promote any that carry meaningful risk via `/create-assumption`, and log architectural choices via `/create-decision`.
10. Flag open questions where the changeability of a part cannot be decided without more investigation.
11. Write the output to `.sdlc/features/FEAT-NNNN-<slug>/codebase-analysis.md`.

## Handling Greenfield Features

If there is no relevant existing code to analyze (the feature introduces an entirely new subsystem with nothing to touch or integrate with):
- Write a short note stating that the feature is greenfield, name the integration boundary (where it will attach to existing systems, if any), and stop.
- Do not fabricate components. A one-paragraph "no relevant existing code" record is a valid, complete output.

## Output Format

```markdown
---
issue: "#<N>"
title: "<Feature Name>"
status: draft
---

# Codebase Analysis: <Feature Name>

## Overview

<One paragraph summarizing the relevant existing code/architecture and the overall changeability outlook.>

## Scope of Analysis

<Which areas were examined, the search entry points used (queries and paths), and what was explicitly out of scope. State "greenfield" here if no relevant existing code exists.>

## Relevant Existing Components

| Component | Path | Responsibility | Interaction |
|---|---|---|---|
| <name> | <file/module path> | <what it does today> | Reuse / Extend / Refactor / Replace / Read-only |

## Dependency and Coupling Map

<How the relevant components depend on each other and on external systems. Call out tight coupling, shared state, synchronous vs. asynchronous boundaries, and the blast radius of a change.>

## Changeability Assessment

### <Component Name>

- **Current state:** <how it works today>
- **Change disposition:** Reuse as-is / Extend / Refactor / Replace
- **Rationale:** <why this disposition, tied to the requirements and the coupling map>
- **Risk:** Low / Medium / High — <what drives it>
- **Constraints:** <what must not change, e.g. public API, persisted data format, ordering guarantees, behavior contracts>

## Migration and Impact Considerations

<For every Refactor or Replace disposition: the path from current to target behavior, backward compatibility, rollout strategy, what else breaks, and how to de-risk. Omit this section if the analysis is greenfield or contains only Reuse/Extend dispositions.>

## Assumptions About Existing Code

- <Belief about current behavior the analysis relies on but has not fully verified. Promote risky ones via /create-assumption.>

## Open Questions

1. <Question that needs an answer before the design can rely on this analysis.>
```

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`, mirroring the `status: approved` written to the artifact. If the artifact could not be produced, omit the file.

## Example Usage

**Scenario 1: Replacing an implementation strategy**
Requirements ask for real-time Kubernetes state instead of minute-level polling reconciliation.
The analysis finds the reconciliation loop, its informer-backed cache, and the consumers of its output. It recommends replacing the polling loop with an event-driven consumer (reusing the existing cache and its resync fallback) while keeping the output contract stable so downstream consumers are untouched. Migration runs both paths behind a feature flag with shadow comparison.

**Scenario 2: Extend, do not rewrite**
Requirements ask for per-tenant quotas on top of an existing rate limiter.
The analysis shows the limiter is well-factored with a clean tenant key seam. Disposition: Extend (add a tenant-scoped counter) rather than Replace. Low risk.

**Scenario 3: Greenfield subsystem**
Requirements ask for a brand-new export pipeline with no existing equivalent.
The analysis records a greenfield note, names the single integration boundary (the queue it will read from), and stops.

## Next Step

Run `/review-codebase-analysis` to audit the analysis for coverage, accuracy, changeability rigor, and impact assessment before moving on.
Once approved, continue with `/create-feasibility`, which consumes this analysis alongside the requirements to judge viability and cost.

## Useful Commands Reference

| Command | Description |
|---|---|
| `grep` / codebase search | Locate the components, modules, and interfaces the feature will touch |
| `read` | Read the relevant source to verify behavior claims instead of assuming them |
| `/create-assumption` | Record an unverified belief about existing behavior that carries risk |
| `/create-decision` | Log an architectural change choice (e.g. replace vs. extend) with its rationale |
