# SVG Diagram & Visualization Style Guide

A set of conventions for producing clean, readable, portable SVG diagrams by hand or by code.
The goal is diagrams that look intentional at any size and render correctly almost anywhere.

## Principles

- One idea per diagram, split anything that needs a second legend or a paragraph to explain.
- Consistency beats cleverness: reuse the same tokens (color, spacing, type) in every diagram.
- Design for the smallest size the diagram will actually be viewed at, then test at that size.
- Flat and minimal by default, decoration must encode meaning or be removed.
- Assume a dumb renderer: external fonts, filters, and CSS are all optional features.

## Canvas and layout

- Always set an explicit `viewBox` and derive size from it: `<svg viewBox="0 0 800 500">`.
- Use a 4px spacing grid (8px for larger diagrams) and snap every coordinate to a whole number.
- Keep at least 24px padding between content and the canvas edge on all sides.
- Align nodes to the grid, eyeballed positions are the fastest way to look amateur.
- Reading order is left-to-right, top-to-bottom, with the entry point at the top-left.
- Balance whitespace across quadrants so no corner feels empty or overcrowded.
- Pick a canvas aspect close to where it will be embedded (16:9 slides, 4:3 docs, square icons).

## Color

| Role       | Value (light mode) | Usage                                  |
| ---------- | ------------------ | -------------------------------------- |
| Background | `#ffffff`          | Canvas, or omit for transparency       |
| Text       | `#0f172a`          | Primary text and dark strokes          |
| Muted text | `#64748b`          | Annotations, edge labels, captions     |
| Border     | `#cbd5e1`          | Secondary boxes, dividers, grid lines  |
| Accent     | `#2563eb`          | Focal element only, one per diagram    |
| Success    | `#16a34a`          | Positive state                         |
| Warning    | `#d97706`          | Caution state                          |
| Error      | `#dc2626`          | Failure state                          |

- One accent color per diagram, reserved for the single most important element.
- Neutrals do the structural work (borders, connectors, containers), accent marks the point.
- Tints: fill boxes with the stroke color at 8-12% opacity for a cohesive look.
- Contrast: body text at least 4.5:1, large text and strokes at least 3:1 (WCAG AA).
- Never encode meaning by color alone, add a label, icon, or pattern so it survives grayscale and colorblind viewing.

## Typography

- Family: `ui-sans-serif, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`.
- Never depend on webfonts, they fail silently in most non-browser renderers.
- Sizes: title 18-22, node labels 12-14, edge labels and annotations 10-11, nothing below 10.
- Weights: 600 for titles and node names, 400 for everything else, avoid light weights at small sizes.
- Estimate label width as `0.6 × font-size × character count` for sans-serif and size boxes to fit the longest label plus 16px horizontal padding.
- Center labels with `text-anchor="middle"` instead of hand-positioning them.
- `dominant-baseline` support is inconsistent across renderers, so position text with explicit `y` values.
- Baseline math: the text baseline sits roughly `0.35 × font-size` below the visual center, so for a 14px label centered in a 48px tall box, use `y = boxCenterY + 5`.

## Strokes and shapes

- Stroke ladder: 1px for grids and hairlines, 1.5px default, 2px emphasis, never more than 3px.
- Add `vector-effect="non-scaling-stroke"` when the diagram will be scaled up.
- Corner radius 6-8px for boxes, fully rounded for pills, keep the radius uniform within an element class.
- `stroke-linecap="round"` and `stroke-linejoin="round"` on all paths.
- Prefer defined `<rect>`, `<circle>`, `<path>` primitives over hand-drawn approximations.

## Connectors and arrows

- Define arrowheads once in `<defs>` with `<marker>` and reference them with `marker-end`.
- Orthogonal (elbow) connectors for flows and architectures, smooth cubic beziers for graphs and relationships, never mix both in one diagram.
- Keep connectors at least 16px away from nodes and 8px from each other.
- Leave a 4-6px gap between the arrowhead tip and its target, touching looks cramped.
- Minimize line crossings, if one is unavoidable, route around or add a bridge hop.
- Label edges sparingly: 11px text, centered on the line, with a background `<rect>` in the canvas color to knock out the line behind it.

