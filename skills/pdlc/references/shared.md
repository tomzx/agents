# Shared PDLC Skill Conventions

This file is the single source of truth for conventions shared across every PDLC skill.
Each skill relies on these conventions instead of restating them.
The instructions below apply automatically whenever a skill reads or writes anything under `.pdlc/` (see `AGENTS.md`).

PDLC is the **Product Development Lifecycle**. It is the loop that surrounds SDLC:
it decides *whether* and *what* to build (discovery, validation, strategy, definition),
hands off the *how* to SDLC, then closes the loop with launch and measurement.
Three properties distinguish PDLC from SDLC, and every skill must respect them:

1. **It is a cycle, not a line.** The Measure phase feeds back into Discover. A pipeline that ends at "shipped" is incomplete.
2. **Every phase has a kill gate.** Each transition runs `make-decision` with verdict `proceed` / `pivot` / `kill`. A PDLC that never kills ideas is broken.
3. **Artifacts are the contract.** Each skill produces one artifact the next skill consumes, so the orchestrator can pause, resume, hand off, and trace end to end.

## Applicability

These conventions apply to every skill that touches `.pdlc/` artifacts:
the orchestrator (`pdlc`), the setup sub-skills (`initialize-pdlc-directory`, `sync-pdlc`, `pdlc-status`, `audit-outcomes`), every phase sub-skill in Discover / Validate / Strategy / Define / Launch / Measure, and any skill that consults `.pdlc/context/` for product context.

All PDLC sub-skills are bundled under the `pdlc` skill at `skills/pdlc/skills/<name>/SKILL.md`. They are **internal**: they are not individually discovered as slash commands, so only `/pdlc` is directly invocable. A bare name like `write-prd` or `make-decision` in these files denotes that internal sub-skill file, not a slash command.

## Sub-Skill Loading

Most PDLC sub-skills end with a `## Next Step` section naming one or more successors.
When a sub-skill completes and points to a successor, read that successor's file at `skills/pdlc/skills/<name>/SKILL.md` (Read tool) before performing any of its work, so its workflow, gates, and commit rules are in context.
Never execute a successor's actions from memory or general knowledge.
This rule applies however the successor was reached:
- via the orchestrator (`/pdlc <phase>`), which reads each phase sub-skill before executing it, or
- via the orchestrator running a cross-cutting sub-skill (`make-decision`, `kill-initiative`, etc.) named by bare name.

## Gates (proceed / pivot / kill)

The gate is the PDLC's defining mechanism. Every phase boundary invokes `make-decision`, which writes a decision record to `.pdlc/decisions/` carrying the gate verdict in its frontmatter:

```yaml
---
initiative: INIT-N
phase: discover            # the phase just completed
gate_verdict: proceed      # proceed | pivot | kill
reviewed_at: <ISO date>
---
```

| Verdict | Meaning | Effect |
|---|---|---|
| `proceed` | The artifact is sound and the opportunity survives | Advance to the next phase |
| `pivot` | The opportunity is real but the framing/scope/solution must change | Return to an earlier phase named in the decision body |
| `kill` | The opportunity is not worth pursuing | Stop the pipeline; run `/kill-initiative` |

Gates are separate from artifact quality: each phase skill self-checks its artifact against a completion checklist before handing off, and `make-decision` judges *the opportunity's continued viability*, not prose quality. `audit-outcomes` is the end-to-end backstop that traces shipped outcomes back to the original problem and metrics.

## Project context files

Before producing a document, read any files present under `.pdlc/context/` and apply the artifact style rules found there to the output.

The context files are:

- `product-overview.md` — product, target customer (ICP), scope, stakeholders
- `vision.md` — product vision and positioning (the anchor `define-vision` writes here)
- `goals.md` — objectives, key results, success metrics, and **guardrail metrics**
- `roadmap.md` — initiatives sequenced across Now/Next/Later horizons
- `pricing.md` (optional) — pricing model and packaging
- `vocabulary.md` — product and domain terms

Style rules found in context (for example, one-sentence-per-line) apply to every document produced during the pipeline.

## AGENTS.md PDLC anchor

So a future agent session knows the project tracks work under `.pdlc/`, every project that has a `.pdlc/` directory carries a short, idempotent **PDLC anchor** block in its primary agent-instruction file.

### Target file

The anchor is written to the repo's primary agent-instruction file, resolved in this order:

1. `AGENTS.md` in the project root, if it exists.
2. Otherwise `CLAUDE.md` in the project root, if it exists.
3. Otherwise, create `AGENTS.md` in the project root.

