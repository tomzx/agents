---
name: review-readme
description: Review a README for template conformance, accuracy, completeness, clarity, and getting-started usability.
---

# Review README

Audits a `README.md` and reports findings across six categories: template conformance, accuracy, completeness, clarity, usability, and hygiene.
Each finding is prioritized with 🔴 MUST fix, 🟡 SHOULD fix, or 🟢 MAY fix.

`/review-documentation` audits the wider documentation tree.
This skill handles the README specifically: it checks the fixed README template, badge correctness, and the getting-started path, which the general documentation review does not cover in depth.

## Prerequisites

- A `README.md` provided in context or as a file path to read
- The project it describes (source tree, `LICENSE`, package manifest such as `go.mod`, `package.json`, `Cargo.toml`, or `pyproject.toml`) for the accuracy checks
- The README template from [`create-readme`](../create-readme/SKILL.md), for the conformance checks

## Steps

1. Read the README thoroughly.
2. Read the project's `LICENSE`, package manifest, and, when needed, the source tree to verify claimed values.
3. Identify issues in each category below.
4. Prioritize each finding: 🔴 MUST, 🟡 SHOULD, 🟢 MAY.
5. Report findings using the output format. Omit categories with no findings.

## Review Checklist

### Template Conformance
- Are the required sections present and in order (header, What, Why, Included, Roadmap, Out of Scope, Requirements, Install, Getting Started, License)?
- Is the centered header present with the repository name and one-sentence description?
- Do the badges follow the template and derive from actual values (license, language and version, platform), with inapplicable badges removed?
- Are sections the template allows to be omitted (Roadmap, Out of Scope, Values-style optional sections) omitted rather than left empty?

### Accuracy
- Do the license badge and License section match the actual `LICENSE`?
- Do the language and version badges match the package manifest?
- Do platform and storage claims match the build targets and dependencies?
- Are links (badges, license, docs) valid and pointing at actual targets?
- Are install and usage commands runnable as written?

### Completeness
- Does the What section explain what the project is in 2-4 sentences?
- Does the Why section explain the motivation and problem solved, not just restate the What?
- Are features listed as user-facing capabilities rather than internal functions?
- Are Requirements complete (language version, OS, external dependencies)?
- Is the project's purpose or scope change not yet reflected in the README?

### Clarity
- Is the one-sentence description specific and concrete, not generic?
- Are concepts explained before they are used, with jargon defined on first use?
- Are features expressed in terms a new user would recognize?
- Is prose free of vague phrasing ("a tool that helps you manage things")?

### Usability
- Can a new user reach a working result from Getting Started in under 5 minutes?
- Are Install steps copy-pasteable and free of unstated prerequisites?
- Is the README scannable (clear headings, no dense unbroken text)?
- Are screenshots or examples present and relevant where they aid understanding?

### Hygiene
- Is each sentence on its own line in the markdown source?
- Are em-dashes avoided in favor of commas or parentheses?
- If a `session_link` comment is present, does it reference a plausible session id?
- Are there leftover placeholders (`{repository}`, `<slug>`, TODO) that were never filled in?

## Output Format

```markdown
## Summary

🔴 / 🟢 <Overall assessment in one sentence.>

## Template Conformance

<Findings with 🔴/🟡/🟢 priority, or "No issues found.">

## Accuracy

<Findings or "No issues found.">

## Completeness

<Findings or "No issues found.">

## Clarity

<Findings or "No issues found.">

## Usability

<Findings or "No issues found.">

## Hygiene

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

**Scenario 1: Stale version badge**
The badge says Go 1.20 but `go.mod` requires 1.22.
🔴 MUST update the badge to match the manifest.

**Scenario 2: Internal functions listed as features**
The Included section lists every exported function.
🟡 SHOULD rewrite the list as user-facing capabilities.

**Scenario 3: Getting Started assumes prior setup**
The first step runs `make build` but Requirements never mentions that a compiler is needed.
🔴 MUST add the compiler to Requirements or the install steps.

**Scenario 4: Empty placeholder section**
The Roadmap heading is present but contains no items.
🟢 MAY remove the empty Roadmap section.

## Next Step

Once all 🔴 MUST findings are resolved, the README is ready to publish.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh repo view --json name,description` | Cross-check the repository name and description used in the header |
| `rg -n "\{[a-zA-Z_]+\}" README.md` | Find unfilled template placeholders |
