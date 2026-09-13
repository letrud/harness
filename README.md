# harness

Shared machinery for repositories whose **intent is the contract and everything else is downstream of it**. Two kinds of repository call it:

```
                     harness (this repo, pinned @v1)
                     ├── on-intent-change      reusable workflow for a fleet repo
                     ├── rebuild-from-intent   reusable workflow for a product repo
                     ├── plugins/fleet-control the fleet engine: schema, scaffold, audit, renderer, skills
                     └── marketplace           fleet-control@fleet-harness, installable by people and by CI

fleet repos          lights-out         every repo in the estate, held to a golden-path baseline
                     ops                every value stream, held to an operating standard
                       intent + data + collector ──► audit ──► control room (static HTML, GitHub Pages)

product repos        psd2-cli           intent/ is the specification; the code is written from it
                       intent change ──► agent reconciles the implementation ──► pull request
```

Neither workflow ever edits an intent. Both open pull requests and never merge. Both run without a Claude credential — they then validate, report and stop.

**How work moves through these repositories — intent changes vs implementation changes, who proves what, how a pull request is accepted, how a release happens — is [WAY-OF-WORKING.md](WAY-OF-WORKING.md).** Read it before changing any of them.

## Fleet repos — `on-intent-change.yml`

A fleet intent describes many comparable units held against a standard. The data file is the implementation; a collector fills it from real sources. On a change under `intent/` the workflow checks, in order:

1. **schema** — the intent is well formed; hard fail
2. **contract** — every instance carries every field the intent now requires
3. **sources** — the collector declares where each field comes from
4. **audit** — ranked gaps against the declared standard; advisory, since raising a standard is *supposed* to produce gaps
5. **Claude** — only if 2 or 3 broke: installs `fleet-control` from this marketplace, updates `collector/sources.yml`, the adapters and the data file, opens a PR
6. **render** — regenerates and commits the control room

Conformance gaps are for humans to decide about; contract breaks are mechanical, and those are the only ones an agent is dispatched to fix.

```yaml
jobs:
  intent:
    uses: letrud/harness/.github/workflows/on-intent-change.yml@v1
    with:
      fleet: lights-out
      harness_repo: letrud/harness
      harness_ref: v1
    secrets:
      anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
      claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

Locally the same scripts run through each fleet repo's Makefile (`make check audit room collect`), which expects this repo at `../harness` or `HARNESS=`.

## Product repos — `rebuild-from-intent.yml`

A product intent is a specification under `intent/` from which source code is written. Every change to it is a reason to reconcile the implementation, so the agent is dispatched on each change, with the diff. The caller knows nothing about the repository and is copied between repos verbatim:

```yaml
on:
  push:
    branches: [main]
    paths: ["intent/**"]
  pull_request:                                 # the intent-boundary guard
  workflow_dispatch:
    inputs:
      before: { type: string, default: "" }   # set by the push hand-off
      after:  { type: string, default: "" }   # empty = full reconcile
permissions:
  contents: write
  pull-requests: write
  id-token: write
  actions: write
jobs:
  rebuild:
    uses: letrud/harness/.github/workflows/rebuild-from-intent.yml@v1
    with:
      before: ${{ inputs.before }}
      after: ${{ inputs.after }}
    secrets: inherit
```

Everything the agent needs — language, layout, distribution, how the implementation proves itself — it reads from the Markdown under `intent/`. Where the intent is silent it decides and records the decision in the PR, never in the intent. What the workflow adds on top:

- **the change** — the `intent/` diff of the push, or "full reconcile" on a bare dispatch. A push cannot run the agent directly (the action accepts dispatch, schedule and PR/issue events, not push), so a push re-dispatches the caller's own workflow with its before/after commits
- **secrets** — the agent's environment gets exactly the secrets the repository's own workflows reference, so it can run the intent's proofs against real test environments before committing; never the Claude credentials or the job token
- **resume** — a `rebuild/*` branch ahead of the default branch with no PR is checked out and continued, not redone; the agent commits and pushes as it goes so a cut-short session leaves its work behind
- **guard** — on every pull request: a change is to `intent/` or to the implementation, never both, and never to paths the automation owns (`derived_paths`, e.g. `data/,site/`). Enforced by the harness, so no repository's CI has to
- **conventions** — `build.yml` proves the implementation on every push and PR; `release.yml` ships on a `v*` tag. A change never carries generated files under `intent/` — the automation on the default branch writes those. These are the harness's, not the repo's, because other systems read stage state from them and every repo must behave the same way
- **transcript** — result, turns, cost and the agent's last words go in the job summary. On a private repo the full transcript is kept as an artifact for 30 days; on a public repo it is not, because it contains every file the agent read
- **budget** — `--max-turns 500` and a 120-minute job by default; override with `claude_args`

Optional inputs: `check` (a command whose outcome is shown to the agent), `instructions` (prefer stating things in the intent), `intent_dir`, `branch_prefix`, `autofix`.

## Credentials

Both workflows accept `anthropic_api_key` (Anthropic API, billed to API credit) and `claude_code_oauth_token` (a Pro/Max subscription, minted with `claude setup-token`). If both are set the API key is used. Neither is required.

GitHub Actions can only read **Actions** secrets — repository, environment or organization scope. Codespaces secrets are not visible to workflows. Sharing one secret across repos needs an organization.

The job token opens the pull requests, so each calling repository must allow Actions to create pull requests (Settings → Actions → General → Workflow permissions).

## The plugin

`plugins/fleet-control` is a Claude Code plugin with five skills — `fleet-intent`, `fleet-scaffold`, `fleet-audit`, `fleet-surface`, `product-intent` — the intent schema, the renderer and three worked examples from different domains. CI installs it from this repo as a marketplace; a person installs it the same way, so authoring an intent and maintaining one use the same rules. See `plugins/fleet-control/README.md`.

## Releasing

Callers pin `@v1`, and `v1` moves forward with every additive change. Tag a new major only for a change that alters what an existing intent means or what a data file must contain — see CLAUDE.md for what counts. `selftest.yml` must be green before the tag moves: it runs every worked example through scaffold, audit and render, and parses both reusable workflows.
