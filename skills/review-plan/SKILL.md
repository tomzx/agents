---
name: review-plan
description: Review an implementation plan for completeness, feasibility, dependency coverage, and risk assessment.
---

# Review Plan

Audits an implementation plan and reports findings across six categories: completeness, feasibility, dependencies, risk coverage, timeline realism, and reversibility.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/plan.md` (unified) **or** `.sdlc/features/N-<slug>/plan/index.md` plus its sibling `plan/<concern>.md` files (split), or an implementation plan provided in context or as a file path
- `.sdlc/features/N-<slug>/specification.md` (optional, improves coverage analysis)

## Steps

1. **Resolve the plan.** Look for `.sdlc/features/N-<slug>/plan.md` first; if absent, look for `.sdlc/features/N-<slug>/plan/index.md` and read it together with every `plan/<concern>.md` it lists. Otherwise read from context or as a file path. Treat the whole plan set (index + concern files) as the unit under review.
2. Cross-reference against the specification or requirements if available.
3. Run the deterministic checker best-effort: render each `mermaid` block with `mmdc` (or `npx -y @mermaid-js/mermaid-cli`) when available. A tool that is not installed is skipped (never blocks); a render failure is a blocking finding under Dependencies or Timeline Realism.
4. Identify issues in each category below. For a split plan, also check that `plan/index.md` aggregates milestones, cross-concern dependencies, risks, and timeline consistently with the concern files.
5. Report findings. Omit any category that has no findings.
6. Write the findings to `.sdlc/features/N-<slug>/review-plan.md` with frontmatter `artifact: plan`, `verdict` (`approved` if there are no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, and the findings as the body, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body. For any question that carries meaningful risk to the implementation, also invoke `/create-assumption` to record it formally.

## Review Checklist

### Completeness
- Does the plan cover all requirements and spec deliverables?
- Are all phases clearly defined with success criteria?
- Are setup, deployment, and rollout steps included?

### Feasibility
- Are effort estimates realistic for the described work?
- Does the plan account for ramp-up, reviews, and integration work?
- Are milestones achievable within the stated constraints?

### Dependencies
- Are all internal and external dependencies identified?
- Does the phase-dependency flowchart match the per-phase `Depends on:` fields (no edge missing, no edge invented)?
- Are critical-path dependencies clearly marked?
- Is there a contingency for delayed or unavailable dependencies?

### Risk Coverage
- Are the most significant risks captured in the risk register?
- Does each risk have a concrete mitigation strategy?
- Are there single points of failure not mentioned as risks?

### Timeline Realism
- Is the timeline consistent with the effort estimates (gantt durations vs. phase effort)?
- When a gantt is present, do its task dependencies match the phase-dependency flowchart?
- Are there parallel tracks that could reduce total duration?
- Are buffer periods included for testing and review?

### Reversibility
- Can we undo this cleanly once implemented, or does the plan create one-way-door commitments?
- Does the plan include a rollback path for each phase (migrations, deployments, config)?
- Are irreversible steps (destructive migrations, deletions, public API removals) flagged and sequenced safely?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Feasibility

<Findings or "No issues found.">

## Dependencies

<Findings or "No issues found.">

## Risk Coverage

<Findings or "No issues found.">

## Timeline Realism

<Findings or "No issues found.">

## Reversibility

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

**Scenario 1: Missing rollout step**
Plan ends at "integration testing complete" with no deployment or rollout phase.
Report under Completeness.

**Scenario 2: Underestimated effort**
Phase 2 (API + auth) is estimated at 1 day for a spec that describes 8 endpoints with complex permission logic.
Report under Feasibility.

**Scenario 3: Unmitigated critical dependency**
Plan depends on a third-party API but lists no spike or contingency if that API is unavailable.
Report under Risk Coverage.

## Next Step

Once the findings verdict is `approved`, run `/publish-plan` to commit the plan and open a draft PR for author sign-off, then continue with `/create-tasks-decomposition`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `mmdc -i <diagram.mmd>` or `npx -y @mermaid-js/mermaid-cli` | Best-effort Mermaid render check; failure is a blocking finding |
