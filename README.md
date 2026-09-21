# Sentry

**Live: https://sentry-ruddy.vercel.app** · [Findings memo](results/FINDINGS.md) · [Every exception](results/exceptions.csv) · [The tests](sentry/tests.py)

An IT audit of logical access and segregation of duties at a company that does not
exist — Mekar Holdings Berhad, four systems, 1,204 employees — with the one thing a
real audit can never have: the answer key. The HR master, account extract,
entitlements, access-change log, exceptions register and a year of expense claims
are generated from a seed with **195 control failures planted, designed in, or
produced by the company's own workflow**, each recorded. Seven access controls and
a set of fraud analytics are tested over the full population, every exception is in
a register, the controls are rated, and the findings memo says what a company whose
extracts looked like this should do. Then the tests are scored: every one of the 195
was found, and nothing else was flagged.

The dataset is fictional. The tests are the ones an IT auditor runs on a real
extract, and the point of the ground truth is to be able to say they work.

## What the audit found

| # | Control | Population | Exceptions | Rating |
|---|---|---|---|---|
| A1 | Joiners: every account belongs to a current employee | 1,890 accounts | 10 (0.5%) | **High** — 6 enabled accounts with no one in HR |
| A2 | Leavers: access removed by the next business day | 183 accounts of 120 leavers | 29 (15.8%) | **High** — 8 leavers still enabled up to 268 days on |
| A3 | Movers: access matches the current role | 940 employees | 26 (2.8%) | Medium — 7 of 24 movers kept the old role's access |
| A4 | Privileged access restricted and named | 52 entitlements | 3 (5.8%) | **High** — generic `admin` and `erp.firefighter`; SAP_ALL on an accountant |
| A5 | Dormant accounts disabled | 1,514 enabled | 38 (2.5%) | Medium |
| A6 | Access changes authorised | 217 grants | 16 (7.4%) | **High** — 6 without a ticket; the ERP owner approving his own |
| S1 | Segregation of duties | 940 employees | 44 (4.7%) | **High** — 33 by design of three roles |
| F1 | Expense analytics | 10,971 claims | 29 | Benford flags Sales; three claimants splitting under RM1,000 |

The finding worth reading is **S1**: the company's role model gives *Treasury Officer*
payment run and bank reconciliation, *AP Supervisor* invoice entry and approval,
*Payroll Manager* payroll approval and bank-file release. Thirty-three people hold a
conflict not because anyone made a mistake with their access but because the roles
were designed that way — a design deficiency, which is a different remediation from
the eleven individuals who accumulated one. The generator did not plant those; the
test found them in the role model I wrote, and the ground truth was extended to
record them rather than the model quietly fixed.

## How it is built

```
sentry/config.py     scope, systems, the role-based access model, SoD rules, thresholds, the controls with COBIT / ISO 27001 / SOX mapping
sentry/generate.py   the seeded generator: clean population, then injected failures, each noted; design and process failures recorded after
sentry/tests.py      one function per control over the full population; Benford, near-limit, duplicate, self-approval, round-amount analytics
sentry/report.py     ratings, exceptions register, scoring against the ground truth, marts for the site
results/             exceptions.csv (195 rows), controls.json, benford.json, FINDINGS.md
tests/               pytest: the generator is byte-for-byte deterministic; every test finds exactly its ground truth; invariants
frontend/            the report as a site (Next.js, New Genre)
```

`python -m sentry.generate && python -m sentry.report && pytest` reproduces everything;
CI does exactly that and fails if the committed data or results drift.

**The ground truth has four kinds**, and the distinction matters for what the score
means. *Injected* (149): failures the generator planted — orphan accounts, leavers
left enabled, kept entitlements, generic admins, dormant accounts, unapproved grants,
accumulated SoD conflicts, split and duplicate and self-approved claims. *Design*
(33): SoD conflicts the role model itself contains. *Process* (4): grants the
company's workflow let the ERP owner approve for himself. *Consequence* (9): a
planted failure that trips a second test — a still-enabled leaver is also dormant; a
mover who kept HR edit rights now also runs payroll. The tests found all four kinds;
the last three were not planted, which is the closest a synthetic audit gets to
finding something it did not put there.

**Rating rule:** High if the exception rate exceeds 5% or there are three or more
High-severity exceptions (each is a live exposure whatever the rate); Medium if
there are exceptions below both; Low if none. Full-population testing means the
rates are exact, so no confidence bound is needed — the sampling machinery of
[Gatekeeper](https://github.com/direenvy/gatekeeper) is for when the population
cannot all be examined.

**Benford** is reported with Nigrini's mean absolute deviation (0.006 / 0.012 / 0.015
thresholds) as the primary statistic and χ² as secondary, because χ² grows with n and
declares Operations' 5,543 claims nonconforming on a deviation that is immaterial.
Sales fails on both, and the reason is three claimants with forty claims each just
under the approval limit.

## Limitations

- The company is fictional and the failure rates are chosen, so the ratings describe
  the tests' behaviour on this data, not any real organisation's control environment.
- The tests assume clean identifiers: an employee ID joins HR to every system. Real
  extracts need an identity-matching step first, and that step is where real audits
  spend their time.
- "Business day" ignores public holidays; the leaver deadline is a calendar rule.
- An exceptions register entry is taken as a valid mitigating control; a real audit
  tests whether the mitigation operates.
- Benford applies to amounts that span orders of magnitude; the claims here are
  log-normal by construction, so conformity of the clean population is partly built
  in. The Sales result is the test doing its job on the part that was not.

## Frameworks

Each control is mapped in `sentry/config.py` to COBIT 2019 (DSS05.04, DSS06.03),
ISO/IEC 27001:2022 Annex A (5.3, 5.15, 5.16, 5.18, 6.5, 8.2) and the SOX ITGC
logical-access and segregation-of-duties objectives. Design: the New Genre reference
in `DESIGN.md`.
