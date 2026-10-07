---
name: refactor-implementation
description: Refactor the code just produced by create-implementation, introducing only the abstractions and seams it needs to stay small, cohesive, and testable, using the dependency-breaking and behavior-preservation techniques from Michael Feathers' Working Effectively with Legacy Code. Use after implementation and before review, when a change has grown bloated, duplicated, or hard to test. Triggers on /refactor-implementation, "refactor this implementation", "this code is bloated", "introduce a seam", "break this dependency so I can test it", "extract the duplication".
argument-hint: "[task, diff, or feature directory]"
---

TODAY=!`date +%Y-%m-%d`

# Refactor Implementation

Refactors the change just produced by `create-implementation`, adding only the abstractions and seams it needs to stay small, cohesive, and testable, and deliberately leaving everything else alone.

It applies the behavior-preservation and dependency-breaking techniques from Michael Feathers' *Working Effectively with Legacy Code* to new code.
The goal is not to fix untested legacy code, but to stop fresh code from turning into it.
The guiding constraint is minimum abstraction: every seam and every extracted type must justify its place, or it is bloat.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- Implementation is complete on the current branch and its tests currently pass (`/create-implementation` ran first).
- The implementation diff is available (`git diff <base>...HEAD`, or the files and lines named in context or `$1`).
- Tests exist for the behavior being restructured; if the touched code is under-tested, characterization tests are written as part of this skill.
- Optional: `.sdlc/features/N-<slug>/specification.md`, `tests.md`, and any `review-implementation.md` findings, for context on what the change must preserve.

## How This Relates to Others

| Skill | Relationship |
|-------|--------------|
| `create-implementation` | Produces the change this skill refactors. It must have run first and left the tests green. |
| `review-implementation` | Reviews the refactored result. This skill runs before it and hands off to it. |
| `analyze-test-coverage` | Its uncovered-code table often shows exactly where a seam is missing or a characterization test belongs. |
| `propagate-changes` | Run after refactoring if the structure change makes a specification, plan, or documentation stale. |

## The Minimum Abstraction Rule

Introduce an abstraction or a seam only when at least one justification holds.
If none holds, leave the code alone.

| Justification | Signal | Smallest response |
|---------------|--------|-------------------|
| Duplication with one reason to change | The same logic appears three or more times | Extract method or function; extract a class only when it carries state |
| Untestable boundary | A clock, network, filesystem, randomness, or third party blocks a test | Inject the dependency as a parameter or constructor argument (object seam) |
| Divergent change | One unit changes for two unrelated reasons | Split it along the change axis |
| Blocked dependency | The code under test cannot be constructed or reached | Break the dependency with the smallest technique below |

Prefer the cheapest move that satisfies the justification, in this order:

1. Rename, introduce a variable, or inline a needless indirection.
2. Extract method or function.
3. Parameterize the method or constructor.
4. Extract class, only when a cohesive cluster of state and behavior has emerged.
5. Extract an interface or protocol, only at a genuine volatility boundary with a second implementation or a test double that must substitute for the production one.
6. Dependency injection, a factory, or a container, only when the object graph itself demands it.

An abstraction with one implementation, one caller, and no test or variation pressure is speculative structure.
Delete it rather than polish it.

## What Bloat Looks Like

Scan the implementation diff for these signals before touching anything.

| Signal | Likely minimal response |
|--------|-------------------------|
| Long method with distinct phases | Extract method per phase |
| Same block in three or more places | Extract method or function; extract class if it carries state |
| Boolean or mode parameter that switches whole behavior | Split into two methods; introduce polymorphism only if variants will genuinely multiply |
| Constructor builds its own collaborators | Parameterize the constructor |
| A test needs an actual clock, network, or random source | Introduce an object seam for that boundary |
| One class changes for several unrelated reasons | Extract class along the change axis |
| Interface, factory, or config layer with a single implementation | Inline it until a second implementation exists |
| Parameter, field, or import never read | Remove it |
| Layer that only forwards calls | Inline the forwarding method |
| Comment explaining what a block does | Extract the block and name it after the comment |

Scope the pass to the change under review.
Do not refactor the surrounding codebase, and do not add features: behavior must be identical before and after.

## Feathers Techniques, Scaled to New Code

### Pin behavior before restructuring

Characterization tests assert what the code currently does, not what it should do.
Write them before touching structure whenever the behavior you are about to rearrange is not already covered.
They are the safety net that proves the refactoring preserved behavior.
Commit them separately, as `create-implementation` does, so the before/after test trail stays easy to read.

### Seams

A seam is a place where behavior can be substituted without editing the code at that place.
New code almost always uses the object seam; use the others only when the language or dependency forces it.

| Seam | Use in new code |
|------|-----------------|
| Object seam | Inject a collaborator through a constructor or parameter, or subclass and override the method that creates it. The default. |
| Link seam | Substitute an imported module, library, or function at test or build time (module mocking, monkeypatching). Use when the dependency is imported rather than injected. |
| Preprocessor seam | Macro or conditional compilation. Applicable only in C and C++. |

### Dependency-breaking techniques

Apply the smallest technique that unblocks the test or isolates the variation.

