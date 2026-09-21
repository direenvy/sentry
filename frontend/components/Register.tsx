"use client";

import { useMemo, useState } from "react";
import { controls, type Exception } from "@/lib/data";

const KINDS = ["injected", "design", "process", "consequence"];

/** Status by shape and weight, never hue: High is filled, Medium outlined, Low plain. */
export function Pill({ level }: { level: string }) {
  const cls = level.startsWith("High") ? "status status-error" : level === "Medium" ? "status status-warn" : level === "Low" ? "status status-ok" : "status status-info";
  return <span className={cls}>{level}</span>;
}

/** The exceptions register: every exception, filterable by control, severity and
 *  the kind of ground truth it matched. */
export default function Register({ rows }: { rows: Exception[] }) {
  const [control, setControl] = useState("All");
  const [severity, setSeverity] = useState("All");
  const [kind, setKind] = useState("All");
  const [q, setQ] = useState("");
  const [limit, setLimit] = useState(40);

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows.filter(
      (r) =>
        (control === "All" || r.control === control) &&
        (severity === "All" || r.severity === severity) &&
        (kind === "All" || r.kind === kind) &&
        (!needle || r.subject.toLowerCase().includes(needle) || r.detail.toLowerCase().includes(needle) || r.key.toLowerCase().includes(needle)),
    );
  }, [rows, control, severity, kind, q]);

  const select = { border: "1px solid var(--color-ash-mist)", borderRadius: "var(--radius-pill)", padding: "8px 14px", fontSize: 14, background: "transparent" };
  const cell = { padding: "10px 14px 10px 0", borderTop: "1px solid var(--hairline)", verticalAlign: "top" as const };

  return (
    <div className="card" style={{ padding: "var(--card-padding)" }}>
      <div className="flex flex-wrap items-center gap-3">
        <select value={control} onChange={(e) => setControl(e.target.value)} style={select} aria-label="Control">
          <option>All</option>
          {controls.map((c) => (
            <option key={c.id} value={c.id}>
              {c.id} · {c.name}
            </option>
          ))}
        </select>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)} style={select} aria-label="Severity">
          <option>All</option>
          <option>High</option>
          <option>Medium</option>
        </select>
        <select value={kind} onChange={(e) => setKind(e.target.value)} style={select} aria-label="Ground-truth kind">
          <option>All</option>
          {KINDS.map((k) => (
            <option key={k}>{k}</option>
          ))}
        </select>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search an account, employee, event…" style={{ ...select, minWidth: 260 }} aria-label="Search" />
        <span className="body-sm tabular" style={{ color: "var(--text-secondary)" }}>
          {shown.length} of {rows.length}
        </span>
      </div>
      <div style={{ overflowX: "auto", marginTop: 20 }}>
        <table className="w-full" style={{ borderCollapse: "collapse", minWidth: 820 }}>
          <thead>
            <tr>
              {["#", "Control", "Subject", "Detail", "Severity", "Kind"].map((h) => (
                <th key={h} className="label text-left" style={{ paddingBottom: 8, paddingRight: 14 }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="body-sm">
            {shown.slice(0, limit).map((r) => (
              <tr key={r.item}>
                <td className="tabular" style={{ ...cell, color: "var(--text-muted)" }}>{r.item}</td>
                <td style={{ ...cell, fontWeight: 500, whiteSpace: "nowrap" }}>{r.control}</td>
                <td className="tabular" style={{ ...cell, whiteSpace: "nowrap" }}>{r.subject}</td>
                <td style={{ ...cell, color: "var(--text-secondary)", minWidth: 360 }}>{r.detail}</td>
                <td style={cell}>
                  <Pill level={r.severity} />
                </td>
                <td className="caption" style={{ ...cell, color: r.kind === "injected" ? "var(--text-muted)" : "var(--text-primary)", fontWeight: r.kind === "injected" ? 400 : 500, whiteSpace: "nowrap" }}>
                  {r.kind}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {shown.length > limit && (
        <button type="button" onClick={() => setLimit((l) => l + 80)} className="pill" style={{ marginTop: 12, paddingLeft: 0, fontSize: 14 }}>
          Show more
        </button>
      )}
    </div>
  );
}
