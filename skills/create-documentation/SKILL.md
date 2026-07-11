---
name: create-documentation
description: Create documentation for a feature or component following the Divio documentation framework (tutorials, how-to guides, reference, explanation).
argument-hint: "[feature or component]"
---

# Create Documentation

Produces documentation for a feature or component organized according to the [Divio documentation framework](https://docs.divio.com/documentation-system/): tutorials, how-to guides, reference, and explanations.

**For detailed Divio guidance** (DO/DON'T lists, decision trees, per-type structures), consult the `divio-documentation` skill. This skill focuses on the production workflow: deciding which types to write and producing the output.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- Feature or component description provided in context or as `$1`
- Access to the codebase, specification, or implementation (if available)

## Steps

1. Understand the feature: what it does, who uses it, and common use cases.
2. Identify which documentation types are needed (use the decision tree in `divio-documentation` if unsure).
3. Follow the DO/DON'T rules and structure templates from `divio-documentation` for each type.
4. Write a tutorial if users need onboarding guidance.
5. Write how-to guides for the most common user tasks.
6. Write reference documentation for all public APIs, config options, and interfaces.
7. Write an explanation section if the design or behavior needs conceptual context.
8. Cross-link between types but keep their boundaries clean.
9. Write the documentation to `.sdlc/features/N-<slug>/documentation.md`, creating the directory if it does not exist.

## Output Format

Use the template at `skills/sdlc/templates/features/documentation.md` (copied to `.sdlc/templates/features/documentation.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`, mirroring the `status: draft` written to the artifact. If the artifact could not be produced, omit the file.

## Example Usage

**Scenario 1: New CLI command**
Document `create-requirements`: tutorial (run your first requirements doc), how-to (generate requirements from a GitHub issue), reference (all input formats accepted), explanation (why MoSCoW prioritization is used).

**Scenario 2: Internal library**
Document a cache abstraction: how-to guides for common cache patterns, full reference for every method, explanation of the eviction strategy chosen.

## Useful Commands Reference

No CLI commands required. This skill operates on information provided in context.
