---
name: craft-messaging
description: Produce the value proposition, messaging house, and audience-specific narratives for a launch. A consumer of the validated vision and pricing. Part of the PDLC Launch phase.
argument-hint: "[initiative-id]"
---

# Craft Messaging

Turns the validated vision and positioning into launch-ready messaging. It is a *consumer* of `vision.md` (from `define-vision`) and `pricing.md` (from `set-pricing`) — messaging that drifts from the validated vision is how products get rebranded into irrelevance, so this skill anchors to those sources.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `vision.md` and `prd.md`. `pricing.md` if pricing is decided.

## Steps

1. State the core value proposition in one sentence, derived from the positioning in `vision.md`.
2. Build the messaging house: the single core message at the top, 3 pillars beneath, each with proof points drawn from `experiment-result.md` or `competitors.md`.
3. Write audience-specific narratives for each priority segment (tie to `market.md` segments). Same core message, different entry points.
4. Produce channel-ready assets: headline options, short descriptions, and a one-paragraph narrative per channel.
5. Sanity-check against the positioning: does every message reinforce the chosen differentiation, or does any undercut it?
6. Write `messaging.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/messaging.md`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Value proposition traceable to `vision.md` positioning
- [ ] Each pillar has a proof point
- [ ] One narrative per priority segment
- [ ] Every message reinforces (not undercuts) the differentiation

## Next Step

Load `enable-teams`, then `set-pricing` if not done, then run the **Launch gate** via `make-decision`.
