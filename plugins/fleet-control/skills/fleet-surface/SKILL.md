---
name: fleet-surface
description: Render a fleet control room from an intent spec and a data file, and publish it. Use for "build the control room", "render the dashboard", "refresh the overview", "publish the fleet page", "regenerate from the intent", or after any change to an intent or its data. The renderer is generic - it draws whatever the intent declares, with no per-domain code.
---

# Render the control room

One renderer draws every fleet. It reads the intent (what the fleet is) and the data (the instances) and knows nothing about the domain. Never fork it per domain, and never hand-edit generated HTML - change the intent or the data and rebuild.

## Build

```bash
python3 references/build.py <intent.json> <data.json> [out.html]
```

The data file is a bare JSON array, or an object with an `items` / `components` / `instances` / `records` / `data` array.

`build.py` validates before rendering and refuses on mismatch. It catches exactly the failures that otherwise produce a silently wrong page:

- a unit missing its id, or duplicate ids;
- a `sequence` dimension whose steps are missing from an instance - absent steps must carry the absent state, never be omitted;
- a `matrix` dimension missing slots in `value` or `state`;
- trend series of differing lengths, which makes sparklines lie.

Fix the data or the intent. Never loosen the validator to get a render.

## What the intent controls

Everything: the rail and its icons, which views exist and in what order, the card's bands, table columns, the summary band, filters, sorts, the legend, the drawer's tabs. Adding a view is an entry in `views`; adding a metric to a card is an entry in a dimension. If something cannot be expressed in the intent, extend the intent format and the renderer together - with the design system's rules in mind - rather than special-casing one page.

View types: `cards` (the overview), `table` (columns with typed cells), `matrix` (units × slots), `static` (panels of rows that are not fleet instances, e.g. templates or policy).

Cell types for table columns: `mono num verdict state bool level rating meter counters sequence trend muted`, or omit `as` for a name cell with an optional `sub`.

## Design rules the renderer enforces

These are baked into the template. Preserve them in any change:

- Neutral ground - paper, strokes, shadows and the idle grey are achromatic, depth comes from white light only. `saturate()` on glass stays at or below 1.05. A tinted ground puts a cast over everything.
- Semantic colour (`ok` / `warn` / `crit`) means state and nothing else. The accent is a separate hue for interaction only: current nav item, selected filter, focus ring, something happening right now.
- A state most units are in most of the time renders neutral.
- State is encoded in form as well as hue: severity stripe, hatching for absent, shimmer for active, arrow versus warning triangle.
- Both themes are defined at token level on bare `:root`, then redefined under `prefers-color-scheme` and `[data-theme]`.
- Type: Archivo for headings and uppercase micro-labels, IBM Plex Sans for UI, IBM Plex Mono with tabular numerals for every version, path and count.

## Publish

Publish the generated file with the Artifact tool.

- First publish: pass a favicon suited to the fleet and a one-sentence description.
- Every refresh: republish the **same file path** in the same session, or pass the artifact's `url`, and omit favicon and icon so the artifact keeps its identity. A new path creates a second control room and the team's link goes stale.

## Look once

Render, look at it once, fix in one pass, publish. Spend the look on:

- the card grid at ~1440px (columns even, nothing clipped) and ~400px (one column, no sideways scroll);
- whether one state colour has spread across most units - that is a severity rule that is too eager, not a styling problem;
- aggregates in the summary band agreeing with the data you just rendered;
- sparkline endpoints inside their boxes.

Then stop. The live page is the review surface.
