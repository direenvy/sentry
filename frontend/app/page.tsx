import BenfordChart from "@/components/BenfordChart";
import Register, { Pill } from "@/components/Register";
import { benford, controls, dateName, exceptions, num, pct, sod, summary } from "@/lib/data";

const REPO = "https://github.com/direenvy/sentry";

const FINDINGS = [
  { n: "F-1", control: "A2", rating: "High", title: "Leaver de-provisioning does not work", body: "Of 120 employees who left in the period, 20 had accounts not disabled by the next business day: 8 still enabled at the extract date, 5 to 268 days after they left; 12 disabled 3–40 days late. Recommendation: a weekly automated reconciliation of HR terminations against enabled accounts on all four systems; disable on the termination date." },
  { n: "F-2", control: "S1", rating: "High", title: "Three roles are designed with a segregation-of-duties conflict", body: "44 active employees hold a conflicting pair; 33 hold it by design — Treasury Officer (payment run + bank reconciliation, 18 people), AP Supervisor (invoice entry + approval, 8), Payroll Manager (payroll approval + bank-file release, 7). A design deficiency, not an access error. Recommendation: split the three roles, bank reconciliation first; until then an evidenced monthly review of those 33 people's transactions." },
  { n: "F-3", control: "A6", rating: "High", title: "Grants are made without approval, or with the wrong approver", body: "16 of 217 grants: 6 with no ticket, 7 approved by the beneficiary — 4 of them the ERP owner approving grants to his own account — 2 by the requester, 1 while the ticket was pending. Recommendation: the owner's own access is approved by the CFO; provisioning refuses a grant without an approved ticket." },
  { n: "F-4", control: "A4", rating: "High", title: "Privileged access on unnamed accounts and in the wrong hands", body: "Generic admin (domain admin) and erp.firefighter (SAP_ALL) are enabled and in daily use with no named individual accountable; a Financial Accountant holds SAP_ALL. Recommendation: named admin accounts, a privileged-access tool for the firefighter case, SAP_ALL removed from the accountant today." },
  { n: "F-5", control: "A1", rating: "High", title: "Accounts with no employee behind them", body: "Six enabled, recently used accounts belong to employee IDs not in HR; four accounts were created 10–60 days before the person's hire date. Recommendation: contractors go through HR; accounts are created from the HR record." },
  { n: "F-6", control: "A3", rating: "Medium", title: "Access accumulates across moves", body: "26 employees hold entitlements outside their role: 7 of the 24 movers kept the previous role's access; 19 others hold an entitlement no one can explain. Five more are covered by a dated exception. Recommendation: a role change triggers the leaver review." },
  { n: "F-7", control: "A5", rating: "Medium", title: "Dormant accounts stay enabled", body: "38 enabled accounts with no logon in 90 days; 30 active staff, 8 leavers. Recommendation: automated disablement at 90 days." },
  { n: "F-8", control: "F1", rating: "Analytics", title: "Expense claims: Benford flags Sales, and the reason is three claimants", body: "Claims overall conform (MAD 0.0075); Sales does not (0.0145, χ² 125): three claimants with 40 claims each between RM900 and RM999.99, under the RM1,000 second-approver limit. Also 15 duplicates paid twice, 10 self-approved claims, one claimant with 25 round-amount claims. For Internal Audit's substantive testing." },
];

function Stat({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="card" style={{ padding: 24 }}>
      <p className="label">{label}</p>
      <p className="tabular" style={{ fontSize: 24, lineHeight: 1.15, letterSpacing: "-0.24px", marginTop: 12 }}>
        {value}
      </p>
      <p className="body-sm" style={{ marginTop: 6, color: "var(--text-secondary)" }}>
        {note}
      </p>
    </div>
  );
}

function Section({ id, kicker, title, lede, children }: { id?: string; kicker: string; title: string; lede: React.ReactNode; children: React.ReactNode }) {
  return (
    <section id={id} style={{ paddingTop: "var(--section-gap)", scrollMarginTop: 24 }}>
      <p className="label">{kicker}</p>
      <h2 className="heading" style={{ marginTop: 12 }}>
        {title}
      </h2>
      <p className="subheading" style={{ marginTop: 10, marginBottom: 24, maxWidth: 720, color: "var(--text-secondary)" }}>
        {lede}
      </p>
      {children}
    </section>
  );
}

