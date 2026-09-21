"""The tests. Each takes the loaded extracts and returns the exceptions it found as a
DataFrame with the same columns: control, key, subject, detail, severity — where key
is the identifier the ground truth uses, so results can be scored.

Full-population tests, not samples: every account, every grant, every claim. That is
what a computer-assisted audit technique is for.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import (
    AS_OF, DATA, DORMANT_DAYS, EXPENSE_APPROVAL_LIMIT, LEAVER_DEADLINE_DAYS, PERIOD_END, PERIOD_START,
    PRIVILEGED, ROLE_ENTITLEMENTS, SOD_RULES,
)

COLS = ["control", "key", "subject", "detail", "severity"]


@dataclass
class Extract:
    employees: pd.DataFrame
    accounts: pd.DataFrame
    entitlements: pd.DataFrame
    changes: pd.DataFrame
    register: pd.DataFrame
    claims: pd.DataFrame

    @classmethod
    def load(cls) -> "Extract":
        emp = pd.read_csv(DATA / "employees.csv", parse_dates=["hire_date", "termination_date", "role_changed_on"])
        acc = pd.read_csv(DATA / "accounts.csv", parse_dates=["created_on", "disabled_on", "last_logon"])
        ent = pd.read_csv(DATA / "entitlements.csv", parse_dates=["granted_on"])
        chg = pd.read_csv(DATA / "access_changes.csv", parse_dates=["date"])
        reg = pd.read_csv(DATA / "exceptions_register.csv", parse_dates=["expires_on"])
        cl = pd.read_csv(DATA / "expense_claims.csv", parse_dates=["date"])
        return cls(emp, acc, ent, chg, reg, cl)

    def holdings(self) -> pd.DataFrame:
        """Entitlements joined to their account and employee: one row per holding."""
        return (self.entitlements.merge(self.accounts, on="account_id", how="left")
                .merge(self.employees[["employee_id", "name", "department", "role", "previous_role", "status", "manager_id"]], on="employee_id", how="left"))


def _df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=COLS) if rows else pd.DataFrame(columns=COLS)


def business_days_after(d: pd.Timestamp, n: int) -> pd.Timestamp:
    return pd.Timestamp(np.busday_offset(d.to_datetime64().astype("datetime64[D]"), n, roll="forward"))


# ---- A1 joiners --------------------------------------------------------------------------

def test_a1_joiners(x: Extract) -> tuple[pd.DataFrame, int]:
    acc = x.accounts[x.accounts.account_type == "personal"]
    hr = x.employees.set_index("employee_id")
    rows = []
    for a in acc.itertuples(index=False):
        if a.employee_id not in hr.index:
            rows.append({"control": "A1", "key": a.account_id, "subject": a.account_id,
                         "detail": f"{a.system} account for {a.employee_id}: no such employee in HR", "severity": "High" if a.enabled else "Medium"})
        elif a.created_on < hr.at[a.employee_id, "hire_date"]:
            rows.append({"control": "A1", "key": a.account_id, "subject": a.account_id,
                         "detail": f"created {a.created_on.date()}, {(hr.at[a.employee_id, 'hire_date'] - a.created_on).days} days before hire on {hr.at[a.employee_id, 'hire_date'].date()}", "severity": "Medium"})
    return _df(rows), len(acc)


# ---- A2 leavers --------------------------------------------------------------------------

def test_a2_leavers(x: Extract) -> tuple[pd.DataFrame, int]:
    lv = x.employees[(x.employees.termination_date >= pd.Timestamp(PERIOD_START)) & (x.employees.termination_date <= pd.Timestamp(PERIOD_END))]
    acc = x.accounts.merge(lv[["employee_id", "termination_date", "name"]], on="employee_id")
    rows = []
    for a in acc.itertuples(index=False):
        deadline = business_days_after(a.termination_date, LEAVER_DEADLINE_DAYS)
        if a.enabled or pd.isna(a.disabled_on):
            rows.append({"control": "A2", "key": a.account_id, "subject": a.account_id,
                         "detail": f"still enabled at {AS_OF}; employment ended {a.termination_date.date()} ({(pd.Timestamp(AS_OF) - a.termination_date).days} days ago)", "severity": "High"})
        elif a.disabled_on > deadline:
            rows.append({"control": "A2", "key": a.account_id, "subject": a.account_id,
                         "detail": f"disabled {a.disabled_on.date()}, {(a.disabled_on - a.termination_date).days} days after termination on {a.termination_date.date()} (deadline {deadline.date()})", "severity": "Medium"})
    return _df(rows), len(acc)


# ---- A3 movers / role model ---------------------------------------------------------------

def _approved_exceptions(x: Extract) -> set[tuple[str, str]]:
    reg = x.register[x.register.expires_on >= pd.Timestamp(AS_OF)]
    return set(zip(reg.employee_id, reg.entitlement))


def test_a3_role_model(x: Extract) -> tuple[pd.DataFrame, int]:
    h = x.holdings()
    h = h[(h.status == "Active") & (h.account_type == "personal") & h.role.notna()]
    approved = _approved_exceptions(x)
    rows = []
    for r in h.itertuples(index=False):
        if r.entitlement in ROLE_ENTITLEMENTS.get(r.role, []):
            continue
        if (r.employee_id, r.entitlement) in approved:
            continue
        mover = isinstance(r.previous_role, str) and r.entitlement in ROLE_ENTITLEMENTS.get(r.previous_role, [])
        rows.append({"control": "A3", "key": f"{r.employee_id}|{r.entitlement}", "subject": r.employee_id,
                     "detail": (f"{r.entitlement} not in the role model for {r.role}" + (f"; carried over from previous role {r.previous_role}" if mover else "")),
                     "severity": "High" if r.entitlement in PRIVILEGED else "Medium"})
    population = int(h.employee_id.nunique())
    return _df(rows), population


# ---- A4 privileged ----------------------------------------------------------------------

def test_a4_privileged(x: Extract) -> tuple[pd.DataFrame, int]:
    h = x.holdings()
    p = h[h.entitlement.isin(PRIVILEGED)]
    rows = []
    for r in p.itertuples(index=False):
        key = f"{r.account_id}|{r.entitlement}"
        if r.account_type != "personal":
            rows.append({"control": "A4", "key": key, "subject": r.account_id, "detail": f"{r.entitlement} on a {r.account_type} account — no named individual is accountable", "severity": "High"})
        elif pd.isna(r.role):
            rows.append({"control": "A4", "key": key, "subject": r.account_id, "detail": f"{r.entitlement} on an account with no employee record", "severity": "High"})
        elif r.status != "Active" and r.enabled:
            rows.append({"control": "A4", "key": key, "subject": r.account_id, "detail": f"{r.entitlement} on the enabled account of a terminated employee", "severity": "High"})
        elif r.entitlement not in ROLE_ENTITLEMENTS.get(r.role, []):
            rows.append({"control": "A4", "key": key, "subject": r.account_id, "detail": f"{r.entitlement} held by a {r.role} ({r.department}), a role not entitled to it", "severity": "High"})
    return _df(rows), len(p)


# ---- A5 dormant --------------------------------------------------------------------------

def test_a5_dormant(x: Extract) -> tuple[pd.DataFrame, int]:
    acc = x.accounts[x.accounts.enabled]
    cutoff = pd.Timestamp(AS_OF) - pd.Timedelta(days=DORMANT_DAYS)
    rows = []
    for a in acc.itertuples(index=False):
        last = a.last_logon if pd.notna(a.last_logon) else a.created_on
        if last < cutoff:
            rows.append({"control": "A5", "key": a.account_id, "subject": a.account_id,
                         "detail": f"enabled; last logon {last.date()}, {(pd.Timestamp(AS_OF) - last).days} days before the extract", "severity": "Medium"})
    return _df(rows), len(acc)


# ---- A6 authorised changes ----------------------------------------------------------------

def test_a6_authorised(x: Extract) -> tuple[pd.DataFrame, int]:
    g = x.changes[(x.changes.action == "grant") & (x.changes.date >= pd.Timestamp(PERIOD_START)) & (x.changes.date <= pd.Timestamp(PERIOD_END))]
    by_acc = x.accounts.set_index("account_id").employee_id.to_dict()
    rows = []
    for c in g.itertuples(index=False):
        beneficiary = by_acc.get(c.account_id)
        if pd.isna(c.ticket_id):
            rows.append({"control": "A6", "key": c.event_id, "subject": c.event_id, "detail": f"{c.entitlement} granted to {c.account_id} on {c.date.date()} with no ticket", "severity": "High"})
        elif c.ticket_status != "Approved":
            rows.append({"control": "A6", "key": c.event_id, "subject": c.event_id, "detail": f"{c.entitlement} granted to {c.account_id} while ticket {c.ticket_id} was {c.ticket_status}", "severity": "Medium"})
        elif c.approver_id == beneficiary:
            rows.append({"control": "A6", "key": c.event_id, "subject": c.event_id, "detail": f"{c.entitlement} on {c.account_id}: approved by the beneficiary ({beneficiary})", "severity": "High"})
        elif c.approver_id == c.requester_id:
            rows.append({"control": "A6", "key": c.event_id, "subject": c.event_id, "detail": f"{c.entitlement} on {c.account_id}: approver is the requester ({c.requester_id})", "severity": "Medium"})
    return _df(rows), len(g)


# ---- S1 segregation of duties ---------------------------------------------------------------

def test_s1_sod(x: Extract) -> tuple[pd.DataFrame, int]:
    h = x.holdings()
    h = h[(h.status == "Active") & (h.account_type == "personal")]
    held = h.groupby("employee_id").entitlement.agg(set)
    who = x.employees.set_index("employee_id")
    mitigated = _approved_exceptions(x)
    rows = []
    for eid, ents in held.items():
        for a, b, risk in SOD_RULES:
            if a in ents and b in ents:
                if (eid, a) in mitigated or (eid, b) in mitigated:
                    continue
                rows.append({"control": "S1", "key": f"{eid}|{a}|{b}", "subject": eid,
                             "detail": f"{who.at[eid, 'role']} ({who.at[eid, 'department']}) holds {a} and {b}: {risk.lower()}", "severity": "High"})
    return _df(rows), int(len(held))


# ---- F1 expense analytics -------------------------------------------------------------------

BENFORD = {d: np.log10(1 + 1 / d) for d in range(1, 10)}


def benford(amounts: pd.Series) -> pd.DataFrame:
    s = amounts[amounts >= 10]
    first = s.astype(str).str.lstrip("0.").str[0].astype(int)
    obs = first.value_counts().reindex(range(1, 10), fill_value=0)
    n = int(obs.sum())
    out = pd.DataFrame({"digit": range(1, 10), "observed": obs.values, "expected": [BENFORD[d] * n for d in range(1, 10)]})
    out["observed_pct"] = 100 * out.observed / n
    out["expected_pct"] = 100 * out.expected / n
    out["chi2"] = (out.observed - out.expected) ** 2 / out.expected
    return out


def mad(b: pd.DataFrame) -> float:
    """Mean absolute deviation of first-digit proportions (Nigrini): < 0.006 close
    conformity, 0.006–0.012 acceptable, 0.012–0.015 marginal, > 0.015 nonconformity."""
    return float((abs(b.observed_pct - b.expected_pct) / 100).mean())


def test_f1_expenses(x: Extract) -> tuple[pd.DataFrame, int, dict]:
    cl = x.claims[(x.claims.date >= pd.Timestamp(PERIOD_START)) & (x.claims.date <= pd.Timestamp(PERIOD_END))]
    rows = []
    # Just under the limit, per claimant: 10 or more claims in [90%, 100%) of the limit.
    near = cl[(cl.amount >= 0.9 * EXPENSE_APPROVAL_LIMIT) & (cl.amount < EXPENSE_APPROVAL_LIMIT)]
    counts = near.groupby("employee_id").size()
    share = counts / cl.groupby("employee_id").size().reindex(counts.index)
    for eid, k in counts[(counts >= 10) & (share >= 0.25)].items():
        rows.append({"control": "F1", "key": eid, "subject": eid, "detail": f"{k} claims between RM{0.9 * EXPENSE_APPROVAL_LIMIT:,.0f} and RM{EXPENSE_APPROVAL_LIMIT:,.0f} ({100 * share[eid]:.0f}% of their claims) — splitting to stay under the limit", "severity": "High"})
    # Duplicates: same claimant, amount and date, more than once.
    dup = cl[cl.duplicated(["employee_id", "amount", "date"], keep="first")]
    for c in dup.itertuples(index=False):
        rows.append({"control": "F1", "key": c.claim_id, "subject": c.claim_id, "detail": f"duplicate: {c.employee_id}, RM{c.amount:,.2f} on {c.date.date()}", "severity": "Medium"})
    # Self-approved.
    for c in cl[cl.approver_id == cl.employee_id].itertuples(index=False):
        rows.append({"control": "F1", "key": c.claim_id, "subject": c.claim_id, "detail": f"approved by the claimant: RM{c.amount:,.2f} on {c.date.date()}", "severity": "High"})
    # Round amounts, per claimant: 15 or more claims in round fifties that are also
    # at least 30% of their claims (a real supplies budget can be round now and then).
    rnd = cl[(cl.amount % 50 == 0) & (cl.amount >= 100)].groupby("employee_id").size()
    rshare = rnd / cl.groupby("employee_id").size().reindex(rnd.index)
    for eid, k in rnd[(rnd >= 15) & (rshare >= 0.3)].items():
        rows.append({"control": "F1", "key": eid, "subject": eid, "detail": f"{k} claims in round fifties ({100 * rshare[eid]:.0f}% of their claims)", "severity": "Medium"})
    # Benford by department, for the narrative (not exceptions).
    bf = {"all": benford(cl.amount)}
    for d, g in cl.groupby("department"):
        bf[d] = benford(g.amount)
    summary = {k: {"n": int(v.observed.sum()), "mad": round(mad(v), 4), "chi2": round(float(v.chi2.sum()), 1),
                   "digits": v[["digit", "observed_pct", "expected_pct"]].round(2).to_dict(orient="records")} for k, v in bf.items()}
    return _df(rows), len(cl), summary


TESTS = {
    "A1": test_a1_joiners, "A2": test_a2_leavers, "A3": test_a3_role_model, "A4": test_a4_privileged,
    "A5": test_a5_dormant, "A6": test_a6_authorised, "S1": test_s1_sod,
}
