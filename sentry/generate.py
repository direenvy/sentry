"""Generate Mekar Holdings' HR master, account extract, entitlements, access-change
log, exceptions register and expense claims — a clean population with known control
failures injected, each recorded in data/injected.json as the ground truth.

Everything is drawn from one seeded generator, so the dataset is reproducible byte
for byte and the tests can be scored: how many injected failures did each test find,
and did it flag anything that was not injected.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .config import (
    AS_OF, DATA, DEPARTMENT_ROLES, DORMANT_DAYS, EXPENSE_APPROVAL_LIMIT, PERIOD_END,
    PERIOD_START, PRIVILEGED, ROLE_ENTITLEMENTS, SEED, SOD_RULES,
)

SCALE = 7  # headcount multiplier over DEPARTMENT_ROLES weights → ~1,200 employees

FIRST = ["Ahmad", "Aisyah", "Amirul", "Farah", "Hafiz", "Nurul", "Syafiq", "Zahra", "Wei Ling", "Jun Hao", "Mei Yee",
         "Kai Xin", "Chee Keong", "Siew Mun", "Arun", "Priya", "Kavitha", "Suresh", "Ganesh", "Deepa", "Daniel", "Michelle",
         "Adrian", "Rachel", "Hakim", "Izzati", "Firdaus", "Nadia", "Yee Han", "Li Wen"]
LAST = ["bin Abdullah", "binti Ismail", "bin Rahman", "binti Yusof", "bin Hassan", "binti Omar", "Tan", "Lim", "Wong", "Lee",
        "Ng", "Chong", "Raj", "Kumar", "Pillai", "Nair", "Menon", "Fernandez", "Anak Jelani", "Wong"]

BUSINESS_DAYS = np.busdaycalendar(weekmask="1111100")


def bday_add(d: date, n: int) -> date:
    return np.busday_offset(np.datetime64(d), n, roll="forward", busdaycal=BUSINESS_DAYS).astype(date)


class Gen:
    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed)
        self.injected: list[dict] = []

    def note(self, control: str, key: str, detail: str, kind: str = "injected", **fields) -> None:
        """Ground truth. kind: injected (a failure this generator planted), design (a
        failure built into the company's role model), process (a failure the
        company's own workflow produces, e.g. the owner approving his own access),
        consequence (a second test that a planted failure also trips)."""
        self.injected.append({"control": control, "key": key, "kind": kind, "detail": detail, **fields})

    def rdate(self, start: date, end: date) -> date:
        return start + timedelta(days=int(self.rng.integers(0, (end - start).days + 1)))

    # ---- HR master ---------------------------------------------------------------------

    def employees(self) -> pd.DataFrame:
        rows = []
        n = 0
        for dept, roles in DEPARTMENT_ROLES.items():
            for role, w in roles:
                for _ in range(w * SCALE):
                    n += 1
                    hire = self.rdate(date(2012, 1, 1), date(2026, 5, 31))
                    rows.append({"employee_id": f"E{n:04d}", "name": f"{self.rng.choice(FIRST)} {self.rng.choice(LAST)}",
                                 "department": dept, "role": role, "hire_date": hire})
        df = pd.DataFrame(rows)
        # Managers: each department's managers/executives manage the rest of it.
        df["manager_id"] = None
        for dept, g in df.groupby("department"):
            mgrs = g[g.role.str.contains("Manager|Executive|Counsel")].employee_id.tolist() or g.employee_id.head(1).tolist()
            df.loc[g.index, "manager_id"] = self.rng.choice(mgrs, size=len(g))
        df.loc[df.employee_id == df.manager_id, "manager_id"] = df.employee_id.iloc[0]
        # Leavers: ~12% terminated before the period (history), ~10% within it.
        df["termination_date"] = None
        old_enough = df.index[df.hire_date < date(2024, 6, 30)]
        idx = self.rng.permutation(old_enough)
        hist = idx[: int(0.12 * len(df))]
        rest = self.rng.permutation([i for i in df.index if i not in set(hist)])
        period = rest[: int(0.10 * len(df))]
        for i in hist:
            df.at[i, "termination_date"] = self.rdate(max(df.at[i, "hire_date"] + timedelta(days=30), date(2020, 1, 1)), PERIOD_START - timedelta(days=1))
        for i in period:
            df.at[i, "termination_date"] = self.rdate(max(df.at[i, "hire_date"], PERIOD_START), PERIOD_END)
        df["status"] = np.where(df.termination_date.notna() & (pd.to_datetime(df.termination_date) <= pd.Timestamp(AS_OF)), "Terminated", "Active")
        # Movers: ~3% of active staff changed role within the period, within their department.
        df["previous_role"] = None
        df["role_changed_on"] = None
        active = df[df.status == "Active"].index
        for i in self.rng.choice(active, size=int(0.03 * len(active)), replace=False):
            dept = df.at[i, "department"]
            options = [r for r, _ in DEPARTMENT_ROLES[dept] if r != df.at[i, "role"]]
            if not options:
                continue
            df.at[i, "previous_role"] = df.at[i, "role"]
            df.at[i, "role"] = self.rng.choice(options)
            df.at[i, "role_changed_on"] = self.rdate(PERIOD_START, PERIOD_END - timedelta(days=30))
        return df

    # ---- accounts and entitlements ------------------------------------------------------

    def accounts(self, emp: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        acc, ent = [], []
        k = 0
        for e in emp.itertuples(index=False):
            systems = sorted({x.split(":")[0] for x in ROLE_ENTITLEMENTS[e.role]} | ({x.split(":")[0] for x in ROLE_ENTITLEMENTS[e.previous_role]} if e.previous_role else set()))
            for sys_ in systems:
                k += 1
                created = e.hire_date + timedelta(days=int(self.rng.integers(0, 3)))
                term = e.termination_date
                if pd.notna(term) and term is not None:
                    # Leavers: disabled on the day, or the next business day (the deadline).
                    disabled_on = bday_add(term, int(self.rng.integers(0, 2)))
                    enabled = False
                    last_logon = term - timedelta(days=int(self.rng.integers(0, 5)))
                else:
                    disabled_on = None
                    enabled = True
                    # Active users log on often; a few on leave for a few weeks.
                    gap = int(self.rng.choice([0, 1, 2, 3, 5, 8, 14, 30, 45], p=[.3, .2, .15, .1, .08, .07, .05, .03, .02]))
                    last_logon = AS_OF - timedelta(days=gap)
                    if last_logon < created:
                        last_logon = created
                aid = f"{sys_.lower()}.{e.employee_id.lower()}"
                acc.append({"account_id": aid, "system": sys_, "employee_id": e.employee_id, "account_type": "personal",
                            "created_on": created, "enabled": enabled, "disabled_on": disabled_on, "last_logon": last_logon})
                for x in ROLE_ENTITLEMENTS[e.role]:
                    if x.split(":")[0] == sys_:
                        granted = created if not e.previous_role or x in ROLE_ENTITLEMENTS[e.previous_role] else e.role_changed_on
                        ent.append({"account_id": aid, "entitlement": x, "granted_on": granted})
        # Service and generic accounts that legitimately exist (no employee).
        for name, sys_, ents in [("svc.backup", "AD", ["AD:user"]), ("svc.erp_batch", "ERP", ["ERP:gl_reporting"]),
                                 ("svc.hris_sync", "HRIS", ["HRIS:employee_view"]), ("svc.monitoring", "AD", ["AD:user"])]:
            acc.append({"account_id": name, "system": sys_, "employee_id": None, "account_type": "service",
                        "created_on": date(2019, 3, 1), "enabled": True, "disabled_on": None, "last_logon": AS_OF})
            ent += [{"account_id": name, "entitlement": x, "granted_on": date(2019, 3, 1)} for x in ents]
        return pd.DataFrame(acc), pd.DataFrame(ent)

    # ---- injected failures --------------------------------------------------------------

    def inject(self, emp: pd.DataFrame, acc: pd.DataFrame, ent: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        emp = emp.copy(); acc = acc.copy(); ent = ent.copy()
        active = emp[emp.status == "Active"]
        leavers = emp[(emp.status == "Terminated") & (pd.to_datetime(emp.termination_date) >= pd.Timestamp(PERIOD_START))]
        rows_acc, rows_ent, register = [], [], []

        # A1: orphan accounts — a contractor who was never in HR, a leaver purged from HR
        for i, sys_ in enumerate(["AD", "ERP", "AD", "HRIS", "AD", "ERP"]):
            aid = f"{sys_.lower()}.x{i:03d}"
            rows_acc.append({"account_id": aid, "system": sys_, "employee_id": f"E9{i:03d}", "account_type": "personal",
                             "created_on": self.rdate(date(2021, 1, 1), date(2025, 6, 30)), "enabled": True, "disabled_on": None,
                             "last_logon": AS_OF - timedelta(days=int(self.rng.integers(0, 20)))})
            rows_ent.append({"account_id": aid, "entitlement": f"{sys_}:user" if sys_ == "AD" else ("ERP:vendor_view" if sys_ == "ERP" else "HRIS:employee_view"), "granted_on": rows_acc[-1]["created_on"]})
            self.note("A1", aid, "account has no employee record in HR")
        # A1: accounts created before hire
        for i in self.rng.choice(active.index, 4, replace=False):
            aid = f"ad.{emp.at[i, 'employee_id'].lower()}"
            acc.loc[acc.account_id == aid, "created_on"] = emp.at[i, "hire_date"] - timedelta(days=int(self.rng.integers(10, 60)))
            self.note("A1", aid, "account created before the hire date")

        # A2: leavers still enabled (8) and disabled late (12)
        lv = self.rng.permutation(leavers.index)
        for i in lv[:8]:
            eid = emp.at[i, "employee_id"]
            m = acc.employee_id == eid
            acc.loc[m, ["enabled", "disabled_on"]] = [True, None]
            for aid in acc[m].account_id:
                self.note("A2", aid, "leaver's account still enabled at the extract date", employee_id=eid)
        for i in lv[8:20]:
            eid = emp.at[i, "employee_id"]
            m = acc.employee_id == eid
            late = bday_add(emp.at[i, "termination_date"], int(self.rng.integers(3, 40)))
            acc.loc[m, "disabled_on"] = late
            for aid in acc[m].account_id:
                self.note("A2", aid, f"leaver's account disabled late, on {late}", employee_id=eid)

        # A3: movers who kept the old role's entitlements (10) and non-movers with excess (8);
        # 5 excess entitlements have an approved exception in the register.
        movers = active[active.previous_role.notna()]
        for i in self.rng.choice(movers.index, min(10, len(movers)), replace=False):
            e = emp.loc[i]
            old = [x for x in ROLE_ENTITLEMENTS[e.previous_role] if x not in ROLE_ENTITLEMENTS[e.role]]
            for x in old[:2]:
                aid = f"{x.split(':')[0].lower()}.{e.employee_id.lower()}"
                if aid not in set(acc.account_id):
                    rows_acc.append({"account_id": aid, "system": x.split(":")[0], "employee_id": e.employee_id, "account_type": "personal",
                                     "created_on": e.hire_date, "enabled": True, "disabled_on": None, "last_logon": AS_OF - timedelta(days=3)})
                rows_ent.append({"account_id": aid, "entitlement": x, "granted_on": e.hire_date})
                self.note("A3", f"{e.employee_id}|{x}", f"mover kept {x} from previous role {e.previous_role}", employee_id=e.employee_id)
                for a, b, _ in SOD_RULES:
                    if {a, b} <= set(ROLE_ENTITLEMENTS[e.role]) | set(old[:2]) and x in (a, b):
                        self.note("S1", f"{e.employee_id}|{a}|{b}", f"the kept {x} conflicts with the new role's entitlements", kind="consequence", employee_id=e.employee_id)
        pool = [x for x in ROLE_ENTITLEMENTS.get("Finance Manager") + ROLE_ENTITLEMENTS.get("Procurement Manager") if x != "AD:user"]
        non_movers = active[active.previous_role.isna() & ~active.role.str.contains("Manager|Administrator")]
        chosen = self.rng.choice(non_movers.index, 13, replace=False)
        for n_, i in enumerate(chosen):
            e = emp.loc[i]
            x = str(self.rng.choice([p for p in pool if p not in ROLE_ENTITLEMENTS[e.role]]))
            aid = f"{x.split(':')[0].lower()}.{e.employee_id.lower()}"
            if aid not in set(acc.account_id) and aid not in {r["account_id"] for r in rows_acc}:
                rows_acc.append({"account_id": aid, "system": x.split(":")[0], "employee_id": e.employee_id, "account_type": "personal",
                                 "created_on": e.hire_date, "enabled": True, "disabled_on": None, "last_logon": AS_OF - timedelta(days=2)})
            rows_ent.append({"account_id": aid, "entitlement": x, "granted_on": self.rdate(date(2024, 1, 1), PERIOD_END)})
            if n_ < 5:
                register.append({"employee_id": e.employee_id, "entitlement": x, "ticket_id": f"EXC-{1040 + n_}", "approved_by": e.manager_id,
                                 "reason": "Temporary cover for vacancy, compensating review by Finance Manager", "expires_on": date(2026, 12, 31)})
            else:
                self.note("A3", f"{e.employee_id}|{x}", f"holds {x}, not in the role model for {e.role}, no approved exception", employee_id=e.employee_id)

        # A4: generic admin accounts, a non-IT role with SAP_ALL
        for aid, sys_, x in [("admin", "AD", "AD:domain_admin"), ("erp.firefighter", "ERP", "ERP:sap_all")]:
            rows_acc.append({"account_id": aid, "system": sys_, "employee_id": None, "account_type": "generic",
                             "created_on": date(2018, 6, 1), "enabled": True, "disabled_on": None, "last_logon": AS_OF - timedelta(days=1)})
            rows_ent.append({"account_id": aid, "entitlement": x, "granted_on": date(2018, 6, 1)})
            self.note("A4", f"{aid}|{x}", "privileged entitlement on a generic (unnamed) account")
        fa = active[active.role == "Financial Accountant"].index
        i = self.rng.choice(fa)
        e = emp.loc[i]
        rows_ent.append({"account_id": f"erp.{e.employee_id.lower()}", "entitlement": "ERP:sap_all", "granted_on": self.rdate(PERIOD_START, PERIOD_END)})
        self.note("A4", f"erp.{e.employee_id.lower()}|ERP:sap_all", f"SAP_ALL held by a {e.role}", employee_id=e.employee_id)
        self.note("A3", f"{e.employee_id}|ERP:sap_all", "same entitlement is also an excess against the role model", employee_id=e.employee_id)

        # A5: dormant enabled accounts (30), on active employees
        cands = acc[(acc.enabled) & acc.employee_id.isin(active.employee_id)].index
        for i in self.rng.choice(cands, 30, replace=False):
            acc.at[i, "last_logon"] = AS_OF - timedelta(days=int(self.rng.integers(DORMANT_DAYS + 1, 400)))
            self.note("A5", acc.at[i, "account_id"], f"enabled, last logon {acc.at[i, 'last_logon']}")

        # S1: SoD conflicts (14), 4 with a documented mitigating control
        rule_pairs = [(a, b) for a, b, _ in SOD_RULES]
        cands = active[~active.role.str.contains("Administrator|Executive|Counsel|Facilities|Operations Staff")]
        done = 0
        for i in self.rng.permutation(cands.index):
            e = emp.loc[i]
            have = set(ROLE_ENTITLEMENTS[e.role])
            options = [(a, b) for a, b in rule_pairs if (a in have) != (b in have)]
            if not options:
                continue
            a, b = options[int(self.rng.integers(len(options)))]
            x = b if a in have else a
            aid = f"{x.split(':')[0].lower()}.{e.employee_id.lower()}"
            if aid not in set(acc.account_id) and aid not in {r["account_id"] for r in rows_acc}:
                rows_acc.append({"account_id": aid, "system": x.split(":")[0], "employee_id": e.employee_id, "account_type": "personal",
                                 "created_on": e.hire_date, "enabled": True, "disabled_on": None, "last_logon": AS_OF - timedelta(days=1)})
            rows_ent.append({"account_id": aid, "entitlement": x, "granted_on": self.rdate(date(2024, 6, 1), PERIOD_END)})
            if done < 4:
                register.append({"employee_id": e.employee_id, "entitlement": x, "ticket_id": f"SOD-{210 + done}", "approved_by": e.manager_id,
                                 "reason": f"Conflict with {a if x == b else b} accepted; monthly review of the affected transactions by Internal Audit", "expires_on": date(2026, 12, 31)})
            else:
                self.note("S1", f"{e.employee_id}|{a}|{b}", f"holds {a} and {b} with no mitigating control", employee_id=e.employee_id)
                self.note("A3", f"{e.employee_id}|{x}", "the conflicting entitlement is also excess against the role model", employee_id=e.employee_id)
            done += 1
            if done == 14:
                break

        acc = pd.concat([acc, pd.DataFrame(rows_acc)], ignore_index=True).drop_duplicates("account_id", keep="first")
        ent = pd.concat([ent, pd.DataFrame(rows_ent)], ignore_index=True).drop_duplicates(["account_id", "entitlement"])
        return acc, ent, pd.DataFrame(register)

    # ---- access-change log ----------------------------------------------------------------

    def changes(self, emp: pd.DataFrame, acc: pd.DataFrame, ent: pd.DataFrame) -> pd.DataFrame:
        """One grant event per entitlement granted in the period, with a ticket and an
        approver; plus revokes for leavers. Then the injected failures."""
        mgr = emp.set_index("employee_id").manager_id.to_dict()
        # System owners approve grants on their system: the first active holder of the owning role.
        active = emp[emp.status == "Active"]
        owner = {sys_: str(active[active.role == role].employee_id.iloc[0])
                 for sys_, role in [("ERP", "Finance Manager"), ("HRIS", "HR Manager"), ("PAYROLL", "Payroll Manager"), ("AD", "IT Administrator")]}
        by_acc = acc.set_index("account_id").employee_id.to_dict()
        rows = []
        n = 0
        in_period = ent[(pd.to_datetime(ent.granted_on) >= pd.Timestamp(PERIOD_START)) & (pd.to_datetime(ent.granted_on) <= pd.Timestamp(PERIOD_END))]
        for r in in_period.itertuples(index=False):
            n += 1
            beneficiary = by_acc.get(r.account_id)
            requester = mgr.get(beneficiary, owner["AD"]) if beneficiary else owner[r.entitlement.split(":")[0]]
            approver = owner[r.entitlement.split(":")[0]]
            rows.append({"event_id": f"CHG-{n:05d}", "date": r.granted_on, "account_id": r.account_id, "entitlement": r.entitlement, "action": "grant",
                         "requester_id": requester, "ticket_id": f"REQ-{20000 + n}", "ticket_status": "Approved", "approver_id": approver})
        for r in acc[acc.disabled_on.notna() & (pd.to_datetime(acc.disabled_on) >= pd.Timestamp(PERIOD_START))].itertuples(index=False):
            n += 1
            rows.append({"event_id": f"CHG-{n:05d}", "date": r.disabled_on, "account_id": r.account_id, "entitlement": "*", "action": "disable",
                         "requester_id": owner["HRIS"], "ticket_id": f"REQ-{20000 + n}", "ticket_status": "Approved", "approver_id": owner[r.system]})
        df = pd.DataFrame(rows)
        grants = df[df.action == "grant"].index
        pick = self.rng.permutation(grants)
        for i in pick[:6]:
            df.loc[i, ["ticket_id", "ticket_status", "approver_id"]] = [None, None, None]
            self.note("A6", df.at[i, "event_id"], "grant with no ticket")
        for i in pick[6:9]:
            df.at[i, "approver_id"] = by_acc.get(df.at[i, "account_id"]) or df.at[i, "requester_id"]
            self.note("A6", df.at[i, "event_id"], "grant approved by its beneficiary")
        for i in pick[9:11]:
            df.at[i, "approver_id"] = df.at[i, "requester_id"]
            self.note("A6", df.at[i, "event_id"], "grant approved by its requester")
        for i in pick[11:12]:
            df.at[i, "ticket_status"] = "Pending"
            self.note("A6", df.at[i, "event_id"], "grant made while the ticket was still pending")
        return df.sort_values("date").reset_index(drop=True)

    # ---- expense claims --------------------------------------------------------------------

    def expenses(self, emp: pd.DataFrame) -> pd.DataFrame:
        mgr = emp.set_index("employee_id").manager_id.to_dict()
        staff = emp[(emp.status == "Active") | (pd.to_datetime(emp.termination_date) >= pd.Timestamp(PERIOD_START))]
        cats = ["Travel", "Meals", "Accommodation", "Supplies", "Training", "Client entertainment"]
        rows = []
        n = 0
        for e in staff.itertuples(index=False):
            k = int(self.rng.poisson(14 if e.department in ("Sales", "Operations") else 6))
            for _ in range(k):
                n += 1
                amt = float(np.round(self.rng.lognormal(4.6, 0.9), 2))
                d = self.rdate(PERIOD_START, PERIOD_END)
                rows.append({"claim_id": f"EXP-{n:06d}", "employee_id": e.employee_id, "department": e.department, "date": d,
                             "category": str(self.rng.choice(cats)), "amount": amt, "approver_id": mgr[e.employee_id], "status": "Paid"})
        df = pd.DataFrame(rows)
        # F1: three Sales claimants who split claims to stay under the approval limit
        sales = staff[staff.department == "Sales"].employee_id.tolist()
        for eid in self.rng.choice(sales, 3, replace=False):
            for _ in range(40):
                n += 1
                df.loc[len(df)] = {"claim_id": f"EXP-{n:06d}", "employee_id": eid, "department": "Sales", "date": self.rdate(PERIOD_START, PERIOD_END),
                                   "category": "Client entertainment", "amount": float(np.round(self.rng.uniform(900, 999.99), 2)), "approver_id": mgr[eid], "status": "Paid"}
            self.note("F1", eid, "40 claims between RM900 and RM999.99 — just under the RM1,000 limit")
        # F1: duplicates (same claimant, amount, date) — 15
        for i in self.rng.choice(df.index[: len(rows)], 15, replace=False):
            n += 1
            dup = df.loc[i].copy(); dup["claim_id"] = f"EXP-{n:06d}"
            df.loc[len(df)] = dup
            self.note("F1", dup["claim_id"], f"duplicate of {df.at[i, 'claim_id']}")
        # F1: self-approved claims — 10
        for i in self.rng.choice(df.index[: len(rows)], 10, replace=False):
            df.at[i, "approver_id"] = df.at[i, "employee_id"]
            self.note("F1", df.at[i, "claim_id"], "claim approved by the claimant")
        # F1: one Operations claimant with round amounts
        eid = str(self.rng.choice(staff[staff.department == "Operations"].employee_id))
        for _ in range(25):
            n += 1
            df.loc[len(df)] = {"claim_id": f"EXP-{n:06d}", "employee_id": eid, "department": "Operations", "date": self.rdate(PERIOD_START, PERIOD_END),
                               "category": "Supplies", "amount": float(self.rng.choice([100, 150, 200, 250, 300, 500])), "approver_id": mgr[eid], "status": "Paid"}
        self.note("F1", eid, "25 claims in round hundreds")
        return df.sort_values(["date", "claim_id"]).reset_index(drop=True)


def design_and_process(g: Gen, emp: pd.DataFrame, acc: pd.DataFrame, chg: pd.DataFrame) -> None:
    """Failures nobody planted: SoD conflicts the role model itself contains, and grants
    the workflow let the system owner approve for himself or his own team."""
    for role, ents in ROLE_ENTITLEMENTS.items():
        for a, b, _ in SOD_RULES:
            if a in ents and b in ents:
                for e in emp[(emp.role == role) & (emp.status == "Active")].itertuples(index=False):
                    g.note("S1", f"{e.employee_id}|{a}|{b}", f"the {role} role itself grants {a} and {b}", kind="design", employee_id=e.employee_id)
    cutoff = AS_OF - timedelta(days=DORMANT_DAYS)
    terminated = set(emp[emp.status == "Terminated"].employee_id)
    for a in acc[acc.enabled & acc.employee_id.isin(terminated)].itertuples(index=False):
        if pd.Timestamp(a.last_logon) < pd.Timestamp(cutoff):
            g.note("A5", a.account_id, "a leaver's still-enabled account is also dormant", kind="consequence", employee_id=a.employee_id)
    by_acc = acc.set_index("account_id").employee_id.to_dict()
    noted = {n["key"] for n in g.injected if n["control"] == "A6"}
    for c in chg[chg.action == "grant"].itertuples(index=False):
        if c.event_id in noted or pd.isna(c.ticket_id):
            continue
        if c.approver_id == by_acc.get(c.account_id):
            g.note("A6", c.event_id, "the system owner approved a grant to his own account", kind="process")
        elif c.approver_id == c.requester_id:
            g.note("A6", c.event_id, "the system owner requested and approved a grant for his own report", kind="process")


def main() -> None:
    g = Gen(SEED)
    emp = g.employees()
    acc, ent = g.accounts(emp)
    acc, ent, register = g.inject(emp, acc, ent)
    chg = g.changes(emp, acc, ent)
    exp = g.expenses(emp)
    design_and_process(g, emp, acc, chg)
    DATA.mkdir(exist_ok=True)
    for name, df in [("employees", emp), ("accounts", acc), ("entitlements", ent), ("access_changes", chg),
                     ("exceptions_register", register), ("expense_claims", exp)]:
        df.to_csv(DATA / f"{name}.csv", index=False, lineterminator="\n")
    (DATA / "injected.json").write_text(json.dumps(g.injected, indent=1, default=str), encoding="utf-8", newline="\n")
    print(f"employees {len(emp):,} ({(emp.status == 'Active').sum():,} active) · accounts {len(acc):,} · entitlements {len(ent):,} · "
          f"changes {len(chg):,} · register {len(register)} · claims {len(exp):,} · injected {len(g.injected)}")


if __name__ == "__main__":
    main()
