import type { Metadata } from "next";
import { DM_Sans, Instrument_Serif } from "next/font/google";
import "./globals.css";

// Instrument Serif stands in for the condensed editorial display face; DM Sans
// is the low-weight geometric sans for everything else (see DESIGN.md).
const serif = Instrument_Serif({ variable: "--font-serif", subsets: ["latin"], weight: "400" });
const sans = DM_Sans({ variable: "--font-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Sentry — logical access and segregation of duties, tested against an answer key",
  description:
    "An IT audit of user access on four systems of a fictional company: seven controls and fraud analytics tested over the full population, every exception registered, the controls rated, and the tests scored against 195 known failures.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${serif.variable} ${sans.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
