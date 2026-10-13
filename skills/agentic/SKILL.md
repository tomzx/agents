---
name: agentic
description: >
  Drive the Agentic app from the command line with the `agentic` CLI: create and
  manage tasks, link Slack/GitHub/Drive/URL/note items to them, register
  repositories, create git worktrees, start and watch agent runs, and read or
  refresh a task's agent-maintained summary and next steps. Trigger when the user
  wants to file or update an Agentic task, attach a thread/issue/doc to a task,
  spin up a worktree, run an agent against a task, refresh task context, or
  inspect tasks by status or tag.
cli: agentic
---

# agentic Skill

`agentic` is the user-facing command-line client for the Agentic app, a local-first task tracker that ties together the Slack threads, GitHub issues/PRs, Drive docs, URLs, and notes that feed a unit of work.
Work is organized around **tasks**; everything else (items, associations, worktrees, agent runs, timeline events) hangs off a task.
The CLI is a thin HTTP client over the Agentic API, so it drives the same data the app UI shows, and it emits JSON for scripting.

The app also ships `agentic-server` (the backend). This skill covers only the `agentic` client.

## Command tree

```
agentic
  health
  task        list | get | create | update | delete | timeline
  tag         list
  item        list | get | create | refresh | delete
  link        add | remove
  repository  list | add | remove
  worktree    list | create | remove
  run         list | get | events | create | cancel | wait | stream
  context     get | refresh
  harness     list | create | update | delete
  person      list | get | create | update | delete | link | unlink
  change      list | get | create | delete | accept | verify | reject | revert | intervene
  metrics     show | baseline (list | set | delete)
  settings    get | set
```

Every command takes `--help` (or `-h`) and prints its own options and arguments.

## Global options and output

Global options are accepted on any command (they live on the app, and every leaf command shows them):

| Option | Meaning |
|---|---|
| `--api-url <url>` | API base URL. Default `http://127.0.0.1:8600`. |
| `--format <auto\|json\|text>` | Output format. `auto` (default) uses JSON when stdout is not a terminal, text otherwise. |
| `--timeout <seconds>` | Per-request timeout. Default `60`. |

The CLI help also advertises `AGENTIC_API_URL`, `AGENTIC_FORMAT`, and `AGENTIC_TIMEOUT`, but the current release ignores them (the flags always win), so pass the flags explicitly.

Output is JSON when piped, so `agentic task list | jq` works without a flag.
Pass `--format text` for the human-readable form (one line per task/item/run) even when piped.

## Prerequisites

### Binary

Check whether the binary is on PATH; install it as a uv tool from the CLI package if not:

```bash
if ! command -v agentic &>/dev/null; then
  uv tool install -e /path/to/agentic/cli   # -e links the working tree
fi
```

Confirm it works: `agentic --help`.

### Server

The CLI talks to a running API. Check it before anything else:

```bash
agentic health          # -> ok (agentic) at http://127.0.0.1:8600
```

If it fails, start the backend from the repository root: `uv run agentic-server serve --host 0.0.0.0 --port 8600`.
Point at another instance with `--api-url`.
The API has no authentication, so expose it only on a trusted network.

## Concepts

| Concept | What it is |
|---|---|
| Task | The unit of work. Carries `status`, `priority`, `tags`, a `summary`, and `next_steps`. |
| Item | Something external: a Slack thread, GitHub issue/PR, Drive doc, URL, note, commit, or file. De-duplicated by URL or external id. |
| Association | A link between an item and a task (many-to-many), with an optional note. |
| Repository | A local git checkout registered by path. |
| Repository group | A named set of repositories a task's agent should consider. Set on a task with `--group-id`. |
| Worktree | An isolated `git worktree` created for a task from a registered repository. |
| Agent run | One prompt sent to a harness (a coding agent) in a working directory. Its transcript is a stream of events. |
| Context refresh | A special agent run that reads the task and its items and rewrites `summary` and `next_steps`. |
| Change | A unit of factory output recorded against a task and moved through a lifecycle (proposed, verified, accepted, rejected, reverted) so the metrics can be computed from it. |
| Person | Someone linked to tasks and items, so a task shows who it is for or about. |

Every meaningful change writes a timeline event, so `agentic task timeline <task>` shows how a task evolved.

## Tasks

```bash
agentic task list                         # most recently updated first
agentic task list --status open
agentic task list --q "flaky"             # substring filter
agentic task list --tag bug --tag ci      # every given tag must match (AND)
agentic task list --format json | jq '.[].id'

agentic task get <task>                    # task plus its items, worktrees, runs, and timeline
agentic task timeline <task>

agentic task create --title "Fix flaky ingest test"
agentic task create --title "Ship feature X" --priority 3 --tags bug --tags ci
agentic task create --github-url https://github.com/o/r/issues/482   # imports the issue

agentic task update <task> --status in_progress
agentic task update <task> --priority 0 --tags triage
agentic task update <task> --summary "hand-written summary"

agentic task delete <task>                 # deletes everything attached
```

