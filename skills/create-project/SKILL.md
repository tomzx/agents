---
name: create-project
description: Interview the user to populate the project context files (.sdlc/context/) for a new or empty project. Use when the user says /create-project, "start a new project", "set up project context", "bootstrap an empty project", or wants to fill .sdlc/context/ by answering questions instead of editing stubs by hand.
argument-hint: "[project-root]"
---

# Create Project

Populates the project context files under `.sdlc/context/` by interviewing the user, so a new or empty project has full context before any feature work starts.

`initialize-sdlc-directory` creates the context files as stubs, and `sync-sdlc` fills them by analyzing existing code.
An empty project has no code to analyze, which leaves stubs.
This skill closes that gap: it asks, one topic per round, the questions the stubs need answered, and writes each file as its round completes.

`goals.md` is deliberately out of scope: `/create-goals` owns it (see Next Step).

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- Optional project root (`$1`); defaults to the current working directory.
- The user is available to answer questions (this skill is interactive; never invent answers).

## Steps

1. If the project root already contains source code (not just scaffolding like `.git/` or a README), ask the user whether `/sync-sdlc` is the better tool, since code analysis produces more accurate context than an interview. Proceed only if the user confirms.

2. If `.sdlc/` does not exist at the project root, load and run `initialize-sdlc-directory` with `$1` first, per the Skill Handoff rule in shared.md, then continue here.

3. Read every existing file under `.sdlc/context/`. Sections that are already filled in count as answered; only ask about what is missing or still a placeholder.

4. If `.sdlc/context/review-project.md` exists with `verdict: changes-requested`, operate in Revision Mode (below) instead of running the full interview.

5. Run one interview round per topic, in this order. Each round presents four to six numbered questions about that topic only, then waits for the answers. The user may skip any question.

   | Round | File | Ask about |
   |---|---|---|
   | 1 | `project-overview.md` | What the project does and the problem it solves, key stakeholders, in-scope and out-of-scope capabilities, hard constraints (technical, business, regulatory) |
   | 2 | `architecture.md` | Major components and their responsibilities, how data flows between them, core domain entities and their relationships, intended topology. For an empty project, capture the intended architecture and mark it as planned |
   | 3 | `infrastructure.md` | Language, runtime, framework, and database choices, development tooling and its exact commands, environments, CI/CD pipelines, deployment and rollback |
   | 4 | `conventions.md` | Naming (files, functions, classes), directory structure, coding standards, commit message format, branching strategy, how SDLC artifacts should be written |
   | 5 | `vocabulary.md` | Domain terms the project will use, technical terms, acronyms and abbreviations |

6. After each round, write the answers into the corresponding file using its template at `skills/sdlc/templates/context/`. Keep the template's section order and structure.

7. Unanswered questions are not a failure: leave the template placeholder in place and record the item as an open question in the final report.

## Interview Guidance

- **One topic per round.** Never mix overview questions with infrastructure questions; the round ends only when its file is written.
- **Ask, do not infer.** If the user is unsure, that section stays a placeholder. Fabricated context is worse than missing context because downstream skills trust these files.
- **Prefer concrete over generic.** For conventions, push for enforceable rules ("kebab-case file names", "Conventional Commits") over aspirations ("clean code").
- **Seed vocabulary from earlier rounds.** When rounds 1 to 3 introduce domain terms, propose them for round 5 instead of asking the user to recall them.

## Revision Mode

If `.sdlc/context/review-project.md` exists with `verdict: changes-requested`, revise the existing context files to address each finding rather than re-interviewing from scratch.
Ask only about the findings; everything the review did not challenge stays as-is.
Make the minimum changes that resolve every finding.

## Output Format

Report what was written and what remains open:

```
## Project context created

| File | Status |
|---|---|
| .sdlc/context/project-overview.md | written / unchanged / revised |
| .sdlc/context/architecture.md | written / unchanged / revised |
| .sdlc/context/infrastructure.md | written / unchanged / revised |
| .sdlc/context/conventions.md | written / unchanged / revised |
| .sdlc/context/vocabulary.md | written / unchanged / revised |

### Open questions
- <unanswered item and the file it blocks>
```

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`.
If the interview could not be completed (for example the user abandoned it), omit the file.

## Example Usage

**Scenario 1: Brand-new empty repository**
```
/create-project
```
No `.sdlc/` exists yet; `initialize-sdlc-directory` runs first, then five interview rounds fill the five context files.
Deployment is undecided, so the deployment section stays a placeholder and is listed as an open question.

**Scenario 2: Partially filled context**
```
/create-project
```
`project-overview.md` was filled in by hand earlier.
Round 1 reads it, confirms it is complete, and moves straight to round 2; only the missing files get a full round.

**Scenario 3: Revision after review**
```
/create-project
```
`review-project.md` has `verdict: changes-requested` with two findings: architecture names components absent from `infrastructure.md`, and one convention is unenforceable.
The skill asks only about those two points and amends the files, leaving everything else untouched.

## Failure Modes

| Mode | Response |
|---|---|
| **User abandons mid-interview** | Write the files for completed rounds only; list the remaining topics as open questions in the report |
| **User declines to answer a round entirely** | Leave that file as the stub; note it in the report and suggest re-running `/create-project` later |
| **Existing context conflicts with new answers** | Surface the conflict to the user before overwriting; never silently replace content |

## Completion Checklist

Before handing off to review, confirm:

- [ ] All five context files written, with placeholders only for explicitly skipped questions
- [ ] Every domain term used across the files appears in `vocabulary.md`
- [ ] Components named in `architecture.md` all appear in `infrastructure.md`

Self-check the drafts against the [`review-project` checklist](../review-project/SKILL.md) and fix what you can, so review finds less to flag.

## Next Step

Run `/review-project` to audit the context files for completeness, consistency, clarity, and actionability.
Then run `/create-goals` (which reads the now-complete `project-overview.md`) to add `goals.md`; this skill intentionally does not author it.
Once the project has code, `/sync-sdlc` keeps the context reconciled with reality.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
