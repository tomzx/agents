---
name: review-project
description: Review the project context files (.sdlc/context/) for completeness, consistency, clarity, and actionability. Use when the user says /review-project, after /create-project, or before relying on project context to drive feature work.
---

# Review Project

Audits the project context files as a set, so downstream skills (`create-goals`, `create-needs-assessment`, `create-feasibility`, the audit family) can rely on them.

The review answers one question: could an agent that has never seen this project orient itself from `.sdlc/context/` alone?

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- The context files under `.sdlc/context/` (`project-overview.md`, `architecture.md`, `infrastructure.md`, `conventions.md`, `vocabulary.md`), or the equivalent documents provided in context or as file paths.
- Source code in the project root (optional, for the currency spot-check).

## Steps

1. Read the context files from `.sdlc/context/` if present, otherwise from context or as file paths.
2. Cross-reference the files against each other, and, where code exists, against the repository.
3. Identify issues in each category below.
4. Report findings. Omit any category that has no findings.
5. Write the findings to `.sdlc/context/review-project.md` with frontmatter `artifact: project`, `verdict` (`approved` if no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body.

## Review Checklist

### Completeness

- Does every section of every context file contain substantive content, with no template placeholders (`<...>`, "TBD") left?
- For an empty project, are not-yet-built parts (architecture, infrastructure) explicitly marked as planned rather than presented as existing?
- Is `goals.md` absent? Note it as informational with a pointer to `/create-goals`; it is not a blocker for this review.

### Consistency

- Do terms used in `project-overview.md` and `architecture.md` match the definitions in `vocabulary.md` (no synonym drift, no redefinitions)?
- Does every component named in `architecture.md` appear in the `infrastructure.md` technology stack, or is the gap explained?
- Does the scope in `project-overview.md` (in and out) agree with what `architecture.md` describes, with no out-of-scope components documented as core?

### Clarity

- Does the purpose state the problem being solved, not just the mechanism being built?
- After reading the five files alone, could a new contributor describe the project's boundaries, parts, and rules without asking anyone?
- Are stakeholder interests concrete enough to resolve a prioritization disagreement?

### Actionability

- Are the conventions enforceable rules ("kebab-case file names", "Conventional Commits") rather than aspirations ("clean code")?
- Are the infrastructure tooling commands runnable as written (test, lint, build commands exist and match the project)?
- Do environments and deployment name concrete workflows, branches, or commands rather than vague procedures?

### Currency

- Where code exists, do the recorded stack and conventions match the repository (dependency manifests, config files, actual file naming)? Drift is a finding.
- Are planned sections dated or anchored so staleness is detectable later?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Consistency

<Findings or "No issues found.">

## Clarity

<Findings or "No issues found.">

## Actionability

<Findings or "No issues found.">

## Currency

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the context passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework (for example, the context describes a different project than the one in the repo) |

## Example Usage

**Scenario 1: Placeholder left behind**
`architecture.md` still contains the template's `<name>` component row.
Report under Completeness: the section is a stub; identify which questions were skipped and point back to `/create-project` revision mode.

**Scenario 2: Vocabulary drift**
`project-overview.md` says "workspace", `architecture.md` says "tenant", and `vocabulary.md` defines neither.
Report under Consistency: pick one term, define it in `vocabulary.md`, and use it everywhere.

**Scenario 3: Unenforceable convention**
`conventions.md` lists "keep the code simple" as a coding standard.
Report under Actionability: replace with a checkable rule, or drop it.

**Scenario 4: Empty project, aspirational architecture**
`architecture.md` describes components that do not exist yet and are explicitly marked "planned".
No finding under Currency: the plan marker is correct. Only unmarked descriptions of unbuilt parts are findings.

## Next Step

On `changes-requested`, re-run `/create-project`, which detects the findings file and enters revision mode.
On `approved`, run `/create-goals` to add `goals.md` (if absent), then `/create-roadmap` once goals exist.
Once the project has code, `/sync-sdlc` keeps the context reconciled with reality.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
