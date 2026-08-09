---
name: create-lifecycle
description: Document how resources evolve over time and what causes them to change, covering states, transitions, invariants, and retention.
argument-hint: "[specification-doc]"
---

# Create Lifecycle

Documents how resources managed by a feature evolve over time and what causes them to change.
Produces a lifecycle document covering states, transitions, invariants, retention policies, and event emissions for each resource that has a meaningful lifecycle.

Without this step, resource state machines are implicit in the code and scattered across API handlers, database constraints, and application logic.
When a new state is added or a transition rule changes, there is no single source of truth to consult, so inconsistencies arise between what the API allows, what the database enforces, and what the UI presents.

For features that do not manage resources with a lifecycle (a pure config change, a read-only dashboard, a documentation update), skip this phase and state the skip explicitly.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/specification.md` (must have passed review with findings verdict `approved`), or a specification document provided in context or as a file path (`$1`)
- `.sdlc/features/N-<slug>/requirements.md` (optional, for cross-referencing functional requirements that drive lifecycle behavior)
- `.sdlc/features/N-<slug>/codebase-analysis.md` (optional, if existing code was analyzed): reuse existing state machines or enums, and honor any "must not change" constraints on shared resource models

## Steps

1. Read the specification, requirements (if present), and codebase analysis (if present).
2. Decide whether the feature manages resources with a meaningful lifecycle. If it does not, emit `verdict: skipped` (do not write `lifecycle.md`). The `skipped` verdict routes the pipeline straight to the next phase, bypassing `/review-lifecycle`.
3. Identify every resource the feature creates, modifies, or tracks that has a lifecycle (resources that pass through distinct states, have retention policies, or emit events on state changes).
4. For each resource, determine its lifecycle type:
   - **State Machine:** the resource moves between named states via defined transitions (e.g., order: pending -> paid -> shipped -> delivered).
   - **Linear:** the resource progresses through a one-way sequence without branching (e.g., a build: queued -> running -> succeeded/failed).
   - **CRUD:** the resource has no meaningful state beyond created/updated/deleted (document only if retention or expiry applies).
5. For each resource with a state machine or linear lifecycle, draw a state diagram showing all states and transitions.
6. For each state, document its meaning, entry condition, exit condition, and a reference to the specification section that defines the behavior.
7. For each transition, document the trigger (event, API call, timer, condition), the actor (user, system, external), side effects (notifications, cascading updates, event emissions), and guard conditions (preconditions that must hold).
8. Define invariants: conditions that must always hold regardless of state (e.g., "a subscription cannot be active without a valid payment method"). Document how each is enforced and what happens on violation.
9. Specify retention and expiry policies: how long resources persist, what triggers expiry, and what cleanup action is taken (hard delete, archive, anonymize).
10. List events emitted on transitions, including payload, downstream consumers, and cross-references to the specification or telemetry plan.
11. Write the output to `.sdlc/features/N-<slug>/lifecycle.md`.

## Lifecycle Types

### State Machine

Use when a resource has distinct named states with guarded transitions between them.
This is the most common lifecycle type for domain objects (orders, subscriptions, tickets, deployments).

Key questions to answer:
- What are all the states the resource can be in?
- Which transitions are valid from each state?
- What triggers each transition?
- What side effects accompany each transition?
- What invariants must hold across all states?
- Can transitions go backward (e.g., from "shipped" back to "pending"), and if so, under what conditions?

### Linear

Use when a resource progresses through a fixed sequence without branching or backward transitions.
Simpler than a state machine but still worth documenting because the sequence and its side effects are easy to get wrong.

### CRUD

Use when the resource has no meaningful state beyond existing or not existing.
Only document if retention, expiry, or soft-delete behavior applies, since those are the lifecycle-relevant aspects.

## Output Format

Use the template at `skills/sdlc/templates/features/lifecycle.md` (copied to `.sdlc/templates/features/lifecycle.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | The lifecycle artifact was produced (or revised) with `status: draft`, ready for `/review-lifecycle` |
| `skipped` | The feature manages no resources with a meaningful lifecycle; no artifact is written and the pipeline proceeds past review to the next phase |

If the artifact could not be produced for any other reason, omit the file.

## Example Usage

**Scenario 1: Order processing system**
The specification defines an `Order` resource with `POST /orders`, payment, and fulfillment endpoints.
The lifecycle document identifies `Order` as a state machine with states: `pending`, `paid`, `fulfilling`, `shipped`, `delivered`, `cancelled`, `refunded`.
Each transition is documented with its trigger (payment confirmation, shipping label creation, delivery confirmation), guard conditions (cannot ship without payment), and side effects (email notifications, inventory decrement, event emissions).
Invariants: "total_amount must equal sum of line items in all states."

**Scenario 2: API key management**
The specification defines API keys with creation, rotation, and revocation.
The lifecycle document identifies `ApiKey` as a state machine with states: `active`, `rotating`, `revoked`, `expired`.
Retention policy: revoked keys retained 90 days for audit, then hard deleted.
Events: `api_key.rotated`, `api_key.revoked` emitted to the audit log.

**Scenario 3: Configuration change, no lifecycle**
The specification defines a threshold update in a YAML config file.
The feature manages no resources with a lifecycle. The skill leaves the artifact unwritten and emits `verdict: skipped` so the pipeline continues without a review.

## Completion Checklist

Before handing off to review, confirm:

- [ ] Every resource with a state machine has a state diagram showing all states and transitions
- [ ] Every transition has a trigger, actor, guard conditions, and side effects documented
- [ ] Every invariant states how it is enforced and what happens on violation

Self-check the draft against the [`review-lifecycle` checklist](../review-lifecycle/SKILL.md) and fix what you can, so review finds less to flag.

## Next Step

Run `/review-lifecycle` to audit the lifecycle document for completeness, consistency, and spec alignment before moving on.
Once approved, continue with `/create-mockups`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
