---
name: review-mockups
description: Review UI mockups and wireframes for coverage, usability, accessibility, consistency, state coverage, responsiveness, spec fidelity, and implementability.
---

# Review Mockups

Audits UI mockups and wireframes and reports findings across eight categories: coverage, usability, accessibility, consistency, state coverage, responsiveness, spec fidelity, and implementability.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/mockups.md`, or a mockups document provided in context or as a file path
- `.sdlc/features/N-<slug>/requirements.md` (optional, improves coverage analysis)
- `.sdlc/features/N-<slug>/specification.md` (optional, improves spec-fidelity analysis)

## Steps

1. Read the mockups from `.sdlc/features/N-<slug>/mockups.md` if present, otherwise from context or as a file path.
2. Cross-reference against the requirements and specification if available.
3. Identify issues in each of the eight categories below.
4. Report findings. Omit any category that has no findings.
5. Write the findings to `.sdlc/features/N-<slug>/review-mockups.md` with frontmatter `artifact: mockups`, `verdict` (`approved` if there are no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, and the findings as the body, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body. For any question that carries meaningful risk to the implementation, also invoke `/create-assumption` to record it formally.

## Review Checklist

### Coverage
- Does every screen, view, or dialog implied by the requirements and spec flows have a wireframe?
- Are entry points, exits, and the back path shown for each screen?
- Are onboarding or first-run surfaces covered where they apply?

### Usability
- Is the primary action on each screen prominent and unambiguous?
- Are flows short, with the main task reachable in as few steps as practical?
- Is cognitive load reasonable, with no screen overloaded with unrelated actions?
- Are destructive or irreversible actions guarded with confirmation?

### Accessibility
- Can every action be reached and operated by keyboard alone?
- Is the focus order logical, and is visible focus preserved?
- Are interactive elements labelled for screen readers, with landmarks and live regions where dynamic updates occur?
- Do color-contrast targets and minimum touch-target sizes meet the stated standard (e.g. WCAG AA)?

### Consistency
- Do the mockups reuse existing components from the codebase analysis where applicable?
- Are spacing, naming, icon, and pattern usage consistent across screens?
- Does the design match established conventions in `.sdlc/context/conventions.md` where they exist?

### State Coverage
- Are empty, loading, populated, and error states defined for every component that fetches or mutates data?
- Are disabled and read-only states shown where permissions or process state require them?
- Is the error state actionable, telling the user how to recover?

### Responsiveness
- Is behavior defined for each viewport the feature targets (mobile, tablet, desktop)?
- Is it clear what collapses, reorders, or hides at each breakpoint, without hiding primary actions?
- Are there layout assumptions (fixed widths, side-by-side columns) that break on small screens?

### Spec Fidelity
- Do the data fields shown in each wireframe match the data model and API contracts in the specification?
- Are the copy placeholders and labels consistent with domain terms in `.sdlc/context/vocabulary.md` where present?
- Do the navigation flows match the sequences defined in the specification?

### Implementability
- Can each screen be built from existing components, or are the new components clearly specified?
- Are there layout or interaction demands that are impractical with the current stack or needlessly complex?
- Where high-fidelity mockups are flagged as needed, is the gap and its pointer clearly recorded?

## Output Format

```markdown
## Coverage

<Findings or "No issues found.">

## Usability

<Findings or "No issues found.">

## Accessibility

<Findings or "No issues found.">

## Consistency

<Findings or "No issues found.">

## State Coverage

<Findings or "No issues found.">

## Responsiveness

<Findings or "No issues found.">

## Spec Fidelity

<Findings or "No issues found.">

## Implementability

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

**Scenario 1: Missing error state**
A wireframe shows the populated list but never shows what the user sees when the fetch fails.
Report under State Coverage.

**Scenario 2: Unreachable by keyboard**
The primary action is a custom div with no keyboard handling called out.
Report under Accessibility.

**Scenario 3: Data mismatch**
The wireframe shows a `user_name` field, but the specification's API contract returns `display_name`.
Report under Spec Fidelity.

**Scenario 4: Broken on mobile**
A two-column comparison table has no responsive behavior defined and would overflow on a phone.
Report under Responsiveness.

## Next Step

Once the findings verdict is `approved`, continue with `/create-plan`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
