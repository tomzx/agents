---
name: create-roadmap
description: Sequence initiatives across Now/Next/Later horizons, aligned to goals, so prioritization and needs-assessment have a strategic plan to follow.
---

# Create Roadmap

Defines the project's roadmap as a single context-level artifact: the initiatives the project is betting on, sequenced across horizons (Now / Next / Later) and tied to the objectives in `goals.md`.

Other skills consult the roadmap when deciding what to work on next. Without a roadmap, prioritization is ad hoc: every issue is ranked in isolation, sequencing constraints are invisible, and there is no shared view of what is committed versus exploratory. A plan (`plan.md`) describes how to build one feature; the roadmap describes what to build and in what order across the whole project.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/context/project-overview.md` (must exist, for purpose and scope).
- `.sdlc/context/goals.md` (strongly recommended; every initiative aligns to an objective and key result. If absent, note that alignment cannot be checked and flag it as an open question).
- `.sdlc/context/roadmap.md` (optional; if present, revise rather than replace, per Revision Mode below).
- Existing features under `.sdlc/features/` and the open issue backlog (optional, to roll up into initiatives and detect orphaned work).

## Steps

1. Read `.sdlc/context/project-overview.md` for purpose, scope, and stakeholders.
2. Read `.sdlc/context/goals.md` if present; these objectives anchor every initiative. Read `.sdlc/context/service-levels.md` if present, for reliability constraints that bound what can be committed to Now.
3. Inventory in-flight and planned work: scan `.sdlc/features/` and, if the backlog is in GitHub, list open issues with `ghx issue list --state open`.
4. Confirm the horizon model with the user if not already stated: prefer **Now / Next / Later** (the default) over date-based quarters, because horizons avoid the false precision of dates. Note the current period.
5. Identify the recurring **themes** for this period, each tied to a `goals.md` objective.
6. Group work into **initiatives** (a coherent bet that moves a metric), not individual tickets. For each initiative capture the objective it advances, an owner, the hypothesis, scope, dependencies, confidence, and a success signal tied to a key result or KPI.
7. Place each initiative in the right horizon:
   - **Now**: committed, in-flight, or starting this horizon. Fully scoped.
   - **Next**: planned for the following horizon. Roughly scoped.
   - **Later**: exploratory, hypothesis-level, low confidence.
8. Map **sequencing and dependencies** between initiatives (hard, soft, external), and render a **Mermaid Gantt chart** in the Timeline section visualizing the initiatives across the horizons, anchored to the current period. Use the horizons as `section` groups, approximate spans (not hard dates), and `after <id>` to show dependencies.
9. State **Not Now** explicitly: deferred work and the condition that would promote it.
10. Record **capacity and hard constraints** if known (team capacity, regulatory deadlines, frozen periods).
11. Set a **review cadence** and today's date.
12. Write the output to `.sdlc/context/roadmap.md`. If it already exists, revise per Revision Mode.

## Output Format

Use the template at `skills/sdlc/templates/context/roadmap.md`. Write the result to `.sdlc/context/roadmap.md`.

## Revision Mode

If `.sdlc/context/review-roadmap.md` exists with `verdict: changes-requested`, revise the existing `.sdlc/context/roadmap.md` to address each finding rather than regenerating from scratch.
Preserve content the review did not challenge.
Make the minimum changes that resolve every finding.

## Roadmap Design Guidance

- **Roadmap is strategy and sequence, not a calendar.** Prefer horizons over dates. A date the team cannot honor is worse than a horizon it can; dates turn the roadmap into a commitment device and penalize honest re-planning.
- **Every initiative aligns to a goal.** An initiative with no objective is a wishlist item. If it advances nothing in `goals.md`, either the goals are incomplete or the initiative does not belong.
- **Group into initiatives, not tickets.** An initiative is a bet: a coherent body of work that moves a metric. Individual features and issues roll up into it, not the other way around.
- **State the bet and the success signal.** For each initiative, write the hypothesis ("if we do this, X improves because Y") and how you will know it worked (a key result or KPI). An initiative with no success signal cannot be evaluated.
- **Confidence falls toward Later.** Now is high-confidence and scoped; Next is medium; Later is a low-confidence hypothesis with open questions. If a Later item is high-confidence, it probably belongs in Next or Now.
- **Not Now matters as much as Now.** Stating what is deliberately deferred, and the condition that would promote it, protects focus and makes re-planning deliberate instead of silent.
- **Sequence honestly.** Mark hard dependencies that block an initiative. Do not put a dependent item in Now while its dependency sits in Next.
- **Capacity bounds Now.** The Now horizon should be achievable with known capacity. An overloaded Now is a plan that will miss.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`.
If the artifact could not be produced, omit the file.

## Example Usage

**Scenario 1: Growth-focused quarter with Now/Next/Later**
Goals objective: "Make existing users more active."
Now: "Onboarding redesign" (in-flight, FEAT-42, owner Growth, confidence High, success signal: activation rate 40% to 60%).
Next: "In-product re-engagement emails" (rough scope, confidence Medium).
Later: "AI-assisted digest" (hypothesis, confidence Low, open question: do users want a digest at all).
Not Now: "Mobile app" (waiting on activation to improve first; promote when activation reaches 55%).

**Scenario 2: Quarter-based alternative**
Team prefers calendar quarters. Horizon scheme set to 2026 Q3 / Q4 / 2027 Q1, with the same initiative fields. Now = Q3, fully scoped; Next = Q4, rough; Later = 2027 Q1, exploratory.

**Scenario 3: Early product, no backlog yet**
No features or issues exist yet.
Define the Now horizon from the goals directly (2-3 initiatives), keep Next and Later thin, and flag "no backlog to roll up" as an open question. Revisit once issues exist.

**Scenario 4: Orphaned in-flight work**
FEAT-17 is in-flight but advances no initiative.
Either add the initiative it belongs to (and the objective), or move FEAT-17 to Not Now. Surface this as a finding for `/review-roadmap` rather than silently dropping it.

## Completion Checklist

Before handing off to review, confirm:

- [ ] Every initiative aligns to a `goals.md` objective and has a success signal tied to a key result or KPI
- [ ] Horizons used (Now/Next/Later) with confidence falling toward Later; Not Now stated with promotion conditions
- [ ] Mermaid Gantt chart included in the Timeline section, anchored to the current period, with horizons as sections and dependencies via `after <id>`

Self-check the draft against the [`review-roadmap` checklist](../review-roadmap/SKILL.md) and fix what you can, so review finds less to flag.

## Next Step

Run `/review-roadmap` to audit the roadmap for alignment, sequencing, focus, horizon discipline, and currency before relying on it for prioritization.
Once approved, `prioritize-issues` and `create-needs-assessment` read `.sdlc/context/roadmap.md` directly when ranking work and checking strategic fit.

## Useful Commands Reference

| Command | Description |
|---|---|
| `ghx issue list --state open --limit 100` | List open issues to roll up into initiatives (cached) |