Only one file ever holds the anchor. It is a repo-level concern: write it to the repository, never to the `PDLC_DIR` mirror. If the target file is read-only or absent and cannot be created, skip the write and note it in the report.

### Content

The block is delimited by HTML comment markers so it can be updated in place without touching the rest of the file:

```
<!-- pdlc-anchor begin -->
## PDLC

This project tracks product initiatives, from discovery through launch and measurement, under [`.pdlc/`](.pdlc/).

Before starting work on an initiative:
- Read `.pdlc/context/` (`product-overview.md`, `vision.md`, `goals.md`) for product context, and apply the style rules found there to anything you write.
- Run `/pdlc status` to see initiative progress, or `/pdlc continue` to resume in-progress work.

Every phase transition runs a proceed/pivot/kill gate via `/make-decision`. Never commit local-only state: `.pdlc/state.yml` and `.pdlc/initiatives/*/progress.md`.
<!-- pdlc-anchor end -->
```

### Idempotency

- If the target file does not exist, create it containing only the block.
- If the file exists but has no `<!-- pdlc-anchor begin -->` ... `<!-- pdlc-anchor end -->` block, append the block at the end of the file, separated from existing content by a blank line.
- If the file exists and the block is already present, replace the delimited content with the canonical text above.
- Never modify content outside the markers.

### When it is written

- `initialize-pdlc-directory` writes the anchor when it creates the `.pdlc/` structure.
- `sync-pdlc` re-ensures the anchor on every run so removing or evolving it self-heals on the next sync.

## Initiative Directory Naming

Initiative directories live under `.pdlc/initiatives/` and are named `N-<slug>`, where `N` is the initiative identifier used verbatim with **no zero-padding** (no `INIT-` prefix on the directory, since the parent `initiatives/` already conveys the kind). The corresponding **initiative ID** used in cross-references is `INIT-N` (e.g., directory `1-onboarding` ↔ initiative ID `INIT-1`; directory `p1-onboarding` ↔ initiative ID `INIT-p1`).

`N` has one of two lexical forms:

- **Issue-driven (default):** when a GitHub issue (or product ticket) is available, `N` is its number used verbatim (e.g., issue `#42` → directory `42-<slug>`, initiative ID `INIT-42`). The artifact frontmatter `issue` field is set (e.g., `issue: "#42"`).
- **Pending (no issue yet):** when there is no issue (a free-text brief, a discovery that has not been ticketed yet), `N` is the letter `p` followed by the next unused sequence among `p`-prefixed directories (e.g., `p1-<slug>`, `p2-<slug>`, initiative ID `INIT-p1`). The frontmatter `issue` field is left unset. A `p`-prefixed initiative is a candidate for promotion once an issue is created.

The `<slug>` is lowercase, with hyphens for spaces and no special characters. A `p` identifier can never collide with an issue number, so issue-driven and pending initiatives coexist unambiguously.

### Handoff to SDLC

One initiative commonly decomposes into one or more SDLC features. The `define-acceptance` skill produces an acceptance contract that is the seam: PDLC owns *what and why* (PRD + acceptance criteria as a testable contract); SDLC owns *how* (specification, plan, code). The acceptance contract is consumed by SDLC's `create-requirements`. Record each spawned feature (`FEAT-N`) reference in the initiative frontmatter `spawns_features` list.

## Artifact Location Resolution (PDLC_DIR)

By default every `.pdlc/` path resolves inside the repository.
When the `PDLC_DIR` environment variable is set, an external mirror keyed by GitHub `{owner}/{repository}` is used as a read fallback (and, when the repo's `.pdlc/` is absent or read-only, as the write target).

```
$PDLC_DIR/
  {owner}/
    {repository}/        # mirrors the repository root
      .pdlc/             # same tree as the repo's .pdlc/
        context/
        initiatives/
        decisions/
        learnings/
        templates/
```

### Deriving `{owner}/{repository}`

Run `git remote get-url origin` in the project root and parse the GitHub URL:

- `git@github.com:owner/repo.git` -> `owner/repo`
- `https://github.com/owner/repo.git` -> `owner/repo`

Strip a trailing `.git`. If there is no remote, the `PDLC_DIR` fallback is unavailable and only the repo's `.pdlc/` is used.

### Read resolution

For any artifact path `<path>` relative to the repo root:

1. Read `<repo>/<path>` if it exists.
2. Otherwise, if `PDLC_DIR` is set and `{owner}/{repository}` was derived, read `$PDLC_DIR/{owner}/{repository}/<path>`.

The repository always wins; `PDLC_DIR` is a fallback only.

### Write resolution

1. The primary write location is `<repo>/<path>`. Try to create `<repo>/.pdlc/` if it does not exist.
2. If writing to `<repo>/<path>` fails and `PDLC_DIR` is set with a derivable `{owner}/{repository}`, write to `$PDLC_DIR/{owner}/{repository}/<path>` instead, creating the directory tree as needed.
3. When a write lands in the repo's `.pdlc/` and `PDLC_DIR` is set, also mirror the same content to `$PDLC_DIR/{owner}/{repository}/<path>`.

### What is never mirrored

- `state.yml` and `initiatives/*/progress.md` are local-only workflow state (regenerated per machine and per run). They are never read from or written to `PDLC_DIR`.
- `sync-meta.yml` and generated reports (`audit-report.md`) stay in the repo's `.pdlc/` only.

## Automation runner environment

When invoked by an automation runner, a PDLC skill resolves its target from environment variables, never from positional arguments or from `.pdlc/state.yml`.

| Variable | Present when | Content |
|---|---|---|
| `REPO` | always | `{owner}/{repository}` of the target repo |
| `ISSUE_NUMBER` | issue events | the issue / initiative number |
| `ISSUE_TITLE` | issue events | issue title |
| `ISSUE_BODY` | issue events | issue body text |
| `PR_NUMBER` | pull request events | the PR number |
| `PR_BRANCH` | pull request events | PR head branch ref |
| `GH_TOKEN` | always | the GitHub auth token, for use with `gh` |
| `OUTCOME_YAML` | when a verdict is wanted | file path to write the verdict |

Exactly one of `ISSUE_NUMBER` or `PR_NUMBER` identifies the subject; the other is empty.

## Outcome Emission ($OUTCOME_YAML)

When `$OUTCOME_YAML` is set to a file path, write a YAML object recording your verdict there as your **final action**:

```yaml
verdict: <value>       # the skill's routing decision (see each skill's Outcome section)
reason: <one sentence>  # optional
```

Rules:

- Emit exactly one `verdict`. Each skill documents its vocabulary in its own `## Outcome` section.
- If `$OUTCOME_YAML` is unset, skip emission entirely.
- This channel only reports the skill's own decision; it does not replace the skill's normal outputs (artifacts, decision records).
- If you cannot reach a verdict, omit the file or write `verdict: unknown`.
- Values must be valid YAML scalars. Quote `reason` whenever it is a free-form sentence.

