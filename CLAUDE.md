# harness

The engine every fleet repo runs on: the intent contract, the renderer, the scripts, and the reusable workflows. Also a Claude Code plugin marketplace, so the same skills that author an intent are available to CI.

## Layout

| Path | What it is |
| --- | --- |
| `.claude-plugin/marketplace.json` | Marketplace manifest. Fleet repos install `fleet-control@fleet-harness` from this repo's git URL |
| `plugins/fleet-control/` | The plugin: five skills, the intent schema, the renderer, three worked examples |
| `.github/workflows/on-intent-change.yml` | Reusable workflow fleet repos call when their intent changes |
| `.github/workflows/rebuild-from-intent.yml` | Reusable workflow for a repo whose `intent/` is its specification: on an intent change, dispatches Claude to bring the implementation into line and open a PR |
| `.github/workflows/selftest.yml` | Proves every worked example still scaffolds, audits and renders |

## The contract this repo owns

Fleet repos pin a tag (`@v1`). Anything that changes what an intent means, or what a data file must contain, is a breaking change for every fleet downstream:

- adding a field to the schema — safe, additive
- adding a render primitive, cell type, view type or band aggregate — safe
- **changing what an existing primitive or predicate does** — breaking. Cut a new major tag and migrate fleets deliberately
- changing `skeleton()` in `scaffold.py` — breaking. It defines the contract every fleet's data file is checked against

Never merge a change to this repo while `selftest.yml` is red. A fleet repo cannot tell a harness bug from its own drift.

## Changing the renderer

Load the `fleet-surface` skill's rules first. The design constraints are not cosmetic:

- neutral ground, `saturate()` at or below 1.05
- semantic colour means state and nothing else; the accent is for interaction
- a state most units are in most of the time renders neutral
- `absent` is never `ok`

A new capability belongs in the intent format *and* the renderer together, added to `intent.schema.json` and to at least one worked example in the same PR — otherwise nothing exercises it.

## Adding a worked example

A new example must come from a genuinely different domain. The examples exist to prove the abstraction is not a software pattern in disguise; a fourth software-shaped fleet proves nothing. Add it to the `selftest.yml` matrix in the same PR.

## Two kinds of intent, two workflows

A *fleet* intent (`on-intent-change.yml`) describes many units held against a standard; the data file is the implementation, and Claude is dispatched only when the contract breaks mechanically. A *product* intent (`rebuild-from-intent.yml`) is a specification under `intent/` from which source code is written; every change to it is a reason to reconcile the implementation, so Claude is dispatched on each change, with the diff. Both never edit the intent, both open pull requests, both run report-only without a credential.

The product caller is deliberately content-free so it can be copied between repositories unchanged: what the agent needs to know is in the intent, and what every such repo must share (the CI file names other systems read) is stated once, in the brief this workflow composes.
