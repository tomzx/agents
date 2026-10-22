---
name: agentic
description: >
  Drive the Agentic app from the command line with the `agentic` CLI: create and
  manage tasks, link Slack/GitHub/Drive/URL/note items to them, work the focus
  stack, link task dependencies and read the graph, register repositories, create
  git worktrees, start and watch agent runs, record agent sessions, manage
  scheduled shell tasks, read the operation audit log, and read or refresh a
  task's agent-maintained summary and next steps. Trigger when the user wants to
  file or update an Agentic task, attach a thread/issue/doc to a task, work or
  inspect the focus stack, spin up a worktree, run an agent against a task,
  schedule a recurring command, refresh task context, or inspect tasks by
  status, tag, deadline, or dependency.
cli: agentic
---

# agentic Skill

`agentic` is the user-facing command-line client for the Agentic app, a local-first task tracker that ties together the Slack threads, GitHub issues/PRs, Drive docs, URLs, and notes that feed a unit of work.
Work is organized around **tasks**; everything else (items, associations, worktrees, runs, sessions, the focus stack, timeline events) hangs off a task.
The CLI is a thin HTTP client over the Agentic API, so it drives the same data the app UI shows, and it emits JSON for scripting.

The app also ships `agentic-server` (the backend). This skill covers only the `agentic` client.

## Command tree

```
agentic
  health
  task        list | deadlines | get | create | update | delete | timeline | link | unlink | deps
  graph
  tag         list
  item        list | get | create | refresh | refresh-due | refresh-source | done | reopen | delete
  link        add | remove
  repository  list | add | remove
  worktree    list | create | remove
  run         list | get | events | create | cancel | wait | stream
  session     list | get | add | update | remove
  context     get | refresh
  harness     list | create | update | delete
  person      list | get | create | update | delete | merge | link | unlink
  change      list | get | create | delete | accept | verify | reject | revert | intervene
  metrics     show | cycle-time | baseline (list | set | delete)
  stack       list | current | history | push | pop | promote | reorder | edit | remove
  schedule    list | get | create | update | run | runs | delete
  operation   list
  settings    get | set | refresh-status
```

Every command takes `--help` (or `-h`) and prints its own options and arguments.

## Global options and output

Global options are accepted on any command (they live on the app, and every leaf command shows them):

| Option | Meaning |
|---|---|
| `--api-url <url>` | API base URL. Default `http://127.0.0.1:8600`. |
| `--format <auto\|json\|text>` | Output format. `auto` (default) uses JSON when stdout is not a terminal, text otherwise. |
| `--timeout <seconds>` | Per-request timeout. Default `60`. |

The CLI reads `AGENTIC_API_URL`, `AGENTIC_FORMAT`, and `AGENTIC_TIMEOUT` at startup, but the current release overwrites all three with the flag defaults before the request runs, so it ignores them (the help advertises `AGENTIC_API_URL` all the same); pass `--api-url`, `--format`, and `--timeout` explicitly.
`AGENTIC_ACTOR` is different: the CLI reads it and sends it to the server, defaulting to `human`.
Set `AGENTIC_ACTOR=agent` to have the server record the work as agent-performed; the run harness sets it automatically for the agent process it spawns.

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
Agent runs need a worker too: `uv run agentic-server worker`.
Point at another instance with `--api-url`.
The API has no authentication, so expose it only on a trusted network.

## Concepts

| Concept | What it is |
|---|---|
| Task | The unit of work. Carries `status`, `priority`, `tags`, a `deadline`, a `summary`, and `next_steps`. |
| Item | Something external: a Slack thread, GitHub issue/PR, Drive doc, URL, note, commit, or file. De-duplicated by URL or external id. |
| Refresh policy | How often the background job re-fetches Slack and GitHub items, given per age bucket (for example `1d=1h,7d=6h,30d=1d,*=7d`). Set with `settings set`. |
| Association | A link between an item and a task (many-to-many), with an optional note. |
| Repository | A local git checkout registered by path. |
| Repository group | A named set of repositories a task's agent should consider. Set on a task with `--group-id`. |
| Worktree | An isolated `git worktree` created for a task from a registered repository. |
| Agent run | One prompt sent to a harness (a coding agent) in a working directory. Its transcript is a stream of events. |
| Agent session | A session recorded against a task by hand (its session id, harness, working directory, and label), for one the app did not start, such as an OpenChamber session. Both runs and sessions produce the links that reopen a session. |
| Context refresh | A special agent run that reads the task and its items and rewrites `summary` and `next_steps`. |
| Change | A unit of factory output recorded against a task and moved through a lifecycle (proposed, verified, accepted, rejected, reverted) so the metrics can be computed from it. |
| Stack entry | A task's place on the focus stack: its position (0 is current), whether it is current, and a soft-delete timestamp. |
| Task session | A stretch of time a stack entry spent as the current task; the stack derives execution count and duration from these. |
| Scheduled task | A shell command the app runs on a 5-field cron schedule, with its run history. |
| Operation | An audit record of a mutating request: its method, path, status, the client that sent it (web, cli, api), and whether a human or an agent was behind it. |
| Person | Someone linked to tasks and items, so a task shows who it is for or about. |

