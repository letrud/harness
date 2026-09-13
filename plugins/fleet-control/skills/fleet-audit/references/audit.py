#!/usr/bin/env python3
"""Score instances against the standard declared in a fleet intent.

    python3 audit.py <intent.json> <data.json> [unit-id] [--json] [--strict]

Prints a ranked gap list per unit: required gaps first, then advisory.
With --strict, exits non-zero when any required gap exists, so the same
command works as a CI gate. Nothing here is domain-specific - every rule
comes from intent.standard.requirements.
"""
import json, sys, pathlib

ROLES = {"crit": 0, "warn": 1, "ok": 2}


# ---------- predicates (mirror of the renderer's evaluator) ----------
def get(o, path):
    cur = o
    for k in str(path).split("."):
        if cur is None:
            return None
        cur = cur.get(k) if isinstance(cur, dict) else None
    return cur


def cmp_op(v, p):
    if "eq" in p: return v == p["eq"]
    if "ne" in p: return v != p["ne"]
    if "gt" in p: return (v or 0) > p["gt"]
    if "gte" in p: return (v or 0) >= p["gte"]
    if "lt" in p: return (v or 0) < p["lt"]
    if "lte" in p: return (v or 0) <= p["lte"]
    if "in" in p: return v in p["in"]
    if "truthy" in p: return bool(v) == p["truthy"]
    return bool(v)


class Fleet:
    def __init__(self, spec):
        self.spec = spec
        self.slots = spec.get("slots", [])
        self.matrix = next((d for d in spec.get("dimensions", [])
                            if d.get("render", {}).get("type") == "matrix"), None)
        self.unit = spec.get("unit", {})
        self.reqs = spec.get("standard", {}).get("requirements", [])

    # -- matrix comparison --
    @staticmethod
    def _parts(v):
        return [int("".join(c for c in p if c.isdigit()) or 0)
                for p in str(v or "0").split("-")[0].split(".")[:3]] + [0, 0, 0]

    def _cmp(self, a, b):
        how = (self.matrix or {}).get("render", {}).get("compare", "semver")
        if how == "number":
            return (float(a or 0) > float(b or 0)) - (float(a or 0) < float(b or 0))
        if how == "string":
            return (str(a) > str(b)) - (str(a) < str(b))
        x, y = self._parts(a), self._parts(b)
        for i in range(3):
            if x[i] != y[i]:
                return 1 if x[i] > y[i] else -1
        pa, pb = "-" in str(a), "-" in str(b)
        return 0 if pa == pb else (-1 if pa else 1)

    def ref_slot(self):
        if not self.matrix:
            return None
        r = self.matrix["render"].get("reference")
        return self.slots[-1] if not r or r == "last" else r

    def slot_value(self, it, s):
        return (get(it, self.matrix["render"]["value"]) or {}).get(s) if self.matrix else None

    def skew(self, it, s):
        if not self.matrix:
            return "same"
        ref = self.ref_slot()
        v, p = self.slot_value(it, s), self.slot_value(it, ref)
        if not v or not p or s == ref:
            return "same" if v else "absent"
        d = self._cmp(v, p)
        return "stale" if d < 0 else "ahead" if d > 0 else "same"

    def stale(self, it):
        return sum(1 for s in self.slots if self.skew(it, s) == "stale")

    def values_live(self, it):
        return len({self.slot_value(it, s) for s in self.slots if self.slot_value(it, s)})

    def drifted(self, it):
        r = (self.matrix or {}).get("render", {}).get("drift", {}) if self.matrix else {}
        return self.values_live(it) > r.get("distinctOver", 2) or (r.get("staleAny", True) and self.stale(it) > 0)

    # -- predicate evaluation --
    def test(self, p, it):
        if not p:
            return True
        if "all" in p: return all(self.test(q, it) for q in p["all"])
        if "any" in p: return any(self.test(q, it) for q in p["any"])
        if "not" in p: return not self.test(p["not"], it)
        if p.get("flag") == "drifted": return self.drifted(it)
        if p.get("flag") == "stale": return self.stale(it) > 0
        if p.get("flag") == "nonconformant": return bool(self.failures(it))
        if "severity" in p: return self.severity(it) == p["severity"]
        if "anyOf" in p: return any(cmp_op(v, p) for v in (get(it, p["anyOf"]) or {}).values())
        if "everyOf" in p: return all(cmp_op(v, p) for v in (get(it, p["everyOf"]) or {}).values())
        return cmp_op(get(it, p.get("field")), p)

    def severity(self, it):
        for rule in self.spec.get("severity", []):
            if self.test(rule["when"], it):
                return rule["role"]
        return "ok"

    # -- conformance --
    def clause(self, req, it):
        cls = str(get(it, self.unit["class"]["field"])) if self.unit.get("class") else "*"
        return (req.get("classes") or {}).get(cls) or (req.get("classes") or {}).get("*")

    def verdict(self, req, it):
        c = self.clause(req, it)
        if not c:
            return "na"
        if self.test(c["when"], it):
            return "met"
        return "failed" if c.get("level") == "required" else "advisory"

    def failures(self, it):
        return [r for r in self.reqs if self.verdict(r, it) == "failed"]

    def report(self, it):
        rows = [(self.verdict(r, it), r) for r in self.reqs]
        return {
            "id": get(it, self.unit["id"]),
            "class": get(it, self.unit["class"]["field"]) if self.unit.get("class") else None,
            "severity": self.severity(it),
            "met": sum(1 for v, _ in rows if v == "met"),
            "applicable": sum(1 for v, _ in rows if v != "na"),
            "required_gaps": [{"id": r["id"], "label": r["label"], "dimension": r.get("dimension"),
                               "remedy": r.get("remedy")} for v, r in rows if v == "failed"],
            "advisory_gaps": [{"id": r["id"], "label": r["label"], "dimension": r.get("dimension"),
                               "remedy": r.get("remedy")} for v, r in rows if v == "advisory"],
        }


