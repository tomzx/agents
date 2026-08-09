---
name: review-lifecycle
description: Review a resource lifecycle document for completeness, consistency, spec alignment, and correctness of state transitions and invariants.
---

# Review Lifecycle

Audits a resource lifecycle document and reports findings across six categories: completeness, consistency, spec alignment, transition correctness, invariant soundness, and retention soundness.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/lifecycle.md`, or a lifecycle document provided in context or as a file path
- `.sdlc/features/N-<slug>/specification.md` (for cross-referencing data models, API contracts, and sequences)
- `.sdlc/features/N-<slug>/requirements.md` (optional, for cross-referencing functional requirements that drive lifecycle behavior)

## Steps

1. Read the lifecycle document from `.sdlc/features/N-<slug>/lifecycle.md` if present, otherwise from context or as a file path.
2. Cross-reference against the specification and requirements if available.
3. Identify issues in each of the six categories below.
4. Report findings. Omit any category that has no findings.
5. Write the findings to `.sdlc/features/N-<slug>/review-lifecycle.md` with frontmatter `artifact: lifecycle`, `verdict` (`approved` if there are no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, and the findings as the body, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body. For any question that carries meaningful risk to the implementation, also invoke `/create-assumption` to record it formally.

## Review Checklist

### Completeness
- Does every resource identified in the specification's data models have a corresponding lifecycle entry (or an explicit decision to exclude it)?
- Does every state machine have a state diagram showing all states and transitions?
- Does every state have an entry condition, exit condition, and description?
- Does every transition have a trigger, actor, side effects, and guard conditions?
- Are all invariants documented, or is there an explicit statement that no invariants apply?
- Are retention and expiry policies documented for resources that are not permanent?

### Consistency
- Do the states and transitions match the API contracts in the specification (e.g., does `PATCH /orders/{id}/cancel` correspond to a `cancelled` state transition)?
- Are state names consistent with field names and enum values in the specification's data models?
- Are event names consistent with the telemetry plan's event taxonomy if one exists?
- Do the resources listed match the entities in the specification's data models?

### Spec Alignment
- Does every transition trace to a specification section, API endpoint, or sequence that causes it?
- Does every specification sequence that changes resource state have a corresponding transition documented here?
- Are guard conditions consistent with constraints described in the specification?
- Are side effects (notifications, cascading updates) consistent with the specification's sequences?

### Transition Correctness
- Are there unreachable states (states with no incoming transition)?
- Are there states with no exit transition that should have one (dead-end states)?
- Are there missing transitions that the specification implies but the lifecycle does not document?
- Can backward transitions occur, and if so, are their guard conditions and side effects documented?
- Are concurrent or racing transitions accounted for (e.g., two actors triggering conflicting transitions)?

### Invariant Soundness
- Is each invariant actually invariant (does it hold in every state, not just some)?
- Is the enforcement mechanism specific enough (which DB constraint, which validation, which application check)?
- Is the violation handling realistic (does it match what the API or system would actually do)?
- Are there implicit invariants the specification implies but the lifecycle does not state?

### Retention Soundness
- Is the retention period stated for resources that should not persist indefinitely?
- Is the expiry trigger specific (what starts the clock: creation, deletion, last access)?
- Is the cleanup action stated and consistent with the specification (hard delete, archive, anonymize)?
- Are there resources that should have a retention policy but do not?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Consistency

<Findings or "No issues found.">

## Spec Alignment

<Findings or "No issues found.">

## Transition Correctness

<Findings or "No issues found.">

## Invariant Soundness

<Findings or "No issues found.">

## Retention Soundness

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

## Example Usage

**Scenario 1: Unreachable state**
The lifecycle defines an `archived` state but no transition leads to it.
Report under Transition Correctness: state `archived` is unreachable, no incoming transition is documented.

**Scenario 2: Missing API correspondence**
The lifecycle documents a transition from `pending` to `shipped` but the specification defines no endpoint or sequence that triggers shipping directly from pending (it requires a `paid` state in between).
Report under Spec Alignment: transition `pending -> shipped` has no corresponding spec sequence; the spec requires `pending -> paid -> shipped`.

**Scenario 3: Invariant not actually invariant**
The invariant "total_amount must be positive" is documented, but the `refunded` state allows `total_amount = 0`.
Report under Invariant Soundness: the invariant does not hold in the `refunded` state, so it is not a true invariant.

**Scenario 4: Missing retention policy**
The lifecycle documents an `ApiKey` resource with `revoked` and `expired` states but no retention policy for how long revoked keys are kept.
Report under Retention Soundness: no retention policy for revoked keys, which may have compliance implications.

## Next Step

Once the findings verdict is `approved`, continue with `/create-mockups`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
