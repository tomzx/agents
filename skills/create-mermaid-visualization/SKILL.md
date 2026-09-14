---
name: create-mermaid-visualization
description: Create any Mermaid diagram (flowchart, sequence, class, state, ER, C4, architecture, gantt, mindmap, timeline, pie, sankey, and 20+ more) from a description or source material. Use when the user says "diagram", "visualize", "mermaid", "draw a flowchart", "sequence diagram", "ER diagram", "mindmap", "gantt chart", or asks to document architecture, processes, data flows, or relationships as a diagram. Covers selecting the right diagram type, correct syntax, validation, and delivery into Markdown or files.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
argument-hint: "[what to visualize or diagram type]"
---

# Create Mermaid Visualization

Produces correct, validated Mermaid diagrams for any of the 30+ diagram types Mermaid supports.
The skill selects the right diagram type from the user's intent, writes syntactically correct Mermaid using family-specific references, validates before delivering, and hands back a diagram that renders in Markdown-aware viewers (GitHub, GitLab, VS Code, Obsidian, Notion).

## Prerequisites

- A subject to visualize: a description from the user, or source material (code, schema, process notes, data).
- The diagram catalog below and the matching file under `references/`.
- Optional: `@mermaid-js/mermaid-cli` (`mmdc`) for rendering validation. Check with `command -v mmdc`; if absent, use `npx -y @mermaid-js/mermaid-cli` or fall back to careful review.

## Steps

### 1. Gather context

Ask for or infer:

- What the diagram should show (process, structure, interactions, data, planning).
- The audience and target (GitHub README, docs site, issue comment, presentation).
- Any entities, steps, actors, or data values already known.
- Layout preference if stated (top-down, left-right).

### 2. Select the diagram type

Match intent to type using the catalog below. When two types fit, prefer the one that renders more reliably in the target (stable types over `-beta` types) and answers the user's actual question (who interacts when, how things are structured, what the data shows).

### 3. Load the family reference

Read only the `references/` file for the chosen family. Follow its syntax exactly; do not mix syntax between families.

### 4. Write the diagram

- Declare the diagram type on the first line.
- Use the exact keyword from the catalog, including `-beta` and `-v2` suffixes.
- Keep one concept per diagram; split large subjects into multiple focused diagrams.
- Label nodes and edges in plain language, so the diagram reads without explanation.

### 5. Validate

Run validation before delivering. If `mmdc` is available (or via `npx`):

```bash
mmdc -i diagram.mmd -o /tmp/opencode/diagram.svg
```

An exit code of 0 means the syntax parses. If `mmdc` is unavailable, re-read the diagram against the family reference line by line and check the pitfalls below.

Never add a diagram to a document until it passes validation.

### 6. Deliver

- Inline in Markdown: fenced code block with the `mermaid` language tag.
- As a file: `.mmd` file, with `.svg` or `.png` exported via `mmdc` when the target cannot render Mermaid (Confluence, Word, PDF, plain web pages).
- Note the rendering limits from the catalog when the target is GitHub (several `-beta` types do not render there).

## Diagram Catalog

Stable types render on GitHub and most Markdown viewers. Types marked `beta` may not render on GitHub; check the target before using them.

| Intent | Type | Keyword | Since | Use for |
|---|---|---|---|---|
| Process or decision flow | Flowchart | `flowchart` (alias `graph`) | stable | Workflows, algorithms, decision trees, data flow |
| Interactions over time | Sequence | `sequenceDiagram` | stable | API calls, protocol steps, request/response chains |
| Interactions over time (code style) | ZenUML | `zenuml` | 11.0+ | Sequence diagrams written as pseudo-code |
| Code structure | Class | `classDiagram` | stable | Classes, interfaces, inheritance, domain models |
| State machines | State | `stateDiagram-v2` | stable | Lifecycle states, mode transitions |
| Database or data model | Entity Relationship | `erDiagram` | stable | Tables, keys, cardinality between entities |
| Software architecture | C4 | `C4Context`, `C4Container`, `C4Component`, `C4Dynamic`, `C4Deployment` | experimental | System context, containers, components, deployment |
| Cloud or CI/CD services | Architecture | `architecture-beta` | 11.1+ | Service and resource relationships in groups |
| Simple boxes and columns | Block | `block-beta` | 10.9+ | Layered component stacks, parent-child block layouts |
| Project schedule | Gantt | `gantt` | stable | Tasks, durations, dependencies, milestones |
| Chronology | Timeline | `timeline` | 10.3+ | Events over periods, roadmaps, history |
| Workflow board | Kanban | `kanban` | 11.3+ | Tasks across column stages |
| Idea hierarchy | Mindmap | `mindmap` | 10.3+ | Topic trees, brainstorming, concept breakdowns |
| Branching strategy | Git graph | `gitGraph` | 10.3+ | Commits, branches, merges, release flows |
| Experience over time | User journey | `journey` | stable | Satisfaction across steps of a user task |
| Two-axis positioning | Quadrant chart | `quadrantChart` | 10.3+ | Items plotted on two axes with four quadrants |
| Cross-team process | Swimlanes | `swimlane-beta` | 11.16+ | Steps grouped by owner, handoffs between lanes |
| Information flow over time | Event modeling | `eventmodeling` | 11.15+ | Commands, events, views, and processors on a timeline |
| Sense-making domains | Cynefin | `cynefin-beta` | 11.16+ | Items classified into five complexity domains |
| Strategy evolution | Wardley map | `wardley-beta` | 11.14+ | Components positioned by value chain and evolution |
| Proportions | Pie chart | `pie` | stable | Parts of a whole |
| Numeric series | XY chart | `xychart-beta` | 10.9+ | Line and bar plots over a numeric or category axis |
| Flow redistribution | Sankey | `sankey-beta` | 10.3+ | Quantities moving between sets of nodes |
| Nested proportions | Treemap | `treemap-beta` | 11.13+ | Hierarchy as sized rectangles |
| Multivariate comparison | Radar | `radar-beta` | 11.6+ | Several series scored over the same axes |
| Set relationships | Venn | `venn-beta` | 11.12+ | Overlapping sets and unions |
| Wire format layout | Packet | `packet-beta` | 11.0+ | Bit ranges of protocol headers and frames |
| Requirements and traces | Requirement | `requirementDiagram` | stable | SysML requirements linked to elements |
| Actors and use cases | Use case | `usecase-beta` | 12.0+ | Actors, system boundary, use cases |
| Cause analysis | Ishikawa | `ishikawa-beta` | 11.12+ | Fishbone causes of a problem |
| Grammar visualization | Railroad | `railroad-beta`, `railroad-ebnf-beta`, `railroad-abnf-beta`, `railroad-peg-beta` | 11.16+ | Context-free grammar rules as paths |
| Directory layout | Tree view | `treeView-beta` | 11.14+ | File trees, box-drawing input supported |
| Agentic workflow | Agentflow | `agentflow-beta` | 12.0+ | Agents, tasks, tools, and data contracts |

