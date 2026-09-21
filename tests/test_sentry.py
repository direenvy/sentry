"""The audit's own controls: the dataset regenerates byte for byte, every test finds
its ground truth and nothing else, and a few invariants that would make the results
meaningless if they failed."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from sentry.config import DATA, ROLE_ENTITLEMENTS, SOD_RULES
from sentry.tests import TESTS, Extract, benford, mad
from sentry.tests import test_f1_expenses as f1_expenses

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def x() -> Extract:
    return Extract.load()


@pytest.fixture(scope="module")
def truth() -> pd.DataFrame:
    return pd.DataFrame(json.load(open(DATA / "injected.json", encoding="utf-8")))


def test_generator_is_deterministic(tmp_path):
    """Regenerating into a temp dir gives the same bytes as data/ — the audit's
    subject cannot drift between runs."""
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.glob("*")}
    env = {"SENTRY_DATA": str(tmp_path)}
    code = "import sentry.config as c, os; from pathlib import Path; c.DATA = Path(os.environ['SENTRY_DATA']); import sentry.generate as g; g.DATA = c.DATA; g.main()"
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, env={**dict(__import__('os').environ), **env}, check=True, capture_output=True)
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.glob("*")}
    assert after == before


@pytest.mark.parametrize("cid", list(TESTS) + ["F1"])
def test_finds_ground_truth_exactly(x, truth, cid):
    ex, _ = TESTS[cid](x) if cid != "F1" else f1_expenses(x)[:2]
    found, expected = set(ex.key), set(truth[truth.control == cid].key)
    assert found == expected, f"{cid}: missed {sorted(expected - found)[:5]}, extra {sorted(found - expected)[:5]}"


def test_one_account_per_id(x):
    assert x.accounts.account_id.is_unique


def test_every_personal_account_has_an_employee_or_is_an_a1_exception(x, truth):
    orphans = set(x.accounts[(x.accounts.account_type == "personal") & ~x.accounts.employee_id.isin(x.employees.employee_id)].account_id)
    assert orphans == set(truth[(truth.control == "A1") & truth.detail.str.contains("no employee")].key)


def test_role_model_conflicts_are_the_design_ground_truth(truth):
    roles = {r for r, ents in ROLE_ENTITLEMENTS.items() for a, b, _ in SOD_RULES if a in ents and b in ents}
    assert roles == {"Treasury Officer", "AP Supervisor", "Payroll Manager"}
    assert (truth[truth.control == "S1"].kind == "design").sum() == 33


def test_benford_reference_distribution():
    """A geometric series spans digits evenly on a log scale; Benford must call it
    conforming."""
    s = pd.Series([1.5 ** k for k in range(1, 60)])
    assert mad(benford(s)) < 0.02


def test_ratings_follow_the_rule():
    r = json.load(open(ROOT / "results" / "controls.json", encoding="utf-8"))["controls"]
    for c in r:
        if c["id"] == "F1":
            continue
        expected = "Low" if c["exceptions"] == 0 else ("High" if c["rate"] > 0.05 or c["high"] >= 3 else "Medium")
        assert c["rating"] == expected, c["id"]
