---
name: improve-autonomy
description: Reflect on the current session and identify what would have been needed to run it fully autonomously end to end, producing a concrete readiness assessment and a prioritized gap list. Use when the user asks /improve-autonomy, "what would it take to run this autonomously?", or wants to assess autonomy readiness.
---

# Agentic Reflection

Asks: "What would have been needed to run this session autonomously, end to end, with no human in the loop?" Produces a structured readiness assessment that surfaces missing context, missing tools, missing decisions, and missing guardrails that prevented full autonomy.

This is not about incremental automation (see `/automate-session` for that). This is about imagining the fully autonomous version of the session and working backward to identify every gap.

## Prerequisites

- A session with at least some completed work (conversation history, git changes, or both)

## Steps

### 1. Reconstruct the session as an autonomous pipeline

Build a chronological trace of the session, then rewrite it as if an autonomous agent had performed it. For each step, describe:

- **What the agent would need to know** before executing it (context, requirements, constraints, preferences)
- **What the agent would need to access** (files, APIs, databases, environments, tools)
- **What the agent would need to decide** (priority, scope, trade-offs, style, tone)
- **How the agent would know it succeeded** (verifiable outcome, acceptance criteria, tests, review)

Sources to draw from:

- Conversation turns: every question asked, answer given, approval granted, or correction made
- `git log --oneline` since session start
- File reads, writes, edits made during the session
- Any external tool calls (GitHub, Slack, etc.)

### 2. Classify every human input by replaceability

For each instance where the human provided input, classify it:

| Label | Meaning |
|---|---|
| **Pre-loaded** | Could have been provided upfront in a spec, config file, AGENTS.md rule, or skill instructions. The information is stable, reusable, or project-specific. |
| **Derivable** | Could have been inferred from available context (codebase state, git history, prior sessions, project conventions). An agent with the right heuristics would have figured it out. |
| **Judgment call** | Required genuine human judgment (novel trade-off, aesthetic preference, business priority, stakeholder alignment). No reasonable heuristic or prior pattern could replace it. |
| **Correction** | The human corrected a wrong assumption or output. This reveals a gap in the agent's knowledge or reasoning that must be fixed before autonomy is possible. |

### 3. Identify the missing capabilities

From the analysis above, enumerate every gap that prevented full autonomy. Group them into categories:

#### Missing Context
Information the agent needed but did not have at the start.

- Unstated requirements or constraints
- Project-specific conventions not captured in AGENTS.md or skill instructions
- Domain knowledge assumed by the user

#### Missing Tools / Access
Things the agent could not do but would need to.

- APIs not available, environments not accessible
- Tools not installed or not in the toolset
- Permissions not granted (push, merge, deploy, notify)

#### Missing Decision Frameworks
Cases where the agent would need to make a choice but has no rule or heuristic to guide it.

- Ambiguous requirements with no resolution path
- Trade-offs with no stated priority
- Style or tone preferences not documented

#### Missing Guardrails
Safety checks or approval gates that would be needed before letting the agent run unsupervised.

- Validation steps (tests, lint, typecheck) not automated
- Review points where human oversight is currently essential
- Rollback mechanisms that need to be in place before autonomous execution

#### Missing Feedback Loops
Ways the agent would detect and recover from errors without human intervention.

- Error detection (how would it know something went wrong?)
- Self-correction paths (what would it try before giving up?)
- Escalation triggers (when should it stop and ask for help?)

### 4. Score autonomy readiness

For each step in the session, assign an autonomy score:

| Score | Meaning |
|---|---|
| **5 - Autonomous** | Could run fully unattended right now with existing tools and context |
| **4 - Almost ready** | Needs one small addition (a config value, a rule in AGENTS.md, a single tool permission) |
| **3 - Gaps exist** | Missing context or a decision framework, but the gap is identifiable and fillable |
| **2 - Major gaps** | Requires significant new capability, tooling, or knowledge to automate |
| **1 - Requires human** | Genuine judgment, creativity, or stakeholder input that cannot be reasonably automated |

Compute the session's overall autonomy readiness as the weighted average across all steps.

### 5. Produce the autonomous session specification

