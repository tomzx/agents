---
name: audit-attention
description: Audit how your time splits between compounding and depreciating activities using the two-year test. Use when the user says /audit-attention, wants to check attention allocation, asks "where is my time going", or wants to know what to delegate vs. protect.
---

# Audit Attention

Classifies the activities on your plate as compounding or depreciating using the two-year test, so you can delegate depreciating work ruthlessly and ring-fence compounding work ferociously. The number that matters is not how much AI you use, nor how much you keep in human hands; it is how much of your time lands on compounding work.
## Prerequisites

- A list of the activities that filled the period (a day, a week, or a longer stretch). Source this from any of:
  - daily notes, calendars, git and Slack activity,
  - the weekly review/summary artifacts under `{NOTES_DIR}/{YEAR}/weekly/{WEEK}/`,
  - or the user's own recall when prompted.
- No codebase access required; this is a personal-attention audit, not a service audit.

## The Distinction

- **Compounding activities** gain value the more you do them and feed back into everything else: deciding what to build, judging whether a design is right, reading a hard paper with the intent of being able to teach it, debugging a subtle failure by reasoning about the system, holding taste about what to ship.
- **Depreciating activities** lose value as the environment changes: boilerplate, scaffolding, routine tests, formatting, summarizing a known pattern, re-deriving an answer a model can produce.

## The Two-Year Test

For each activity, ask: *If I let the model do this for the next two years, will the me that emerges be more valuable, or less, than the me that kept doing it by hand?*

- More valuable if delegated -> **depreciating**; delegate next cycle and route the freed time to compounding work.
- Less valuable if delegated -> **compounding**; protect ferociously, do not delegate even when a model offers to.

## Steps

1. Gather the activity list for the period (see Prerequisites). If no list is provided, ask the user to enumerate the significant activities of the period before proceeding.
2. Apply the two-year test to each significant activity and classify it compounding or depreciating.
3. Estimate the fraction of the period that landed on compounding work.
4. Note boundary moves since the last audit: activities that shifted category, and which direction.
5. Produce the report using the format below.

## Output Format

```markdown
# Attention Audit — <period>

**Date:** <YYYY-MM-DD>
**Period:** <day / week N / month / custom>

## Two-Year Test Results

| Activity | Compounding / Depreciating | Keep / Delegate next cycle |
|----------|---------------------------|---------------------------|
| <activity> | <C/D> | <keep/delegate> |

## Summary

**Fraction of period on compounding work:** <X>% (direction cycle over cycle: up / flat / down / first audit)

**Boundary moves since last audit:** <activities that shifted category, and which direction; or "none / first audit">

**Time to ring-fence next cycle:** <specific compounding activity and the block that protects it>

**To delegate next cycle:** <specific depreciating activities and the delegation path>

## Notes

<one or two sentences on what the allocation reveals>
```

## Watch the Boundary

The line between compounding and depreciating is not fixed; a thing that compounded last year (writing SQL by hand, reading raw logs) can become depreciating as models improve, and occasionally the reverse. Re-run the audit on a regular cadence (weekly via end-week, or at least every few weeks) rather than treating the sort as final. The meta-skill of telling the two apart is itself compounding, which is the strongest case for spending attention on it.

## Do Not Optimize the Delegation Ratio

An engineer who delegates ninety percent of their work and spends the freed time going deeper on the remaining ten percent is doing it right. The high delegation ratio is a symptom of correctly identifying the compounding layer, not a target. Flag for the user any period where the delegation ratio is being treated as a score in either direction.

## Example Usage

**Scenario 1: Weekly close (via end-week)**
```
/audit-attention
```
Run as part of end-week. Classifies the week's activities, finds 40% on compounding work, flags two depreciating activities (manual test scaffolding, status-summarizing) to delegate next week, and one compounding activity (architecture decision) that got crowded out and needs a ring-fenced block.

**Scenario 2: Mid-week drift check**
```
/audit-attention
```
User feels scattered. Audit of the last three days shows most time on reactive, depreciating tasks. Output recommends two specific compounding activities to protect for the rest of the week.

**Scenario 3: Quarterly re-sort**
```
/audit-attention
```
Full re-sort of recurring activities. Notes that "reviewing generated PRs" has shifted from compounding toward depreciating as review tooling improved, while "designing evals" has grown more compounding. Updates the keep/delegate plan accordingly.

## Next Step

- During a weekly close, append this audit as the `## Attention Allocation` section of end-of-week-review's `review.md`.
- To act on results, add ring-fenced focus blocks to the next day or week plan via `/start-day` or `/start-week`.
