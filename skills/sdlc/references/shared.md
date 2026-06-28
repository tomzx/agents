# Shared SDLC Skill Conventions

This file is the single source of truth for conventions shared across every SDLC skill.
Each skill relies on these conventions instead of restating them.
The instructions below apply automatically whenever a skill reads or writes anything under `.sdlc/` (see `AGENTS.md`).

## Applicability

These conventions apply to every skill that touches `.sdlc/` artifacts:
the orchestrator (`sdlc`), the setup skills (`initialize-sdlc-directory`, `sync-sdlc`, `update-sdlc-templates`, `sdlc-status`, `backpropagate-sdlc`, `audit-sdlc`), every `create-*` and `review-*` pipeline skill, and any skill that consults `.sdlc/context/` for project context.

## Project context files

Before producing a document, read any files present under `.sdlc/context/` and apply the artifact style rules found there to the output.

The context files are:

- `project-overview.md` — project goals, scope, stakeholders
- `architecture.md` — system topology, components, data flow
- `conventions.md` — naming, structure, and coding standards (the source of style rules)
- `vocabulary.md` — domain terms, technical terms, abbreviations

Conventions found in `conventions.md` (for example, documentation formatting, one-sentence-per-line rules) apply to every document produced during the pipeline.

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

For any artifact path `<path>` relative to the repo root (e.g. `.sdlc/context/conventions.md`, `.sdlc/features/FEAT-0001-x/requirements.md`):

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

- Emit exactly one `verdict`. Each skill documents its vocabulary in its own `## Outcome` section. The `verdict` is a runner-facing routing decision and is separate from the artifact frontmatter `status`: a `create-*` skill writes `status: draft` to its artifact and emits `verdict: approved` to signal it produced the draft; the matching `review-*` skill later promotes the artifact `status` to `approved`.
- If `$OUTCOME_YAML` is unset, skip emission entirely. The variable is the only signal that an outcome is wanted; in normal interactive use it is not set.
- This channel only reports the skill's own decision. It does not replace the skill's normal outputs (artifacts, comments, labels, PRs).
- If you cannot reach a verdict (error, inconclusive), omit the file or write `verdict: unknown`.
- Values must be valid YAML scalars. If `verdict` or `reason` contains a colon `:`, hash `#`, or any indicator character (``{}[]&*!|>'"%@` ``), quote the value (single or double quotes) or use a literal block scalar (`|`). Prefer quoting `reason` whenever it is a free-form sentence.

## Review Findings Persistence (review-* skills)

The automation engine is stateless: each rule run starts from a fresh checkout, and the only cross-run persistence is the per-issue working branch (the runner commits `.sdlc/` after the skill runs via `commit-sdlc.sh`). A review's findings must therefore survive on that branch, not only as the posted comment (which is ephemeral relative to the branch).

When a `review-*` skill runs, after producing its findings it writes them to a findings file beside the artifact under review:

```
.sdlc/features/FEAT-NNNN-<slug>/review-<artifact>.md
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
| `telemetry.md` | `review-telemetry.md` |
| `observability.md` | `review-observability.md` |
| `tasks/` | `review-tasks.md` |
| `tests.md` | `review-tests.md` |

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

## Revision Mode (create-* skills)

A `create-*` skill may be re-invoked after its artifact was returned with `changes-requested`. Before drafting, detect whether a revision is in progress:

1. Locate the feature directory for `$ISSUE_NUMBER` (the directory whose frontmatter `issue` field references it).
2. Look for `review-<artifact>.md` next to the target artifact (see Review Findings Persistence).

If that file exists and its `verdict` is `changes-requested`, operate in **revision mode**:

- Read the existing artifact and the findings together.
- Amend the artifact to address each finding. Do not regenerate from scratch: preserve content the findings did not challenge, and make the minimum changes that resolve every finding.
- Keep the artifact frontmatter `status` at `in-review` (the review skill set it; do not regress it to `draft`).
- Optionally bump a `revision: <n>` counter in the artifact frontmatter, starting at 1 on the first revision.

Otherwise (no findings file, or `verdict: approved`), draft fresh as normal.

Either way, emit the usual outcome (`approved` -> the next `review-*` step). Revision mode changes how the artifact is produced, not the verdict the skill emits.