Write a concise spec for the fully autonomous version of this session. Include:

- **Inputs required before start**: everything the agent needs up front
- **Step-by-step autonomous workflow**: the full pipeline with no human checkpoints
- **Validation at each step**: how the agent confirms correctness before proceeding
- **Failure handling**: what the agent does when something goes wrong
- **Final acceptance criteria**: how the agent knows the overall session succeeded
- **Estimated confidence**: how confident you are that this autonomous version would produce equivalent or better results than the human-guided session

### 6. Prioritize the gap list

Rank the identified gaps by: **impact on autonomy × ease of filling ÷ recurrence frequency**.

For each gap, specify:

- What it is
- Which category it falls into (context, tools, decisions, guardrails, feedback)
- What it would take to fill it (one-time action, ongoing maintenance, tool development)
- How many sessions it currently blocks from full autonomy

### 7. Offer to act

For the top-ranked gap(s), ask:

> "Want me to fill this gap now? I can [update AGENTS.md / create a skill / add a config / write a spec]."

If the user says yes, implement it immediately.
If the user says no or wants to backlog it, append the gap to `{BASE_DIR}/agentic-gaps-backlog.md` (create if absent) with today's date and a one-line description.

## Output Format

```markdown
## Agentic Reflection

### Session Intent
<One or two sentences describing what the session accomplished.>

### Autonomous Pipeline

| Step | What the agent does | Autonomy Score | Missing |
|---|---|---|---|
| 1 | <description> | 5/5 | — |
| 2 | <description> | 3/5 | <gap description> |
| ... | ... | ... | ... |

**Overall autonomy readiness: X.X / 5.0**

---

### Human Input Analysis

| Input | Type | Replaceable by |
|---|---|---|
| <What the human provided> | Pre-loaded / Derivable / Judgment call / Correction | <how to eliminate it> |

---

### Gap Inventory

#### Missing Context
- <gap>: <what it would take to fill>

#### Missing Tools / Access
- <gap>: <what it would take to fill>

#### Missing Decision Frameworks
- <gap>: <what it would take to fill>

#### Missing Guardrails
- <gap>: <what it would take to fill>

#### Missing Feedback Loops
- <gap>: <what it would take to fill>

---

### Priority Gaps

1. **[Gap name]** — [category] — [effort to fill] — blocks N sessions/week
2. ...

---

### Autonomous Session Spec

**Inputs:** <list>
**Workflow:** <numbered steps>
**Validation:** <at each step>
**Failure handling:** <strategy>
**Acceptance criteria:** <how success is measured>
**Confidence:** <high / medium / low>

---

### Recommendation

> [One sentence on the single highest-leverage thing to do next to increase autonomy.]
```

## Example

**Session:** User asked the agent to fix a failing CI pipeline. The agent read the error log, identified a missing dependency, added it to `pyproject.toml`, ran the tests, committed, and pushed.

**Autonomous Pipeline:**
1. Detect CI failure from GitHub notification — Score: 4/5 (needs webhook or polling setup)
2. Read error log — Score: 5/5
3. Identify root cause — Score: 4/5 (needs a heuristic for common CI failure patterns)
4. Apply fix — Score: 3/5 (needs rule: "prefer minimal fixes, do not refactor while fixing CI")
5. Run tests locally — Score: 5/5
6. Commit and push — Score: 4/5 (needs guardrail: "only push to CI-fix branches, never to main")
7. Monitor CI result — Score: 4/5 (needs polling loop with timeout)

**Overall readiness: 4.1 / 5.0**

**Top gap:** Missing decision framework for "should I also fix the related warning?" — fillable by adding a rule to AGENTS.md: "When fixing CI, address only the reported failure. Do not touch unrelated code."

## Differentiation from `/automate-session`

`/automate-session` asks "which steps could be automated and what hooks/skills should I create?" It focuses on incremental automation within the current session structure.

`/agentic-reflection` asks "what would it take to run this entire session with zero human input?" It starts from the ideal (full autonomy) and works backward to identify every gap, including gaps in context, decision-making, and error recovery that `/automate-session` may not surface because it accepts the current workflow as given.
