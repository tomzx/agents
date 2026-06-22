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
