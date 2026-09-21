"""Run the tests, rate the controls, write the deliverables:

  results/exceptions.csv   every exception, with the ground-truth kind it matched
  results/controls.json    population, exceptions, rate, rating, scoring per control
  results/benford.json     first-digit distributions by department
  results/FINDINGS.md      the findings memo (ratings, root causes, recommendations)
  frontend/data/*.json     the same, for the site
"""

from __future__ import annotations

import json

import pandas as pd

from .config import AS_OF, COMPANY, CONTROLS, FIELDWORK, MARTS, PERIOD_END, PERIOD_START, RESULTS, SOD_RULES, TOLERABLE_RATE, DATA
from .tests import TESTS, Extract, test_f1_expenses


def rate(exceptions: pd.DataFrame, population: int) -> str:
    """High: the rate exceeds the tolerable rate, or three or more High-severity
    exceptions (each one is a live exposure, whatever the rate). Medium: exceptions
    below both thresholds. Low: none."""
    if len(exceptions) == 0:
        return "Low"
    if len(exceptions) / population > TOLERABLE_RATE or (exceptions.severity == "High").sum() >= 3:
        return "High"
    return "Medium"


def main() -> None:
    x = Extract.load()
    truth = pd.DataFrame(json.load(open(DATA / "injected.json", encoding="utf-8")))
    kinds = truth.set_index(["control", "key"]).kind.to_dict()
    all_ex, controls = [], []
    benford = {}
    for c in CONTROLS:
        cid = c["id"]
        if cid == "F1":
            ex, pop, benford = test_f1_expenses(x)
        else:
            ex, pop = TESTS[cid](x)
        ex = ex.copy()
        ex["kind"] = [kinds.get((cid, k), "not in ground truth") for k in ex.key]
        all_ex.append(ex)
        found = set(ex.key)
        t = truth[truth.control == cid]
        by_kind = t.groupby("kind").apply(lambda g: int(g.key.isin(found).sum()), include_groups=False).to_dict()
        controls.append({
            **c,
            "population": int(pop),
            "exceptions": int(len(ex)),
            "rate": round(len(ex) / pop, 4) if pop else 0.0,
            "high": int((ex.severity == "High").sum()),
            "rating": "n/a (analytics)" if cid == "F1" else rate(ex, pop),
            "truth": {"total": int(len(t)), "by_kind": {k: int(v) for k, v in t.groupby("kind").size().items()}},
            "caught": {"total": int(t.key.isin(found).sum()), "by_kind": by_kind},
            "extra": int(len(found - set(t.key))),
        })
    exceptions = pd.concat(all_ex, ignore_index=True)
    exceptions.insert(0, "item", range(1, len(exceptions) + 1))
    RESULTS.mkdir(exist_ok=True)
    MARTS.mkdir(parents=True, exist_ok=True)
    exceptions.to_csv(RESULTS / "exceptions.csv", index=False, lineterminator="\n")
    summary = {
        "company": COMPANY, "period_start": str(PERIOD_START), "period_end": str(PERIOD_END), "as_of": str(AS_OF), "fieldwork": str(FIELDWORK),
        "employees": int(len(x.employees)), "active": int((x.employees.status == "Active").sum()),
        "accounts": int(len(x.accounts)), "entitlements": int(len(x.entitlements)), "changes": int(len(x.changes)), "claims": int(len(x.claims)),
        "exceptions": int(len(exceptions)), "truth": int(len(truth)),
        "ratings": {r: sum(1 for c in controls if c["rating"] == r) for r in ("High", "Medium", "Low")},
        "sod_rules": [{"a": a, "b": b, "risk": r} for a, b, r in SOD_RULES],
    }
    (RESULTS / "controls.json").write_text(json.dumps({"summary": summary, "controls": controls}, indent=1), encoding="utf-8", newline="\n")
    (RESULTS / "benford.json").write_text(json.dumps(benford, indent=1), encoding="utf-8", newline="\n")
    (MARTS / "controls.json").write_text(json.dumps({"summary": summary, "controls": controls}), encoding="utf-8", newline="\n")
    (MARTS / "benford.json").write_text(json.dumps(benford), encoding="utf-8", newline="\n")
    (MARTS / "exceptions.json").write_text(exceptions.to_json(orient="records"), encoding="utf-8", newline="\n")
    # SoD matrix for the site: conflicts found per rule.
    s1 = exceptions[exceptions.control == "S1"]
    matrix = []
    for a, b, r in SOD_RULES:
        n = int(s1.key.str.endswith(f"|{a}|{b}").sum())
        matrix.append({"a": a, "b": b, "risk": r, "conflicts": n, "design": int(((s1.kind == "design") & s1.key.str.endswith(f"|{a}|{b}")).sum())})
    (MARTS / "sod.json").write_text(json.dumps(matrix), encoding="utf-8", newline="\n")
    for c in controls:
        print(f"{c['id']}  {c['rating']:<16} {c['exceptions']:>3}/{c['population']:<6} {100 * c['rate']:5.1f}%   caught {c['caught']['total']}/{c['truth']['total']}  extra {c['extra']}")
    print(f"{len(exceptions)} exceptions; ratings {summary['ratings']}")


if __name__ == "__main__":
    main()
