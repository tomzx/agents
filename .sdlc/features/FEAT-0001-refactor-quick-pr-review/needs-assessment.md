---
issue: "#15"
title: "Complexity: Refactor quick-pr-review (451 lines) with excessive branching"
status: draft
---

# Needs Assessment: Complexity: Refactor quick-pr-review (451 lines) with excessive branching

## Problem Statement

The `quick-pr-review` skill has grown to 498 lines (451 at filing) with 8 review checks and trust-level branching at 3 steps. This makes the skill difficult to maintain, reason about, extend with new checks, and increases the risk of logic errors in automated PR reviews that directly affect other teams' workflows.

## Stakeholders

| Stakeholder | Role | How they experience the problem |
|---|---|---|
| Skill maintainers | Developer | Navigating a 500-line skill file with deeply nested branching is slow and error-prone |
| Skill consumers | Developer | Review quality degrades as complexity makes it harder to add or adjust checks correctly |
| Codebase health | System | Complexity hotspots accumulate, making the wider skills library harder to onboard into |

## Evidence of Need

| Source | What it shows | Strength |
|---|---|---|
| `find-complexity-hotspots` diagnostic | Identified `quick-pr-review/SKILL.md` as a Critical complexity hotspot at 451 lines with 8 review checks and trust-level branching at 3 steps | Strong |

**Evidence rating:** Strong

The need is demonstrated by an automated diagnostic tool, not by assumption. The hotspot analysis is quantitative and reproducible.

## Cost of Inaction

| Aspect | Impact |
|---|---|
| What breaks or degrades today | The skill is already flagged as a Critical hotspot; maintenance difficulty grows with each new check added |
| Existing workarounds | None — the skill continues to function but is brittle |
| Trend | Growing — as more review checks are considered (e.g., new dependency types, new security patterns), the file will only grow longer |

**Cost-of-inaction rating:** Strong

The status quo is tolerable (the skill works), but the maintenance burden and error risk are already flagged as critical. Each future addition increases complexity linearly.

## Alternative Paths

| Alternative | How it addresses the need | Trade-offs |
|---|---|---|
| Extract review checklist to a shared reference | Reduces the main skill file size and centralizes check definitions | Does not address the trust-level branching complexity |
| Leave as-is | No effort required | Complexity continues to grow; maintenance burden increases |

**Could the need be met without new code?** Partially

Extracting checklist logic to a shared reference file addresses part of the problem but does not simplify the trust-level branching or structural complexity. Some new code/restructuring is justified to make the skill maintainable long-term.

## Strategic Alignment

| Criterion | Assessment |
|---|---|
| Aligns with project goals | Yes — code quality and maintainability are core to the SDLC skills library |
| Serves core or edge use case | Core — quick-pr-review is a frequently-used skill that unblocks other developers |
| Dependency enabler | Unblocks future review checks and reduces risk when modifying the skill |

**Alignment rating:** Strong

## Verdict

**Overall needs assessment:** Needed

**Rationale:** The complexity hotspot is objectively demonstrated by a diagnostic tool, the skill is core to the workflow (used to unblock PRs), and the cost of inaction grows with each new check added. The evidence is strong, strategic alignment is strong, and while the skill still works today, the trend is growing. This is a clear case of proactive maintenance to prevent future quality degradation.

## Conditions to Proceed

- None — the need is clearly established by the diagnostic evidence.

## Open Questions

1. What is the ideal shared location for extracted checklist items (a `references/` file within the skill directory or a cross-skill shared reference)?