| Situation | Technique |
|-----------|-----------|
| A collaborator is hard-coded with `new` or a direct construction | Parameterize Constructor, then Extract Interface only if variation is genuinely needed |
| A static or global access (clock, config, singleton) is called inline | Parameterize Method, Replace Global Reference with Getter, or Introduce Instance Delegator |
| A call to a function you do not control | Extract and Override Call, Replace Function with Function Pointer, or Adapt Parameter |
| A method is too tangled with its dependencies to test in place | Break Out Method Object, or Expose Static Method when no state is needed |
| Behavior varies by subclass | Subclass and Override Method, Extract and Override Factory Method, or Supersede Instance Variable |
| Behavior branches on a global flag or environment | Pull Up Feature or Push Down Dependency, so the branch becomes a composition choice |

### Add behavior without disturbing the old path

| Technique | When |
|-----------|------|
| Sprout Method | New behavior goes in a new method called from the existing code, leaving the old body untouched |
| Sprout Class | New behavior needs its own state, so it becomes a new class the old code delegates to |
| Wrap Method | New behavior runs before or after an existing method, which keeps its original body |
| Wrap Class | New behavior surrounds an existing class without modifying it |

### Structural cleanup

Once behavior is pinned by tests, the ordinary safe refactorings apply: extract method or function, extract variable, rename, move, inline, extract class, and remove dead code.
Replace a conditional with polymorphism only when the branches are a true variant axis with more than two actual implementations, not when they are two fixed cases.

## Steps

1. Read the implementation diff, the specification, the tests, and the codebase conventions.
2. Confirm the passing baseline: run the focused test suite for the changed code.
3. Scan the diff for bloat and missing seams using the signals above.
4. For each candidate, apply the Minimum Abstraction Rule and drop anything unjustified.
5. For every behavior you will rearrange, if it is not pinned by tests, write characterization tests first and commit them separately.
6. If the change touches a boundary that blocks testing (clock, network, filesystem, randomness, third party), introduce the smallest seam that removes the block.
7. Apply one refactoring at a time, running the focused tests after each, keeping behavior identical.
8. Remove what the change left behind: dead code, unused parameters and imports, single-use indirection, commented-out code.
9. Run the full test suite and confirm it passes.
10. Write `.sdlc/features/N-<slug>/refactorings.md` recording each applied technique, its minimality justification, and what was deliberately left alone.
11. Self-check the result against the [`review-implementation` checklist](../review-implementation/SKILL.md) and fix what you can.
12. Commit the refactoring and the `refactorings.md` artifact together, separately from the implementation commit, so the structural change has its own reviewable history.

## Output Format

Use the template at `skills/sdlc/templates/features/refactorings.md` (copied to `.sdlc/templates/features/refactorings.md` by `/initialize-sdlc-directory`; use the project's customized copy if present).
Write the result to `.sdlc/features/N-<slug>/refactorings.md`.
Record each applied refactoring with its location, technique, the seam or abstraction it introduced, its justification, and the tests that pin the behavior, then list what was deliberately left alone and the before/after verification.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md` when the implementation was refactored or no refactoring was justified.
Emit `verdict: changes-requested` when a needed refactoring could not be completed safely, so the pipeline routes it for human attention.
Emit nothing (leave the file as the previous step wrote it) when there is no implementation diff to work on, so this refinement step cannot overwrite the implementation phase's routing verdict.
In the same emission, list the artifact under `artifacts:` (`.sdlc/features/N-<slug>/refactorings.md`) when it was written.

## Example Usage

**Scenario 1: Duplication and an untestable clock** `create-implementation` added three report methods that each repeat the same period-validation block and each call `datetime.now()` directly.
The skill extracts the validation into one private method (duplication with one reason to change) and adds a clock parameter to the constructor (untestable boundary).
It does not extract an interface for the database client: the tests reach it through the existing test database, so there is no justification.
It records the database decision under "Deliberately Not Refactored".

**Scenario 2: Speculative indirection in fresh code** The implementation introduced a `Notifier` interface, a `NotifierFactory`, and a `NotifierConfig` for a single email path called from one place.
The skill inlines the factory and config back into the one call site, keeps the interface only if a test double genuinely replaces the email client, and records the removal.

**Scenario 3: Nothing to do** The diff is a small, cohesive change already covered by tests, with no duplication and no blocked boundary.
The skill applies the Minimum Abstraction Rule, finds no justification, writes a `refactorings.md` whose "Refactorings Applied" table is empty, and leaves the code untouched.

## Completion Checklist

- [ ] Tests passed before the refactoring and still pass after
- [ ] Every abstraction and seam introduced maps to a stated justification
- [ ] No speculative extension points, single-implementation interfaces, or forward-looking parameters were added
- [ ] Behavior is unchanged; no features were added or removed
- [ ] Dead code, unused parameters, and commented-out code were not introduced (and existing ones were removed)
- [ ] The refactoring is committed separately from the implementation
- [ ] `.sdlc/features/N-<slug>/refactorings.md` written, including the "Deliberately Not Refactored" section

## Next Step

A review subagent is dispatched automatically to run `/review-implementation` to audit the refactored code for correctness, quality, security, and spec alignment.
Once findings are resolved, continue with `/create-documentation`, then `/validate-implementation` to capture visual proof and get user sign-off before opening a PR, then `/create-pr`.

## Useful Commands Reference

| Action | Common commands |
|--------|-----------------|
| Diff the change | `git diff main...HEAD`, `git diff HEAD~1` |
| Run tests | `pytest`, `npm test`, `go test ./...` |
| Lint | `ruff check`, `eslint` |
| Type check | `mypy`, `tsc`, `pyright` |
