---
name: improve-sessions
description: Mine past AI coding sessions from the agentsview SQLite archive and produce prioritized recommendations for improving future sessions (recurring friction, corrections, repeated questions, manual loops, missing skills). Use when the user says /improve-sessions, "improve future sessions", "what should I learn from my sessions", "review my session history for improvements", "why do my sessions keep going off the rails", or wants recommendations derived from session history rather than the current session.
allowed-tools: Bash(uv:*), Read, Glob, Grep
argument-hint: "[--since YYYY-MM-DD] [--until YYYY-MM-DD] [--limit N]"
---

BASE_DIR=!`~/.agents/scripts/get-env NOTES_DIR`

TODAY=!`date +%Y-%m-%d`

# Improve Sessions

Reads a window of past sessions from the agentsview archive (which syncs OpenCode, Codex, Gemini, Claude, and other harnesses), identifies recurring friction patterns across them, and proposes concrete changes that make future sessions better: AGENTS.md rules, memory entries, new or improved skills, hooks, and scheduled agents.

The analysis is read-only over the archive.
It never advances the `sessions-memory` watermark, so it can run at any cadence without interfering with memory processing.

## Prerequisites

- **agentsview archive**: a `sessions.db` produced by the agentsview daemon, resolved by the shared script in this order: explicit `--db` flag, `$AGENTSVIEW_DATA_DIR`, then `~/.agentsview/sessions.db`.
  If none exists, tell the user to install and run agentsview first.
- **Data access** comes from the `sessions-memory` script; do not write a second parser:

```bash
uv run skills/sessions-memory/scripts/fetch_sessions.py status
```

- Read-only discipline: use `fetch` and `show` only.
  Never run `commit`, that belongs to `sessions-memory`; skipping it is safe and only means the same sessions reappear there later.

## Scope boundaries

- `/automate-session` and `/improve-autonomy` reflect on the **current** session.
  This skill works over **historical** sessions and only produces recommendations.
- `/sessions-memory` turns sessions into memory artifacts.
  This skill turns them into improvement recommendations, and may hand some findings to it (memory entries) or to `/identify-skill-gaps` (skill backlog entries).

## Steps

### 1. Scope the window and fetch sessions

```bash
uv run skills/sessions-memory/scripts/fetch_sessions.py status
uv run skills/sessions-memory/scripts/fetch_sessions.py fetch --since 2026-09-11 --min-user-messages 2 --limit 30
```

Defaults when the user gives no window: the last 14 days, limit 30.
Raise `--max-content` (or set `0`) when transcripts need to be read in full, and use `show <id>` for deep dives on specific sessions.
Sessions with fewer than two user messages offer little to improve, so `--min-user-messages 2` is the default lens here.
The script also excludes deleted sessions, automated runs, subagents, and scheduler-triggered runs (title carries the run timestamp); pass `--include-scheduled` when a scheduled run itself is under review.

### 2. Take the quantitative sweep

Before reading transcripts, build a coverage table from the fetch JSON so the deep dive targets the right sessions:

| Metric | Value |
|--------|-------|
| Sessions in window | <N> |
| By project / agent | <counts> |
| Outcomes | <completed / failed / abandoned counts> |
| Longest sessions | <ids and durations> |
| Sessions with many user turns | <ids, top 5> |

Flag for close reading: failed or abandoned sessions, sessions with unusually many user turns (a proxy for friction), and the longest sessions.

### 3. Extract friction signals per session

Read the flagged transcripts and, for each, list every friction signal found.
Every signal must cite its evidence: session id plus a short quote or tool sequence.
No evidence, no signal.

| Signal | Look for |
|--------|----------|
| **Repeated instruction** | The user teaches the same preference or convention more than once, in this session or across sessions |
| **Correction** | The agent took a wrong approach and the user redirected it (classify the root cause: missing context, unclear guidance, wrong tool, missing skill) |
| **Repeated lookup** | The same information is looked up again across sessions (file locations, commands, API behavior) |
| **Manual loop** | The user performs the same mechanical approval or edit sequence repeatedly |
| **Missed skill** | An existing library skill should have been used but was not |
| **Dead end** | An approach was explored then abandoned, or the session failed outright |

