---
name: devils-advocate
description: Challenge an idea, plan, decision, or argument by constructing the strongest case against it. Use when the user says /devils-advocate, "challenge me", "play devil's advocate", "what am I missing", "steelman the other side", "poke holes in this", or wants stress-testing before committing.
argument-hint: "[idea, plan, decision, or argument to challenge]"
---

# Devil's Advocate

Takes the user's position and constructs the strongest possible case against it, then surfaces assumptions, risks, blind spots, and alternatives the user may not have considered.
The goal is not to win an argument but to find the weak points before reality does.
If the position survives serious challenge, the user proceeds with confidence; if it does not, they learn that now instead of later.

## Prerequisites

- A position to challenge: an idea, plan, decision, proposal, argument, or course of action provided as an argument, in context, or via file paths.
- No codebase access required, though if the position involves code or architecture, read the relevant files to ground the challenge in reality rather than speculation.

## How to Be a Useful Adversary

- **Steel-man, do not straw-man.** Construct the strongest version of the opposing view, not a weak one that is easy to knock down. The user benefits from the best counterarguments, not the easiest.
- **Be specific, not generic.** "This might fail" is useless; "this fails if the API rate limit is hit during peak hours because the retry logic has no backoff" is useful.
- **Challenge the problem, not just the solution.** Sometimes the idea is well-executed but solves the wrong problem. Flag that.
- **Distinguish fatal flaws from manageable risks.** Not every concern is a reason to stop. Be clear about severity.
- **Stay constructive.** The goal is to strengthen the user's thinking, not to paralyze them. End with a clear verdict and actionable next steps.

## Steps

1. Restate the user's position in your own words to confirm understanding. If the restatement does not match, ask for clarification before proceeding.
2. Identify the core assumptions the position depends on. Mark each as explicit (stated by the user) or implicit (unstated but necessary).
3. For each assumption, assess: how confident should the user be that it holds? What evidence supports it? What would disconfirm it?
4. Construct the strongest counterargument. Argue against the position as if you genuinely believed the opposite, using the best available reasoning.
5. Enumerate failure modes: what specifically goes wrong, under what conditions, and what the blast radius is.
6. Identify blind spots: perspectives, stakeholders, or scenarios the user has not considered.
7. Consider alternative paths: is there a meaningfully different way to achieve the same goal that the user dismissed or never considered?
8. Trace second-order effects: what happens after the immediate outcome? What does this enable or block downstream?
9. Assess opportunity cost and timing: is this the right thing to do now, or is there something more valuable being displaced?
10. Deliver the verdict and recommendations using the output format below.

## Challenge Framework

### Assumptions
- What must be true for this to work?
- Which assumptions are the weakest, and what happens if they break?
- Are any assumptions inherited from a context that no longer applies?

### Counterargument
- What is the strongest case against this?
- Who would make it, and what would their reasoning be?
- What evidence or experience would they point to?

### Failure Modes
- How does this break under stress, scale, or edge cases?
- What is the worst realistic outcome, and how likely is it?
- Are there failure modes that are irreversible or hard to recover from?

### Blind Spots
- Whose perspective is missing from this position?
- What scenarios or edge cases have not been considered?
- What information would change the conclusion, and has the user looked for it?

### Alternatives
- Is there a meaningfully different approach that achieves the same goal?
- Was an alternative dismissed too quickly? Why?
- Could a smaller version of this achieve most of the value at a fraction of the cost or risk?

### Second-Order Effects
- What does this enable or block downstream?
- Does this create new dependencies, constraints, or expectations?
- Will this decision be easy to reverse if conditions change?

### Opportunity Cost
- What is the user not doing because they are doing this?
- Is now the right time, or would waiting improve the odds?
- Is the effort proportional to the expected value?

## Output Format

```markdown
## Devil's Advocate Challenge

### Position Restated
<one or two sentences confirming the position being challenged>

### Assumptions

| Assumption | Explicit / Implicit | Confidence | If it breaks |
|------------|---------------------|------------|--------------|
| <assumption> | <E/I> | <High/Med/Low> | <consequence> |

### Strongest Counterargument

<the best case against the position, argued earnestly>

### Failure Modes

- <failure mode>: <conditions> -> <blast radius>. Severity: fatal / serious / manageable.
- ...

### Blind Spots

- <blind spot and why it matters>
- ...

### Alternatives

- <alternative approach and why it may be better>
- ...

### Second-Order Effects

- <downstream consequence>
- ...

### Opportunity Cost

<what is being displaced, and whether the timing is right>

## Verdict

**Holds / Needs revision / Reconsider**

<one paragraph explaining the verdict>

## Recommendations

1. <actionable step to address the most serious concern>
2. <actionable step to de-risk before proceeding>
3. <what to monitor after proceeding, if applicable>
```

## Verdict Definitions

| Verdict | When |
|---------|------|
| **Holds** | The position survives serious challenge. Concerns are manageable and do not undermine the core logic. Proceed with confidence. |
| **Needs revision** | Valid concerns that should be addressed before or during execution, but the core direction is sound. Proceed with adjustments. |
| **Reconsider** | A fatal flaw, a broken core assumption, or a better alternative that was not considered. Rethink the approach before committing. |

## Example Usage

**Scenario 1: Challenging a build-vs-buy decision**
User proposes building an internal feature flag system instead of buying one. The challenge surfaces an implicit assumption that the team will maintain it long-term, a failure mode where the system becomes a maintenance burden with no owner, and an alternative (using a managed service for the first 6 months to learn the real requirements before building). Verdict: Needs revision.

**Scenario 2: Challenging a technical approach**
User proposes migrating from REST to gRPC for all internal services. The counterargument points out that the team has no gRPC expertise, the operational tooling (debugging, monitoring) is built around HTTP, and the latency gains are irrelevant at current traffic. Verdict: Reconsider.

**Scenario 3: Challenging a product direction**
User proposes adding a complex rules engine to satisfy one enterprise customer. The challenge identifies that the core assumption (other customers will want this) is unsupported by evidence, the opportunity cost is high (3 months of engineering), and a simpler configuration approach would satisfy 80% of the need. Verdict: Needs revision.

**Scenario 4: Position survives challenge**
User proposes adopting a specific library after evaluating three alternatives with benchmarks. The challenge confirms the assumptions are well-grounded, the failure modes are manageable, and the alternatives were fairly considered. Verdict: Holds.

## Next Step

- If the verdict is **Holds**: proceed with the plan and consider recording the decision via `/create-decision`.
- If the verdict is **Needs revision**: address the top recommendations, then re-run `/devils-advocate` on the revised position if the changes are significant.
- If the verdict is **Reconsider**: use `/create-needs-assessment` or `/create-feasibility` to re-examine the foundation before investing further.

## Useful Commands Reference

No CLI commands required. This skill operates on the position provided in context or via file reads.
