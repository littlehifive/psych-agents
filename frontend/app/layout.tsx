import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agentic Researcher Studio",
  description:
    "Helping NGO researchers apply agency-based theories and interventions.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased">{children}</body>
    </html>
  );
}

