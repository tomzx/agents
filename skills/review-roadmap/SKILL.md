---
name: review-roadmap
description: Review a roadmap for alignment, sequencing, focus, horizon discipline, and currency before it drives prioritization.
---

# Review Roadmap

Audits a roadmap across six categories: alignment, sequencing, focus and capacity, horizon discipline, evidence and outcomes, and currency, so the roadmap can reliably drive prioritization and needs-assessment.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/context/roadmap.md`, or a roadmap provided in context or as a file path.
- `.sdlc/context/goals.md` (to verify every initiative aligns to an objective).
- `.sdlc/context/project-overview.md` (to verify purpose and scope alignment).
- Features under `.sdlc/features/` and the open issue backlog (optional, to spot orphaned work and stale roll-ups).

## Steps

1. Read the roadmap from `.sdlc/context/roadmap.md` if present, otherwise from context or as a file path.
2. Cross-reference against the goals, project overview, and existing features/issues.
3. Identify issues in each category below.
4. Report findings. Omit any category that has no findings.
5. Write the findings to `.sdlc/context/review-roadmap.md` with frontmatter `artifact: roadmap`, `verdict` (`approved` if no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, with the findings as the body, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body.

## Review Checklist

### Alignment
- Does every initiative advance a stated objective (and ideally a key result) in `goals.md`?
- Are existing features and open issues rolled up under an initiative, or is there orphaned work advancing no initiative?
- Do the themes follow from the project overview's purpose and scope?

### Sequencing
- Are dependencies honored: no initiative in Now while a hard dependency sits in Next or Later?
- Is the critical path sensible, with no impossible or circular ordering?
- Are hard, soft, and external dependencies distinguished, and do external ones have a contingency?
- If a Mermaid Gantt chart is present, does it agree with the sequencing table (same dependencies, same horizon placement), and does it avoid false-precision dates by using approximate spans?

### Focus and Capacity
- Is the Now horizon achievable given stated capacity, or is it overloaded?
- Are there too many parallel Now initiatives for the focus and ownership available?
- Is each Now initiative fully scoped (owner, scope, dependencies, success signal)?

### Horizon Discipline
- Does confidence fall toward Later (Now high and scoped, Next medium, Later low and hypothesis-level)?
- Are horizons used rather than false-precision dates, or if dates are used, are they honest commitments and clearly marked?
- Is a high-confidence item stranded in Later, or a low-confidence hypothesis placed in Now?

### Evidence and Outcomes
- Does each initiative state the bet (the hypothesis) and a success signal tied to a key result or KPI?
- Is "why now" implied or stated for Now items, and is there an invalidating condition for the riskier bets?
- Are success signals measurable outcomes, not outputs ("ship the dashboard" is an output)?

### Currency
- Is a review cadence set, with a last-reviewed date that is recent?
- Are initiatives that have shipped, been abandoned, or been descoped still listed as active (drift)?
- Do the roll-up references (FEAT-N / issues) still match the actual backlog?

## Output Format

```markdown
## Alignment

<Findings or "No issues found.">

## Sequencing

<Findings or "No issues found.">

## Focus and Capacity

<Findings or "No issues found.">

## Horizon Discipline

<Findings or "No issues found.">

## Evidence and Outcomes

<Findings or "No issues found.">

## Currency

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

## Example Usage

**Scenario 1: Orphaned in-flight feature**
FEAT-17 is in-flight but rolls up to no initiative.
Report under Alignment: map it to an initiative (and objective), or move it to Not Now with a reason.

**Scenario 2: Dependency violates sequencing**
A Now initiative depends on an external API migration that sits in Next.
Report under Sequencing: either move the dependent initiative to Next, or pull the dependency into Now.

**Scenario 3: Output mistaken for outcome**
Initiative success signal reads "ship the reporting dashboard."
Report under Evidence and Outcomes: rephrase as the outcome the dashboard enables (e.g., "X% of admins generate a weekly report").

**Scenario 4: Overloaded Now**
Now lists seven initiatives for a two-person team with no stated capacity headroom.
Report under Focus and Capacity: Now must be achievable; move lower-confidence items to Next.

**Scenario 5: Stale roadmap**
Last reviewed date is six months old and two Now initiatives have since shipped.
Report under Currency: re-baseline, remove shipped/abandoned items, and reset the review cadence.

## Next Step

Once the findings verdict is `approved`, the roadmap is ready to drive prioritization.
`prioritize-issues` and `create-needs-assessment` read `.sdlc/context/roadmap.md` directly when ranking work and checking strategic fit.

In a greenfield project with no issue backlog yet, skip `/create-issue`: the first Now initiative is already committed and scoped by the roadmap, so take it straight to `/create-requirements` as its feature brief.
The requirements skill creates a `p`-prefixed pending feature for it; promote that feature to an issue later with `/create-placeholder-issue`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `ghx issue list --state open --limit 100` | List open issues to check roll-ups and orphaned work (cached) |
