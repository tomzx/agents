---
name: review-requirements
description: Review a requirements document for clarity, completeness, testability, and feasibility.
---

# Review Requirements

Audits a requirements document and reports findings across five categories: clarity, completeness, testability, feasibility, and conflicts.

## Prerequisites

- `.sdlc/features/FEAT-NNNN-<slug>/requirements.md`, or a requirements document provided in context or as a file path

## Steps

1. Read the requirements document. If reading from `.sdlc/features/FEAT-NNNN-<slug>/requirements.md`, update `status: draft` → `status: in-review` in the frontmatter before proceeding.
2. Identify issues in each of the five categories below.
3. Report findings using the output format. Omit any category that has no findings.
4. Resolve each conflict before approval: amend the requirements document so the conflicting requirements are reconciled (relax, re-prioritize, split, or merge them). If a conflict cannot be resolved within the document, append it to `.sdlc/features/FEAT-NNNN-<slug>/questions.md` as an open question and invoke `/create-decision` (for a chosen trade-off) or `/create-assumption` (for an unverified resolution) to record it formally.
5. After all findings are resolved: update `status: in-review` → `status: approved` in the frontmatter. Append unresolved open questions to `.sdlc/features/FEAT-NNNN-<slug>/questions.md` (create the file if it does not exist). For any question that carries meaningful risk to the implementation, also invoke `/create-assumption` to record it formally.

## Review Checklist

### Clarity
- Is each requirement unambiguous and precisely worded?
- Does it avoid vague terms ("fast", "user-friendly", "easy")?
- Is the subject and action of each requirement clear?

### Completeness
- Are all stakeholders represented?
- Are happy-path and error/edge cases covered?
- Are non-functional requirements (performance, security, reliability) present?
- Are acceptance criteria defined for every requirement?

### Testability
- Can each requirement be verified with a concrete test?
- Are acceptance criteria measurable and observable?
- Are quantitative thresholds given where applicable (e.g., "< 200 ms")?

### Feasibility
- Are any requirements technically impractical given the stated constraints?
- Are there scope or effort concerns that should be flagged?
- Do dependencies on external systems introduce unaddressed risk?

### Conflicts

Identify pairs (or groups) of requirements that cannot all be satisfied at once, or that pull the design in incompatible directions. Check for these conflict types:

- **Direct contradiction:** two requirements assert opposite behaviors (e.g., FR-02 "data is stored locally only" vs FR-07 "data syncs to the cloud").
- **Mutual exclusivity:** both are individually valid but cannot hold simultaneously (e.g., offline-first vs real-time sync).
- **Priority conflict:** two requirements compete for the same resource or attention and are both marked Must, with no stated tie-breaker.
- **Functional vs non-functional tension:** a behavior conflicts with a quality attribute (e.g., FR "log full request payloads" vs NFR "store no PII").
- **Constraint violation:** a requirement cannot coexist with a stated constraint (e.g., a requirement implying a library the constraints forbid).
- **Acceptance-criteria contradiction:** acceptance criteria for two requirements assert incompatible outcomes.

For each conflict found, report: the requirement IDs involved, the nature of the conflict, and a suggested resolution (relax one, re-prioritize, split, or escalate as an open question).

## Output Format

```markdown
## Clarity

<Findings or "No issues found.">

## Completeness

<Findings or "No issues found.">

## Testability

<Findings or "No issues found.">

## Feasibility

<Findings or "No issues found.">

## Conflicts

<For each conflict, or "No issues found.":>

| Requirements | Type | Description | Suggested Resolution |
|---|---|---|---|
| FR-01, NFR-01 | Mutual exclusivity | Offline support cannot coexist with real-time sync as both Must. | Re-prioritize one to Should, or define an offline-then-sync model. |
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

## Example Usage

**Scenario 1: Missing acceptance criteria**
FR-03 states "the system shall send notifications" but no acceptance criterion defines when, how, or to whom.
Report under Completeness.

**Scenario 2: Untestable requirement**
NFR-02 says "the UI must be intuitive."
Flag under Testability — rewrite as a measurable usability criterion.

**Scenario 3: Conflicting priorities**
FR-01 is marked Must (offline support) while NFR-01 is Must (real-time sync).
These conflict. Report under Conflicts.

## Next Step

Once all findings are resolved and `status` is set to `approved`, continue with `/create-existing-solutions` to survey prior art before designing.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