export default function Home() {
  const th = "label text-left" as const;
  const cell = { padding: "12px 16px 12px 0", borderTop: "1px solid var(--hairline)", verticalAlign: "top" as const };
  const caught = controls.reduce((a, c) => a + c.caught.total, 0);
  const truth = controls.reduce((a, c) => a + c.truth.total, 0);
  const extra = controls.reduce((a, c) => a + c.extra, 0);
  const kinds = ["injected", "design", "process", "consequence"];

  return (
    <>
      <header className="relative" style={{ background: "var(--gradient-dawn-arc)", minHeight: "min(92vh, 860px)" }}>
        <nav className="mx-auto flex items-center justify-between px-6 lg:px-12" style={{ maxWidth: "var(--page-max-width)", height: 72 }}>
          <span style={{ fontSize: 14, fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--color-parchment-canvas)" }}>Sentry</span>
          <div className="flex items-center gap-1">
            <a href="#findings" className="pill on-dark" style={{ fontSize: 14 }}>
              Findings
            </a>
            <a href="#register" className="pill on-dark hidden sm:inline-flex" style={{ fontSize: 14 }}>
              Register
            </a>
            <span aria-hidden="true" style={{ width: 1, height: 16, background: "rgba(255,255,255,0.35)", margin: "0 8px" }} />
            <a href={REPO} target="_blank" rel="noreferrer" className="pill on-dark" style={{ fontSize: 14 }}>
              Repository
            </a>
          </div>
        </nav>
        <div className="mx-auto px-6 lg:px-12" style={{ maxWidth: "var(--page-max-width)", position: "absolute", left: 0, right: 0, bottom: 56 }}>
          <h1 className="display" style={{ maxWidth: 980 }}>
            Every account, every grant, every claim, <span className="dissolve">tested against an answer key.</span>
          </h1>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2" style={{ marginTop: 24 }}>
            <a href="#findings" className="pill" style={{ paddingLeft: 0 }}>
              The findings ↓
            </a>
            <a href={`${REPO}/blob/main/results/FINDINGS.md`} target="_blank" rel="noreferrer" className="pill">
              Findings memo ↗
            </a>
            <span className="body-sm tabular" style={{ color: "var(--text-secondary)" }}>
              {summary.company} (fictional) · {dateName(summary.period_start)} – {dateName(summary.period_end)} · extract as at {dateName(summary.as_of)}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full px-6 lg:px-12" style={{ maxWidth: "var(--page-max-width)" }}>
        <section style={{ paddingTop: 48 }}>
          <p className="subheading" style={{ maxWidth: 780 }}>
            An IT audit of logical access and segregation of duties on four systems — ERP, HR, payroll, the Windows domain — of a company that does not exist, generated from a seed with {num(summary.truth)} control
            failures recorded. Seven access controls and a set of fraud analytics are tested over the full population, every exception is registered, the controls are rated, and the tests are scored: every
            one of the {num(summary.truth)} was found, and nothing else was flagged. The data is fictional; the tests are the ones an auditor runs on a real extract.
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" style={{ marginTop: 32 }}>
            <Stat label="Population" value={`${num(summary.accounts)} accounts`} note={`${num(summary.employees)} employees (${num(summary.active)} active) · ${num(summary.entitlements)} entitlements · ${num(summary.changes)} change events · ${num(summary.claims)} claims`} />
            <Stat label="Exceptions" value={num(summary.exceptions)} note="across eight tests, full population — no sampling" />
            <Stat label="Ratings" value={`${summary.ratings.High} High · ${summary.ratings.Medium} Medium`} note={`${summary.ratings.Low} Low · the analytics are not rated`} />
            <Stat label="Tests scored" value={`${caught} of ${truth}`} note={`ground-truth failures found; ${extra} flagged that were not in it`} />
          </div>
        </section>

        <Section kicker="Scope" title="The controls" lede="Joiners, leavers, movers, privileged access, dormancy, authorisation, segregation of duties — the logical-access ITGCs as the frameworks describe them, each with one test over the whole population.">
          <div className="card" style={{ padding: "var(--card-padding)" }}>
            <div style={{ overflowX: "auto" }}>
              <table className="w-full" style={{ borderCollapse: "collapse", minWidth: 900 }}>
                <thead>
                  <tr>
                    <th className={th} style={{ paddingBottom: 10, width: "26%" }}>Control</th>
                    <th className={th} style={{ paddingBottom: 10, width: "34%" }}>Test</th>
                    <th className={th} style={{ paddingBottom: 10 }}>Population</th>
                    <th className={th} style={{ paddingBottom: 10 }}>Exceptions</th>
                    <th className={th} style={{ paddingBottom: 10 }}>Rating</th>
                  </tr>
                </thead>
                <tbody>
                  {controls.map((c) => (
                    <tr key={c.id}>
                      <td style={cell}>
                        <span style={{ fontWeight: 500 }}>{c.id}</span> {c.name}
                        <span className="caption secondary" style={{ display: "block", marginTop: 4 }}>
                          {Object.entries(c.frameworks)
                            .filter(([, v]) => v !== "—")
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(" · ")}
                        </span>
                      </td>
                      <td className="body-sm" style={{ ...cell, color: "var(--text-secondary)", paddingRight: 24 }}>
                        {c.test}
                      </td>
                      <td className="body-sm tabular" style={cell}>
                        {num(c.population)}
                      </td>
                      <td className="body-sm tabular" style={cell}>
                        {c.exceptions} <span style={{ color: "var(--text-secondary)" }}>({pct(c.rate)})</span>
                        {c.high > 0 && <span className="caption" style={{ display: "block", color: "var(--text-secondary)" }}>{c.high} High severity</span>}
                      </td>
                      <td style={cell}>
                        <Pill level={c.rating === "n/a (analytics)" ? "Analytics" : c.rating} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="caption" style={{ marginTop: 16, color: "var(--text-muted)" }}>
              Rating: High if the exception rate exceeds 5%, or three or more High-severity exceptions (each one is a live exposure whatever the rate); Medium if exceptions below both; Low if none. Full-population testing, so
              the rates are exact.
            </p>
          </div>
        </Section>

        <Section id="findings" kicker="Findings" title="What a company with these extracts should fix" lede="Eight findings, most severe first. The finding worth reading is the second: thirty-three of the segregation-of-duties conflicts are in the role model itself.">
          <div className="grid gap-4 md:grid-cols-2">
            {FINDINGS.map((f) => (
              <div key={f.n} className="card" style={{ padding: "var(--card-padding)" }}>
                <div className="flex items-center justify-between gap-3">
                  <p className="label">
                    {f.n} · {f.control}
                  </p>
                  <Pill level={f.rating} />
                </div>
                <h3 className="heading-sm" style={{ marginTop: 12 }}>
                  {f.title}
                </h3>
                <p className="body-sm" style={{ marginTop: 12, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  {f.body}
                </p>
              </div>
            ))}
          </div>
        </Section>

        <Section kicker="Segregation of duties" title="Twelve rules, and who breaks them" lede="Each rule is a pair of entitlements one person must not hold, with the fraud the pair enables. Conflicts by design are the roles that were built that way.">
          <div className="card" style={{ padding: "var(--card-padding)" }}>
            <div style={{ overflowX: "auto" }}>
              <table className="w-full" style={{ borderCollapse: "collapse", minWidth: 760 }}>
                <thead>
                  <tr>
                    <th className={th} style={{ paddingBottom: 10 }}>Must not be held together</th>
                    <th className={th} style={{ paddingBottom: 10 }}>Enables</th>
                    <th className={th} style={{ paddingBottom: 10, textAlign: "right" }}>Conflicts</th>
                    <th className={th} style={{ paddingBottom: 10, textAlign: "right" }}>By design</th>
                  </tr>
                </thead>
                <tbody className="body-sm">
                  {sod.map((r) => (
                    <tr key={r.a + r.b}>
                      <td className="tabular" style={{ ...cell, whiteSpace: "nowrap", fontWeight: r.conflicts ? 500 : 400 }}>
                        {r.a} <span style={{ color: "var(--text-muted)" }}>+</span> {r.b}
                      </td>
                      <td style={{ ...cell, color: "var(--text-secondary)" }}>{r.risk}</td>
                      <td className="tabular" style={{ ...cell, textAlign: "right" }}>{r.conflicts || <span style={{ color: "var(--text-muted)" }}>0</span>}</td>
                      <td className="tabular" style={{ ...cell, textAlign: "right", color: r.design ? "var(--text-primary)" : "var(--text-muted)" }}>{r.design}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Section>

        <Section kicker="Analytics" title="Benford's law on a year of expense claims" lede="First digits of 10,911 claims of RM10 or more, by department. The population conforms; Sales does not, and the register says why.">
          <BenfordChart data={benford} />
        </Section>

        <Section id="register" kicker="Register" title="Every exception" lede={<>{num(summary.exceptions)} items. The kind column says which part of the ground truth each one matched: planted by the generator, built into the role model, produced by the company&apos;s own workflow, or a consequence of a planted failure tripping a second test.</>}>
          <Register rows={exceptions} />
        </Section>

        <Section kicker="Scoring" title="The tests against the answer key" lede="What a synthetic audit is for: the ground truth was recorded when the data was generated, so each test can be scored on what it found and what it flagged that was not there.">
          <div className="card" style={{ padding: "var(--card-padding)" }}>
            <div style={{ overflowX: "auto" }}>
              <table className="w-full" style={{ borderCollapse: "collapse", minWidth: 640 }}>
                <thead>
                  <tr>
                    <th className={th} style={{ paddingBottom: 10 }}>Test</th>
                    {kinds.map((k) => (
                      <th key={k} className={th} style={{ paddingBottom: 10, textAlign: "right" }}>
                        {k}
                      </th>
                    ))}
                    <th className={th} style={{ paddingBottom: 10, textAlign: "right" }}>Found</th>
                    <th className={th} style={{ paddingBottom: 10, textAlign: "right" }}>Extra</th>
                  </tr>
                </thead>
                <tbody className="body-sm tabular">
                  {controls.map((c) => (
                    <tr key={c.id}>
                      <td style={{ ...cell, fontWeight: 500 }}>{c.id}</td>
                      {kinds.map((k) => (
                        <td key={k} style={{ ...cell, textAlign: "right", color: c.truth.by_kind[k] ? "var(--text-primary)" : "var(--text-muted)" }}>
                          {c.truth.by_kind[k] ? `${c.caught.by_kind[k] ?? 0} / ${c.truth.by_kind[k]}` : "–"}
                        </td>
                      ))}
                      <td style={{ ...cell, textAlign: "right" }}>
                        {c.caught.total} / {c.truth.total}
                      </td>
                      <td style={{ ...cell, textAlign: "right", color: c.extra ? "var(--text-primary)" : "var(--text-muted)" }}>{c.extra}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="caption" style={{ marginTop: 16, color: "var(--text-muted)", maxWidth: 820, lineHeight: 1.5 }}>
              The design, process and consequence failures were not planted. The tests found them in the role model and the workflow the generator was given, and the ground truth was extended to record them rather than the
              model quietly fixed — the closest a synthetic audit gets to finding something it did not put there.
            </p>
          </div>
        </Section>

        <section style={{ paddingTop: "var(--section-gap)" }}>
          <p className="label">Limitations</p>
          <div className="grid gap-4 md:grid-cols-2" style={{ marginTop: 16 }}>
            {[
              "The company is fictional and the failure rates were chosen, so the ratings describe the tests' behaviour on this data, not any real organisation's control environment.",
              "The tests assume clean identifiers: one employee ID joins HR to every system. Real extracts need an identity-matching step first, and that is where real audits spend their time.",
              "An exceptions-register entry is taken as a valid mitigating control; a real audit tests whether the mitigation operates. Business days ignore public holidays.",
              "Benford applies to amounts spanning orders of magnitude; the clean claims are log-normal by construction, so their conformity is partly built in. The Sales result is the test working on the part that was not.",
            ].map((t) => (
              <p key={t} className="body-sm" style={{ color: "var(--text-secondary)", lineHeight: 1.5 }}>
                {t}
              </p>
            ))}
          </div>
        </section>
      </main>

      <footer className="mx-auto w-full px-6 lg:px-12" style={{ maxWidth: "var(--page-max-width)", paddingTop: 64, paddingBottom: 40 }}>
        <div className="hairline" style={{ paddingTop: 20 }}>
          <p className="caption" style={{ color: "var(--text-muted)", maxWidth: 900, lineHeight: 1.5 }}>
            Mekar Holdings Berhad is fictional; every record was generated from seed {20260921} by the code in the repository. Controls mapped to COBIT 2019, ISO/IEC 27001:2022 and the SOX ITGC objectives. pandas · pytest ·
            Next.js. Fieldwork {dateName(summary.fieldwork)}. Built by Yio Lim Hoong.
          </p>
        </div>
      </footer>
    </>
  );
}
