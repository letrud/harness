#!/usr/bin/env python3
"""Scaffold from a fleet intent — skeletons and fleet-wide edits.

    python3 scaffold.py <intent.json> instance <id> [--class 1] [--set k=v ...]
        Emit one honest day-one record: sequence steps absent, gauges at zero,
        matrix slots empty, facts false. Printed as JSON.

    python3 scaffold.py <intent.json> data <data.json> add-slot <name> [--after <slot>]
        Add a slot (environment, market, region) to the intent and to every
        instance in the data file. Writes both in place.

    python3 scaffold.py <intent.json> data <data.json> check
        Report which fields each instance is missing against the intent.

Never seeds optimistic values: a thing that has never run must look like it.
"""
import json, sys, pathlib


def absent_state(spec):
    """The domain's own word for 'not configured'."""
    for word, role in (spec.get("states") or {}).items():
        if role == "absent":
            return word
    return "idle"


def numeric_fields(spec):
    """Fields the intent itself treats as numbers - so the skeleton seeds 0, not ""."""
    nums = set()
    for c in spec.get("band", []):
        if c.get("agg") in ("avg", "sum") and c.get("field"):
            nums.add(c["field"])
    unit = spec.get("unit", {})
    textual = {unit.get("id"), unit.get("label"), unit.get("subtitle")}
    for d in spec.get("dimensions", []):
        for det in d.get("details", []):
            if det.get("mono"):
                textual.add(det["field"])
    for f in spec.get("card", {}).get("footer", []):
        textual.add(f["field"])
    for so in spec.get("sorts", []):
        # a sort key is numeric unless it names the unit or a mono/text field
        if so.get("field") and so["field"] not in textual:
            nums.add(so["field"])
    for d in spec.get("dimensions", []):
        r = d.get("render", {})
        if r.get("type") == "gauge":
            nums.add(r["value"]["field"])
        for det in d.get("details", []):
            if "%" in (det.get("suffix") or ""):
                nums.add(det["field"])
    return {f.split(".")[0] for f in nums}


def boolean_fields(spec):
    """Fields the declared standard tests for truthiness - seed False, not ""."""
    found = set()

    def walk(p):
        if not isinstance(p, dict):
            return
        if "truthy" in p and p.get("field"):
            found.add(p["field"].split(".")[0])
        for k in ("all", "any"):
            for q in p.get(k, []):
                walk(q)
        walk(p.get("not"))

    for r in spec.get("standard", {}).get("requirements", []):
        for c in (r.get("classes") or {}).values():
            walk(c.get("when"))
    return found


def skeleton(spec, uid, cls=None, overrides=None):
    unit, out = spec.get("unit", {}), {}
    nums, bools = numeric_fields(spec), boolean_fields(spec)
    out[unit["id"]] = uid
    if unit.get("label") and unit["label"] != unit["id"]:
        out[unit["label"]] = uid
    for key in ("subtitle",):
        if unit.get(key):
            out[unit[key]] = ""
    if unit.get("group"):
        out[unit["group"]["field"]] = ""
    if unit.get("class"):
        out[unit["class"]["field"]] = cls if cls is not None else 3
    if unit.get("accent"):
        out.setdefault(unit["accent"]["field"], "")

    absent = absent_state(spec)
    for d in spec.get("dimensions", []):
        r = d.get("render", {})
        if r.get("type") == "sequence":
            out[r["field"]] = {s["key"]: absent for s in r.get("steps", [])}
        elif r.get("type") == "gauge":
            out[r["value"]["field"]] = 0
            if r.get("verdict"):
                roles = r["verdict"].get("roles", {})
                worst = next((k for k, v in roles.items() if v == "crit"), None)
                out[r["verdict"]["field"]] = worst or list(roles)[0] if roles else ""
            for c in r.get("counters", []):
                path = c["field"].split(".")
                out.setdefault(path[0], {})
                if len(path) > 1:
                    out[path[0]][path[1]] = 0
                else:
                    out[path[0]] = 0
        elif r.get("type") == "matrix":
            out[r["value"]] = {s: None for s in spec.get("slots", [])}
            out[r["state"]] = {s: "none" for s in spec.get("slots", [])}
        elif r.get("type") == "facts":
            for f in r.get("facts", []):
                out.setdefault(f["field"], False if f.get("as") == "bool" else 0)
        for det in d.get("details", []):
            key = det["field"].split(".")[0]
            out.setdefault(key, False if key in bools else 0 if key in nums else "")
        if d.get("trend"):
            out[d["trend"]["field"]] = []
    if spec.get("card", {}).get("trend"):
        out[spec["card"]["trend"]] = []
    for f in spec.get("card", {}).get("footer", []):
        out.setdefault(f["field"], "")
    for so in spec.get("sorts", []):
        if so.get("field"):
            out.setdefault(so["field"], 0 if so["field"] in nums else "")
    for k, v in (overrides or {}).items():
        out[k] = v
    return out


