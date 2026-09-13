---
name: fleet-intent
description: Capture the intent of a fleet - any set of things held against a standard - as a declarative spec, so it can be rendered and reasoned about without writing code. Use for "model this domain", "capture the intent", "define the fleet", "write an intent spec", "what dimensions should we track", "add a dimension", "our repos/services/data products/suppliers/models/controls need an overview", or before building any control room. The intent is the artifact; everything else derives from it.
---

# Capture a fleet's intent

A **fleet** is a set of comparable things held against a standard: repos under a delivery standard, data products under a contract, suppliers under an assurance policy, models under a governance regime, stores under an operating standard. If the things are comparable and something says what "good" means for them, the pattern fits.

The intent spec is the deliverable. It declares what the fleet is, what dimensions it is judged on, what states those take, and when something needs attention. A renderer draws it; nothing needs to be coded per domain. Full field reference: `references/intent.schema.json`. Three worked, working examples in `references/examples/` - software delivery, supplier assurance, value streams - deliberately from different worlds to show what stays constant.

## Elicit in this order

Do not start from the screen. Start from the judgement being made.

1. **The unit.** What is one of these things, and what identifies it to the people who care? Name, a subtitle that locates it, who owns it, and how critical it is. If you cannot name the unit in one word, the fleet is probably two fleets.
2. **The standard.** What does "good" mean here, and who decided? A fleet with no standard produces a page nobody acts on - this is the question that most often exposes there is no shared answer yet. Say so rather than inventing one.
3. **The dimensions.** Two to four, no more. Each answers one question about a unit and holds together as a band on a card. Test each candidate: *can I say what this dimension is asking in one question?* "Can it ship without a human", "is what ships sound", "what is running where" pass. "Metrics" and "status" fail - they are buckets, not questions.
4. **The states.** The vocabulary each thing can be in, mapped to five roles: `ok`, `warn`, `crit`, `active` (happening now), `absent` (not configured / not applicable). Keep the domain's own words in the data; map them to roles in the spec. **`absent` is not `ok`** - "never set up" and "passing" must never render the same.
5. **Severity.** The rule that decides which units need attention. Write it as structured predicates over fields, and keep it conservative: if most units come out amber, the rule is wrong, not the fleet.
6. **Only then, the surface.** Which views, in what order, with which columns.

## Pressure-test before you render

- **Is a dimension actually two?** If its summary needs an "and", split it or drop half.
- **Does every state earn its colour?** A state most units are in most of the time must be neutral. In the software factory, an environment *ahead* of production is the ordinary flow, so it carries a grey arrow; only *behind* production is amber. Getting this wrong is the single most common way one of these pages becomes useless.
- **Is the reference point explicit?** Any comparison across slots needs a declared reference - production, the EU master contract, last quarter. Without it "drift" means nothing.
- **Would someone act on the top of the sorted list?** If not, the severity rule is not modelling the standard.
- **Can a unit be absent from a slot?** Nearly always yes. Model it as `null` + the `none` state, never as a missing key.

## The four render primitives

Dimensions are expressed with these, and only these. Choosing one forces useful precision about what kind of thing you are measuring.

| Primitive  | Shape of the thing                                   | Examples                                                        |
| ---------- | ---------------------------------------------------- | --------------------------------------------------------------- |
| `sequence` | Ordered steps, each in a state; optional `links` field of step → URL so a chip opens the thing in that state | build→test→scan→sign→release→deploy; screening→contract→approval  |
| `gauge`    | One number against a target, with a verdict and counts| coverage vs 80% + gate + open CVEs; control coverage vs 90% + audit |
| `matrix`   | The same thing present in several slots, comparable   | versions per environment; contract terms per market               |
| `facts`    | Flat attributes, each good or not                     | SBOM, signed, SLSA level; ISO 27001, SOC 2                        |

If a dimension fits none of them, it is usually prose, not a dimension. Say that rather than forcing it.

## Predicates

Severity rules and filters are structured, not expressions - safe to author, safe to read:

```json
{ "any": [
  { "field": "gate", "eq": "fail" },
  { "field": "vuln.c", "gt": 0 },
  { "anyOf": "stages", "eq": "crit" },
  { "flag": "drifted" }
] }
```

Operators: `eq ne gt gte lt lte in truthy`. Combinators: `all any not`. Collection tests: `anyOf` / `everyOf` over an object's values. Built-in flags: `drifted`, `stale`. Dotted paths address nested fields.

## Make it enforceable, not descriptive

An intent is read by agents as well as people - the harness dispatches one when the intent changes - and every gap in it becomes a guess downstream. Running two fleets and a product repo from intents taught what has to be stated, not implied:

- **Every field is a contract.** The moment the intent names a field, every instance must carry it and something must supply it. Declare where each comes from in `collector/sources.yml` - a real adapter (`live`), a human by design (`owned`), or nobody yet (`todo`, with a one-line note). `collect.py --check` fails when the intent requires a field nothing declares; that failure, not a conformance gap, is what dispatches an agent. **Never invent a plausible adapter** - a declared gap is honest, a fabricated source is worse than none.
- **Two questions, two consequences.** Conformance - "does this unit meet the standard" - is advisory: raising a standard is *supposed* to produce gaps, and they are for humans to decide about. The contract - "does the data carry what the intent requires" - is mechanical and breaks the build. Say which is which in the intent; an agent given a gap without its kind will fix the wrong thing.
- **Derived data has one writer.** Data a collector fills is refreshed by CI on the default branch, on a schedule. Nobody hand-edits a `live` field, and a conflict in a derived file is resolved by regenerating it, never by merging. Say so, or the first human push after the collector runs is a conflict.
- **Declare limitations, not only requirements.** A source that cannot supply a value yet, an environment that never exercises a state - give them a place (`todo`, `absent`, a note) so an honest zero is not mistaken for a broken adapter. `absent` is never `ok`; nor is `null` ever a guess.
- **Point at the thing.** A state is more useful with the URL of what put it there. `sequence` takes an optional `links` field of step → URL; a running build opens the run. Declare it in the intent, fill it in the data.
- **Silence is a decision surface.** Nothing outside the intent reaches the agent - not a commit message, not a chat. Where the intent is silent it decides and records the decision in the pull request, never in the intent. If you care about a choice, it is one line in the intent.
- **Specific knowledge goes in the data, not in prompts.** What an adapter learned about its system - a quirk, a mapping, a workflow-name-to-stage convention - lives as a declared field on the instance (`pipeline`, `envMap`), where the next implementer inherits it.

The `product-intent` skill covers the same ground for a specification that source code is written from; the harness's `WAY-OF-WORKING.md` says how a change then moves to acceptance and release.

## Data is separate

The intent describes the shape; a data file carries the instances. Keep them in separate files - the intent changes when the standard changes, the data changes constantly. `build.py` in the fleet-surface skill validates one against the other and refuses to render a mismatch, which is the point: the intent is enforceable, not decorative.

## Changing an intent

Adding a dimension, a view or a filter is cheap. Before changing what an existing dimension *means*, check whether it is really a new dimension - redefining one silently invalidates every trend anyone remembers. Bump `spec` only for a change that breaks existing data files.