## Hierarchy and emphasis

- Emphasis recipe: accent color + 2px stroke, optionally one subtle shadow, nothing else.
- De-emphasize context: muted gray, 1px stroke, no fill.
- The focal element should be visibly larger, accented, or both.
- Emphasize at most 10% of elements, if everything is highlighted nothing is.

## Depth and effects

- At most one subtle drop shadow for elevated elements: `feDropShadow` with `dy="1"`, `stdDeviation="2"`, `flood-opacity="0.2"`.
- No glows, bevels, inner shadows, or gradients used as decoration, gradients are only acceptable for data encoding (heat, magnitude).
- `feDropShadow` is more portable than a `feGaussianBlur` + `feOffset` chain but still verify support in the target renderer.

## Reuse and structure

- Put shared styling in one `<style>` block with classes (`.node`, `.label`, `.edge`), or fall back to presentation attributes if the target renderer drops CSS.
- Define repeated elements once in `<defs>` and instantiate with `<use>`.
- Draw order: background first, connectors before nodes, labels last so nothing gets covered.
- Group related elements in `<g>` with descriptive ids, it makes edits and animations far easier.
- Run SVGO on delivered files and keep the unminified source in the repo.

## Accessibility

- Add `<title>` as the first child of the `<svg>`, plus `role="img"` and `aria-labelledby` pointing at it.
- Add `<desc>` when the diagram structure is not obvious from the title.
- Keep text as real `<text>` elements, never outlined to paths, so it stays selectable, searchable, and screen-reader accessible (logos are the exception).
- Verify the diagram works in grayscale.

## Dark mode

- Use `currentColor` for strokes and text where the embedding context can set it.
- For standalone files, add a `@media (prefers-color-scheme: dark)` block swapping the background, text, and border tokens.
- Never hardcode pure black or pure white, use the neutral scale so both modes keep contrast.

## Renderer compatibility

| Renderer                     | Notes                                                           |
| ---------------------------- | --------------------------------------------------------------- |
| Browsers                     | Full support                                                    |
| resvg                        | No external resources, solid filter support, no webfonts        |
| librsvg (Linux tools, GNOME) | No external resources, older versions ignore `<style>`, use attributes |
| Office and chat previews     | Often strip `<style>` and filters, keep a plain-attribute fallback |

- Compatibility order: presentation attributes > inline `<style>` > external CSS.
- Avoid `foreignObject`, it is the most commonly unsupported feature.

## Starter template

```svg
<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t">
  <title id="t">Service request flow</title>
  <style>
    .box  { fill: #2563eb; fill-opacity: 0.1; stroke: #2563eb; stroke-width: 1.5; rx: 8; }
    .ctx  { fill: none; stroke: #cbd5e1; stroke-width: 1; rx: 8; }
    .name { font: 600 14px ui-sans-serif, -apple-system, sans-serif; fill: #0f172a; text-anchor: middle; }
    .note { font: 400 11px ui-sans-serif, -apple-system, sans-serif; fill: #64748b; text-anchor: middle; }
    .edge { stroke: #94a3b8; stroke-width: 1.5; fill: none; marker-end: url(#arrow); }
  </style>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0 0 L10 5 L0 10 z" fill="#94a3b8"/>
    </marker>
  </defs>
  <!-- background, then edges, then nodes, then labels -->
</svg>
```

## Pre-flight checklist

- Zoomed out (25%): is the overall structure still readable?
- Zoomed in (400%): are lines crisp and coordinates grid-aligned?
- Longest label in every box: no overflow?
- Grayscale pass: does the meaning survive?
- Non-browser renderer pass: does it still look right?
- One accent, one focal point, one message?
