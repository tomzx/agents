# Architecture Diagrams Reference

C4, architecture, and block diagrams describe systems, services, and their composition.
None of these render on GitHub Markdown; export to `.svg`/`.png` or fall back to `flowchart` when the target is GitHub.

## C4 Diagrams (experimental)

Keywords: `C4Context`, `C4Container`, `C4Component`, `C4Dynamic`, `C4Deployment`.
Leading spaces before the keyword are allowed; keep the keyword on its own line.

```
    C4Context
      title System context for payment platform

      Person(customer, "Customer", "Buys products")
      System(store, "Store", "Sells products")
      System_Ext(payment, "Payment provider", "External")

      Rel(customer, store, "Uses")
      Rel(store, payment, "Charges via", "HTTPS")
      UpdateRelStyle(customer, store, $offsetX="-40", $offsetY="40")
```

- Elements: `Person`, `Person_Ext`, `System`, `System_Ext`, `SystemDb`, `SystemQueue`; container level adds `Container`, `ContainerDb`, `Container_Ext`, `Container_Boundary`; component level adds `Component`.
- `Enterprise_Boundary(b0, "Name") { ... }` (alias `Boundary`) groups elements; `System_Boundary` for containers inside a system.
- `Rel(a, b, "label")` and variants `Rel_Back`, `Rel_Neighbor`, `Rel_L`/`Rel_R`/`Rel_U`/`Rel_D` with optional tags and technology: `Rel(a, b, "label", "HTTPS")`.
- `Show_Boundary()` toggles boundary rendering; `LAYOUT_WITH_LEGEND()` adds a legend; `LAYOUT_LEFT_RIGHT()` changes direction.
- Layout nudges with `UpdateRelStyle(a, b, $offsetX="..", $offsetY="..")`; titles with `title ...` and `skipline` spacing helpers.
- `C4Dynamic` orders `RelIndex` calls to narrate a runtime flow inside one container.

## Architecture Diagrams (`architecture-beta`)

Models cloud or CI/CD services connected by edges, grouped in groups.

```
architecture-beta
    group api(logos:aws-lambda)[API]
    service db(logos:aws-database)[Database] in api
    service lb(logos:aws-load-balancer)[Load balancer]
    service app(logos:react)[App] in api

    lb:B -- T:app
    app:R -- L:db
```

- `service id(icon)[Label] in groupId` declares a service; `group id(icon)[Label]` declares a group; icons are optional.
- Edges attach to sides: `L`, `R`, `T`, `B` (left, right, top, bottom): `a:T -- b:B`.
- Arrow variants: `--` plain, `<--`/`-->` arrow, `<-->` both.
- Icon syntax `iconName` resolves from iconify prefixes such as `logos:`; omit the parentheses entirely when not using icons.

## Block Diagrams (`block-beta`)

Arranges labeled boxes in columns without the flowchart's edge-driven layout.

```
block-beta
    columns 3
    a["Top"] b["Top"] c["Top"]
    block:middle:3
        columns 2
        d e
    end
    space:3
    f g h
```

- `columns N` sets the grid width; each element fills the next cell.
- `block:id:span` starts a nested block spanning `span` columns, closed with `end`.
- `space` and `space:N` skip cells.
- Edge and arrow forms from flowcharts work here too: `a --> b`, plus `blockArrowId<["label"]>(direction)` with directions `up`, `down`, `left`, `right`, `x`, `y` for thick block arrows.
- Node shapes mirror flowchart shapes: `id[...]`, `id(...)`, `id{...}`, `id((...))`, `id[(...)]`, `id>{{...}}` and others; quote labels containing special characters.
- Styling with `style id fill:#f9F`, `classDef` and `class` apply as in flowcharts.
