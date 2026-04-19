---
name: session-review
description: End-of-session checklist covering code quality (tests, docs, specs, simplicity, observability) and higher-level concerns (architectural fit, breaking changes, rollback, technical debt, communication).
---

# Session Review

Runs a structured end-of-session review to ensure every change made during the session is properly covered by tests, documented, specified, intentional, and as clean as possible. Also extracts and persists any newly identified practices.

## Prerequisites

- A git repository with changes from the current session
- AGENTS.md present in the repository root (or a known location)
- Spec files accessible (if the project uses specifications)

## Steps

### 1. Collect the Intent Behind the Change

Review `git diff HEAD~..HEAD` (or all commits since the session started) and ask the user:

> "What was the goal of this session? What problem were you solving, and what approach did you take?"

Record the stated intent. If the user does not respond, infer the intent from commit messages and changed code.

### 2. Simplicity Review

Before writing any tests or docs, review the changed code and ask:

> "Could this be implemented more simply, cleanly, succinctly, or elegantly? Are there any abstractions that can be removed, renamed, or consolidated? Is there anything here that is over-engineered for what is actually needed?"

Apply any improvements the review surfaces. Tests, docs, and specs are written against this final, clean implementation.

### 3. Add Tests to Cover the Change

Identify all changed or added functions, classes, and modules. For each:

- Check whether a test already exists that exercises the new or modified behavior.
- If no test covers it, write one (or ask the user to confirm before writing).
- Focus on "green path" tests that cover the main functionality.
- Run the test suite to confirm all tests pass:
  ```
  # Python
  uv run pytest

  # JavaScript / TypeScript
  npm test

  # Go
  go test ./...
  ```
- Report any failing tests and fix them before proceeding.

### 4. Update Documentation

For each changed public interface, module, or behavior:

- Update inline docstrings or comments if the behavior changed.
- Update any relevant `README.md`, `docs/`, or wiki pages.
- If the project uses a changelog (`CHANGELOG.md`), add an entry under `## Unreleased`.
- If the project uses the Divio documentation system (tutorials, how-tos, reference, explanation), identify which document type needs updating and make the edit.

### 5. Update Specifications

Locate spec files related to the changed code (e.g., `specs/`, `*.spec.md`, `docs/specs/`).

For each relevant spec:

- Confirm the spec reflects the current behavior after the change.
- Add new requirements or constraints introduced by this session.
- Remove or update any requirements that the change made obsolete.
- Run `/spec-review` on updated specs to check for ambiguities, inconsistencies, or missing information.

### 6. Observability Review

Check that the change has appropriate logging, metrics, and tracing at key decision points:

- Are significant events (errors, state transitions, external calls) logged with enough context to diagnose issues in production?
- If the project uses structured logging, are new log statements consistent with the existing format and fields?
- If the change adds a new code path that could be slow or fail, is there a metric or trace span covering it?
- Remove any debug logging that was added temporarily during development.

### 7. Architectural Fit

Step back from the implementation and ask whether the change sits cleanly within the existing design:

- Does any module now do too much, or has a new responsibility been added without a clear home?
- Are dependencies pointing in the right direction (e.g., no lower-level modules depending on higher-level ones)?
- Does the abstraction feel right at this level, or is it either too leaky or too opaque?
- Would a future developer reading this code find it obvious where the logic lives and why?

If the design feels awkward, note it. Either fix it now or record it explicitly as debt in step 9.

### 8. Architecture Decision Records

Review the decisions made during this session and determine whether any warrant an ADR. A decision warrants an ADR if it:

- Affects the overall structure, technology choices, or design patterns of the system
- Has meaningful trade-offs that future developers should understand
- Is not obvious from the code alone (i.e., the "why" is non-trivial)
- Could be revisited or questioned in the future without this record

Ask the user:

> "Did this session involve any significant architectural or technical decisions that should be recorded as an ADR? For example: choosing a library, adopting a pattern, deciding on a data model, or making a trade-off between approaches."

For each identified decision, run the `adr` skill to collect details and create the record:

```
/adr <decision title>
```

If no decisions warrant an ADR, note that explicitly in the summary.

### 9. Breaking Changes

Check whether anything in the public surface has changed:

- API contracts (endpoints, request/response shapes, status codes)
- Exported types, function signatures, or module interfaces
- Event or message payloads
- Database schema or file formats
- Configuration keys or environment variables