Statuses: `open`, `in_progress`, `blocked`, `done`, `archived`.
Priorities: `0` low, `1` medium, `2` high (default), `3` urgent.
`--tags` and `--repository-ids` are repeatable; pass `--empty-tags` or `--empty-repository-ids` to clear them.
`create` takes `--group-id` and `--harness-id`; `update` takes `--harness-id` but not `--group-id`.

`task create --github-url` fetches the GitHub issue (via `ghx`), fills the title and description, and links the issue as an item in one call.

## Items and links

```bash
agentic item list
agentic item list --source github
agentic item get <item>
agentic item create --url https://github.com/o/r/issues/482
agentic item create --url https://acme.slack.com/archives/C0123/p1700000000123456
agentic item create --content "Remember to rotate the token"   # a note
agentic item create --url <url> --no-fetch                      # store without fetching
agentic item refresh <item>            # re-fetch metadata and content
agentic item delete <item>             # deletes the item and its associations
```

Item sources: `slack`, `github`, `gdrive`, `url`, `note`, `commit`, `file`.
The source is inferred from `--url` or `--content`; pass `--source` to override.

Link items to a task, either an existing item or a new one created in the same call:

```bash
agentic link add <task> --item-id <item>
agentic link add <task> --url https://github.com/o/r/issues/482 --note "the repro"
agentic link add <task> --content "scratch note"
agentic link remove <task> <item>
```

`link add` with no `--item-id` creates a new item from `--url`, `--content`, or `--title`, then associates it.
Use `--note` to record why the item is attached.

## Repositories and worktrees

```bash
agentic repository list
agentic repository add /home/me/src/myrepo
agentic repository add /home/me/src/myrepo --name myrepo
agentic repository remove <repository>     # removes its worktrees from disk, then untracks
```

Worktrees are per task:

```bash
agentic worktree list <task>
agentic worktree create <task>                                  # defaults to one of the task's repositories
agentic worktree create <task> --repository-id <repository> --branch fix/ingest --base main
agentic worktree remove <task> <worktree>                       # git worktree remove --force, then prune
```

There is no CLI command for repository groups; set `--group-id` at task creation and manage groups in the app.

## Agent runs

```bash
agentic run create <task> --prompt "Investigate the failing test"
agentic run create <task> --worktree-id <worktree> --prompt "Implement the fix"
agentic run create <task> --cwd /home/me/src/myrepo --harness-id opencode --prompt "Summarize the repo"

agentic run list <task>
agentic run get <run-id>          # includes session_id, cwd, and session links
agentic run events <run-id>       # full transcript
agentic run stream <run-id>       # live: JSON lines when piped, text on a TTY; stops at run_finished
agentic run wait <run-id>         # polls every --interval (default 2s) up to --timeout (default 600s)
agentic run cancel <run-id>
```

Run statuses: `queued`, `running`, `succeeded`, `failed`, `cancelled`.
Run kinds: `chat` (a normal prompt) and `refresh_context` (started by `context refresh`).
Transcript event types a run streams include `message`, `thought`, `user`, `tool_call`, `tool_update`, `plan`, `usage`, `info`, `permission`, and `error`; `run stream` stops when it sees `run_finished`.

`run create` picks the working directory in this order: `--cwd`, then `--worktree-id`, then a default worktree or the task's first repository.
Leave `--harness-id` unset to use the task's harness, then the app default.

## Task context

The summary and next steps are agent-maintained and make resuming a task quick.

```bash
agentic context get <task>        # current summary and next steps
agentic context refresh <task>    # starts a refresh_context run that rewrites them
```

`context refresh` returns a run; watch it with `run wait` or `run stream`.

## Harnesses

```bash
agentic harness list              # id, whether the command is on PATH, and its path
agentic harness create myagent opencode --args acp --model gpt-x
agentic harness update <harness> --model other-model
agentic harness delete <harness>
```

A harness is a coding-agent process reachable over ACP (Agent Client Protocol); `opencode acp` is the default and `pi-acp` is also seeded.
`harness list` marks each harness `available` or `missing` by looking its command up on PATH.

## Changes and metrics

A **change** is the unit of factory output the metrics are computed from. Record one per piece of work that reaches production, move it through its lifecycle, and record the human interventions it needed.

```bash
agentic change create <task> --title "Fix flaky ingest test"
agentic change create <task> --title "Add retry" --change-class bugfix --external-ref <sha>

agentic change list                          # newest first
agentic change list --task-id <task> --status accepted
agentic change get <change>                  # includes its interventions

agentic change verify <change>               # verified
agentic change accept <change>               # reached production
agentic change reject <change>               # rejected before acceptance
agentic change revert <change>               # an accepted change that did not survive

agentic change intervene <change> --kind correction --note "fixed the migration by hand"
agentic change delete <change>               # deletes the change and its interventions
```

