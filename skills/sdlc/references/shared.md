# Shared SDLC Skill Conventions

This file is the single source of truth for conventions shared across every SDLC skill.
Each skill relies on these conventions instead of restating them.
The instructions below apply automatically whenever a skill reads or writes anything under `.sdlc/` (see `AGENTS.md`).

## Applicability

These conventions apply to every skill that touches `.sdlc/` artifacts:
the orchestrator (`sdlc`), the setup skills (`initialize-sdlc-directory`, `sync-sdlc`, `update-sdlc-templates`, `sdlc-status`, `backpropagate-sdlc`, `audit-sdlc`), every `create-*` and `review-*` pipeline skill, and any skill that consults `.sdlc/context/` for project context.

## Skill Handoff

Most SDLC skills end with a `## Next Step` section naming one or more successor skills.
When a skill completes and points to a successor, load that successor with the `skill` tool before performing any of its work.

A skill's `allowed-tools`, workflow, attribution steps, and gates take effect only once its content is in context.
Never execute a successor's actions from memory or general knowledge.
This is mandatory for skills that commit, push, or open PRs (`create-pr`, `fix-issue`, `publish-plan`, `merge-pr`, `deploy-pr`, `handle-pr-ci`, `handle-pr-feedback`): their commit and push rules are bypassed whenever the skill is not loaded.

This rule applies however the successor was reached:
- via the orchestrator (`/sdlc <phase>`), which loads each phase skill before executing it, or
- via direct invocation of an individual skill (for example `/create-implementation`), where this file is the only place the handoff rule is stated.

If a successor needs to commit, push, or open a PR and its skill is not yet loaded, load it first, then follow its workflow.
Do not start the successor's commit, push, or PR actions and load the skill only afterward.

## Project context files

Before producing a document, read any files present under `.sdlc/context/` and apply the artifact style rules found there to the output.

The context files are:

- `project-overview.md` — project goals, scope, stakeholders
- `goals.md` — project objectives, key results, and KPIs
- `architecture.md` — system topology, components, data flow
- `conventions.md` — naming, structure, and coding standards (the source of style rules)
- `vocabulary.md` — domain terms, technical terms, abbreviations
- `service-levels.md` (optional) — service-level objectives, indicators, agreements, and error budgets

Conventions found in `conventions.md` (for example, documentation formatting, one-sentence-per-line rules) apply to every document produced during the pipeline.

## AGENTS.md SDLC anchor

So a future agent session knows the project tracks work under `.sdlc/`, every project that has a `.sdlc/` directory carries a short, idempotent **SDLC anchor** block in its primary agent-instruction file. This is the entry point that tells an agent the SDLC artifacts exist and where to find them.

### Target file

The anchor is written to the repo's primary agent-instruction file, resolved in this order:

1. `AGENTS.md` in the project root, if it exists.
2. Otherwise `CLAUDE.md` in the project root, if it exists (projects that standardized on Claude).
3. Otherwise, create `AGENTS.md` in the project root.

Only one file ever holds the anchor. It is a repo-level concern: write it to the repository, never to the `SDLC_DIR` mirror, because it must be visible to any agent that opens the repo. If the target file is read-only or absent and cannot be created, skip the write and note it in the report.

### Content

The block is delimited by HTML comment markers so it can be updated in place without touching the rest of the file:

