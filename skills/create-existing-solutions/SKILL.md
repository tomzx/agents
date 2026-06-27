---
name: create-existing-solutions
description: Survey existing solutions (libraries, products, internal code, standards, prior art) that address the requirements, evaluate their fit, and recommend whether to adopt, extend, or build.
argument-hint: "[requirements-doc]"
---

# Create Existing Solutions Survey

Surveys existing solutions that already solve part or all of what the feature needs, before committing to a design.
The goal is twofold: avoid reinventing what already exists, and harvest proven approaches as a source of information even when we end up building our own.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/features/FEAT-NNNN-<slug>/requirements.md` (must have `status: approved`), or a requirements document provided in context or as a file path (`$1`)

## Steps

1. Read the requirements document and extract what the feature must do (functional requirements) and the quality attributes it must satisfy (non-functional requirements).
2. Define the search scope: the categories below, plus any project-specific sources noted in `.sdlc/context/`.
3. Search each category for candidates:
   - Existing code in this repository or organization that already does something similar (search the codebase first, it is the cheapest to adopt).
   - Open-source libraries, frameworks, and tools.
   - Commercial or SaaS products.
   - Standards, protocols, and specifications.
   - Reference material: articles, papers, and write-ups describing how others solved this problem.
4. For each candidate, capture what it is, its license, its maturity, and how it maps to the requirements (which FR/NFR it covers and which it leaves as gaps).
5. Evaluate the strongest candidates: strengths, weaknesses, integration effort, cost, and risks (license, maintenance, security, lock-in).
6. Recommend a direction (adopt, adopt and extend, build, or hybrid) with a rationale tied to the requirements.
7. Record the sources of information worth borrowing from even if we do not adopt the solution (patterns, data models, edge cases they handle, pitfalls they document).
8. Flag open questions where the evaluation is uncertain or needs validation.
9. Write the output to `.sdlc/features/FEAT-NNNN-<slug>/existing-solutions.md`.

## Output Format

```markdown
---
issue: "#<N>"
title: "<Feature Name>"
status: draft
---

# Existing Solutions: <Feature Name>

## Overview

<One paragraph summarizing what was searched for and the recommended direction.>

## Search Scope

| Source | Searched | Notes |
|---|---|---|
| Internal codebase | Yes / No | <queries or paths checked> |
| Open-source | Yes / No | <queries used> |
| Commercial / SaaS | Yes / No | ... |
| Standards / protocols | Yes / No | ... |
| Reference material | Yes / No | ... |

## Candidate Solutions

| Solution | Type | License | Maturity | Covers | Gaps |
|---|---|---|---|---|---|
| <name + link> | Library / Product / Internal / Standard | MIT / proprietary / ... | Mature / Active / Stale | FR-01, FR-03 | FR-02, NFR-01 |

## Evaluation

### <Solution Name>

- **Strengths:** <what it does well>
- **Weaknesses:** <where it falls short>
- **Integration effort:** <low / medium / high, with reasoning>
- **Cost:** <licensing, hosting, or maintenance cost>
- **Risks:** <license, maintenance health, security, lock-in>
- **Forward compatibility:** <upgrade stability, semver discipline, version range safety, how future dependency upgrades or additive contract changes would affect us>

## Recommendation

**Direction:** Adopt / Adopt and extend / Build / Hybrid

<Rationale tied to the requirements and the evaluation above.>

## Sources of Information

- <Solution or write-up>: <pattern, edge case, or pitfall worth borrowing even if not adopted>

## Open Questions

1. <Question that needs an answer before the design can rely on this survey.>
```

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`, mirroring the `status: approved` written to the artifact. If the artifact could not be produced, omit the file.

## Example Usage

**Scenario 1: A well-served problem**
Requirements describe rate limiting on an API.
The survey finds mature libraries (token-bucket implementations), recommends adopting one, and notes the FR it does not cover (per-tenant quotas) as a gap to build.

**Scenario 2: Reinvention avoided by internal code**
Requirements ask for CSV export.
A codebase search finds an existing export helper used elsewhere.
The recommendation is to reuse and extend it rather than write a new exporter.

**Scenario 3: Build, but learn from prior art**
Requirements describe a domain-specific scheduler with no off-the-shelf fit.
The survey recommends building, and records the data model and failure modes documented by two open-source schedulers as sources of information for the specification.

## Next Step

Run `/review-existing-solutions` to audit the survey for coverage, evaluation rigor, and a sound recommendation before moving on.
Once approved, continue with `/create-codebase-analysis`, which analyzes the internal code and architecture the feature will touch.

## Useful Commands Reference

| Command | Description |
|---|---|
| `WebSearch` | Find open-source projects, products, standards, and write-ups |
| `WebFetch` | Read a candidate's docs, README, license, or release history |
| `grep` / codebase search | Find existing internal code that already solves part of the problem |
| `gh-cached search ...` | Search the organization's repositories for prior art (cached) |
