# Sentry — findings memo

**Subject:** logical access and segregation of duties at Mekar Holdings Berhad (fictional), four systems: ERP, HRIS, Payroll, Active Directory
**Period:** 1 July 2025 – 30 June 2026 · **Extract as at:** 30 June 2026 · **Fieldwork:** 21 September 2026
**Scope:** 1,204 employees (940 active), 1,896 accounts, 2,681 entitlements, 217 grants in the period, 10,971 expense claims
**Method:** full-population computer-assisted tests (`sentry/tests.py`); every exception in `results/exceptions.csv`; ratings per `sentry/report.py` (High: exception rate above 5% tolerable, or three or more High-severity exceptions; Medium: exceptions below both; Low: none)

The data is synthetic, generated with known failures so the tests could be scored. Every one of the 195 items in the ground truth was found and nothing else was flagged — see *Scoring* at the end. Read the findings as what these tests would say about a real company whose extracts looked like this.

## Summary of ratings

| # | Control | Population | Exceptions | Rate | Rating |
|---|---|---|---|---|---|
| A1 | Joiners: every account belongs to a current employee | 1,890 accounts | 10 | 0.5% | **High** |
| A2 | Leavers: access removed when employment ends | 183 accounts of 120 leavers | 29 | 15.8% | **High** |
| A3 | Movers: access matches the current role | 940 employees | 26 | 2.8% | Medium |
| A4 | Privileged access restricted and named | 52 privileged entitlements | 3 | 5.8% | **High** |
| A5 | Dormant accounts disabled | 1,514 enabled accounts | 38 | 2.5% | Medium |
| A6 | Access changes authorised | 217 grants | 16 | 7.4% | **High** |
| S1 | Segregation of duties | 940 employees | 44 | 4.7% | **High** |
| F1 | Expense analytics | 10,971 claims | 29 | — | analytics |

## Findings

### F-1 · A2 · Leaver de-provisioning does not work — High
Of 120 employees who left in the period, **20 had accounts that were not disabled by the next business day**: 8 employees' accounts (12 accounts) were **still enabled at the extract date**, between 5 and 268 days after they left, and 12 employees' accounts (17) were disabled 3–40 days late. Eight of the still-enabled accounts are also dormant (A5), which is the only reason they have not been used; the control that should have caught them is the one that failed.
*Root cause:* HR's termination record does not trigger de-provisioning; IT acts on an email from the line manager, and no one reconciles the two.
*Recommendation:* a weekly automated reconciliation of HR terminations against enabled accounts on all four systems, with the exceptions to the system owners; disable on the termination date, not after.

### F-2 · S1 · Three roles are designed with a segregation-of-duties conflict — High
44 active employees hold a conflicting pair of entitlements. **33 of them hold it by design**: the *Treasury Officer* role grants payment run *and* bank reconciliation (18 people), *AP Supervisor* grants invoice entry *and* approval (8), *Payroll Manager* grants payroll approval *and* bank-file release (7). This is a design deficiency — the role model itself, not any individual's access, breaks the rule — and it means the ERP's own SoD check, if it exists, has been switched off for these roles. The other 11 are individuals who accumulated a conflict (ten planted, one a mover who kept HR edit rights and now runs payroll). Four further conflicts are covered by a documented mitigating control in the exceptions register and are not counted.
*Recommendation:* split the three roles (payment run from bank reconciliation is the urgent one: one person can pay and hide the payment); until then, a monthly independent review of the transactions those 33 people processed, evidenced.

### F-3 · A6 · Grants are made without approval, or with the wrong approver — High
16 of 217 grants in the period fail the test: **6 with no ticket at all**, 7 approved by the beneficiary (3 planted, and **4 where the ERP owner approved grants to his own account**), 2 approved by their requester, 1 made while the ticket was still pending.
*Root cause:* the workflow lets the system owner approve anything on his system, including his own access; and provisioning does not check for a ticket.
*Recommendation:* the owner's own access is approved by the CFO; provisioning tooling refuses a grant without an approved ticket reference.

### F-4 · A4 · Privileged access on unnamed accounts and in the wrong hands — High
Two generic accounts — `admin` (domain admin) and `erp.firefighter` (SAP_ALL) — are enabled and in daily use, with no named individual accountable; and a *Financial Accountant* holds SAP_ALL, granted in the period, on a ticket that exists. Three of 52 privileged entitlements.
*Recommendation:* named admin accounts with a privileged-access management tool for the firefighter case; remove SAP_ALL from the accountant today and review what was done with it.

### F-5 · A1 · Accounts with no employee behind them — High
Six enabled, recently used accounts belong to employee IDs that are not in HR (contractors never onboarded through HR, or leavers purged from HR before their accounts were removed); four accounts were created 10–60 days before the person's hire date.
*Recommendation:* contractors go through HR like employees; accounts are created from the HR record, not before it.

### F-6 · A3 · Access accumulates across moves — Medium
26 employees hold entitlements outside their role: **7 of the 24 who changed role in the period kept entitlements from the previous role**, and 19 others hold an entitlement no one can explain — 1 of them SAP_ALL (F-4). Five further excess entitlements have an approved, dated exception in the register and are not counted.
*Recommendation:* a role change triggers the same review as a leaver: remove the old role's entitlements on the effective date.

### F-7 · A5 · Dormant accounts stay enabled — Medium
38 enabled accounts have not logged on in more than 90 days; 30 belong to active staff, 8 to leavers (F-1).
*Recommendation:* automated disablement at 90 days, with a re-enable path through the service desk.

### F-8 · F1 · Expense analytics — for substantive follow-up
- **Benford's law:** claims overall conform (mean absolute deviation 0.0075, "acceptable" on Nigrini's scale). **Sales does not** (MAD 0.0145, χ² 125 on 8 df): first digit 9 is over-represented. Drilling in finds **three Sales claimants with 40 claims each between RM900 and RM999.99** — every one under the RM1,000 second-approver limit. Splitting.
- **15 duplicate claims** (same claimant, amount and date) paid twice.
- **10 claims approved by the claimant.**
- One Operations claimant with **25 claims in round fifties** (RM100 to RM500), 66% of their claims.
*Recommendation:* the three Sales claimants and the duplicates go to Internal Audit for substantive testing; the approval workflow rejects self-approval; the limit test moves to a rolling monthly total per claimant.

## Scoring the tests against the ground truth

The dataset was generated with 195 failures recorded: 149 planted, 33 built into the role model, 4 produced by the company's own workflow, 9 consequences of a planted failure tripping a second test (a still-enabled leaver is also dormant; a mover's kept entitlement is also an SoD conflict). Every test found all of its ground truth and flagged nothing else:

| Test | Ground truth | Found | Extra |
|---|---|---|---|
| A1 | 10 | 10 | 0 |
| A2 | 29 | 29 | 0 |
| A3 | 26 | 26 | 0 |
| A4 | 3 | 3 | 0 |
| A5 | 38 (30 + 8 consequence) | 38 | 0 |
| A6 | 16 (12 + 4 process) | 16 | 0 |
| S1 | 44 (10 + 33 design + 1 consequence) | 44 | 0 |
| F1 | 29 | 29 | 0 |

That is a statement about the tests, not the company: on a real extract the tests would find what is there, and the ground truth is what makes it possible to say they would.