```
<!-- sdlc-anchor begin -->
## SDLC

This project tracks features, requirements, specifications, and decisions under [`.sdlc/`](.sdlc/).

Before starting work on a feature:
- Read `.sdlc/context/` (`project-overview.md`, `architecture.md`, `conventions.md`, `vocabulary.md`) for project context, and apply the style rules in `conventions.md` to anything you write.
- Run `/sdlc status` to see feature progress, or `/sdlc continue` to resume in-progress work.
- Run `/sync-sdlc` to reconcile `.sdlc/` with the current codebase.

Never commit local-only state: `.sdlc/state.yml` and `.sdlc/features/*/progress.md`.
<!-- sdlc-anchor end -->
```

### Idempotency

- If the target file does not exist, create it containing only the block.
- If the file exists but has no `<!-- sdlc-anchor begin -->` ... `<!-- sdlc-anchor end -->` block, append the block at the end of the file, separated from existing content by a blank line.
- If the file exists and the block is already present, replace the delimited content with the canonical text above. This lets later syncs evolve the wording without leaving stale duplicates.
- Never modify content outside the markers.

### When it is written

- `initialize-sdlc-directory` writes the anchor when it creates the `.sdlc/` structure.
- `sync-sdlc` re-ensures the anchor on every run (first sync via `initialize-sdlc-directory`, later syncs via its own ensure step), so removing or evolving it self-heals on the next sync.

## Feature Directory Naming

Feature directories live under `.sdlc/features/` and are named `N-<slug>`, where `N` is the feature identifier used verbatim with **no zero-padding** (no `FEAT-` prefix on the directory either, since the parent `features/` already conveys the kind). The corresponding **feature ID** used in cross-references is `FEAT-N` (e.g., directory `42-notification-system` ↔ feature ID `FEAT-42`; directory `p1-onboarding` ↔ feature ID `FEAT-p1`).

`N` has one of two lexical forms, chosen by whether the work is tied to a GitHub issue:

- **Issue-driven (default):** when a GitHub issue is available, `N` is the issue number used verbatim (e.g., issue `#42` → directory `42-<slug>`, feature ID `FEAT-42`). The issue number is available when it is passed as an argument, read from the `$ISSUE_NUMBER` environment variable, or present as `github_ref` in `.sdlc/state.yml`. The artifact frontmatter `issue` field is set (e.g., `issue: "#42"`).
- **Pending (no issue yet):** when there is no issue (a free-text brief, a code-analysis reconciliation in `sync-sdlc`, or an ad-hoc description), `N` is the letter `p` followed by the next unused sequence among `p`-prefixed directories (e.g., `p1-<slug>`, `p2-<slug>`, feature ID `FEAT-p1`). The `p` prefix marks the feature as **pending a placeholder issue**: it has no GitHub issue yet and is a candidate for promotion. The artifact frontmatter `issue` field is left unset.

The `<slug>` is lowercase, with hyphens for spaces and no special characters.

A `p`-prefixed identifier can never collide with an issue number, so issue-driven and pending features can coexist in the same `.sdlc/features/` tree without ambiguity. This is why numbering is independent of storage location: an external mirror for a third-party repo may hold issue-driven features built from upstream issues alongside `p`-prefixed features that have no issue. Location decides where files live, not how `N` is chosen.

### Placeholder-issue promotion

A pending feature is expected to be promoted to an issue-driven feature once a GitHub issue can be created for it (always, in a repo you own; only if an upstream issue is filed or accepted, in a third-party repo). Promotion is a single operation:

1. Create a placeholder GitHub issue in the repo with a stub body (include an `<!-- sdlc-placeholder -->` marker and the feature slug).
2. Capture the returned issue number `M`.
3. Rename the directory `p<seq>-<slug>` → `M-<slug>`.
4. Rewrite every feature ID occurrence: `FEAT-p<seq>` → `FEAT-M` in frontmatter and in every cross-reference across `.sdlc/`, including qualified forms like `FEAT-p1-FR-2`.
5. Set `issue: "#M"` in the artifact frontmatter. Clear the placeholder marker once the issue body is filled in.

Rename-on-promotion keeps the directory matching the issue number, preserving the direct issue ↔ directory traceability at the cost of a one-time, automatable cross-reference update.

### Create-time check

Before creating a new feature directory, check `.sdlc/features/` for an existing directory whose `N` matches the candidate and reuse it instead of creating a duplicate:

- Creating issue-driven `M` → only an existing `M-<slug>` whose frontmatter `issue` references `#M` can match; a `p`-prefixed directory never matches a numeric `M`.
- Creating pending → take the next unused `p<seq>`.

This matters for revision mode, where a `create-*` skill is re-invoked after a review returned `changes-requested`.

> All SDLC numeric identifiers are unpadded: feature, task, assumption, decision, learning, and per-feature requirement/test IDs use the bare number (`FEAT-42`, `FR-1`, `TC-5`, task `3`), never zero-padded. The `p` prefix is the only non-numeric token permitted in a feature identifier.

## Artifact Location Resolution (SDLC_DIR)

By default every `.sdlc/` path resolves inside the repository.
When the `SDLC_DIR` environment variable is set, an external mirror keyed by GitHub `{owner}/{repository}` is used as a read fallback (and, when the repo's `.sdlc/` is absent or read-only, as the write target).

```
$SDLC_DIR/
  {owner}/
    {repository}/        # mirrors the repository root
      .sdlc/             # same tree as the repo's .sdlc/
        context/
        features/
        knowledge/
        templates/
        ...
```

This mirrors the existing `repositories/{owner}/{repository}/` convention used for per-repository `AGENTS.md` overrides.

### Deriving `{owner}/{repository}`

Run `git remote get-url origin` in the project root and parse the GitHub URL:

- `git@github.com:owner/repo.git` -> `owner/repo`
- `https://github.com/owner/repo.git` -> `owner/repo`

Strip a trailing `.git`. If there is no remote, the `SDLC_DIR` fallback is unavailable for this project and only the repo's `.sdlc/` is used.

### Read resolution

For any artifact path `<path>` relative to the repo root (e.g. `.sdlc/context/conventions.md`, `.sdlc/features/42-x/requirements.md`):

1. Read `<repo>/<path>` if it exists.
2. Otherwise, if `SDLC_DIR` is set and `{owner}/{repository}` was derived, read `$SDLC_DIR/{owner}/{repository}/<path>`.

The repository always wins; `SDLC_DIR` is a fallback only.

### Write resolution

1. The primary write location is `<repo>/<path>`. Try to create `<repo>/.sdlc/` if it does not exist.
2. If writing to `<repo>/<path>` fails (the directory cannot be created or is read-only) and `SDLC_DIR` is set with a derivable `{owner}/{repository}`, write to `$SDLC_DIR/{owner}/{repository}/<path>` instead, creating the directory tree as needed.
3. When a write lands in the repo's `.sdlc/` and `SDLC_DIR` is set, also mirror the same content to `$SDLC_DIR/{owner}/{repository}/<path>` so the external store does not go stale.

### What is never mirrored

- `state.yml` and `features/*/progress.md` are local-only workflow state (regenerated per machine and per run). They are never read from or written to `SDLC_DIR`.
- `sync-meta.yml` and generated reports (`audit-report.md`, `backpropagation-report.md`, `improvement-dryrun-*.md`) stay in the repo's `.sdlc/` only.

## Automation runner environment

When invoked by an automation runner, an SDLC skill resolves its target from environment variables, never from positional arguments or from `.sdlc/state.yml` (which may be absent).
A variable that does not apply to the current event is present but empty, and is treated as unset.

| Variable | Present when | Content |
|---|---|---|
| `REPO` | always | `{owner}/{repository}` of the target repo, e.g. `tomzx/agents` |
| `ISSUE_NUMBER` | issue events | the issue number, e.g. `42` |
| `ISSUE_TITLE` | issue events | issue title |
| `ISSUE_BODY` | issue events | issue body text |
| `ISSUE_LABELS` | issue events | comma-separated current label names |
| `LABEL` | `labeled` events | the label that was added |
| `PR_NUMBER` | pull request events | the PR number |
| `PR_BRANCH` | pull request events | PR head branch ref, e.g. `plan/issue-42`, `impl/42` |
| `PR_TITLE` | pull request events | PR title |
| `PR_BODY` | pull request events | PR body text |
| `PR_MERGED` | pull request events | merged flag, `true` only when the PR was merged on close, otherwise `false`/empty |
| `COMMENT_AUTHOR` | comment events | login of the commenter |
| `COMMENT_BODY` | comment events | comment text |
| `COMMENT_TYPE` | comment events | `inline` (PR review comment) or `general` (issue or PR comment) |
| `GH_TOKEN` | always | the GitHub auth token, for use with `gh` |
| `OPENCODE_DISABLE_AUTO_UPDATE` | always | `1` |

Exactly one of `ISSUE_NUMBER` or `PR_NUMBER` identifies the subject; the other is empty.

The following `GITHUB_*` variables are also available when present: `GITHUB_EVENT_NAME` (event name), `GITHUB_EVENT_PATH` (full event payload JSON), `GITHUB_WORKSPACE` (checked-out repository root, the working directory), `GITHUB_REPOSITORY` (same value as `REPO`), and `GITHUB_SERVER_URL` with `GITHUB_RUN_ID` (used to construct a run URL).

Reporting a verdict back to the runner uses `$OUTCOME_YAML` (see below).

## Outcome Emission ($OUTCOME_YAML)

A runner may invoke a skill and need its result as structured data. When the `$OUTCOME_YAML` environment variable is set to a file path, write a YAML object recording your verdict there as your **final action**:

```yaml
verdict: <value>       # the skill's routing decision (see each skill's Outcome section)
reason: <one sentence>  # optional
```

Rules:

- Emit exactly one `verdict`. Each skill documents its vocabulary in its own `## Outcome` section. The `verdict` is a runner-facing routing decision and is separate from the artifact frontmatter `status`: a `create-*` skill writes `status: draft` to its artifact and emits `verdict: approved` to signal it produced the draft; the matching feature-pipeline `review-*` skill records its outcome in a `review-<artifact>.md` findings file (see Review Findings Persistence) and does not modify the artifact `status` (knowledge-record reviews are the exception; they set domain lifecycle statuses).
- If `$OUTCOME_YAML` is unset, skip emission entirely. The variable is the only signal that an outcome is wanted; in normal interactive use it is not set.
- This channel only reports the skill's own decision. It does not replace the skill's normal outputs (artifacts, comments, labels, PRs).
- If you cannot reach a verdict (error, inconclusive), omit the file or write `verdict: unknown`.
- Values must be valid YAML scalars. If `verdict` or `reason` contains a colon `:`, hash `#`, or any indicator character (``{}[]&*!|>'"%@` ``), quote the value (single or double quotes) or use a literal block scalar (`|`). Prefer quoting `reason` whenever it is a free-form sentence.

## Review Findings Persistence (review-* skills)

The automation engine is stateless: each rule run starts from a fresh checkout, and the only cross-run persistence is the per-issue working branch (the runner commits `.sdlc/` after the skill runs via `commit-sdlc.sh`). A review's findings must therefore survive on that branch, not only as the posted comment (which is ephemeral relative to the branch).

When a `review-*` skill that governs a feature-pipeline artifact runs (see the table below for which artifacts), after producing its findings it writes them to a findings file beside the artifact under review. That review skill writes only this file: it does not modify the reviewed artifact's review-bookkeeping `status` (`draft`/`in-review`/`approved`). Open questions discovered during review are recorded in the findings body. (Domain lifecycle statuses are separate and still set by the relevant review skill: task `pending`, and the knowledge-record statuses (assumption `Validated`, decision `Accepted`, learnings `complete`). Knowledge-record reviews are not listed below.) The findings file path is:

```
.sdlc/features/N-<slug>/review-<artifact>.md
```

The `<artifact>` stem matches the primary artifact the skill reviews:

| Artifact | Findings file |
|---|---|
| `needs-assessment.md` | `review-needs-assessment.md` |
| `requirements.md` | `review-requirements.md` |
| `existing-solutions.md` | `review-existing-solutions.md` |
| `codebase-analysis.md` | `review-codebase-analysis.md` |
| `feasibility.md` | `review-feasibility.md` |
| `specification.md` | `review-specification.md` |
| `mockups.md` | `review-mockups.md` |
| `telemetry.md` | `review-telemetry.md` |
| `observability.md` | `review-observability.md` |
| `plan.md` | `review-plan.md` |
| `tasks/` | `review-tasks.md` |
| `tests.md` | `review-tests.md` |
| documentation | `review-documentation.md` |
| implementation (code) | `review-implementation.md` |

Frontmatter:

```yaml
---
artifact: <artifact>
verdict: <approved | changes-requested | rejected>
reviewed_at: <ISO date>
---
```

The body is the findings in the skill's normal output format.

Rules:

- Write this file for every verdict when running under automation (`$OUTCOME_YAML` set). On `approved`, overwrite it with `verdict: approved` (body "No blocking findings.") so the corresponding `create-*` skill sees a clean state and does not re-enter revision mode.
- This file is the durable record the create step reads to decide whether to revise. The posted comment (`post_reason`) is for humans; this file is for the next run.
- The file follows the same `SDLC_DIR` read/write resolution as the artifact it accompanies, and is committed to the working branch by the runner's `commit-sdlc.sh`.
- `backpropagate-sdlc` and `sync-sdlc` may regress an approved findings file to `verdict: changes-requested`, recording the drift in the body, when they detect the reviewed artifact has drifted from the code. The forward pipeline then resyncs the artifact via revision mode (see below) and the matching `review-*` skill restores `approved` once the drift is resolved.

Context-level review skills (`review-goals`, `review-service-levels`) write their findings beside the context artifact instead of under a feature directory: `.sdlc/context/review-goals.md` and `.sdlc/context/review-service-levels.md`, with the same frontmatter (`artifact`, `verdict`, `reviewed_at`) and verdict semantics.

## Revision Mode (create-* skills)

A `create-*` skill may be re-invoked after its artifact was returned with `changes-requested`. Before drafting, detect whether a revision is in progress:

1. Locate the feature directory for `$ISSUE_NUMBER` (the directory whose frontmatter `issue` field references it).
2. Look for `review-<artifact>.md` next to the target artifact (see Review Findings Persistence).

If that file exists and its `verdict` is `changes-requested`, operate in **revision mode**:

- Read the existing artifact and the findings together.
- Amend the artifact to address each finding. Do not regenerate from scratch: preserve content the findings did not challenge, and make the minimum changes that resolve every finding.
- Set the artifact frontmatter `status` to `in-review` while revising. Reviews do not modify the artifact frontmatter; the authoring `create-*` skill owns the `status` field.
- Optionally bump a `revision: <n>` counter in the artifact frontmatter, starting at 1 on the first revision.

Otherwise (no findings file, or `verdict: approved`), draft fresh as normal.

Either way, emit the usual outcome (`approved` -> the next `review-*` step). Revision mode changes how the artifact is produced, not the verdict the skill emits.
