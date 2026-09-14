---
name: create-svg-image
description: Create great looking SVG diagrams, images, and visualizations as hand-authored SVG following a bundled style guide. Use when the user says "svg", "create an svg image", "svg diagram", "draw this as svg", "architecture diagram in svg", or asks for a figure that needs pixel-level control over layout, color, or branding that Mermaid cannot express. For Mermaid-rendered diagrams use create-mermaid-visualization instead.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
argument-hint: "[what to visualize]"
---

# Create SVG Image

Produces hand-authored SVG diagrams and visualizations that look intentional at any size and render correctly across browsers and non-browser renderers (resvg, librsvg, chat previews).
The aesthetic rules live in `references/svg-style-guide.md`; this skill supplies the workflow, the geometry math, and the validation loop.

## Prerequisites

- A subject to visualize: a user description, or source material (code, schema, process notes, data).
- The target medium (README, docs page, slide, issue comment, standalone file), since it fixes width, aspect ratio, and renderer limits.
- `references/svg-style-guide.md`, read in step 2.
- Optional tools, each with a graceful fallback: `xmllint` or `npx svglint` for parse checks, `rsvg-convert` or a browser for render checks.

## Steps

### 1. Gather context

Ask for or infer:

- What the visualization should show, and the one message a viewer should take away.
- The audience, target medium, and approximate display width.
- Any brand palette or sibling diagrams the output must match.
- Whether a dark mode variant is needed (style guide, Dark mode section).

### 2. Load the style guide and choose the tool

- Read `references/svg-style-guide.md` and adopt its tokens: color table, type scale, stroke ladder, corner radii, spacing grid.
- Start from the starter template in the guide and replace its content.
- When the user did not ask for SVG specifically, check whether a Mermaid type covers the need: if yes, prefer `create-mermaid-visualization`; hand-author SVG when precise layout, branding, or a non-diagram figure is required.

### 3. Plan the layout before writing XML

Compute the geometry first; retrofitting layout is the main source of ugly SVG.

- Pick display width from content: list 400px, flowchart 600-700px, architecture 700-800px.
- Set `viewBox` to content bounds plus 24px margins, snapped to the 4px grid.
- Estimate every label's width as 0.6 × font-size × characters, then size boxes: width = longest label + 32px, height = 3 × font-size for one line plus 1.5 × font-size per extra line.
- Compute baselines: label baseline = box center y + 0.35 × font-size; title baseline = top padding + 0.75 × font-size, centered on the content, not the canvas.
- Route connectors: at least 16px clear of nodes and 8px from each other, orthogonal or curved per the guide, never mixed.
- If any two elements would overlap, move them now, not after rendering.

### 4. Write the SVG

- Paint in order: defs, background, connectors, boxes, text, so nothing is covered.
- Escape XML special characters in all text: `&` as `&amp;`, `<` as `&lt;`, `>` as `&gt;`.
- Define the arrowhead once in `<defs>` with `markerUnits="userSpaceOnUse"`, so its size never scales with stroke width.
- Compute arrow endpoints: start 5px from the source edge, end 11px from the target edge so the tip lands about 5px out.
- Center labels with `text-anchor="middle"`, one accent color on the focal element, neutrals everywhere else.
- Keep coordinates on the grid and annotate container boundaries with comments.

### 5. Validate

The first output must pass the full checklist; never ship a diagram the user has to fix.

- Parse check: `xmllint --noout file.svg`, or `npx svglint file.svg` when available.
- Render check when a tool exists: `rsvg-convert file.svg -o /tmp/opencode/file.png` and inspect it, otherwise open the file in a browser.
- Walk the pre-flight checklist at the end of the style guide: clipping, text overflow, overlaps, grayscale legibility, one accent.
- Fix everything found and re-check before showing the result.

### 6. Deliver

- Document figure: write to an `assets/` directory next to the document (`docs/foo.md` gets `docs/assets/foo.svg`) and reference it by relative path, never inline the XML.
- Standalone image: write to the path the user gave, otherwise the repo root or an `assets/` directory.
- Report the file path first, then validation performed and any renderer caveat from the style guide's compatibility table (for example, librsvg ignoring `<style>`).
- Keep the source unminified; run SVGO only when the user asks for a smaller artifact.

## Geometry Quick Reference

| Quantity | Formula |
|---|---|
| Text width estimate | 0.6 × font-size × character count |
| Box width | longest label + 32px (16px padding per side) |
| Box height, one line | 3 × font-size |
| Each extra line | +1.5 × font-size |
| Label baseline in a box | box center y + 0.35 × font-size |
| Title baseline from top | top padding + 0.75 × font-size |
| Arrow start clearance | source edge + 5px |
| Arrow end (8px marker, refX 2) | target edge - 11px (tip lands 5px out) |
| Minimum box-to-box gap | 24px (4px grid) |
| Connector clearance from nodes | 16px |

## Editing Existing Diagrams

- Collect the full change list before touching the file; if the user gave one change, ask what else before editing.
- Apply all changes in one pass and update dependents in lockstep: arrows to and from moved elements, their labels, the container box wrapping them, and siblings aligned in the same row or column.
- Reply with the change list first, then the final file; do not emit the diagram after each individual edit.
- Treat spacing or alignment requests ("tighten it", "center it") as intent statements covering every related element, adjusted in one pass.

## Common Pitfalls

| Symptom | Cause and fix |
|---|---|
| SVG fails to render at all | Unescaped `&`, `<`, or `>` in text; escape or drop the characters |
| Arrowhead balloons when stroke width changes | Marker missing `markerUnits="userSpaceOnUse"` |
| Bottom of the diagram clipped | viewBox height must reach the lowest element edge plus the margin |
| Arrowhead crooked on a curve | Constrain the last control point to share x (vertical approach) or y (horizontal approach) with the endpoint |
| Arrowhead invisible | Gap below the minimum; increase box-to-box spacing |
| Renders differently outside the browser | Renderer dropped `<style>` or filters; move critical styling to presentation attributes |
| Diagram looks loose and empty | Spacing or margins beyond the guide's limits; tighten spacing and shrink the viewBox |

## Output Format

```text
<path>/<name>.svg

<one-line note on what the figure shows>
<validation performed, plus any renderer caveat>
```

When the figure accompanies a document, also make the relative-path edit in that document.

## Example Usage

**Scenario 1: Architecture diagram for a README**
User: "Draw our ingest pipeline as an SVG for the README."
Gather context, load the style guide, compute the geometry (three 160px boxes, 32px gaps, 700px canvas), write the SVG with one accent on the bottleneck node, validate with xmllint plus a render check, write `docs/assets/ingest-pipeline.svg`, and reference it from the README.

**Scenario 2: Iterating on an existing SVG**
User: "Move the cache box left and make errors red."
Collect the full change list, apply both changes in one pass, update the cache box's arrows and labels in lockstep, then reply with the change list and the final file.

**Scenario 3: Renderer compatibility**
User: "The diagram looks broken when attached in Slack."
The compatibility table predicts chat previews strip `<style>` and filters. Move critical styling to presentation attributes, drop the shadow, re-validate, and deliver a portable variant.