Every meaningful change writes a timeline event, so `agentic task timeline <task>` shows how a task evolved.

## Tasks

```bash
agentic task list                         # most recently updated first
agentic task list --status open
agentic task list --q "flaky"             # substring filter
agentic task list --tag bug --tag ci      # every given tag must match (AND)
agentic task list --format json | jq '.[].id'

agentic task deadlines                    # in-flight tasks due within 7 days, soonest first (overdue included)
agentic task deadlines --within-days 30

agentic task get <task>                    # task plus its items, worktrees, runs, sessions, people, changes, and timeline
agentic task timeline <task>

agentic task create --title "Fix flaky ingest test"
agentic task create --title "Ship feature X" --priority 3 --tags bug --tags ci
agentic task create --title "Ship X" --deadline 2026-11-01
agentic task create --github-url https://github.com/o/r/issues/482   # imports the issue
agentic task create --slack-url https://acme.slack.com/archives/C0123/p1700000000123456   # imports the thread

agentic task update <task> --status in_progress
agentic task update <task> --priority 0 --tags triage
agentic task update <task> --deadline 2026-12-01 --clear-deadline
agentic task create --title "Renew TLS cert" --snooze 2026-11-01   # parked until then
agentic task update <task> --snooze 2026-11-05                     # park until a date or date-time
agentic task update <task> --clear-snooze                          # bring it back now
agentic task update <task> --waiting-on <person> --follow-up 2026-11-05
agentic task update <task> --clear-waiting                         # stop waiting
agentic task update <task> --summary "hand-written summary"

agentic task delete <task>                 # deletes everything attached
```

Statuses: `open`, `in_progress`, `blocked`, `done`, `archived`.
Priorities: `0` low, `1` medium, `2` high (default), `3` urgent.
`--tags` and `--repository-ids` are repeatable; pass `--empty-tags` or `--empty-repository-ids` to clear them.
`create` takes `--group-id` and `--harness-id`; `update` takes `--harness-id` but not `--group-id`.
`--deadline` is an ISO 8601 date or date-time; `update` also takes `--clear-deadline`.
`--snooze` is likewise an ISO 8601 date or date-time: the task leaves the focus stack until then, and `--clear-snooze` brings it back immediately.
`--waiting-on <person>` parks the task until that person acts, forever unless `--follow-up` sets a date to check back; `--clear-waiting` stops waiting.

`task create --github-url` fetches the GitHub issue (via `ghx`), fills the title and description, and links the issue as an item in one call.
`task create --slack-url` fetches the Slack thread, links it, and starts an agent run that names the task and summarizes the discussion (the title stays a placeholder until it finishes).

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
agentic item refresh-due               # re-fetch the Slack/GitHub items the refresh policy says are due
agentic item refresh-source slack      # re-fetch every item of one source now, ignoring the policy
agentic item done <item>               # mark a Slack conversation done (later replies are flagged, not reopened)
agentic item reopen <item>             # clear the done decision
agentic item delete <item>             # deletes the item and its associations
```

The background refresh job re-fetches Slack and GitHub items on a per-age schedule (the refresh policy); `refresh-due` runs that same selection on demand, and `refresh-source` ignores the schedule and refreshes one whole source now.
`done`/`reopen` are for Slack conversations: `done` records the newest message at that moment, so a later reply is flagged rather than silently reopening the thread.

Item sources: `slack`, `github`, `gdrive`, `url`, `note`, `commit`, `file`.
The source is inferred from `--url` or `--content`; pass `--source` to override, and `--external-id` to set the upstream id used for de-duplication.

Link items to a task, either an existing item or a new one created in the same call:

```bash
agentic link add <task> --item-id <item>
agentic link add <task> --url https://github.com/o/r/issues/482 --note "the repro"
agentic link add <task> --content "scratch note"
agentic link remove <task> <item>
```

`link add` with no `--item-id` creates a new item from `--url`, `--content`, or `--title`, then associates it.
Use `--note` to record why the item is attached.

## Dependencies and the graph

Tasks can depend on each other through before/after links, which form a DAG.

```bash
agentic task link <task> <related> --relation before   # <related> must be done first
agentic task link <task> <related> --relation after    # <related> follows <task> (default)
agentic task deps <task>                               # the tasks linked before and after this one
agentic task unlink <task> <related>

