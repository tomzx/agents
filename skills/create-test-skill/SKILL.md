---
name: create-test-skill
description: Generate a project-specific skill that documents every test level the codebase actually supports (unit, integration, end-to-end, and the rest), how to set up the environment for each one, and the exact commands that run them, and that makes every run leave a trace of the commands called and any temporary change made. Use when the user says /create-test-skill, "make a skill that tests this project", "generate a test skill for this repo", "document how to test this codebase", or wants to review what an agent actually ran before it claimed the tests pass.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
argument-hint: "[skill-name]"
---

# Create Test Skill

Generates a project-specific skill that runs the project's test suites and writes a trace of what it ran.

The generated skill answers four questions for its project: which test levels exist, how each one is set up, which exact command runs it, and whether an agent or a person runs it.
Every run also writes a trace document listing the commands called, their results, and any temporary change made to get the tests to execute.

The trace is the point.
An agent can make a suite look green by running one narrow test, relaxing an assertion, mocking the code under test, or skipping the slow part.
The trace makes those moves visible, so a reviewer can decide in a couple of minutes whether a green result proves what it claims.
That intent is written into the generated skill, not just into this one, so it survives after this generation session is gone.

## Prerequisites

- Working directory is the project root, or the project is the current repository.
- Read `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, and `.sdlc/context/infrastructure.md` when present, since they often name the test commands and the environment.
- Permission to install project dependencies and start local services.
- A working copy, not a read-only or detached checkout, because most levels need to write build outputs, caches, or a local database.
- Ask the user before any step that: runs a level expected to take more than 10 minutes, contacts a non-local host, resets or migrates a database that is not obviously disposable, or downloads a large toolchain.

## Scope

This skill owns test discovery, environment setup, execution, and the run trace for one project.
It writes a project-specific test skill and proves that the skill's commands work.

It does not write tests, review assertions, or fix failing code.
A failing suite is recorded as found, because the generated skill must describe the project as it is.

## Steps

### 1. Resolve the project and the generated skill name

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$PROJECT_ROOT"
REPO_NAME=$(git remote get-url origin 2>/dev/null | sed -E 's#\.git$##; s#.*[:/]##')
REPO_NAME=${REPO_NAME:-$(basename "$PROJECT_ROOT")}
SKILL_NAME=${SKILL_NAME:-test-$REPO_NAME}
SKILL_DIR=".agents/skills/$SKILL_NAME"
```

Set `SKILL_NAME` to the skill-name argument before running the block. When the argument is omitted, the block defaults it to `test-$REPO_NAME`, for example `test-davies` or `test-blog-content`.
Normalize it to kebab-case.
Use `.agents/skills/` unless the project already keeps skills somewhere else (`skills/`, `.claude/skills/`, `.opencode/skill/`); if it does, use that location and record it in the summary.

If `$SKILL_DIR/SKILL.md` already exists, treat this run as an update: read the existing skill, keep any project-specific additions the previous run or the user made, and state which sections were replaced.
Never silently drop a hand-written warning or workaround from an existing generated skill.

### 2. Read what the project already says about testing

Read, in this order:

1. `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, and the testing section of `README.md`.
2. `.sdlc/context/infrastructure.md` if it exists, since it is supposed to carry the exact tooling commands.
3. `.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/config.yml`, `azure-pipelines.yml`, `Jenkinsfile`, or `.buildkite/pipeline.yml`.

CI configuration is the strongest signal, because it is the set of commands the project actually runs on every change.
Note every mismatch between the documented command and the CI command, and prefer the CI command, saying so in the generated skill.

### 3. Inventory the test surface

```bash
ls -1 package.json pnpm-lock.yaml yarn.lock bun.lock bun.lockb uv.lock pyproject.toml setup.cfg tox.ini noxfile.py requirements*.txt \
      Cargo.toml go.mod pom.xml build.gradle build.gradle.kts settings.gradle Gemfile composer.json mix.exs \
      Makefile justfile Taskfile.yml 2>/dev/null
