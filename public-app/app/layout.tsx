import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Northstar | Monthly Business Review AI",
  description: "A governed analytics portfolio project: Databricks-calculated KPIs, AI-explained insights.",
};

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
