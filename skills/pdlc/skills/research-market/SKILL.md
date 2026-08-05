---
name: research-market
description: Size the market, map trends and segments, and assess timing for a candidate problem space. Part of the PDLC Discover phase.
argument-hint: "[initiative-id or topic]"
---

# Research Market

Quantifies the opportunity space around a candidate problem: how big, who's in it, where it's heading, and whether the timing window is open. Pairs with `analyze-competition` and feeds `frame-opportunities`.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `problems.md` from `discover-problems` (the problem space to size), or an explicit topic.

## Steps

1. Define the market boundary tied to the problem (TAM/SAM/SOM), using a clearly stated method (bottom-up counts, value-based, or top-down proxy). State assumptions explicitly.
2. Segment the market: who has the problem most acutely. Rank segments by acuity, reachability, and value.
3. Map trends affecting the space (technology, regulation, behavior, economy) and assess whether each is a tailwind or headwind.
4. Assess timing: is the window opening, open, or closing? What event opens or closes it?
5. Flag data confidence: mark each figure `measured` / `estimated` / `guessed`. A market sized entirely by guesses is a finding, not a result.
6. Write `market.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/market.md`. Carry the standard initiative frontmatter with `phase: discover`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Market sized with a stated method and explicit assumptions
- [ ] Segments ranked by acuity and reachability
- [ ] Each figure tagged `measured` / `estimated` / `guessed`
- [ ] Timing window assessed with a trigger event

## Next Step

Load `frame-opportunities` once discovery inputs (`problems.md`, `market.md`, `competitors.md`) are ready.