For each breaking change, identify the consumers and determine whether they need to be updated, notified, or given a migration path before this ships.

### 10. Rollback / Reversibility

Assess how easy it would be to undo this change if it causes problems in production:

- Is the change purely in code and trivially revertable by redeploying the previous version?
- Are there irreversible side effects: data migrations, dropped columns, published events, sent emails, external API calls with lasting state?
- If the change is hard to reverse, document a rollback procedure or mitigation plan (a feature flag, a compensating migration, a manual remediation script).

### 11. Technical Debt Delta

Reflect on whether the session improved or worsened the codebase's long-term health:

- Were any shortcuts taken that should be tracked? Create issues for them rather than leaving silent TODOs.
- Was any existing debt paid down? Note it so the trend is visible over time.
- Did the change make the next related change easier or harder?

### 12. Communication / Coordination

Identify anyone who needs to know about this change:

- Teammates who own code that calls or depends on what changed.
- Consumers of a shared library, API, or event schema.
- Stakeholders who need to know a behavior changed or a feature shipped.
- On-call engineers if the change affects production risk.

For each, determine whether to notify now, at deploy time, or after observing production.

### 13. Update AGENTS.md

Reflect on the session and identify any practices, patterns, constraints, or lessons learned that should be encoded for future sessions. For each:

- Write a concise rule in the appropriate section of `AGENTS.md`.
- Prefer concrete, actionable statements over vague guidance.
- Do not duplicate rules that already exist.

Examples of things to encode:
- A linting or formatting rule that was enforced during the session
- A library or tool preference that emerged
- A naming convention that was established
- An architectural constraint that was discovered
- A testing pattern that proved useful

## Output Format

After completing all steps, print a summary:

```markdown
## Session Review Summary

### Intent
<One or two sentences describing the goal of the session.>

### Simplicity Review
<Brief summary of what was found and any improvements made, or "No changes needed.">

### Tests
- [ ] Tests added or confirmed for: <list of changed units>
- [ ] Test suite passes

### Documentation
- [ ] Updated: <list of updated files, or "none needed">

### Specifications
- [ ] Updated: <list of updated spec files, or "none needed">
- [ ] Spec review run: yes / no

### Observability
- [ ] Logging adequate for production diagnosis: yes / no
- [ ] Debug logging removed: yes / n/a
- [ ] Metrics/tracing added for new slow or failure-prone paths: yes / n/a

### Architectural Fit
<One sentence on whether the design feels clean, or what feels awkward and why.>

### Architecture Decision Records
- [ ] ADRs created: <list of ADR files created, or "none needed">

### Breaking Changes
- [ ] Breaking changes identified: <list, or "none">
- [ ] Consumers notified or updated: yes / n/a

### Rollback / Reversibility
- [ ] Reversible by redeploy: yes / no
- [ ] Irreversible side effects documented: yes / n/a

### Technical Debt Delta
- [ ] Shortcuts taken and tracked as issues: <list, or "none">
- [ ] Debt paid down: <list, or "none">

### Communication / Coordination
- [ ] Parties to notify: <list, or "none">

### AGENTS.md Updates
- [ ] Added rules: <list of new rules, or "none">
```

## Example Usage

**Scenario 1: Python feature addition**
New endpoint added to a FastAPI service. Session review adds a pytest test for the happy path, updates the OpenAPI description in the spec file, confirms the README example still works, and encodes a rule in AGENTS.md about always using `structlog` for endpoint logging.

**Scenario 2: Refactor session**
Internal module restructured with no behavior change. Session review confirms all existing tests still pass, updates the architecture spec to reflect the new module boundary, and notes in AGENTS.md that the old module name is deprecated.

**Scenario 3: Bug fix**
Off-by-one error fixed in a date calculation. Session review adds a regression test for the specific input that triggered the bug, updates the relevant spec with a note about boundary conditions, and the simplicity review confirms no further changes are needed.

## Useful Commands Reference

| Command | Description |
|---|---|
| `git diff HEAD~..HEAD` | Show changes from the most recent commit |
| `git log --oneline -20` | Show recent commits for session scope |
| `uv run pytest` | Run Python test suite |
| `uv run ruff check . && uv run ruff format .` | Lint and format Python code |
| `npm test` | Run JavaScript/TypeScript test suite |
| `go test ./...` | Run Go test suite |
