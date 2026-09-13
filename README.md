# harness

The engine three fleet repos run on — and a Claude Code plugin marketplace, so CI works from the same skills a person does.

```
harness ──┬── plugins/fleet-control   the intent contract, renderer, scripts, skills
          ├── reusable workflow       called by each fleet repo on intent change
          └── marketplace             fleet-control@fleet-harness, installed in CI

software-factory ──► intent + data + collector ──► control room
ops              ──► intent + data + collector ──► control room
```

## Using it from a fleet repo

```yaml
jobs:
  intent:
    uses: letrud/harness/.github/workflows/on-intent-change.yml@v1
    with:
      fleet: software-factory
      harness_repo: letrud/harness
      harness_ref: v1
    secrets:
      anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

The workflow validates the intent, checks whether the fleet repo's data and collector still satisfy it, runs the audit, and — only when the contract actually broke — dispatches Claude Code to update that repo's local implementation and open a PR. It always regenerates the control room.

## Using it locally

```bash
git clone letrud/harness
git clone letrud/software-factory
cd software-factory && make check      # expects ../harness, or set HARNESS=
```

## Installing the plugin

In Claude Code or Cowork, add this repo as a marketplace and install `fleet-control`. The four skills — intent, scaffold, audit, surface — are then available for authoring and maintaining any fleet.

## Releasing

Fleet repos pin `@v1`. Tag a new major only for a change that alters what an existing intent means; see CLAUDE.md. `selftest.yml` must be green before tagging — it runs all three worked examples through scaffold, audit and render.