agentic graph                        # every in-flight task as a node, plus the edges between them
agentic graph --include-done         # include done and archived tasks
```

`--relation before` means the related task must be done first; `after` means it follows this one.
A link that would close a cycle is refused.
`graph` returns `nodes` (id, title, status, priority) and `edges` (`before_id` -> `after_id`); done and archived tasks are hidden unless you pass `--include-done`.

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
`--model` overrides the harness's model for that run only; leave it unset to let the harness decide.
A run records the session it produced, so `run get` shows the links that reopen it.

## Sessions

A session records an agent session against a task by hand, for one the app did not start, such as an OpenChamber session.
`run get` and `session get` both expose the links that reopen a session: OpenChamber, a terminal template, and the harness's resume command.

```bash
agentic session list <task>
agentic session add <task> <agent-session-id> --harness-id opencode --cwd /home/me/src/myrepo --label "investigation"
agentic session get <task> <record-id>          # shows the recorded session and how to reopen it
agentic session update <task> <record-id> --label "renamed"
agentic session remove <task> <record-id>       # removes the record only; the session itself is untouched
```

Mind the two ids: `session add` takes the agent's session id (the one the harness reports), while `get`, `update`, and `remove` take the recorded session's id (the first column of `session list`).
`session add` defaults the harness to the task's harness.

## Task context

The summary and next steps are agent-maintained and make resuming a task quick.

```bash
agentic context get <task>        # current summary and next steps
agentic context refresh <task>    # starts a refresh_context run that rewrites them
```

`context refresh` returns a run; watch it with `run wait` or `run stream`.

## Focus stack

The focus stack is the current task plus the queue below it, so you work one thing at a time.
The app materializes the stack from in-flight tasks: every task that is open, in progress, or blocked and has never been on the stack joins at the bottom automatically.

```bash
agentic stack list                 # the stack, current task first
agentic stack current              # the current task (the top of the stack)
agentic stack history              # soft-deleted entries, most recent first

agentic stack push --title "Fix the flaky test"          # add a new task on top (position default)
agentic stack push --task-id <task> --position next      # add an existing task after the current one
agentic stack push --task-id <task> --position last      # add it at the bottom

agentic stack pop                  # mark the current task done and promote the next one
agentic stack promote <entry>      # move an entry to the top (make it current)
agentic stack reorder <entry> 2    # move an entry to position 2 (0 is current)
agentic stack edit <entry> --title "Better title" --description "..."
agentic stack remove <entry>       # soft delete the entry; the task is kept
```

`--position` is `top` (becomes current), `next` (after the current task), or `last` (the bottom).
`pop` marks the task `done`; `remove` only takes it off the stack and leaves the task as it was.
A task you popped or removed keeps its soft-deleted entry, so it is not re-added automatically; push it again to bring it back.
Each entry's text line shows its execution count and total time as the current task.

## Harnesses

```bash
agentic harness list              # id, whether the command is on PATH, and which is the default (marked *)
agentic harness create myagent opencode --args acp --model gpt-x --resume-command "opencode --session {session}"
agentic harness update <harness> --model other-model
agentic harness delete <harness>
```

A harness is a coding-agent process reachable over ACP (Agent Client Protocol).
`opencode2` (`opencode2 acp`) is seeded as the default when installed, otherwise `opencode` (`opencode acp`); `pi` (via `pi-acp`) is also seeded.
`harness list` marks each harness `available` or `missing` by looking its command up on PATH.
`--resume-command` is the template that builds a session's resume link (placeholders `{session}`, `{cwd}`, `{harness}`).
`--model` sets the model the harness uses, and `--default-model-source` names the JSON file and `{dotted.path}` template (`<file>#<template>`) the app reads to display the harness's own default model.

