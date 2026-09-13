# Fleet control

Capture what a fleet of things is judged on, as a spec. Scaffold it, audit it, render it. No code per domain.

## The idea

A **fleet** is any set of comparable things held against a standard — repos under a delivery standard, data products under a contract, suppliers under an assurance policy, models under a governance regime.

Two files describe one:

- an **intent spec** — the unit, its dimensions, the states they take, the standard it is held to, when something needs attention, and which views exist;
- a **data file** — the instances.

## The loop

```
                 ┌─────────────────────────────────────────┐
                 ▼                                         │
   intent.json ──┬──► scaffold ──► new instance, slot, dimension
                 │                        │                │
                 │                        ▼                │
                 ├──► audit  ◄────── data.json             │
                 │      │                 │                │
                 │      ├── ranked gaps ──┴─► remediate ───┘
                 │      └── --strict ──► CI gate
                 │
                 └──► surface ──► control-room.html ──► Artifact
```

The standard is declared once, in the intent. The audit enforces it and the conformance view draws it, so a CI gate and the published page can never disagree.

## Five skills

| Skill            | What it does                                                                              |
| ---------------- | ----------------------------------------------------------------------------------------- |
| `fleet-intent`   | Elicits and writes the intent: unit, standard, dimensions, states, severity, views.         |
| `fleet-scaffold` | Stands up a fleet, onboards an instance with honest day-one values, adds slots, dimensions. |
| `fleet-audit`    | Scores instances against the declared standard; ranked gaps, or a non-zero exit for CI.     |
| `fleet-surface`  | Renders and publishes the control room, validating data against the intent first.           |
| `product-intent` | Authors a specification an implementation is written from - what it must say for an agent to act on it correctly. |

## Four primitives

A dimension is expressed as exactly one of these, which is what keeps the format small and the pages consistent:

- **sequence** — ordered steps, each in a state (build→test→scan→sign→release→deploy; screening→contract→approval). An optional `links` field names an object of step → URL, so the chip for a running build opens the run
- **gauge** — a number against a target, with a verdict and counters (coverage vs 80% + gate + open CVEs)
- **matrix** — the same thing across slots, comparable (versions per environment; contract terms per market)
- **facts** — flat attributes, each good or not (SBOM, signed, SLSA level; ISO 27001, SOC 2)

## Worked examples

All in `skills/fleet-intent/references/examples/` — three fleets from different worlds, one renderer, one audit:

- `software-factory.intent.json` — 14 repos; automation, quality, environments, supply chain; 11 baseline requirements across three tiers
- `supplier-assurance.intent.json` — 8 suppliers; onboarding, assurance, markets, certification; 9 policy requirements
- `value-streams.intent.json` — 10 end-to-end value streams; flow, performance, regional footprint, resilience; 12 operating requirements

The value-stream example is the proof the pattern is not a software one: its states are the domain's own words (`flowing`, `bottleneck`, `broken`, `changing`, `manual`), its slots are regions rather than environments, and its reference point is a design authority rather than production.

```bash
E=skills/fleet-intent/references/examples

python3 skills/fleet-scaffold/references/scaffold.py $E/software-factory.intent.json \
    instance orders-api --class 1 --set squad=Ledger

python3 skills/fleet-audit/references/audit.py \
    $E/software-factory.intent.json $E/software-factory.data.json --strict

python3 skills/fleet-surface/references/build.py \
    $E/software-factory.intent.json $E/software-factory.data.json control-room.html
```

## Rules that survive every domain

- The intent is the artifact. Never hand-edit generated HTML; never fork the renderer per domain.
- `absent` is not `ok` — "never configured" must never look like "passing".
- A state most units are in most of the time renders neutral. Colour is for what needs attention.
- Any cross-slot comparison needs a declared reference point, or "drift" means nothing.
- Severity ("needs attention now") and conformance ("meets the standard") are different questions with separate rule sets.
- Scaffolding never seeds optimistic values. Day one must look like day one.
- `build.py` refuses to render data that does not match the intent. That refusal is the feature.
