---
name: fleet-audit
description: Score fleet instances against the standard declared in their intent and produce a ranked gap list. Use for "audit this", "score this repo/supplier/product", "how does it measure up", "what's missing", "which units fail the baseline", "conformance report", "is this fleet compliant", or as a CI gate on a data file. Reads the standard from the intent - no hard-coded rules.
---

# Audit against the declared standard

An audit compares instances to `standard.requirements` in the intent. It invents nothing: if a rule is not in the intent it is not enforced, and if it should be enforced, add it to the intent first.

## Run it

```bash
python3 references/audit.py <intent.json> <data.json>            # whole fleet, ranked
python3 references/audit.py <intent.json> <data.json> <unit-id>  # one instance
python3 references/audit.py <intent.json> <data.json> --json     # machine-readable
python3 references/audit.py <intent.json> <data.json> --strict   # non-zero exit on any required gap
```

Output is ordered by number of required gaps, then severity. Each gap names the requirement and its remedy from the intent.

`--strict` makes the same command a merge gate. Wire it where the fleet's data is produced, not as a separate opinion about quality.

## Declaring the standard

A requirement is a predicate that must hold, per class of unit:

```json
{
  "id": "coverage",
  "short": "cov",
  "label": "Line coverage at or above the tier threshold",
  "dimension": "quality",
  "remedy": "Raise coverage before the gate can be enforced",
  "classes": {
    "1": { "level": "required", "when": { "field": "cov", "gte": 80 } },
    "2": { "level": "required", "when": { "field": "cov", "gte": 70 } },
    "3": { "level": "advisory", "when": { "field": "cov", "gte": 50 } }
  }
}
```

- **`classes`** keys match the values of `unit.class` — the tier or criticality. Use `"*"` for a rule that applies to every class regardless. A class with no entry means the requirement does not apply to it, which renders as `·`, not as a pass.
- **`level`** is `required` (a gap that blocks) or `advisory` (a gap that is reported but does not block).
- **`when`** is a normal predicate, so it can reach built-in flags: `{"not": {"flag": "stale"}}` asserts nothing is behind the reference slot.
- **`remedy`** is what someone should do. Write the action, not the restatement — "Add the signing step to the release stage", not "Artifacts are not signed".
- **`dimension`** links the requirement to the dimension it belongs to, so gaps can be grouped the way the fleet is already presented.

## Writing good requirements

- **One requirement, one check.** If a rule needs "and", it is two requirements with two remedies.
- **Thresholds belong in the class, not the label.** The same requirement at different levels per tier is one entry with three clauses, never three requirements.
- **Severity and conformance are different questions.** Severity is "does this need attention now"; conformance is "does it meet the standard". A unit can be healthy today and still non-conformant, and that gap is exactly what a baseline is for. Keep the two rule sets separate even when they overlap.
- **If nearly everything fails a requirement**, the standard is aspirational rather than agreed. Say so — and consider `advisory` until it is real.

## Surfacing it

Add a `conformance` view to the intent and the matrix renders itself: units down the side, requirements across, `✓` met, `✕` required gap, `!` advisory, `·` not applicable, with a met/applicable count. A band cell with `"agg": "conformance"` shows the fleet's share of applicable requirements met. Both come from the same declaration the audit uses, so the page and the CI gate can never disagree.

## After an audit

Gaps are the input to the next step, not the end of it:

- a gap that is a data problem → fix the data file and re-run;
- a gap that is a real shortfall → remediate the thing itself, then refresh the data;
- a gap nobody intends to close → change the standard deliberately, in the intent, with the reason recorded — never by quietly dropping the requirement.

Then regenerate the control room with the fleet-surface skill so the page and the audit agree.
