# Flowchart Reference

Flowcharts (`flowchart`, alias `graph`) express processes, decision logic, and data flow.
Direction: `TB` (top-down), `TD` (same as TB), `BT`, `LR`, `RL`.

```
flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action]
    B -->|No| D[Other action]
```

## Node Shapes

| Shape | Syntax | Meaning |
|---|---|---|
| Rectangle | `id[text]` | Process step |
| Rounded | `id(text)` | Start or end |
| Stadium | `id([text])` | Terminal event |
| Subroutine | `id[[text]]` | Subprocess |
| Cylinder | `id[(text)]` | Database |
| Circle | `id((text))` | Connector point |
| Diamond | `id{text}` | Decision |
| Hexagon | `id{{text}}` | Preparation |
| Parallelogram | `id[/text/]` | Input or output |
| Trapezoid | `id[/text\]` | Manual operation |
| Double circle | `id(((text)))` | Highlighted terminal |
| Flag / note | `id>text]` | Asymmetric tag |

## Edges

| Syntax | Result |
|---|---|
| `A --> B` | Arrow |
| `A --- B` | Open link (no arrow) |
| `A -.-> B` | Dotted arrow |
| `A ==> B` | Thick arrow |
| `A -- text --> B` | Arrow with text |
| `A -->|text| B` | Arrow with text (alternative) |
| `A <---> B` | Bidirectional arrow (9.4+) |
| `A --> B & C` | Fan-out to multiple targets |
| `A & B --> C & D` | Multiple sources and targets |
| `A --o B` | Circle edge |
| `A --x B` | Cross edge |
| `A ~~~ B` | Invisible link (spacing only, 10.3+) |
| `A --> B --> C` | Chained |

Edge text with special characters needs quotes: `A -->|"label: text"| B`.
Edges get IDs when annotated: `A -- e1 --> B`, then style with `e1@{ animate: true }` for animation (11.3+).

## Subgraphs

```
flowchart LR
    subgraph title["Group title"]
        direction TB
        A --> B
    end
    subgraph other
        C
    end
    B --> C
```

- `direction` inside a subgraph is ignored when an external edge links into it.
- Subgraph IDs can be reused as link endpoints.

## Nodes on Multiple Lines

Link straight to a new node label in one statement:

```
flowchart LR
    A["A double quote: #quot;"] --> B["A line break<br/>in the label"]
```

## Styling and Classes

```
flowchart LR
    A:::primary --> B
    classDef primary fill:#90EE90,stroke:#333,stroke-width:2px,color:#000
    class A primary
    style B fill:#BBF
```

- `classDef name props` defines a class, `class id name` applies it, `:::name` applies inline.
- Always set `color:` so text contrasts with the fill.
- Default class `classDef default ...` styles all nodes without a class.

## Configuration and Interaction

Front matter sets title, theme, and layout:

```
---
title: Deploy pipeline
config:
  theme: forest
  layout: elk
  flowchart:
    curve: basis
---
flowchart TD
    A --> B
```

Clickable nodes: `click A callback "tooltip"` or `click A "https://example.com" "tooltip"`.
Accessibility: `accTitle:` and `accDescr:` lines after the keyword, or front matter `accTitle`/`accDescr`.

## Limits

- Very large graphs render slowly with `dagre`; consider `layout: elk` or splitting.
- Subgraph titles containing quotes must be quoted: `subgraph id["Title with spaces"]`.
