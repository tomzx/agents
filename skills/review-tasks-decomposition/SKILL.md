---
name: review-tasks-decomposition
description: Review a task decomposition for granularity, completeness, dependency clarity, and estimability.
---

# Review Tasks Decomposition

Audits a task decomposition and reports findings across five categories: granularity, completeness, dependencies, acceptance criteria, and estimability.

## Prerequisites

- `.sdlc/features/FEAT-NNNN-<slug>/tasks/` directory containing individual task files, or task files provided in context
- `.sdlc/features/FEAT-NNNN-<slug>/plan.md` (optional, improves completeness check)

## Steps

1. Read all `.md` files in `.sdlc/features/FEAT-NNNN-<slug>/tasks/`. Update each task file's `status: draft` → `status: in-review` in the frontmatter before proceeding.
2. Evaluate each task against the checklist below.
3. Report findings by category. Omit categories with no findings.
4. After all findings are resolved: update every task file's `status: in-review` → `status: pending`. Append unresolved open questions to `.sdlc/features/FEAT-NNNN-<slug>/questions.md` (create the file if it does not exist). For any question that carries meaningful risk to the implementation, also invoke `/create-assumption` to record it formally.
5. Populate the Task Progress table in `.sdlc/features/FEAT-NNNN-<slug>/progress.md` with all tasks, their sizes, and `pending` status. Set `re_entry_point: "tests"` and `current_phase: "tasks-complete"` in the frontmatter.

## Review Checklist

### Granularity
- Are any tasks too large to complete in one session (> 2 days)?
- Are any tasks too small and should be merged with adjacent work?
- Is each task independently deliverable?

### Completeness
- Do the tasks collectively cover all plan phases and deliverables?
- Are setup, teardown, and operational tasks included (migrations, feature flags, monitoring)?
- Are documentation and testing tasks explicitly listed?

### Dependencies
- Are all dependencies explicitly declared?
- Are there implicit dependencies (shared state, ordering assumptions) not captured?
- Is the critical path identified?
- Are there dependency cycles?

### Acceptance Criteria
- Does every task have verifiable acceptance criteria?
- Are the criteria specific and measurable?
- Do criteria distinguish "done" from "done and tested"?

### Estimability
- Is a size or effort estimate given for each task?
- Are estimates consistent with the described scope?
- Are there tasks with high uncertainty that need a spike first?

## Output Format

```markdown
## Granularity

<Findings or "No issues found.">

## Completeness

<Findings or "No issues found.">

## Dependencies

<Findings or "No issues found.">

## Acceptance Criteria

<Findings or "No issues found.">

## Estimability

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

**Scenario 1: Missing test tasks**
Every feature task has a corresponding code task, but no testing tasks appear anywhere in the decomposition.
Report under Completeness.

**Scenario 2: Dependency cycle**
T-05 depends on T-08, and T-08 depends on T-05.
Report under Dependencies.

**Scenario 3: XL task left unbroken**
T-03 "Implement the payment module" is marked `[L]` but its description spans 6 distinct features.
Report under Granularity.

## Next Step

Once all findings are resolved and tasks are set to `status: pending`, continue with `/create-tests`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
