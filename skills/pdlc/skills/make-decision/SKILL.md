---
name: make-decision
description: Record a product decision, including the PDLC proceed/pivot/kill gate verdict at each phase boundary. One reusable decision record, invoked at every gate.
argument-hint: "[initiative-id or topic]"
---

# Make Decision

The single decision skill reused across the PDLC. It does double duty:

1. **Gate decisions** — invoked at every phase boundary to decide `proceed` / `pivot` / `kill`.
2. **General product decisions** — any consequential choice (positioning, segmentation, trade-offs) recorded for traceability.

One record format, one storage location (`.pdlc/decisions/`). The difference is purely whether the frontmatter carries a `gate_verdict` tied to a phase.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- For a gate: the phase artifact just produced, and the initiative it belongs to.
- For a general decision: the context and options under consideration.

## Steps

1. Identify whether this is a gate or a general decision. A gate is invoked by the orchestrator right after a phase skill completes its artifact.
2. For a **gate decision**, evaluate the opportunity's continued viability using the gate criteria below. The artifact's prose quality is the phase skill's job (it self-checks); this gate judges *whether the opportunity still deserves to move forward*.
3. For a **general decision**, capture context, at least two options, the choice, trade-offs, and consequences (use the decision template).
4. Write the record to `.pdlc/decisions/N-<slug>.md` where `N` is the next unused number. Use the template at `skills/pdlc/templates/decision.md`.
5. Set frontmatter per the gate table below when this is a gate.

## Gate Criteria

A `proceed` requires all of:
- The phase artifact answers the phase's question (Discover: is there a real problem? Validate: does evidence support the hypothesis? Strategy: is this the right focus? Define: is the scope buildable and outcome-linked? Launch: is the market ready? Measure: did we move the metric without breaking guardrails?).
- No unresolved blocker that would waste the next phase's effort.
- The estimated cost of the next phase is justified by the opportunity's expected value.

A `pivot` is chosen when the opportunity is real but the current framing/scope/solution is wrong. The decision body names the phase to return to and why.

A `kill` is chosen when the opportunity is not worth pursuing (no real problem, negative experiment, cost exceeds value, guardrails broken beyond tolerance). On `kill`, the orchestrator runs `kill-initiative`.

The Measure-phase gate uses a different verdict vocabulary: `double-down` (scale what works), `iterate` (return to Discover with feedback), or `sunset` (run `sunset-product`).

## Gate Frontmatter

```yaml
---
initiative: INIT-N
phase: discover            # the phase just completed
gate_verdict: proceed      # proceed | pivot | kill (double-down | iterate | sunset for Measure)
reviewed_at: <ISO date>
---
```

For a general (non-gate) decision, omit `initiative`, `phase`, and `gate_verdict`.

## Output Format

Use the decision template (context, options with pros/cons, decision, consequences). For a gate, add a `## Gate Verdict` section stating the verdict in one line and the one-paragraph rationale, plus the target phase if `pivot`.

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `references/shared.md`.

| Verdict | When |
|---|---|
| `proceed` / `double-down` | The opportunity survives the gate |
| `pivot` / `iterate` | Reframe and return to a named phase |
| `kill` / `sunset` | Stop; the opportunity is not worth pursuing |

## Next Step

- Gate `proceed` → the orchestrator advances to the next PDLC phase.
- Gate `pivot` → return to the phase named in the decision body and re-run its skill in revision mode.
- Gate `kill` → run `kill-initiative`.
- General decision → return to the calling phase.

## Completion Checklist

- [ ] At least two options considered (including the chosen one), each with pros and cons (gate decisions may cite the phase artifact as the evidence instead of restating options)
- [ ] Gate verdict present in frontmatter when invoked as a gate
- [ ] If `pivot`, the target phase is named
- [ ] If replacing an earlier decision, note the supersession in the new record's body