## Frontmatter conventions

Every initiative artifact carries YAML frontmatter:

```yaml
---
initiative: INIT-N
issue: "#42"            # set when tied to a GitHub issue; omitted for p-prefixed initiatives
title: "Human title"
status: draft           # draft on creation; gate outcome lives in the decision record
phase: discover         # the PDLC phase that owns this artifact
---
```

`create`/phase skills write artifacts with `status: draft`. Gate verdicts are recorded in decision records under `.pdlc/decisions/`, not by mutating the artifact `status`. Downstream phases gate on the decision record's `gate_verdict`, not on the artifact `status`.

## Revision Mode

A phase skill may be re-invoked after a gate returned `pivot`. Before re-drafting, detect whether a revision is in progress:

1. Locate the initiative directory.
2. Look for the most recent decision record whose `initiative` matches and whose `phase` matches this skill's phase and `gate_verdict` is `pivot`.

If found, operate in **revision mode**:

- Read the existing artifact and the pivot rationale together.
- Amend the artifact to address the pivot. Do not regenerate from scratch; preserve content the rationale did not challenge and make the minimum changes that resolve every point.
- Bump a `revision: <n>` counter in the artifact frontmatter, starting at 1 on the first revision.

Otherwise, draft fresh as normal. Either way, emit the usual outcome.

## ID Formats

| Artifact | Format | Scope | Example |
|---|---|---|---|
| Initiative | `INIT-N` | Project-wide | `INIT-42` |
| Decision | `DEC-N` | Project-wide | `DEC-3` |
| Learning | `N` | Project-wide | `2` |
| Functional requirement (PRD) | `FR-N` | Per-initiative | `FR-1` |
| Success metric | `SM-N` | Per-initiative | `SM-2` |
| Guardrail metric | `GM-N` | Per-initiative | `GM-1` |

All PDLC numeric identifiers are unpadded. Within an initiative document, use bare IDs (`FR-1`, `SM-2`). Across initiatives, qualify: `INIT-2-FR-3`.

## Commit / Push / PR Gate (mandatory)

Never commit, push, or open a PR without an explicit request from the user, even when a phase would normally include these actions (for example posting a launch plan as a PR, or filing a placeholder issue). Complete non-destructive work, then stop and report, and wait for explicit confirmation. This applies at every phase and entry point.
