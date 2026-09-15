---
name: select-issue
description: Select the next issue to work on from a GitHub project's priority view, constrained to work also planned in the roadmap view. Use when the user says /select-issue, "what should I work on", "pick the next issue", or wants the next planned high-priority issue.
allowed-tools: Bash(gh:*, ghx:*, ~/.agents/scripts/get-env:*), Read
argument-hint: "[owner/project-number] [priority-view] [roadmap-view]"
---

# Select Issue

Reads a GitHub Project (V2) and selects the next issue to work on by intersecting two project views:
1. A **priority view** (board or table grouped or sorted by priority), which ranks issues by priority.
2. A **roadmap view** (timeline grouped by an iteration or date field), which confirms the work is scheduled.

The selected issue is the highest-priority open issue that is also scheduled (planned) in the roadmap. This avoids working on high-priority-but-unplanned items and on planned-but-low-priority items.

## Prerequisites

- `gh` CLI authenticated with read access to the project and its linked repositories
- The `gh` token must have the `read:project` scope (project fields and items require it). Refresh with `gh auth refresh -s read:project` if queries return `INSUFFICIENT_SCOPES`
- A GitHub Project (V2) that has a priority view and a roadmap view
- Project in `owner/number` format (`$1`), or omit to use `GITHUB_PROJECT` from `.env`
- Priority view name (`$2`), or omit to use `PRIORITY_VIEW` from `.env`, defaulting to `Priority`
- Roadmap view name (`$3`), or omit to use `ROADMAP_VIEW` from `.env`, defaulting to `Roadmap`

## Resolution rules

1. Project: `$1` overrides the `GITHUB_PROJECT` env var.
2. Priority view: `$2` overrides the `PRIORITY_VIEW` env var, which overrides the default `Priority`.
3. Roadmap view: `$3` overrides the `ROADMAP_VIEW` env var, which overrides the default `Roadmap`.

## Workflow

```
Fetch project: fields, views, items (one GraphQL query)
         |
         v
Identify priority field (priority view group-by, else by name)
         |
         v
Identify roadmap scheduling field (iteration or date)
         |
         v
Build candidates: open, non-draft issues
         |
         v
For each candidate read: priority value + roadmap value
         |
         v
Filter to "planned": current or future roadmap slot
         |
         v
Sort: priority (field option order), then roadmap (soonest)
         |
         v
Select top candidate -> recommendation
```

## Priority ordering

The priority order is the **order of options defined on the priority single-select field**, matching the columns shown in the priority view. The first option is the highest priority.

If the option order cannot be read from the field, fall back to name-based ranking:

| Rank | Option name patterns (highest first) |
|---|---|
| 1 | urgent, p0, critical, blocker |
| 2 | high, p1 |
| 3 | medium, p2, normal |
| 4 | low, p3, backlog |

## Roadmap scheduling

A candidate is "planned" when its roadmap field value is scheduled for now or soon:

- **Iteration field**: assigned to the current iteration (whose range contains today) or a future iteration. Items in completed iterations, or unassigned, are not planned.
- **Date field** (start, end, or due): the date falls within today through a near-term window (default: next 4 weeks). Unset dates are not planned.

If the project has no detectable roadmap field, treat all items as planned, rank by priority alone, and note that no roadmap constraint was applied.

## Steps

### 1. Resolve inputs

```
PROJECT="${1:-$(~/.agents/scripts/get-env GITHUB_PROJECT)}"
PRIORITY_VIEW="${2:-$(~/.agents/scripts/get-env PRIORITY_VIEW)}"; PRIORITY_VIEW="${PRIORITY_VIEW:-Priority}"
ROADMAP_VIEW="${3:-$(~/.agents/scripts/get-env ROADMAP_VIEW)}"; ROADMAP_VIEW="${ROADMAP_VIEW:-Roadmap}"
```

Split `PROJECT` into `OWNER` and `NUMBER` on the `/`. If `PROJECT` is empty, stop and ask the user to pass `owner/number`.

### 2. Fetch the project in one query

Pull fields, views, and items together. `repositoryOwner` works for both user and organization owners:

```
gh api graphql -f query='query($owner: String!, $number: Int!) {
  repositoryOwner(login: $owner) {
    ... on ProjectV2Owner {
      projectV2(number: $number) {
        title
        fields(first: 50) {
          nodes {
            ... on ProjectV2SingleSelectField { id name options { id name } }
            ... on ProjectV2IterationField {
              id name
              configuration {
                iterations { id title startDate duration }
                completedIterations { id title startDate duration }
              }
            }
          }
        }
        views(first: 30) { nodes { name layout } }
        items(first: 100) {
          nodes {
            id
            content {
              ... on Issue { number title state url labels(first:10){nodes{name}} repository { nameWithOwner } }
            }
            fieldValues(first: 30) {
              nodes {
                ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } }
                ... on ProjectV2ItemFieldIterationValue { title startDate duration field { ... on ProjectV2FieldCommon { name } } }
                ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
                ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
              }
            }
          }
        }
      }
    }
  }
}' -f owner="$OWNER" -F number="$NUMBER"
```

