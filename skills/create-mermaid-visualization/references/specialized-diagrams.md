# Specialized Diagrams Reference

Domain-specific diagram types with a narrower purpose.

## Requirement Diagrams (`requirementDiagram`)

SysML-style requirements traced to design elements.

```
requirementDiagram

requirement auth_req {
    id: 1
    text: users shall authenticate with SSO
    risk: low
    verifymethod: test
}

functionalRequirement perf_req {
    id: 2
    text: p99 latency under 200 ms
    risk: high
    verifymethod: analysis
}

element auth_service {
    type: service
}

auth_req - contains -> perf_req
auth_service - satisfies -> auth_req
```

- Requirement kinds: `requirement`, `functionalRequirement`, `interfaceRequirement`, `performanceRequirement`, `physicalRequirement`, `designConstraint`.
- Blocks carry `id`, `text`, `risk` (`low|medium|high`), `verifymethod` (`analysis|inspection|test|demonstration`); `element` blocks name traced artifacts with a `type`.
- Trace relations: `contains`, `copies`, `derives`, `satisfies`, `verifies`, `refines`, `traces`; arrows go `a - rel -> b` or `<- rel -` reversed.

## Use Case Diagrams (`usecase-beta`)

Actors interacting with use cases inside a system boundary.

```
usecase-beta
direction LR
actor Customer("Customer")
actor Admin("Administrator")
systemBoundary "Order system"
  Checkout("Place order")
  Refund("Request refund")
end
Customer --> Checkout
Admin --> Refund
```

- `actor Name("Display")` and use cases as `Name("Display")`; `systemBoundary "Name" ... end` groups use cases.
- `direction LR|TB|BT|RL` sets layout.
- Newer type (12.0+); not supported on GitHub.

## Ishikawa Diagrams (`ishikawa-beta`)

Fishbone cause-and-effect analysis of a single problem.

```
ishikawa-beta
    Slow builds
    Process
        Sequential steps
        Missing cache
    Tooling
        Compiler version
            Old toolchain
        Bundler config
    Environment
        Cold CI runners
```

- Line 1 is the effect (problem); every following line is a cause.
- Indentation builds the hierarchy: first level = main bones, deeper = sub-causes.
- One problem per diagram; not supported on GitHub.

## Railroad Diagrams (`railroad-beta` and notation variants)

Visualize context-free grammars. Keywords: `railroad-ebnf-beta` (EBNF, most common), `railroad-abnf-beta` (ABNF), `railroad-peg-beta` (PEG); plain `railroad-beta` auto-detects.

```
railroad-ebnf-beta
letter = "a" | "b" | "c" ;
identifier = letter { letter | digit } ;
digit = "0" | "1" | "2" ;
```

- One rule per statement, ending with `;` (`=` or `::=` assignment).
- Terminals are quoted strings; unquoted identifiers reference other rules.
- Operators: sequence (juxtaposition), `|` choice, `{ ... }` zero-or-more (EBNF), `[ ... ]` optional, `( ... )` grouping.
- Optional `title` line and `accTitle:`/`accDescr:` accessibility lines.
- Not supported on GitHub.

## Tree Views (`treeView-beta`)

Directory-style hierarchy with connector lines.

```
treeView-beta
    my-project/
        src/
            index.js
        package.json
        README.md
```

- Structure is indentation only; a trailing `/` renders the label as a directory.
- Box-drawing input is auto-detected, so existing `├──` / `└──` trees convert directly:

```
treeView-beta
├── src/
│   ├── index.ts
│   └── utils.ts
├── package.json
└── README.md
```

- Quoted labels allow spaces; `showIcons` config enables file/folder icons; annotations append after labels.
- Newer type (11.14+); not supported on GitHub.

## Agentflow (`agentflow-beta`)

Agentic workflows: agents, tasks, tools, and data contracts.

```
agentflow-beta TB
  brief["Release brief"]@{ shape: input }
  flow writer["Drafting Agent"]
    draft["Draft the notes"]@{ shape: task }
    lookup["changelog_search"]@{ shape: tool }
    draft --> lookup
  end
```

- `flow Name["Agent"] ... end` containers nest to any depth and represent agents.
- Node kinds attach via `@{ shape: ... }`: `input`, `task`, `tool`, `decision`, `refdoc`, and others; bare labels render as generic nodes.
- Metadata blocks `@{ model: "...", instruction: "...", params: ... }` attach non-visual detail to nodes.
- Edges reuse flowchart syntax; sequence, reference (`-.-`), and failure edges carry distinct meanings.
- Layout uses ELK by default; newer type (12.0+); not supported on GitHub.
