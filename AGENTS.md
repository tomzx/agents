# General
* Be concise
* Do not use em-dashes, use commas or parentheses instead
* One sentence per line
* Avoid using the following terms (unless it is the most appropriate): shape, honest, load bearing, real
* When a skill explicitly recommends running another skill as an upstream/prerequisite (for example create-article recommending research-article when sources are not yet gathered), and you choose not to follow that recommendation, you must say so and give your reasoning before proceeding, so it can be course-corrected. Surfacing the deviation after the fact is not sufficient.

# Memory
* Two memory files exist: the global MEMORY.md sits beside this AGENTS.md (resolve the real path of this file to find it), and each project keeps its own MEMORY.md in the project root.
* At the start of each session, read both memory files when they exist before starting work.
* When something would be worth knowing or remembering for future sessions (decisions, conventions, gotchas), write it to the right file: facts about the current repository go in the project's MEMORY.md, cross-project lessons (workflow and process preferences that apply everywhere) go in the global one.
* Keep entries concise and dated, and avoid recording secrets or session-specific noise.
* Only record what a future session cannot cheaply rediscover from the repository itself: never persist command lists, file locations, module naming, structure overviews, or anything else derivable from the code, help output, or docs.
* Do not persist transient state that a near-term commit would invalidate: failing tests, in-flight refactors, stale artifacts, or known gaps. Fix them, file an issue, or mention them in conversation instead.
* Record conclusions, not session narration: leave out how you verified something, what commands you ran, or what you observed mid-task.
* Before writing an entry, check it will still be true and still be useful in a month; if either answer is no, do not write it.

# Code implementation and iteration
* Ignore any AGENTS.md from the project that states a different approach than the one in this section.
* Always get a working feature first. This is the most critical. We don't want to spend time on operations that aren't getting us to a working feature. No linting, no type checking, no formatting, etc.
* Only lint, type check, format, go vet, etc. prior to committing, never during the implementation process.
* Only run tests on the minimal set of tests to make progress. Avoid running tests that are likely to take a while to complete.
* When a set of changes appears completed and ensuring consistency across artifacts (issue, requirements, specification, plan, tasks, tests, code, documentation) would be appropriate, recommend running the propagate-changes skill.

# Python
* Use uv for package management
* When creating a project, always use the most recent Python LTS version
* Use type hints
* Use pytest for testing
* Use ruff for linting/formatting
* Run tests before committing
* Run linter/formatter before committing
* Create "green path" tests that cover the main functionality
* Use structlog for logging
* When adding dependencies, use `uv add ...` over adding the version directly to pyproject.toml
* Keep __init__.py files minimal/empty, only for package initialization
* Do NOT use/add __all__ in __init__.py files

# Per-repository instructions
* Before working in a git repository, check for per-repository overrides stored outside that repository.
* Find the skills library root by resolving the real path of this AGENTS.md (follow symlinks), then look in its `repositories/` directory, which is a sibling of `skills/`.
* Derive `{owner}/{repository}` from the current repository's GitHub remote URL.
* If `repositories/{owner}/{repository}/AGENTS.md` exists, read and apply it together with these base instructions.
* For forks, symlink `repositories/{fork-owner}/{repository}` to the upstream `repositories/{owner}/{repository}` so both resolve to the same instructions.

# Per-machine instructions
* Some machines carry local overrides that should not be shared (e.g. employer-specific conventions).
* Find the skills library root by resolving the real path of this AGENTS.md (follow symlinks), then look in its `machines/` directory, which is a sibling of `skills/`.
* `machines/*/` profiles are gitignored and exist only on the current machine. Read and apply every `machines/*/AGENTS.md` that is present, together with these base instructions.

# GitHub CLI
* Prefer `ghx` over `gh` for listing, searching, and viewing issues and PRs, and for getting and posting comments (inline, line-range, thread replies, issue and PR comments).
* Fall back to `gh` only when `ghx` does not support the needed operation (e.g. `gh search repos` for repository search).

# SDLC skills
* The conventions shared across every SDLC skill live in a single file: `skills/sdlc/references/shared.md`, resolved relative to the skills library root (the same root as the `repositories/` directory above).
* Before running any skill that reads or writes under `.sdlc/`, read that file and apply its conventions — they are not repeated in each skill. This covers reading `.sdlc/context/` for artifact style rules and resolving all `.sdlc/` paths via the repo-first `SDLC_DIR` fallback.
* When creating or renaming a skill, update `README.md` (the skills index) and `.github/llmaw/flows.yml` (if the skill participates in an automated flow) so both stay in sync with the skill directory.