For projects with more than 100 items, paginate the `items` connection with the `after` cursor until exhausted.

### 3. Identify the priority field

Primary: find a single-select field whose name matches `/priority/i` (for example, `Priority`, `Prio`). Store its option list in the order returned, since the first option is the highest priority. If several match, prefer the one whose options look like priority levels (urgent, high, medium, low, p0-p3).

If the priority view exists in the fetched views but no priority field matches by name, list the single-select fields found and ask the user which one ranks priority.

### 4. Identify the roadmap scheduling field

Pick the field the roadmap view uses for its timeline:

1. Prefer an iteration field (any field of type `ProjectV2IterationField`).
2. Else a date field whose name matches `/(start|end|due|date)/i`.

Store its iteration configuration (start dates and durations) so a candidate's slot can be compared against today.

### 5. Build and rank candidates

For each project item whose `content` is an `Issue`:

- Skip closed issues (`state` is not `OPEN`). Draft project items are a separate `DraftIssue` content type, so matching `... on Issue` already excludes them.
- Read the priority value (the single-select value whose field name matches the priority field).
- Read the roadmap value (the iteration or date value whose field name matches the roadmap field).

Then:

1. **Planned filter**: keep only items whose roadmap value is current or future (see Roadmap scheduling). If no roadmap field exists, keep all.
2. **Sort**: priority option index ascending (highest priority first), then roadmap start date ascending (soonest first).

### 6. Select and recommend

Take the top candidate. If no candidate is planned, fall back to the highest-priority open issue overall and note that nothing is currently scheduled in the roadmap.

Present the recommendation, the candidates considered, and the next step.

## Output Format

```markdown
## Selected Issue

- **Issue**: #42 - Add OAuth login refresh token flow (<url>)
- **Repository**: owner/repo
- **Priority**: High (option 2 of 4)
- **Roadmap**: Iteration "Sprint 24" (Jun 24 to Jul 7), starts in 2 days
- **Labels**: feature, area:auth

### Why this issue
<one or two sentences: highest priority among issues scheduled in the current or next roadmap slot>

### Candidates considered
| Issue | Title | Priority | Roadmap | Planned |
|---|---|---|---|---|
| #42 | Add OAuth login refresh token flow | High | Sprint 24 | yes |
| #38 | Retry failed webhooks | High | Sprint 24 | yes |
| #51 | Migrate config to TOML | Urgent | unassigned | no |

### Next step
- If this is a bug: `/reproduce-issue 42 owner/repo`
- If this is a feature: `/create-implementation` or `/sdlc` starting at create-issue
```

## Example Usage

**Scenario 1: Default project from .env**
```
/select-issue
```
Reads `GITHUB_PROJECT`, `PRIORITY_VIEW`, and `ROADMAP_VIEW` from `.env`. Selects the highest-priority issue scheduled in the current roadmap iteration.

**Scenario 2: Explicit project**
```
/select-issue myorg/5
```
Uses project 5 owned by `myorg` with default view names `Priority` and `Roadmap`.

**Scenario 3: Custom view names**
```
/select-issue myorg/5 "Triage Board" "Timeline"
```
Uses the named views instead of the defaults.

**Scenario 4: Nothing planned**
```
/select-issue myorg/5
```
All high-priority issues are unscheduled. Falls back to the highest-priority open issue and notes the roadmap gap.

## Relationship to other skills

- Pair with **start-day** or **start-week** to turn the selected issue into a concrete focus block.
- After selecting, continue with **reproduce-issue** (bugs), **create-implementation** (features), or the **sdlc** orchestrator.
- This skill is read-only and does not post to GitHub, so it needs no `github-post-attribution` footer.

## Useful Commands Reference

| Command | Description |
|---|---|
| `~/.agents/scripts/get-env GITHUB_PROJECT` | Read default project `owner/number` from `.env` |
| `~/.agents/scripts/get-env PRIORITY_VIEW` | Read default priority view name from `.env` |
| `~/.agents/scripts/get-env ROADMAP_VIEW` | Read default roadmap view name from `.env` |
| `gh api graphql -f query='...' -f owner=<o> -F number=<n>` | Fetch project fields, views, and items in one query |
| `gh project item-list --owner <o> --project <n>` | Lower-level item list fallback (no custom field values) |