## Changes and metrics

A **change** is the unit of factory output the metrics are computed from. Record one per piece of work that reaches production, move it through its lifecycle, and record the human interventions it needed.

```bash
agentic change create <task> --title "Fix flaky ingest test"
agentic change create <task> --title "Add retry" --change-class bugfix --external-ref <sha>
agentic change create <task> --title "Add retry" --repository-id <repository> --worktree-id <worktree>

agentic change list                          # newest first
agentic change list --task-id <task> --status accepted --change-class bugfix
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
Any intervention (including an approval) marks the change non-touchless, which lowers the autonomy rate.

The metrics read those records:

```bash
agentic metrics show                         # autonomy rate and yield vs their baselines
agentic metrics show --window-days 30 --observation-days 14 --tolerance 0.02
agentic metrics show --task-id <task> --change-class bugfix

agentic metrics cycle-time                    # issue close, review wait, and review-to-merge trends per repository
agentic metrics cycle-time --days 30 --bucket-days 7 --refresh
agentic metrics cycle-time --repository <repository>

agentic metrics baseline list
agentic metrics baseline set autonomy_rate 0.2 --note "before the factory run"
agentic metrics baseline set yield 0.8
agentic metrics baseline delete autonomy_rate
```

- **Autonomy rate** is the share of accepted changes that needed no human intervention.
- **Yield** is the share of accepted changes that survived the observation window without being reverted.
- `metrics show` reports each metric's direction (`improving`, `worsening`, `flat`, `no-baseline`, or `no-data`) against its stored baseline; `--tolerance` sets the flat band.
- `metrics cycle-time` reads each repository's GitHub activity and reports issue-close, review-wait, and review-to-merge trends.
  It makes one request per repository with a GitHub remote; use `--repository` to scope it to one.
  `--days` (default 90) sets the window, `--bucket-days` (default 7) the bucket size, and `--refresh` bypasses the cache.
- `metrics baseline set <metric> <value>` takes a metric of `autonomy_rate` or `yield`.

## People

Link people to tasks and items so a task shows who it is for or about.

```bash
agentic person list
agentic person get <person>

agentic person create --name "Alice Smith" --aliases alice --aliases alice@example.com
agentic person update <person> --notes "owns ingest"
agentic person update <person> --aliases alice   # replaces the whole alias list
agentic person merge <person> --into <person>    # absorbs the source's aliases and links
agentic person delete <person>                   # deletes the person and their links

agentic person link <person> --task <task>
agentic person link <person> --item <item>
agentic person link <person> --requested-by <task>     # mark them as the task's requester
agentic person unlink <person> --task <task>
```

`--aliases` is repeatable (a handle or email); on `update` it replaces the whole list.
`merge` folds one person into another, moving their aliases and links.
`person link`/`unlink` take exactly one of `--task`, `--item`, or `--requested-by` (the task the person asked for).
`person get` shows what the person is linked to, and `task get` also lists the task's people.

## Operations (audit log)

Every mutating API request is recorded with the client that sent it and whether a human or an agent was behind it.

```bash
agentic operation list                       # newest first, up to 100 by default
agentic operation list --client cli --actor agent
agentic operation list --limit 500
```

`--client` is `web`, `cli`, or `api`; `--actor` is `human` or `agent`.
This covers operations with no task to hang a timeline event off (settings, repositories, harnesses, people), so it is the cross-cutting view of how work entered the system.

## Scheduled tasks

A scheduled task runs a shell command on a cron schedule inside the app, separate from agent runs. Each keeps its run history.

```bash
agentic schedule list                       # soonest next run first
agentic schedule get <schedule>
agentic schedule runs                       # run history for every task, newest first
agentic schedule runs --schedule-id <schedule> --limit 50

agentic schedule create "nightly" "npm test" "0 3 * * *"
agentic schedule create "digest" "uv run digest" "0 9 * * 1-5" --cwd /home/me/src/repo --timezone Europe/Paris
agentic schedule create "paused" "make audit" "0 0 1 * *" --disabled

