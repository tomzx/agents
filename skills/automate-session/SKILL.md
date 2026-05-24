---
name: automate-session
description: Analyze what was done in the current session and surface concrete ways the workflow could have been automated to remove the user from the loop. Use when the user asks /automate-session, "how could this be automated?", or "what could we automate from this session?".
---

# Automation Opportunities

Reflects on the current session and identifies which steps could have been handled autonomously, a scheduled agent, or a triggered hook, removing the user from the loop entirely or reducing their involvement to review-only.

## Prerequisites

- A session with at least some completed work (conversation history, git changes, or both)

## Steps

### 1. Reconstruct the session workflow

Build a chronological list of the steps taken during this session. Sources to draw from:

- Conversation turns: what did the user ask, decide, or approve?
- `git log --oneline` since session start: what changed?
- File reads, writes, edits made during the session
- Any external tool calls (GitHub, Slack, etc.)

Produce a numbered step-by-step trace of the session as if writing a runbook someone else would follow.

### 2. Classify each step by automation potential

For each step in the trace, assign one of three labels:

| Label | Meaning |
|---|---|
| **Auto** | Could run fully autonomously with no human input — deterministic, low-risk, well-scoped |
| **Review-gate** | An agent could execute it, but a human checkpoint (approve / reject) makes sense before or after |
| **Human** | Requires human judgment, creative direction, or irreversible external action with unclear scope |

A step qualifies as **Auto** if:
- Its inputs are available programmatically (git state, file content, API response)
- Its output is verifiable (tests pass, lint clean, diff is small and scoped)
- Failure is detectable and recoverable without human intervention
- It follows a pattern used repeatedly in prior sessions

A step is **Review-gate** if it is automatable but touches shared state (pushes to a remote, sends a message, opens a PR) or produces output a human should sanity-check before it propagates.

A step is **Human** if it involves priority trade-offs, novel design decisions, or communication requiring context only the user holds.

### 3. Identify the automation patterns

Group the Auto and Review-gate steps into one or more named automation patterns. For each pattern, describe:

- **What it would do**: the concrete actions it would take
- **Trigger**: what event starts it (commit pushed, PR opened, cron schedule, file saved, manual `/skill`)
- **Implementation path**: which agent primitive fits best
  - *Hook* — `PreToolUse`, `PostToolUse`, `Stop` hook in `settings.json`
  - *Skill* — a new `/skill-name` the user invokes once
  - *Scheduled agent* — a routine via `/schedule` that runs on a cron
  - *Background agent* — a long-running or triggered agent via `Agent(run_in_background: true)`
- **Review gate** (if any): what the user would see and approve before the automation continues
- **Risk / caveat**: what could go wrong and how it would be detected

### 4. Estimate the time savings

For each automation pattern, estimate:

- How many minutes this session spent on the steps it would cover
- Whether this workflow recurs (daily / weekly / per-PR / ad-hoc)
- Rough total minutes saved per week if automated

### 5. Prioritize

Rank the patterns by: **impact × frequency ÷ implementation effort**.

High-value candidates: high recurrence, low risk, existing skill or hook primitives map cleanly.
Low-value candidates: one-off tasks, steps that are mostly thinking, or steps where an agent would need unavailable context.

### 6. Offer to implement

For the top-ranked pattern(s), ask:

> "Want me to implement [pattern name] now? I can [create a skill / add a hook / set up a scheduled agent]."

If the user says yes, implement it immediately using the appropriate primitive.
If the user says no or wants to backlog it, append the suggestion to `~/notes/automation-backlog.md` (create if absent) with today's date and a one-line description.

## Output Format

```markdown
## Automation Opportunities

### Session Trace

1. <Step> — **Auto** / **Review-gate** / **Human**
2. ...

---

### Patterns

#### [Pattern Name]

- **What it does:** <description>
- **Trigger:** <event>
- **Implementation:** <Hook | Skill | Scheduled agent | Background agent>
- **Review gate:** <what the user approves, or "none">
- **Risk:** <failure mode and detection>
- **Time saved:** ~N min/session, recurs <frequency> → ~N min/week

---

### Priority Order

1. [Pattern A] — high impact, low effort, daily recurrence
2. [Pattern B] — medium impact, medium effort, weekly recurrence
3. ...

---

### Recommendation

> [One sentence on which pattern to implement first and why.]
```

## Example

**Session:** User asked an agent to check open PRs, summarize each one, post a comment on any PR older than 3 days, then update a tracking doc.

**Trace:**
1. Fetch open PRs from GitHub — **Auto**
2. Summarize each PR — **Auto**
3. Decide which PRs are "stale" (>3 days) — **Auto**
4. Draft comment text — **Auto**
5. Approve comment before posting — **Review-gate**
6. Post approved comment — **Auto**
7. Update tracking doc — **Auto**

**Pattern identified:** `stale-pr-nudge` — a scheduled agent running daily at 09:00 that fetches open PRs, identifies stale ones, drafts a comment, surfaces a review-gate notification to the user, and posts on approval.

**Implementation:** `/schedule` with a `quick-pr-reviews`-style skill + a `PostToolUse` hook that surfaces the draft before GitHub writes happen.
