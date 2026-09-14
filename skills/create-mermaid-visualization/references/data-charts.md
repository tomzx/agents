# Data Charts Reference

Charts for quantities, proportions, sets, and wire layouts.

## Pie (`pie`)

```
pie showData
    title Pets adopted
    "Dogs" : 386
    "Cats" : 85
    "Rabbits" : 15
```

- `pie showData` adds value labels to slices; `title` is optional.
- Slice: `"Label" : number`; negatives or zero values are ignored.
- Config via front matter `pie: { textPosition: 0.6 }` controls label distance.

## XY Chart (`xychart-beta`)

```
xychart-beta
    title "Monthly revenue"
    x-axis [jan, feb, mar, apr]
    y-axis "Revenue (k)" 0 --> 100
    bar [10, 25, 18, 40]
    line [8, 22, 24, 38]
```

- `x-axis` takes a category list or a numeric range `x-axis 0 --> 12`; add a quoted title before the range.
- `y-axis "Title" min --> max` sets the scale.
- Plot one or both of `bar [...]` and `line [...]`; both accept a title: `bar "Plan" [1, 2]`.
- Not supported on GitHub.

## Sankey (`sankey-beta`)

```
sankey-beta

Source,Target,Value
Coal plant,Electricity,50
Wind farm,Electricity,30
Electricity,Homes,60
Electricity,Industry,20
```

- Body is CSV: `Source,Target,Value`, one link per line; nodes are created implicitly from names.
- Values are numbers; omit a header row unless `csvHeader` config expects it.
- Front matter config `sankey: { linkColor: "source", nodeAlignment: "justify" }` controls appearance.
- Link order matters for layout; group links by source for a clean read.
- Quoted CSV cells required for names containing commas.

## Treemap (`treemap-beta`)

```
treemap-beta
"Languages"
    "Go": 40
    "Python": 55
    "Rust": 12
"Docs"
    "Guides": 20
    "Reference": 33
```

- Hierarchy is indentation; sections are quoted names, leaves end with `: value`.
- Rectangle area is proportional to value; leaves only carry values.
- Nodes accept `:::class` styling; not supported on GitHub.

## Radar (`radar-beta`)

```
radar-beta
  title Team skills
  axis m["Math"], s["Science"], e["English"]
  axis h["History"], g["Geography"]
  curve a["Alice"]{90, 80, 70, 85, 75}
  curve b["Bob"]{70, 85, 90, 65, 80}
  max 100
```

- `axis` lines declare axes in order, optionally labeled; `curve` lines declare one series each with values in `{}` in axis order.
- `max N` sets the scale ceiling; `graticule` config toggles grid shape.
- Not supported on GitHub.

## Venn (`venn-beta`)

```
venn-beta
  title Feature viability
  set Desirable
  set Feasible
  set Viable
  union Desirable,Feasible["Buildable"]
  union Desirable,Feasible,Viable["Ship it"]
```

- `set Name` declares a circle; `union Set1,Set2["Label"]` (and up to three sets) declares an overlap region with an optional label.
- Not supported on GitHub.

## Packet (`packet-beta`)

Bit-field layouts of protocol headers.

```
packet-beta
title TCP header
0-15: "Source port"
16-31: "Destination port"
32-63: "Sequence number"
96-127: "Checksum"
128-159: "Options (variable)"
```

- Fields are `start-end: "Label"` in bit positions; ascending ranges pack left to right, wrapping by row width.
- `packet-16`/`packet-32` keywords set bits-per-row variants; default row width is 32 bits.
- Labels are quoted; do not overlap ranges.
- Not supported on GitHub.