def load_items(raw):
    if isinstance(raw, list):
        return raw
    for k in ("items", "components", "instances", "records", "data"):
        if isinstance(raw.get(k), list):
            return raw[k]
    raise SystemExit("data file has no instance array")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) < 2:
        raise SystemExit(__doc__)
    spec = json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8"))
    items = load_items(json.loads(pathlib.Path(args[1]).read_text(encoding="utf-8")))
    fleet = Fleet(spec)
    if not fleet.reqs:
        raise SystemExit("This intent declares no standard. Add standard.requirements before auditing.")
    if len(args) > 2:
        items = [it for it in items if str(get(it, fleet.unit["id"])) == args[2]]
        if not items:
            raise SystemExit(f"no {fleet.unit.get('singular', 'unit')} named {args[2]}")

    reports = sorted((fleet.report(it) for it in items),
                     key=lambda r: (-len(r["required_gaps"]), ROLES[r["severity"]], r["id"]))

    if "--json" in flags:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    else:
        label = spec.get("standard", {}).get("label", "the standard")
        blocked = sum(1 for r in reports if r["required_gaps"])
        print(f"{label} — {len(reports)} {spec['unit'].get('plural', 'units')}, "
              f"{blocked} with required gaps\n")
        for r in reports:
            cls = f" · {spec['unit']['class'].get('prefix', '')}{r['class']}" if r["class"] is not None else ""
            print(f"{r['id']}{cls} · {r['severity']} · {r['met']}/{r['applicable']} met")
            for i, g in enumerate(r["required_gaps"], 1):
                print(f"  {i}. [required] {g['label']}" + (f" — {g['remedy']}" if g["remedy"] else ""))
            for g in r["advisory_gaps"]:
                print(f"   · [advisory] {g['label']}")
            print()

    if "--strict" in flags and any(r["required_gaps"] for r in reports):
        sys.exit(1)


if __name__ == "__main__":
    main()