### 4. Aggregate signals into patterns

Group signals by underlying cause, not by surface topic.
A pattern requires at least two occurrences in the window, otherwise it is a one-off and belongs in the report's appendix only.
For each pattern record:

- **Name**: one line, cause-focused (for example "re-derives project layout every session").
- **Occurrences**: count and affected session ids.
- **Cost**: rough minutes lost per occurrence, or the risk when wrong.
- **Class**: context gap, guidance gap, missing automation, or missing skill.

### 5. Map patterns to improvement primitives

| Pattern class | Primitive | Where it lands |
|---------------|-----------|----------------|
| Context gap | Memory entry | `sessions-memory` / `para-memory-files` |
| Guidance gap | AGENTS.md rule | repo or global AGENTS.md |
| Missing automation | Hook, scheduled agent, or background agent | `automate-session` implementation paths |
| Missing skill | New skill or backlog entry | `/create-skill`, or `/identify-skill-gaps` backlog |
| Weak existing skill | Skill improvement | `/improve-skill <name>` |

One pattern can map to several primitives; prefer the cheapest one that fully resolves the pattern.

### 6. Prioritize

Rank patterns by **frequency × cost ÷ effort**, where effort is the cost of the mapped primitive.
Break ties toward patterns that recur across multiple projects, since their fixes generalize.

### 7. Present the report and gate on changes

Show the report (format below), then stop and ask:

> "Want me to apply the top recommendations now?
> I can update AGENTS.md, write memory entries, create a skill, or set up a scheduled agent."

Apply only what the user approves, using the primitive's own skill.
For anything declined or deferred, append one line per item to `{BASE_DIR}/session-improvement-backlog.md` (create if absent), dated `{TODAY}`.

## Output Format

```markdown
## Session Improvement Report

**Window:** <since> to <until> | **Sessions analyzed:** <N> | **Date:** {TODAY}

### Coverage

<Quantitative sweep table from step 2.>

### Friction Patterns

#### <Pattern name> (<class>)
- **Evidence:** <N> occurrences, e.g. <session-id>: "<quote>"
- **Cost:** <minutes per occurrence or risk>
- **Fix:** <primitive and concrete change>

### Priority Order

1. **<Pattern>** — <freq>×/<wk>, ~<N> min each, <effort> to fix
2. ...

### Proposed Changes

| Change | Target file / system | Approved? |
|--------|----------------------|-----------|
| <AGENTS.md rule text> | <repo> AGENTS.md | pending |
| <memory entry fact> | $AGENT_HOME/life/<entity>/items.yaml | pending |

### Recommendation

> <One sentence on the single change with the largest effect.>
```

## Anti-patterns

- **Blaming the agent**: assume a context or guidance gap first; asking "why didn't the agent figure it out" prevents finding the systemic fix.
- **The surface fix**: if a fact was missing, ask why it was missing; the fix is the capture mechanism, not one more fact.
- **The retrospective-only**: every run must produce at least one applied change or one backlog entry, never analysis alone.
- **The guidance overdose**: before adding a rule, check no existing rule already covers it; prefer clarifying over accumulating.

## Example Usage

**Scenario 1: weekly improvement pass**

```
/improve-sessions --since 2026-09-15
```

Fetches the last week, finds "re-derives project layout" in 4 sessions and "approves each commit by hand" in 6, and recommends one AGENTS.md rule plus a scheduled review agent.

**Scenario 2: after a bad stretch**

```
/improve-sessions --since 2026-09-01 --until 2026-09-14
```

The sweep shows 40% of sessions ended abandoned.
Deep dives reveal two dead-end patterns, one of which maps to a missing feasibility rule for AGENTS.md and one to a `/create-skill` candidate.

**Scenario 3: nothing actionable**

The window holds 5 one-off signals under the pattern threshold.
The report lists them in the appendix, recommends nothing, and states why.
