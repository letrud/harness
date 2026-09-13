---
name: fleet-scaffold
description: Scaffold fleet structure - stand up a new fleet, onboard an instance with honest day-one values, add a slot across every instance, or add a dimension or view. Use for "add a new service/supplier/product to the fleet", "onboard this", "set up a new fleet", "add a staging environment", "add a market", "add a dimension", "add a view", "start tracking X". Generates from the intent so new instances match the contract on day one.
---

# Scaffold

Four things get scaffolded. Identify which, then follow that section. Everything derives from the intent, so nothing here is domain-specific.

## A. A new fleet

1. Write the intent with the fleet-intent skill. Do not skip to data — the elicitation order (unit → standard → dimensions → states → severity → surface) is what makes the rest work.
2. Create the data file with an empty `items` array.
3. Onboard instances (section B), or bulk-import existing ones and run the audit to see where they stand.
4. Render and publish with the fleet-surface skill.

Report the fleet picture once it renders: how many at each severity, the most common required gap, and which high-class units miss the baseline.

## B. A new instance

```bash
python3 references/scaffold.py <intent.json> instance <id> --class 1 --set squad=Ledger
```

This emits a skeleton record that is honest about being new: every sequence step in the absent state, gauges at zero, the worst verdict, matrix slots `null` with the `none` state, boolean facts `false`, trend series empty. Field types are inferred from how the intent uses each field — numeric where the intent aggregates or sorts on it, boolean where the standard tests it for truthiness.

**Never seed optimistic values.** A thing that has never run must look like it has never run; the overview is only useful if day one looks like day one. Running the audit immediately after will show nearly everything as a gap — that is correct, and it is the onboarding checklist.

Fill in what is genuinely known (owner, class, subtitle), append to the data file, and re-render. Keep the file sorted by id so diffs stay readable.

## C. A new slot

Slots — environments, markets, regions — touch every instance, so change them in one pass:

```bash
python3 references/scaffold.py <intent.json> data <data.json> add-slot stage --after test
```

This inserts the slot in promotion order (the reference slot stays last unless named explicitly) and adds `null` / `none` entries to every instance. Above four slots, check the card grid at phone width — the script warns, and the matrix dimension's pill grid may need to wrap.

`... data <data.json> check` reports which fields each instance is missing against the intent, which is the fastest way to find records that predate a contract change.

## D. A new dimension or view

Load the fleet-intent skill first — a new dimension is a modelling decision, not a layout one.

- **Dimension**: pick the primitive that fits (`sequence`, `gauge`, `matrix`, `facts`), add it to `dimensions`, add the fields to every instance (use `check` to find gaps), and decide whether it belongs on the card or only in the drawer (`"card": false`).
- **View**: add an entry to `views` with a type and an icon. Table columns reference existing fields; nothing new is needed in the renderer.
- **Requirement**: if the new dimension is something units are held to, add requirements to `standard` at the same time — a dimension with no requirement is a dimension nobody is accountable for, which is worth noticing.

## Rules

- Scaffolding writes intent and data files. It never edits generated HTML.
- One instance per record, one record per instance. Duplicates double-count the fleet.
- After any scaffold, re-run the audit and regenerate the page, republishing to the same artifact URL so the team's link keeps working.
