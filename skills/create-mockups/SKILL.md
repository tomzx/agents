---
name: create-mockups
description: Create UI mockups, wireframes, and screen designs for a feature from its specification, so the visual and interaction design is settled before implementation.
argument-hint: "[specification-doc]"
---

# Create Mockups

Produces UI mockups and wireframes for a feature from its requirements and specification, settling the visual layout, component breakdown, interaction states, and flows before a line of UI code is written.

Without this step, UI work starts with no shared picture of what to build, so layout, states, and accessibility are improvised during implementation and reworked in review.

For features with no user interface (a pure API, a background job, a CLI), skip this phase and state the skip explicitly.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/requirements.md` (must have passed review with findings verdict `approved`), or a requirements document provided in context or as a file path (`$1`)
- `.sdlc/features/N-<slug>/specification.md` (must have passed review with findings verdict `approved`, if produced): reuse the data models, API contracts, and flows it defines so the mockups stay faithful to what the system can actually deliver
- `.sdlc/features/N-<slug>/codebase-analysis.md` (optional, if existing code was analyzed): reuse existing UI components and patterns it inventoried, and honor any "must not change" constraints on shared components

## Steps

1. Read the requirements, the specification if present, and the codebase analysis if present.
2. Decide whether the feature has a UI surface. If it does not, emit `verdict: skipped` (do not write `mockups.md`). The `skipped` verdict routes the pipeline straight to the next phase, bypassing `/review-mockups`.
3. Inventory every screen, view, or dialog the feature needs, cross-referenced against the requirements and the spec's flows.
4. For each screen, draw an ASCII wireframe inside a fenced block, annotated with the regions, primary action, and data shown.
5. Break the UI down into components, marking which already exist in the codebase (reuse), which must be extended, and which are new.
6. For each key component and screen, enumerate its interaction states: empty, loading, populated, error, and disabled or read-only where relevant.
7. Map the navigation between screens as a flow, including entry points, exits, and the back path.
8. Specify responsive behavior across the viewports the feature targets (mobile, tablet, desktop), noting what collapses, reorders, or hides.
9. Call out accessibility requirements: keyboard reachability, focus order and visible focus, screen-reader labels, color-contrast targets, and minimum touch-target sizes.
10. Note copy and content as placeholders so writers can fill them without changing layout.
11. Flag where high-fidelity mockups (Figma, HTML/CSS, a prototype) are warranted and cannot be conveyed by ASCII, and record a pointer or a request for them.
12. Write the output to `.sdlc/features/N-<slug>/mockups.md`.

## Output Format

Use the template at `skills/sdlc/templates/features/mockups.md` (copied to `.sdlc/templates/features/mockups.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.
+-----------------------------------------------+
|  <logo>              <nav>            <avatar> |
+-----------------------------------------------+
|                                               |
|  <primary content region>                     |
|                                               |
|  [ primary action ]                           |
|                                               |
+-----------------------------------------------+
```

**Regions**

| Region | Content | Data source (spec ref) |
|---|---|---|
| <region name> | <what it shows> | <specification.md section or API endpoint> |

**Primary action:** <the single most important action on this screen>

### <Screen 2>

...

## Component Breakdown

| Component | Status | Notes |
|---|---|---|
| <name> | Reuse / Extend / New | <where it lives or what it needs> |

## Interaction States

### <Component or Screen>

| State | What the user sees |
|---|---|
| Empty | <placeholder, zero-data state> |
| Loading | <skeleton or spinner> |
| Populated | <happy path> |
| Error | <failure messaging and recovery> |

## Navigation Flow

```
<List view> --select--> <Detail view> --save--> <Confirmation>
    ^                                          |
    |_________________back_____________________|
```

## Responsive Behavior

| Viewport | Layout changes |
|---|---|
| Mobile (<640px) | <what collapses, reorders, or hides> |
| Tablet (640-1024px) | <changes> |
| Desktop (>1024px) | <changes> |

## Accessibility

- **Keyboard:** <focus order, shortcuts, traps to avoid>
- **Screen reader:** <labels, landmarks, live regions>
- **Contrast:** <target ratio, e.g. WCAG AA 4.5:1>
- **Touch targets:** <minimum size, spacing>

## Copy Notes

- <placeholder text the writer must fill, marked so layout is not disturbed>

## High-Fidelity Needs

- <Where ASCII is insufficient and a Figma/HTML/prototype is warranted, with a pointer or request>

## Out of Scope

- <What is explicitly not designed here and why>
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | The mockups artifact was produced (or revised) with `status: draft`, ready for `/review-mockups` |
| `skipped` | The feature has no UI surface; no artifact is written and the pipeline proceeds past review to the next phase |

If the artifact could not be produced for any other reason, omit the file.

## Example Usage

**Scenario 1: Notification center**
Requirements describe a notification list with read/unread state and an empty state for new users.
Wireframes cover the list screen, the empty state, and the per-notification detail, with states for loading, populated, and error, plus the navigation flow from the app shell.

**Scenario 2: Bulk file upload**
Requirements describe a multi-file upload with progress and failure retry.
Wireframes cover the drop zone, the in-progress list with per-file progress, and the failure state with retry, plus a responsive note that the list collapses to one column on mobile.

**Scenario 3: Pure API feature, no UI**
The specification defines a webhook receiver with no user interface.
The skill leaves the artifact unwritten and emits `verdict: skipped` so the pipeline continues to the next phase without a review.

## Next Step

Run `/review-mockups` to audit the mockups for coverage, usability, accessibility, consistency, and spec fidelity before moving on.
Once approved, continue with `/create-plan`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