ls -d test tests spec __tests__ e2e e2e-tests integration_tests 2>/dev/null
ls -1 .github/workflows/*.yml .gitlab-ci.yml compose.y*ml docker-compose*.yml playwright.config.* cypress.config.* 2>/dev/null
```

Then expand the signals that exist:

| Signal | What to read |
|---|---|
| `package.json` | `scripts` (test, test:unit, test:e2e, lint, typecheck), and `devDependencies` for the runner (vitest, jest, playwright, cypress) |
| `pyproject.toml`, `tox.ini`, `noxfile.py` | `[tool.pytest.ini_options]`, markers, `addopts`, tox or nox environments, test extras |
| `Makefile`, `justfile`, `Taskfile.yml` | targets named `test`, `check`, `e2e`, `lint`, `ci` |
| `Cargo.toml`, workspace layout | test targets, `[[test]]` entries, benchmark harnesses |
| `go.mod` | packages with `_test.go`, build tags, integration test tags |
| Compose files, `devcontainer.json` | services a level needs, their ports, health checks, and volumes |
| `.env.example`, `settings/test*` | required environment variables and their test values |
| Migrations (`alembic/`, `prisma/`, `db/migrate/`, `flyway.conf`) | how the test database reaches the current schema |
| `playwright.config.*`, `cypress.config.*` | base URL, web server command, projects and browsers, retries |
| Fixtures, factories, seeds | how test data gets created, and whether a level needs seeding |
| `.sdlc/context/` | documented infrastructure and testing conventions |

Collect the concrete artifacts: directory names, runner config files, marker or tag names, and the scripts that wrap the runner.

### 4. Classify the levels the project supports

Place every level in one of four states: **present** (a runnable command exists and was executed), **canary only** (a runnable command exists and only a subset was executed), **documented** (named in docs or CI but no command can be run here), or **blocked** (a command exists but its environment cannot be established, with the obstacle named).

| Level | What it exercises | Typical signals |
|---|---|---|
| `static` | Lint, format check, type check, build. It gates merges but asserts little behavior. | `lint`, `typecheck`, `build` scripts, ruff, mypy, tsc, eslint, `make check` |
| `unit` | One module in isolation, no external I/O | `tests/unit`, colocated `*.test.ts`, a fast target |
| `integration` | Modules plus an actual database, queue, HTTP client, or filesystem | `tests/integration`, compose services, testcontainers, fixtures |
| `contract` | Provider and consumer schemas stay compatible | pact, schemathesis, OpenAPI diff, a `contract/` directory |
| `e2e` | The assembled product through its UI or CLI | Playwright, Cypress, Selenium, `e2e/`, a web server command |
| `agent driven` | Checks whose steps are decided while the test runs, by an agent or a model: agentic UI goals, LLM-graded evaluations, exploratory runs with a verdict | an agent-runner config, `evals/`, promptfoo or similar, model-graded tests, a goal file |
| `manual` | Checks only a person can perform: visual review, device or hardware checks, exploratory QA | a QA checklist, a manual test plan, a test-management tool, a `manual/` directory |
| `smoke` | The application starts and serves its basic surface | a smoke script, a health endpoint check, `make smoke` |
| `migration` | Schema and data migrations apply, and roll back | alembic, prisma migrate, flyway, `rails db:*`, a migration test |
| `performance` | Latency, throughput, benchmarks | k6, locust, jmeter, criterion, a `bench` target |
| `security` | Dependency, secret, and container scans | `npm audit`, `pip-audit`, gitleaks, trivy, a scheduled workflow |

Rules for classification:

- A level is present only when a command exists in the repository and was executed. A level that was only partly executed is `canary only`.
- A level with a documented workflow and no local command is documented. Say so, and name what CI runs and why it is not reproducible locally.
- A level whose prerequisites cannot be met is blocked. Name the obstacle (private registry, cloud credentials, an unavailable service) and what was tried.
- A `manual` level is never present or canary only, because no command can execute it. Classify it `documented`, record the checklist location, and record the executor as a person.
- An `agent driven` level is present only when its runner command executes end to end. Its verdict comes from an agent or a model, so it never substitutes for a deterministic assertion that exists.
- Do not invent a level to fill the table. Leave out the ladder levels the project does not have, and say in one line which ones are missing.

### 5. Establish the environment for each present level

For each level, answer every row that applies, and record the answer with the command that produced it.

| Question | Where the answer usually lives |
|---|---|
| Which runtime version, and how is it pinned? | `.nvmrc`, `.python-version`, `rust-toolchain.toml`, `go.mod`, `engines` in `package.json` |
| How are dependencies installed for tests only? | lockfile plus dev or test extras, `uv sync --group test`, `bundle install --with test` |
| Which services must run, and how are they started? | compose files, testcontainers, a `docker run` line in CI |
| How does the test database reach the right schema? | migration command, a per-run create and drop, a template database |
| Which environment variables are required, and what are safe local values? | `.env.example`, CI `env:` blocks, `settings/test*` |
| Which ports are assumed, and what happens if they are taken? | compose port mappings, `playwright.config` base URL, CI service ports |
| What must be built before the level runs? | a `build` step in CI before the test step |
| Does the level need browsers or other downloads? | `playwright install`, a CI cache step |
| Which model and credentials does an agent-driven level need, and what caps its budget? | the runner config, `.env.example`, a CI secret name, a budget or step cap in the config |
| What is the expected duration on a clean machine? | CI timing, or measure it |
| How is the level cleaned up afterwards? | teardown commands, `down`, temporary directories |

Prefer the project's own entry point (a script, a make target, a compose profile) over reconstructing the command from flags.
When you must reconstruct it, say in the generated skill which part came from where.

### 6. Prove each level by running it

Prove the commands before writing them down. A command that was never executed is a guess.

For each present level:

1. Run a canary first: the cheapest meaningful subset, usually one test file, one test, or one spec. It proves the environment works before spending minutes on the full run.
2. Run the level's full command when its expected duration is under 10 minutes or the user approved it.
3. Capture the exact command, working directory, environment overrides, exit code, duration, and the runner's summary counts.
4. For a level that is too slow or too costly, canary it and mark it `canary only` in the generated skill and in the trace. Never mark it `passing` on the strength of the canary alone.
5. Run an `agent driven` level under the budget or scope cap its config sets, and capture the goal, the model, the verdict, and the cost when the runner prints it.

A `manual` level is not executed.
Confirm its checklist exists and still names what a person should check, classify the level `documented`, and hand the checklist to the user in the summary.

A red baseline is a valid result.
Record it with its failure output and move on.
Do not fix the project's tests or code in this skill, unless the user asks, because the generated skill must describe the project as it is, including a suite that currently fails.

Timebox each level at the shorter of the project's own CI timeout and 10 minutes.
If a command is still running at the limit, stop it, record the truncation, and mark the level `not completed` rather than passed.

### 7. Record and revert temporary changes

Temporary changes are where corner cutting hides, so every one is declared with its diff and its revert.

```bash
mkdir -p /tmp/opencode/test-skill
git status --porcelain > /tmp/opencode/test-skill/status-before.txt
git diff --stat > /tmp/opencode/test-skill/diff-before.txt
# ... run levels ...
git status --porcelain > /tmp/opencode/test-skill/status-after.txt
git diff --stat > /tmp/opencode/test-skill/diff-after.txt
diff /tmp/opencode/test-skill/status-before.txt /tmp/opencode/test-skill/status-after.txt
diff /tmp/opencode/test-skill/diff-before.txt /tmp/opencode/test-skill/diff-after.txt
```

| Allowed, environment only | Forbidden, it invalidates the run |
|---|---|
| Copy `.env.example` to `.env` with local values | Edit a test, fixture, snapshot, or assertion |
| Create a disposable local database or volume and migrate it | Skip, xfail, quarantine, or mark a test `only` |
| Install project dependencies and browsers | Deselect, filter, ignore, or exclude tests |
| Change a port, socket path, or cache directory | Add a mock or stub for the code under test |
| Seed local fixtures through the project's own script | Change product code so a test passes |
| Set a timeout flag the project already documents | Add `|| true`, `; true`, or `--no-verify` |
| Raise log verbosity to diagnose a failure | Disable or bypass a CI check |

For each change, record: the path or resource, the exact command or diff, why it was needed, the revert command, and whether it was reverted and verified.
Keep a persistent change only when the project needs it (for example a missing `.env.example` fix), and ask the user before keeping it.
Delete generated artifacts the run created and that git does not ignore, or list them as left behind.

### 8. Write the generated skill

Write `$SKILL_DIR/SKILL.md` following the skeleton in Output Format.
Every section there is required.

The intent paragraph is copied from the skeleton and adapted with the project name.
Do not shorten it to "run the tests".
Its job is to tell the next agent, and the reviewer reading the trace, why the run has to be traceable.

Keep the skill specific: exact commands, exact paths, exact service names, exact expected counts or output lines where they are stable.
Do not describe a level the project does not have, and do not include a command that Step 6 did not execute.
The one exception is a `canary only` level: include its full command, mark it `not yet executed` in the level section, and say what the canary proved instead.

### 9. Write the probe trace

Write the trace for your own probing to `.agents/test-runs/<YYYY-MM-DDTHHMMZ>-generate-<SKILL_NAME>.md` using the Trace Template below.
It records how the commands in the generated skill were validated, which levels were canaried rather than run, and what you changed to get them executing.

If the project is read-only or the path is not writable, write the trace to `/tmp/opencode/test-runs/` and say so in the summary.

### 10. Prove the generated skill

Run the generated skill once, at its cheapest present level:

```
/$SKILL_NAME <level>
```

`<level>` is the level name recorded in Step 6, usually `unit`.

Confirm from its output and trace that:

- The command it chose matches the command recorded in Step 6.
- The trace lists the command, the exit code, the counts, and any temporary change.
- Nothing in the project was modified by the run.

Fix the generated skill when a command in it is wrong or a prerequisite is missing.
Do not fix the project's tests.

### 11. Summarize

Report:

- The generated skill path and name.
- Each level with its state (present, canary only, documented, blocked), its command, and its baseline result.
- Temporary changes made during probing, and their revert status.
- The probe trace path, and the first run's trace path.
- What a reviewer should read first.

If the user wants the generated skill discoverable through the project's agent instructions, print the one line to add to `AGENTS.md` and let them decide; do not edit it unasked.

## Trace Template

Every run writes `.agents/test-runs/<YYYY-MM-DDTHHMMZ>-<label>.md`.
The label is the level, or a short purpose such as `pre-pr` or `generate-test-<name>`.

````markdown
# Test run: <label>

- Date: <YYYY-MM-DD HH:MM UTC>
- Requested by: <the request, or the claim this run supports>

## Intent

<One sentence saying why the run happened and what it is meant to prove.>

## Environment

- Repository: <owner/repo>
- Commit: <sha> on <branch>
- Working tree: clean | dirty (<N> modified, <M> untracked, listed below)
- Tree before and after the run: `git status --porcelain` and `git diff --stat`, unchanged | changed (details under Temporary changes)
- Runtime: <name and version>; package manager: <name and version>
- Services: <name, how started, port>
- Environment variables set for this run: <names only, no values>
- Env files created or modified: <paths>

## Levels attempted

| Level | Command | Exit | Duration | Collected | Passed | Failed | Skipped | Deselected | Status |
|---|---|---|---|---|---|---|---|---|---|

Compared with the expected counts in the skill: <same, or the drop and its explanation>.

- Agent-driven runs: <level, goal or eval name, model, verdict, steps taken or the run log path, budget spent>
- Manual levels: <level, checklist location, not executed>

## Command log

### 1. <purpose>

Working directory: `<path>`

```bash
<the command exactly as run>
```

- Exit: <code>, duration: <seconds>
- Notes: <environment overrides, deviations, why this command and not the default one>

Output (tail):

```
<the last 20 lines, or the failure output>
```

## Temporary changes

| Path or resource | Change | Reason | Reverted | Verified by |
|---|---|---|---|---|

```diff
<the diff, or the exact command that made the change>
```

## Not run or narrowed

- <Level, test, or flag>: <reason>, <what would have run instead>

## What this run does not prove

<One or two plain lines: which levels were canaried only, which failed, which were skipped, and what a green result therefore covers.>
````

Rules for the trace:

- Write it even when the run fails, and especially then.
- One entry per command actually executed, in order, with the command copy-pasteable as run.
- Never paste a command that was not executed. If a step was skipped, it belongs under "Not run or narrowed".
- The counts come from the runner's own summary. If the runner does not print one, say so rather than estimating.
- Record the tree before and after the run. A difference means something changed while the tests ran, so it is either a declared temporary change or a violation.
- Compare each level's collected count with the expected count recorded in the skill. Fewer tests collected than expected is a finding, not a pass, and must be explained.
- An agent-driven verdict is evidence of what the agent or model observed, not of a deterministic assertion. Record the model, the goal, and the steps, because that record is what a reviewer judges.
- A manual level is listed as not executed, with its checklist location. It never appears as passed.
- The trace is written before the answer is given, so the claim and the evidence cannot drift apart.
- Traces live in the repository so a reviewer can read them beside the change. Recommend adding `.agents/test-runs/` to `.gitignore` when the project does not want run history committed, and keep the trace in a PR when it is the evidence for that PR.

## Output Format

The generated skill must follow this skeleton.

````markdown
---
name: <test-project>
description: Run the <project> test suites at the requested level (<levels>), set up the environment each level needs, and write a trace of every command run and every temporary change made. Use when the user says /<test-project>, "run the tests", "run the <level> tests", "does the suite pass", or before claiming that a change is tested.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
argument-hint: "[<level> | all] [extra args]"
---

# Test <project>

## Why this skill exists

Run <project>'s test suites the way the project itself runs them, and leave a trace a reviewer can check in a couple of minutes.

**Intent.** Prove that the code does what the tests assert, and show how it was proven.
A passing run only counts as evidence when the trace names the commands, the tests actually selected, and every temporary change made.
This guards against the failure where an agent runs one narrow test, weakens or skips what is inconvenient, and then reports that the suite passes.
When the trace and the claim disagree, the trace wins.

## Project snapshot

| | |
|---|---|
| Repository | <owner/repo> |
| Commit at generation | <sha> on <branch> |
| Generated | <YYYY-MM-DD> |
| Runtime | <name and version> |
| Package manager | <name and version> |
| Test runner | <name and version> |

## Levels at a glance

| Level | Status | Run by | Scope | Location | Setup | Command | Time | Expected |
|---|---|---|---|---|---|---|---|---|
| `<level>` | present, canary only, documented, or blocked | agent or person | <what it covers> | <directory or config> | <the few commands from the level section> | `<command>` | <duration> | <collected count and green summary line, or the verdict threshold> |

Levels this project does not have: <one line, or "none of the remaining ladder levels">.

`all` runs every level whose `Run by` is `agent`, and reports the manual levels as handed over.

## `<level>` (`/<test-project> <level>`)

Run by: <`agent`, or `a person`: this level is documented and handed over, never claimed as run>

### Setup

<Every command needed from a clean checkout, in order, with the working directory.>
<Services to start, migrations to run, env vars to export, build steps, and how to confirm each one is ready.>

### Run

```bash
<the full command, as validated, or the full command marked "not yet executed">
```

- Working directory: `<path>`
- Expected duration: <duration>
- Expected green output: <the runner's summary line or counts>

### Run one test

```bash
<the command for a single test, file, or spec, with the placeholder named>
```

### Cleanup

```bash
<the commands that stop services, drop the test database, and remove run artifacts>
```

### Notes

<Known flakiness, ports that collide, data that must be seeded, and anything that differs from CI.>

<Repeat the `<level>` section for every present or canary-only level, and for every manual level so the checklist location is written down. A manual level section records the checklist and what a person should check, and omits the Run and Run one test commands. Omit the levels the project does not have.>

## Levels that cannot run here

| Level | State | Run by | Why | What CI runs |
|---|---|---|---|---|
| `<level>` | documented or blocked | agent or person | <the obstacle and what was tried> | `<command, if known>` |

## Run rules

These rules are what make a green result worth trusting.

1. Run the command in this skill as written. Narrow it only when the user asked for a narrower selection, and record the narrowing in the trace.
2. Never add a selection flag the project does not use: `-k`, `--deselect`, `-m`, `--ignore`, `--exclude`, `--grep`, `--testNamePattern`, file paths that drop other tests.
3. Never add a flag that hides work: `--last-failed`, `--failed-first`, `-x` or `--maxfail=1` without being asked, retries, `--no-verify`, `|| true`, `; true`.
4. Never edit a test, fixture, snapshot, or assertion to make it pass.
5. Never add a skip, `only`, xfail, quarantine, or `#[ignore]`.
6. Never weaken an assertion, loosen a tolerance, or relax a matcher.
7. Never mock or stub the module under test, and never replace a dependency with a fake just to get green.
8. Never change product code to make a test pass, unless the user asked for the fix.
9. Temporary changes are limited to environment setup. Declare each one in the trace with its diff and its revert status.
10. A level that cannot run is reported with the blocker and the commands tried. It is never silently omitted or reported as passing.
11. A level counts as passed only when its command was executed in this session and its exit code and counts, where the runner prints one, are in the trace.
12. When a run is red, report the failures and stop. Do not fix the code as part of running the tests.
13. Record `git status --porcelain` and `git diff --stat` before and after the run, and explain every difference.
14. Compare the collected count with the expected count in this skill, and treat a drop as a finding rather than a pass.
15. For an agent-driven level, run the goal, prompt, or rubric as written. Do not rewrite it, raise its budget, or change its model to reach a pass, and record the model, the steps, and the verdict in the trace.
16. An agent-driven verdict counts as a pass only when the runner exits green under its own criteria, and it never replaces a deterministic assertion that exists for the same behavior.
17. Never report a manual level as run. List it as not executed with its checklist location, and hand the checklist to the user.

## Trace

<Paste this skill's `## Trace Template` section here, adapted to this project, and set the default path to `.agents/test-runs/<YYYY-MM-DDTHHMMZ>-<label>.md`. The generated skill must be self-contained: a runner that only loads this skill must still have the full template.>

## When a level is red

<The project-specific first moves: where the logs land, which service to restart, which fixture to reseed, and what evidence to capture before asking for help.>

## What not to touch

<Generated files, committed snapshots, vendored dependencies, and directories that a run must leave alone.>
````

## Example Usage

**Scenario 1: A Python service with unit and integration tests**

```
/create-test-skill
```

Reads `pyproject.toml` and the CI workflow, finds `uv run pytest -q` for unit tests and `uv run pytest -m integration` backed by a Postgres service in CI.
Copies `.env.example` to `.env`, starts Postgres from the compose file, runs migrations, canaries one unit test and one integration test, then runs both levels.
Writes `.agents/skills/test-billing/SKILL.md` with the two levels, the service setup, and the trace rules, and writes the probe trace showing the env copy was made and kept, plus the database created and dropped.

**Scenario 2: A Node app with a Playwright suite**

```
/create-test-skill test-web
```

Discovers `pnpm test` (vitest) and `pnpm test:e2e` (Playwright, web server on port 3000).
Installs the Chromium binary, runs the vitest suite, canaries one Playwright spec because the full run takes 22 minutes, and marks e2e `canary only` in the generated skill with the reason.
The trace records the browser download, the web server command, and that the canary proved the selector rather than the whole flow.

**Scenario 3: A repository with a broken baseline**

```
/create-test-skill
```

Finds a unit suite that currently fails on two tests unrelated to any change.
Records the red baseline with the failure output instead of fixing it, and writes the generated skill so the next runner knows those two failures are pre-existing and must not be hidden by deselecting them.

**Scenario 4: An LLM feature with an eval suite and a manual checklist**

```
/create-test-skill
```

Finds unit tests, an `evals/` suite graded by a model, and a QA checklist for the review flow.
Runs the eval suite under its configured budget, records the model, the pass rate, the verdict, and the cost, and classifies the checklist `manual` with its location.
The generated skill tells the next runner to execute the evals as written, and to hand the checklist to a person instead of counting it as run.

## Failure Modes

| Mode | Response |
|---|---|
| **No test command exists anywhere** | Still write the skill with a single "no automated tests" section naming what was searched, and tell the user the project has no runnable level. Do not invent one. |
| **A level needs credentials or a paid service** | Mark it blocked with the missing prerequisite, and record the canary result if one was possible. |
| **An agent-driven level has no model key** | Mark it blocked with the missing variable name. Do not substitute a different model or a lower budget to make it run. |
| **An agent-driven run is flaky across repeats** | Record each run's verdict and say the level is unstable. Do not keep the best run. |
| **The manual checklist is missing or stale** | Record the level as documented with what exists, and tell the user it needs updating. |
| **The suite is red at the start** | Record the baseline as red with evidence. The generated skill describes the project as found. |
| **A generated command changes between runs** | Prefer the project's own script or make target over a hand-built command, and note the volatility. |
| **The project has no `.agents/` directory** | Create it. Ask before adding it to `.gitignore`. |
| **The existing generated skill has user edits** | Keep them, update only the sections that drifted, and list what changed. |

## Completion Checklist

- [ ] Every level in the generated skill is classified present, canary only, documented, or blocked.
- [ ] Every level records its executor: agent, or person for a manual level.
- [ ] Every command in the generated skill was executed at least once, except the full command of a canary-only level, which is marked `not yet executed` and backed by its canary result.
- [ ] Each level section has setup, run, single-test, expected output, and cleanup.
- [ ] The intent paragraph is present and names the project.
- [ ] The run rules and the trace contract are in the generated skill, not only in this one.
- [ ] Temporary changes are declared with diffs and revert status.
- [ ] The probe trace is written and the generated skill was run once successfully.
- [ ] Changes are confined to `$SKILL_DIR` and `.agents/test-runs/`, apart from reverted environment setup.

