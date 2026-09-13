#!/usr/bin/env python3
"""Render a fleet control room from an intent spec plus instance data.

    python3 build.py <intent.json> <data.json> [out.html]

data.json is either a bare JSON array of instances, or an object with an
"items" (or "components"/"instances") array. Nothing about the fleet is
hard-coded here or in the template - the intent decides everything.
"""
import json, sys, pathlib

TEMPLATE = pathlib.Path(__file__).with_name("renderer.template.html")
KEYS = ("items", "components", "instances", "records", "data")


def load_items(raw):
    if isinstance(raw, list):
        return raw
    for k in KEYS:
        if isinstance(raw.get(k), list):
            return raw[k]
    raise SystemExit(f"data file has no array under any of {KEYS}")


def validate(spec, items):
    """Fail loudly on the mistakes that silently produce a blank or wrong page."""
    problems = []
    unit = spec.get("unit", {})
    idf = unit.get("id")
    if not idf:
        problems.append("unit.id is required")
    slots = spec.get("slots", [])
    matrix = next((d for d in spec.get("dimensions", []) if d.get("render", {}).get("type") == "matrix"), None)
    seen = set()
    for i, it in enumerate(items):
        key = it.get(idf) if idf else None
        if key is None:
            problems.append(f"item {i} has no '{idf}'")
        elif key in seen:
            problems.append(f"duplicate id '{key}'")
        else:
            seen.add(key)
        for dim in spec.get("dimensions", []):
            r = dim.get("render", {})
            if r.get("type") == "sequence":
                got = it.get(r["field"], {}) or {}
                missing = [s["key"] for s in r.get("steps", []) if s["key"] not in got]
                if missing:
                    problems.append(f"{key}: {r['field']} missing steps {missing} (use the absent state, never omit)")
            if r.get("type") == "gauge":
                if r["value"]["field"].split(".")[0] not in it:
                    problems.append(f"{key}: missing gauge field {r['value']['field']}")
        if matrix:
            for coll in (matrix["render"]["value"], matrix["render"]["state"]):
                got = it.get(coll, {}) or {}
                missing = [s for s in slots if s not in got]
                if missing:
                    problems.append(f"{key}: {coll} missing slots {missing}")
    trends = {len(it[spec["card"]["trend"]]) for it in items
              if spec.get("card", {}).get("trend") and isinstance(it.get(spec["card"]["trend"]), list)}
    if len(trends) > 1:
        problems.append(f"trend series have differing lengths {sorted(trends)} - sparklines will mislead")
    return problems


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    spec = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    items = load_items(json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")))
    out = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else "control-room.html")

    problems = validate(spec, items)
    if problems:
        print("Intent/data mismatch:", file=sys.stderr)
        for p in problems:
            print("  -", p, file=sys.stderr)
        raise SystemExit(1)

    html = (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", spec.get("title", "Control room"))
            .replace("__SPEC__", json.dumps(spec, ensure_ascii=False))
            .replace("__DATA__", json.dumps(items, ensure_ascii=False)))
    out.write_text(html, encoding="utf-8", newline="\n")
    print(f"{out}  ·  {len(items)} {spec.get('unit', {}).get('plural', 'items')}  ·  {len(html)//1024}KB")


if __name__ == "__main__":
    main()
