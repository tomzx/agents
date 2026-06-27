---
issue: "#4"
title: "Contextual Slack Support"
status: in-review
---

# Needs Assessment: Contextual Slack Support

## Problem Statement

People asking for help on Slack get answers that lack relevant context from past conversations, and the person answering questions must manually recall or search through prior discussions instead of having the system surface relevant historical context, learn from how questions were answered before, or answer routine questions autonomously.

## Stakeholders

| Stakeholder | Role | How they experience the problem |
|---|---|---|
| Repository owner | Developer / maintainer | Answers repetitive or previously-answered questions on Slack, wasting time searching history or re-explaining |
| Team members / colleagues | User | Receive slower or less complete answers because historical context is not surfaced |
| Agent system | System | Cannot currently answer Slack questions from past conversation context despite having Slack KB skills available |

## Evidence of Need

| Source | What it shows | Strength |
|---|---|---|
| Blog post (May 2026) | Author describes wanting contextually relevant answers and mentions slack-cached as a start | Moderate |
| Existing slack-kb-channel, slack-kb-individual, kb-organized-memory skills | Skills exist to capture Slack knowledge but are not wired into a question-answering flow | Weak (indirect) |

**Evidence rating:** Weak

No user requests, support tickets, or usage data are cited. The need is inferred from the author's own experience answering questions on Slack. The existence of the KB skills suggests the need was recognized before, but no concrete demand signals are presented.

## Cost of Inaction

| Aspect | Impact |
|---|---|
| What breaks or degrades today | Manual effort to answer Slack questions; institutional knowledge in past conversations goes underused |
| Existing workarounds | Manual search of Slack history; slack-kb-channel can be run manually per channel/month to build KB, but there is no query/QA layer on top |
| Trend | Stable |

**Cost-of-inaction rating:** Weak

The problem is real but the current workflow is functional. Slack conversation history is searchable, and the existing KB skills already capture and organize channel knowledge. The marginal cost of not having a contextual QA layer is moderate inconvenience, not a broken process.

## Alternative Paths

| Alternative | How it addresses the need | Trade-offs |
|---|---|---|
| Use existing slack-kb-channel + kb-organized-memory manually | Channel knowledge is already captured and organized by theme | No query/QA interface; requires manual invocation per channel/month; does not answer questions autonomously |
| Write a process guide for searching Slack history | Makes existing Slack search more discoverable | Still manual; no learning from past answers |
| Build a thin orchestrator skill that queries existing KBs | Wires existing pieces together without new infrastructure | Less integrated; may still lack answer-generation quality |

**Could the need be met without new code?** Partially

The existing slack-kb-channel, slack-kb-individual, and kb-organized-memory skills already capture and organize Slack conversation knowledge. A new contextual QA layer would add value on top, but the core knowledge-capture problem is already addressed.

## Strategic Alignment

| Criterion | Assessment |
|---|---|
| Aligns with project goals | Yes — the project's purpose is encoding repeatable workflows as composable skills |
| Serves core or edge use case | Core — answering questions from past context is a fundamental knowledge-work pattern |
| Dependency enabler | May unify existing KB skills into a higher-level capability |

**Alignment rating:** Strong

A contextual Slack support feature fits the project's mission of building composable skills for repeatable tasks. It would likely compose existing KB skills with a new query/QA layer, following the project's architectural pattern.

## Verdict

**Overall needs assessment:** Nice-to-have

**Rationale:** The problem is real and strategically aligned, but evidence of need is weak (no external demand signals, no usage data) and the cost of inaction is low (existing workflows and KB skills already capture knowledge). The strongest dimension is strategic alignment; the weakest is evidence. This is worth building once higher-priority work is complete, but should not block other efforts.

## Conditions to Proceed

- The author confirms they regularly spend significant time answering repeat questions on Slack that the KB skills already capture.
- Alternatively, a concrete time-savings estimate is produced from a week of manual tracking.

## Open Questions

1. What specific questions or patterns are being asked repeatedly on Slack today?
2. How much time per week is spent answering questions that existing KB content already covers?
3. What is the success rate of the existing slack-kb-channel and kb-organized-memory skills when used manually?
