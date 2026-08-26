"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  ["/", "Monthly review", "01"],
  ["/trends", "Performance trends", "02"],
  ["/markets", "Market analysis", "03"],
  ["/archive", "Report archive", "04"],
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="shell">
      <aside className="sidebar">
        <Link className="brand" href="/" aria-label="Northstar home">
          <i />Northstar
        </Link>
        <p className="eyebrow">BUSINESS INTELLIGENCE</p>
        <nav aria-label="Primary navigation">
          {navigation.map(([href, label, number]) => {
            const active = href === "/" ? pathname === href : pathname.startsWith(href);
            return (
              <Link className={active ? "active" : ""} href={href} key={href}>
                <small>{number}</small><span>{label}</span>
              </Link>
            );
          })}
        </nav>
        <footer>
          <span>CONTROLLED ANALYTICS</span>
          Databricks-calculated<br />AI-explained
          <b>v3.0 · DATE-REBASED DEMO</b>
        </footer>
      </aside>
      <main>{children}</main>
    </div>
  );
}
