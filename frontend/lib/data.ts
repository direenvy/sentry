import controlsJson from "@/data/controls.json";
import benfordJson from "@/data/benford.json";
import exceptionsJson from "@/data/exceptions.json";
import sodJson from "@/data/sod.json";

export type Control = {
  id: string;
  name: string;
  objective: string;
  test: string;
  population: number;
  frameworks: Record<string, string>;
  exceptions: number;
  rate: number;
  high: number;
  rating: string;
  truth: { total: number; by_kind: Record<string, number> };
  caught: { total: number; by_kind: Record<string, number> };
  extra: number;
};

export type Summary = {
  company: string;
  period_start: string;
  period_end: string;
  as_of: string;
  fieldwork: string;
  employees: number;
  active: number;
  accounts: number;
  entitlements: number;
  changes: number;
  claims: number;
  exceptions: number;
  truth: number;
  ratings: Record<string, number>;
};

export type Exception = { item: number; control: string; key: string; subject: string; detail: string; severity: string; kind: string };

export type Benford = Record<string, { n: number; mad: number; chi2: number; digits: { digit: number; observed_pct: number; expected_pct: number }[] }>;

export type SodRule = { a: string; b: string; risk: string; conflicts: number; design: number };

export const summary = controlsJson.summary as Summary;
export const controls = controlsJson.controls as unknown as Control[];
export const benford = benfordJson as unknown as Benford;
export const exceptions = exceptionsJson as Exception[];
export const sod = sodJson as SodRule[];

export function num(v: number): string {
  return new Intl.NumberFormat("en-GB").format(v);
}

export function pct(v: number, dp = 1): string {
  return `${(100 * v).toFixed(dp)}%`;
}

export function dateName(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
}

export const RATING_ORDER = ["High", "Medium", "Low"];
