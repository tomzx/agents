# Planning Diagrams Reference

Diagrams for schedules, roadmaps, hierarchies of intent, and process ownership.

## Gantt (`gantt`)

```
gantt
    title Release plan
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Build
    Design      :done,    des1, 2026-01-01, 2026-01-10
    Implement   :active,  des2, after des1, 20d
    section Test
    QA          :         des3, after des2, 10d
    Milestone   :milestone, m1, after des3, 0d
```

- Task line: `Task name :tags, id, start, duration-or-end`.
- Status tags: `done`, `active`, `crit`; `milestone` marks zero-length events.
- Start dates: absolute (`2026-01-01`), `after id`, or `after id1 id2`; durations in `Nd`, `Nw`, or an end date.
- Dependencies: `Implement : des2, after des1, 20d`; explicit `excludes weekends` config, `excludes` dates at the top.
- Config via front matter: `dateFormat`, `axisFormat` (strftime), `tickInterval`, `todayMarker`.

## Timeline (`timeline`)

```
timeline
    title Product history
    section 2024
        Launch : Beta release
                : First customers
    section 2025
        Growth : 10k users : Mobile app
```

- Periods (time periods or section headers) each own one or more `: event` entries; multiple events stack vertically.
- `section Name` groups periods horizontally.
- Icons and classes are experimental; skip them unless asked.

## Kanban (`kanban`)

```
kanban
    columnId1[Todo]
        taskId1[Write docs]@{ priority: High, assigned: tom }
        taskId2[Review PR]
    columnId2[Done]
        taskId3[Ship release]@{ done: true }
```

- `columnId[Column Title]` declares a column; tasks are indented `taskId[Description]`.
- Task metadata via `@{ key: value, ... }`: `priority`, `assigned`, `icon`, `created`/`updated` timestamps, `done` on the column or task.
- Configure tags with a `config` front matter block under the `kanban` key.

## Mindmap (`mindmap`)

```
mindmap
  root((Product))
    Backend
      API
      Workers
    Frontend
      Web
      Mobile
```

- Hierarchy is indentation only (spaces or tabs); a child is anything more indented than its parent.
- Node shapes reuse flowchart shapes: `[square]`, `(rounded)`, `((circle))`, `))bang((`, `)cloud(`, `{{hexagon}}`.
- Icons and classes via `::icon(fa fa-book)` lines are experimental; prefer plain text labels.

## Git Graphs (`gitGraph`)

```
gitGraph
    commit id: "init"
    branch develop
    commit id: "feat A"
    checkout main
    merge develop tag: "v1.0.0"
    branch hotfix
    commit id: "fix" type: REVERSE
    checkout main
    cherry-pick id: "fix"
```

- `commit` options: `id`, `tag`, `type` (`NORMAL`, `REVERSE`, `HIGHLIGHT`).
- `branch name` and `checkout name` move context; `merge name` merges into the current branch; `cherry-pick id:` copies a commit.
- Horizontal lanes form per branch automatically; keep strategies readable by ordering branch/checkout calls chronologically.

## User Journey (`journey`)

```
journey
    title Ordering coffee
    section Order
      Browse menu: 5: Customer
      Ask a question: 2: Customer: Barista
    section Pay
      Pay at counter: 4: Customer: Cashier
```

- Step line: `Step name: score: Actor1: Actor2`; score is 0-7 satisfaction.
- `section Name` groups steps; multiple actors after the second colon render as stacked names.
- Tasks and scores are mandatory in that order.

## Quadrant Charts (`quadrantChart`)

```
quadrantChart
    title Campaign review
    x-axis Low reach --> High reach
    y-axis Low engagement --> High engagement
    quadrant-1 Expand
    quadrant-2 Promote
    quadrant-3 Re-evaluate
    quadrant-4 Improve
    Campaign A: [0.3, 0.6]
    Campaign B: [0.45, 0.23]
```

- Axes declared once each with `Low --> High` direction text; points use `Name: [x, y]` with 0-1 coordinates.
- Quadrants number from top-right (1) counterclockwise; quadrant labels are optional per line.
- Optional `@{ points: ... }` styling blocks exist for radius and color.

## Swimlanes (`swimlane-beta`)

Process steps grouped by owner, with handoffs visible across lanes.

```
swimlane-beta LR
  subgraph Customer
    Browse[Browse catalogue]
    Pay[Pay]
  end
  subgraph Warehouse
    Pick[Pick items]
    Ship[Ship order]
  end
  Browse --> Pay
  Pay --> Pick
  Pick --> Ship
```

- `swimlane-beta LR` or `TB` sets lane direction; lanes are `subgraph LaneName ... end` blocks.
- Node and edge syntax inside lanes matches flowchart conventions.
- Newer diagram type (11.16+); not supported on GitHub.

## Event Modeling (`eventmodeling`)

Information flow over time: UI, commands, events, views, processors.

```
eventmodeling

tf 01 ui Cart UI
tf 02 cmd AddItem
tf 03 evt ItemAdded
tf 04 view Cart total
```

- `tf N` (compact) or `timeframe N` (relaxed) starts a time frame; entity tokens: `ui`, `cmd`, `evt`, `view`/`rm`, `proc`, `repl`/`sys`.
- Relations are inferred by default; add explicit ones only when the user asks for control.
- Titles and notes attach per entity; keep each entity on its own line.

## Cynefin (`cynefin-beta`)

Classifies items into five domains with optional transitions.

```
cynefin-beta
title Situational assessment

complex
"Probe with experiments"

complicated
"Expert analysis needed"

clear
"Run the runbook"

chaotic
"Crisis response"

confusion
"Unknown domain"

complex --> complicated : "Pattern identified"
clear --> chaotic : "Complacency"
```

- Domain blocks (`complex`, `complicated`, `clear`, `chaotic`, `confusion`) hold quoted items.
- Transitions use `domain --> domain : "label"`; the clear-to-chaotic cliff transition is typical.
- Newer type (11.16+); not supported on GitHub.

## Wardley Maps (`wardley-beta`)

Components positioned by evolution stage (x) and value chain (y).

```
wardley-beta
title Tea shop

anchor Business [0.95, 0.63]
component Cup of Tea [0.79, 0.61]
component Tea [0.63, 0.81]
component Hot Water [0.52, 0.80]
component Kettle [0.43, 0.35]

Cup of Tea -> Tea
Cup of Tea -> Hot Water
Hot Water -> Kettle
```

- `component Name [x, y]` with coordinates 0-1 (x: genesis to commodity, y: visibility); `anchor` for external fixed points.
- Dependencies: `Component -> Dependency`.
- Supports evolution/stage decorators, notes (`note ...`), pipelines, and inertia/market markers.
- Newer type (11.14+); not supported on GitHub.