agentic schedule update <schedule> --schedule "30 4 * * *"
agentic schedule update <schedule> --disable
agentic schedule update <schedule> --enable

agentic schedule run <schedule>             # run it now, in the background
agentic schedule delete <schedule>          # deletes the task and its run history
```

`create` takes `NAME`, `COMMAND`, and a 5-field cron `SCHEDULE` (minute hour day-of-month month day-of-week).
`--cwd` defaults to the server's directory and `--timezone` to the server's zone; `--disabled` creates the task paused.
`update` also takes `--name`, `--command`, `--cwd`, and `--timezone`, and `--enable`/`--disable`.

## Settings

```bash
agentic settings get
agentic settings refresh-status               # when the background refresh job last ran, per source

agentic settings set --openchamber-url http://box:3001
agentic settings set --openchamber-session-path "/?session={session}"
agentic settings set --terminal-url-template "https://terminal.example/?cwd={cwd}"
agentic settings set --openchamber-url ""     # empty string disables the link

agentic settings set --slack-refresh-policy "1d=1h,7d=6h,30d=1d,*=7d"
agentic settings set --github-refresh-policy "1d=1h,7d=6h"

agentic settings set --ghx-backend rpc --ghx-rpc-url http://box:8010
agentic settings set --ghx-backend cli
agentic settings set --slackx-backend rpc --slackx-rpc-url http://box:8011 --slackx-rpc-token secret
```

`settings set` handles the three session-link settings (`--openchamber-url`, `--openchamber-session-path`, `--terminal-url-template`), the two refresh policies (`--slack-refresh-policy`, `--github-refresh-policy`), and how the server runs ghx and slackx (`--ghx-backend`, `--ghx-rpc-url`, `--ghx-rpc-token`, `--slackx-backend`, `--slackx-rpc-url`, `--slackx-rpc-token`); an empty string disables a link or a source's refresh.
A backend is `cli` (spawn the binary per call) or `rpc` (call its JSON-RPC server); the URL is the server's base and the endpoint is `<url>/rpc`.
A refresh policy is a comma-separated list of `age=interval` buckets from newest to oldest age, with `*` as the catch-all.
`settings refresh-status` shows when the background refresh job last ran for each source.
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

**Work the focus stack.**

```bash
agentic stack list
agentic stack push --title "Next thing to do"
agentic stack pop                  # finish the current task and move on
```

**Attach a session you opened elsewhere.**

```bash
agentic session add <task> <agent-session-id> --cwd /home/me/src/myrepo --label "openchamber"
agentic session get <task> <record-id>    # the links that reopen it
```

## Safety

Several commands have side effects beyond the database. Confirm the target and intent with the user before running them.

- `task delete <task>` removes the task's worktrees from disk (best effort) and deletes its associations, worktrees, runs, transcript events, sessions, changes, and timeline. There is no undo.
- `worktree remove <task> <worktree>` runs `git worktree remove --force` and prunes; any uncommitted changes in that worktree are lost.
- `repository remove <repository>` removes that repository's worktrees from disk (best effort) before untracking it; the main checkout stays in place, but uncommitted changes in its worktrees are lost.
- `stack pop` marks the current task `done`; `stack push --title` creates a task; `stack remove` only takes the entry off the stack (the task is kept).
- `run create` and `context refresh` start a coding agent, which can edit files and run commands, and permissions are auto-approved by default. State the prompt and the working directory before starting.

## Tips

- Start a session with `agentic health`, then `agentic task list --format json` to see current work.
- Pipe to `jq` for scripting; the CLI emits JSON whenever stdout is not a terminal.
- `task get` already includes items, worktrees, runs, sessions, people, changes, and timeline, so prefer it over several list calls.
- Whether an item carries useful content depends on the fetch; if `content` is empty, run `agentic item refresh <item>`.
- `run wait` returns once the run reaches `succeeded`, `failed`, or `cancelled`; on timeout it prints the still-running state instead of failing.
- `task create` imports a GitHub issue via `ghx`; if the import fails, create the task by title and link the issue with `link add --url`.
- Set `AGENTIC_ACTOR=agent` so the server records your mutations as agent-performed in the timeline and the operations log.

## Wrap up

After completing the user's request, summarise:

1. Which task(s) were touched, by id and title.
2. Which items, worktrees, or runs were created, with their ids.
3. Any agent run started, its run id and final status.
