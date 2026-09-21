"use client";

import { useState } from "react";
import { type Benford } from "@/lib/data";

/** First-digit distribution against Benford's expectation, one department at a
 *  time. Observed in Onyx, expected as a hairline marker on each bar. */
export default function BenfordChart({ data }: { data: Benford }) {
  const keys = Object.keys(data);
  const [key, setKey] = useState("Sales");
  const d = data[key];
  const max = Math.max(...d.digits.map((x) => Math.max(x.observed_pct, x.expected_pct))) * 1.1;
  const verdict = d.mad < 0.006 ? "close conformity" : d.mad < 0.012 ? "acceptable conformity" : d.mad < 0.015 ? "marginal" : "nonconformity";

  return (
    <div className="card" style={{ padding: "var(--card-padding)" }}>
      <div className="flex flex-wrap items-center gap-1">
        {keys.map((k) => (
          <button key={k} type="button" onClick={() => setKey(k)} className={`pill${k === key ? " outlined" : ""}`} style={{ fontSize: 14, padding: "8px 14px" }} aria-pressed={k === key}>
            {k === "all" ? "All claims" : k}
          </button>
        ))}
      </div>
      <p className="body-sm tabular" style={{ marginTop: 16, color: "var(--text-secondary)" }}>
        {d.n.toLocaleString("en-GB")} claims · mean absolute deviation {d.mad.toFixed(4)} — <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{verdict}</span> · χ² {d.chi2.toFixed(1)} on 8 df
      </p>
      <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(9, 1fr)", alignItems: "end", height: 220, marginTop: 24 }}>
        {d.digits.map((x) => (
          <div key={x.digit} className="flex flex-col justify-end" style={{ height: "100%" }}>
            <div style={{ position: "relative", flex: 1, display: "flex", alignItems: "flex-end" }}>
              <div style={{ width: "100%", height: `${(100 * x.observed_pct) / max}%`, background: "var(--color-onyx)", borderRadius: "4px 4px 0 0" }} />
              <span aria-hidden="true" style={{ position: "absolute", left: -4, right: -4, bottom: `${(100 * x.expected_pct) / max}%`, borderTop: "2px solid var(--color-ash-mist)" }} />
            </div>
            <span className="caption tabular" style={{ marginTop: 8, textAlign: "center" }}>
              {x.digit}
            </span>
            <span className="caption tabular" style={{ textAlign: "center", color: "var(--text-secondary)" }}>
              {x.observed_pct.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
      <p className="caption" style={{ marginTop: 16, color: "var(--text-muted)" }}>
        Bars: observed share of first digits. Grey marks: Benford&apos;s expectation, log₁₀(1 + 1/d). Nigrini&apos;s thresholds for the mean absolute deviation: 0.006 close, 0.012 acceptable, 0.015 marginal; above that, nonconformity.
      </p>
    </div>
  );
}