def load_items(raw):
    for k in ("items", "components", "instances", "records", "data"):
        if isinstance(raw.get(k), list):
            return k, raw[k]
    raise SystemExit("data file has no instance array")


def add_slot(spec_path, spec, data_path, name, after=None):
    slots = spec.setdefault("slots", [])
    if name in slots:
        raise SystemExit(f"slot '{name}' already exists")
    idx = slots.index(after) + 1 if after in slots else len(slots) - 1
    slots.insert(idx, name)
    raw = json.loads(pathlib.Path(data_path).read_text(encoding="utf-8"))
    key, items = load_items(raw)
    matrix = next((d for d in spec["dimensions"] if d["render"]["type"] == "matrix"), None)
    if not matrix:
        raise SystemExit("intent has no matrix dimension, so it has no slots")
    for it in items:
        it.setdefault(matrix["render"]["value"], {})[name] = None
        it.setdefault(matrix["render"]["state"], {})[name] = "none"
    pathlib.Path(spec_path).write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    pathlib.Path(data_path).write_text(json.dumps({key: items}, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"slot '{name}' added at position {idx + 1} of {len(slots)}; {len(items)} instances updated")
    if len(slots) > 4:
        print("note: more than four slots — check the card grid at phone width")


def check(spec, data_path):
    raw = json.loads(pathlib.Path(data_path).read_text(encoding="utf-8"))
    _, items = load_items(raw)
    ref = skeleton(spec, "__ref__")
    problems = 0
    for it in items:
        missing = [k for k in ref if k not in it]
        if missing:
            problems += 1
            print(f"{it.get(spec['unit']['id'], '?')}: missing {', '.join(missing)}")
    print(f"{len(items)} instances checked, {problems} incomplete")


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    spec_path = sys.argv[1]
    spec = json.loads(pathlib.Path(spec_path).read_text(encoding="utf-8"))
    mode = sys.argv[2]

    if mode == "instance":
        uid = sys.argv[3]
        cls, overrides = None, {}
        args = sys.argv[4:]
        while args:
            a = args.pop(0)
            if a == "--class":
                cls = args.pop(0)
                cls = int(cls) if cls.isdigit() else cls
            elif a == "--set":
                k, _, v = args.pop(0).partition("=")
                overrides[k] = json.loads(v) if v[:1] in "[{0123456789tfn\"" else v
        print(json.dumps(skeleton(spec, uid, cls, overrides), indent=2, ensure_ascii=False))

    elif mode == "data":
        data_path = sys.argv[3]
        sub = sys.argv[4]
        if sub == "add-slot":
            after = sys.argv[sys.argv.index("--after") + 1] if "--after" in sys.argv else None
            add_slot(spec_path, spec, data_path, sys.argv[5], after)
        elif sub == "check":
            check(spec, data_path)
        else:
            raise SystemExit(__doc__)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