Reference files by family:

- `references/flowchart.md`: flowchart syntax, node shapes, edges, subgraphs, styling.
- `references/structure-diagrams.md`: class, state, entity relationship.
- `references/interaction-diagrams.md`: sequence, ZenUML.
- `references/architecture-diagrams.md`: C4, architecture, block.
- `references/planning-diagrams.md`: gantt, timeline, kanban, mindmap, git graph, user journey, quadrant, swimlanes, event modeling, Cynefin, Wardley.
- `references/data-charts.md`: pie, XY chart, sankey, treemap, radar, venn, packet.
- `references/specialized-diagrams.md`: requirement, use case, ishikawa, railroad, tree view, agentflow.

## Common Syntax Rules

- Comments start with `%%`. Unknown words break the parse; misspelled keywords fail loudly.
- Wrap labels containing special characters (`{}`, `[]`, `|`, `;`, quotes) in double quotes: `A["Label (with) chars"]`.
- Use HTML entities for angle brackets and ampersands inside labels (`&lt;`, `&amp;`), not raw `<` or `&`.
- Diagram-level front matter config goes at the top, before the keyword:

````
---
title: Example
config:
  theme: base
---
flowchart TD
    A --> B
````

- Themes: `default`, `forest`, `dark`, `neutral`, `base`. Layout: `layout: dagre` (default) or `layout: elk` for complex graphs. Look: `look: classic` or `look: handDrawn`.

## Common Pitfalls

| Symptom | Cause and fix |
|---|---|
| Parse error on a labeled node | Unquoted special characters; wrap the label in double quotes |
| Diagram silently misrenders on GitHub | `-beta` keyword unsupported there; use the stable type or export an image instead |
| Everything on one line renders cramped | Add line breaks and indentation; they are free and improve diffs |
| Node text shows HTML tags literally | Use `<br/>` for line breaks inside labels; escape `<`, `>`, `&` as entities |
| C4, architecture, or block fails on GitHub | GitHub does not render these; deliver `.svg`/`.png` or fall back to `flowchart TD` |
| Edge labels break the parser | Quote the label text: `A -->|'label text'| B` or `A -- "text" --> B` |
| Too many entities in one diagram | Split by domain or phase; link the parts in surrounding prose |
| State diagram uses old syntax | Always use `stateDiagram-v2`, not `stateDiagram` |

## Styling Guidelines

- Prefer unstyled diagrams by default; theme and color only when the user asks or readability demands it.
- When styling, always pair a light fill with dark text (`color:`) or a dark fill with light text in `classDef`.
- Keep styling consistent across diagrams in the same document.

## Output Format

Inline Markdown form:

````markdown
## <Diagram Title>

```mermaid
<diagram definition>
```

<Optional 1-3 sentence note on what the diagram shows or assumes.>
````

File form: `<name>.mmd` plus `<name>.svg` or `<name>.png` when the target needs an image, with a one-line note stating what each file contains.

## Example Usage

**Scenario 1: Process description to flowchart**
User: "Visualize our deploy pipeline: build, then test, then canary or full deploy depending on smoke tests."
Select `flowchart TD` (process with decision), write nodes with quoted labels, validate with `mmdc`, deliver a fenced `mermaid` block.

**Scenario 2: Database schema to ER diagram**
User: "Document the orders and customers tables."
Select `erDiagram`, read `references/structure-diagrams.md`, define entities with keys and attributes, express cardinality (`||--o{`), validate, deliver inline in the README.

**Scenario 3: Rendering limits on GitHub**
User: "Add an architecture diagram to our GitHub README."
The catalog marks `architecture-beta` as not rendering on GitHub. Options offered: a `flowchart` equivalent that renders on GitHub, or `architecture-beta` exported to `.svg` and referenced as an image. Deliver the chosen one.