Change classes: `feature`, `bugfix`, `refactor`, `chore`, `docs`, `test`, `trivial`.
Statuses: `proposed`, `verified`, `accepted`, `rejected`, `reverted`.
`change create` starts `proposed`; `verify`, `accept`, `reject`, and `revert` move it and stamp the transition time.
`change intervene --kind` is one of `question`, `correction`, `manual_fix`, `rerun`, `approval`, `other`.
Any intervention (including an approval) marks the change human-intervened, which lowers the autonomy rate.

The metrics read those records:

```bash
agentic metrics show                         # autonomy rate and yield vs their baselines
agentic metrics show --window-days 30 --observation-days 14 --tolerance 0.02
agentic metrics show --task-id <task> --change-class bugfix

agentic metrics baseline list
agentic metrics baseline set autonomy_rate 0.2 --note "before the factory run"
agentic metrics baseline set yield 0.8
agentic metrics baseline delete autonomy_rate
```

- **Autonomy rate** is the share of accepted changes that needed no human intervention.
- **Yield** is the share of accepted changes that survived the observation window without being reverted.
- `metrics show` reports each metric's direction (`improving`, `worsening`, `flat`, `no-baseline`, or `no-data`) against its stored baseline; `--tolerance` sets the flat band.
- `metrics baseline set <metric> <value>` takes a metric of `autonomy_rate` or `yield`.

## People

Link people to tasks and items so a task shows who it is for or about.

```bash
agentic person list
agentic person get <person>

agentic person create --name "Alice Smith" --handle alice --email alice@example.com
agentic person update <person> --notes "owns ingest"
agentic person delete <person>               # deletes the person and their links

agentic person link <person> --task <task>
agentic person link <person> --item <item>
agentic person unlink <person> --task <task>
```

`person link`/`unlink` take exactly one of `--task` or `--item`. `person get` shows what the person is linked to, and `task get` also lists the task's people.

## Settings

```bash
agentic settings get
agentic settings set --openchamber-url http://box:3001
agentic settings set --openchamber-session-path "/?session={session}"
agentic settings set --terminal-url-template "https://terminal.example/?cwd={cwd}"
agentic settings set --openchamber-url ""     # empty string disables the link
```

`settings set` handles the three session-link settings only.
`settings get` also shows `editor_url_template`, which is set in the app, not the CLI.

## Common workflows

**File a task from a GitHub issue.**

```bash
agentic task create --github-url https://github.com/o/r/issues/482 --tags bug
agentic context refresh <task>
```

**Attach evidence to a task.**

```bash
agentic link add <task> --url https://acme.slack.com/archives/C0123/p1700000000123456
agentic link add <task> --url https://github.com/o/r/pull/77 --note "the fix"
```

**Start work on a task.**

```bash
agentic repository add /home/me/src/myrepo
agentic worktree create <task> --branch fix/482
agentic run create <task> --worktree-id <worktree> --prompt "Fix issue 482 and run the tests"
agentic run wait <run-id>
agentic task update <task> --status in_progress
```

## Safety

Four commands have side effects beyond the database. Confirm the target and intent with the user before running them.

- `task delete <task>` removes the task's worktrees from disk (best effort) and deletes its associations, worktrees, runs, transcript events, and timeline. There is no undo.
- `worktree remove <task> <worktree>` runs `git worktree remove --force` and prunes; any uncommitted changes in that worktree are lost.
- `repository remove <repository>` removes that repository's worktrees from disk (best effort) before untracking it; the main checkout stays in place, but uncommitted changes in its worktrees are lost.
- `run create` and `context refresh` start a coding agent, which can edit files and run commands, and permissions are auto-approved by default. State the prompt and the working directory before starting.

## Tips

- Start a session with `agentic health`, then `agentic task list --format json` to see current work.
- Pipe to `jq` for scripting; the CLI emits JSON whenever stdout is not a terminal.
- `task get` already includes items, worktrees, runs, timeline, and people, so prefer it over several list calls.
- Whether an item carries useful content depends on the fetch; if `content` is empty, run `agentic item refresh <item>`.
- `run wait` returns once the run reaches `succeeded`, `failed`, or `cancelled`; on timeout it prints the still-running state instead of failing.
- `task create` imports a GitHub issue via `ghx`; if the import fails, create the task by title and link the issue with `link add --url`.

## Wrap up

After completing the user's request, summarise:

1. Which task(s) were touched, by id and title.
2. Which items, worktrees, or runs were created, with their ids.
3. Any agent run started, its run id and final status.
