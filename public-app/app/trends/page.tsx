"use client";

import { useEffect, useMemo, useState } from "react";
import { LineChart } from "@/app/components/line-chart";
import { StatusPill } from "@/app/components/status-pill";
import type { TrendsResponse } from "@/lib/analytics-types";
import { formatReportMonth } from "@/lib/report-months";

const fmt = (value: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);

export default function TrendsPage() {
  const [response, setResponse] = useState<TrendsResponse | null>(null);
  const [range, setRange] = useState<12 | 24 | 48>(12);
  const [metric, setMetric] = useState<"sales" | "profit">("sales");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    fetch("/api/trends").then(async (result) => {
      if (!result.ok) throw new Error("Performance history could not be loaded.");
      return result.json() as Promise<TrendsResponse>;
    }).then((data) => { if (active) setResponse(data); }).catch((caught) => { if (active) setError(caught instanceof Error ? caught.message : "Performance history could not be loaded."); });
    return () => { active = false; };
  }, []);

  const points = useMemo(() => response?.points.slice(-range) ?? [], [response, range]);
  const metrics = useMemo(() => {
    if (!points.length) return null;
    const totalSales = points.reduce((sum, item) => sum + item.sales, 0);
    const totalProfit = points.reduce((sum, item) => sum + item.profit, 0);
    const best = points.reduce((winner, item) => item.sales > winner.sales ? item : winner, points[0]);
    return { totalSales, totalProfit, margin: totalSales ? (totalProfit / totalSales) * 100 : 0, best };
  }, [points]);

  return <>
    <header className="pageHeader"><div><span className="sectionLabel">02 / LONGITUDINAL ANALYSIS</span><h1>Performance Trends</h1><p>Explore the full four-year operating history and identify durable patterns.</p></div><div className="segmented" aria-label="Trend period">{([12, 24, 48] as const).map((value) => <button className={range === value ? "active" : ""} onClick={() => setRange(value)} key={value}>{value === 48 ? "All" : `${value}M`}</button>)}</div></header>
    {error && <div className="errorBanner" role="alert"><b>Trend data unavailable.</b><span>{error}</span></div>}
    {!response && !error && <div className="loadingState"><div className="spinner" /><span>Loading governed performance history…</span></div>}
    {response && metrics && <section className="analyticsPage animateIn">
      <div className="analyticsMeta"><StatusPill source={response.dataSource} /><span>{points.length} monthly periods</span></div>
      <div className="kpis trendKpis"><MetricCard label="Cumulative sales" value={fmt(metrics.totalSales)} note={`${points.length}-month selected range`} /><MetricCard label="Cumulative profit" value={fmt(metrics.totalProfit)} note={`${metrics.margin.toFixed(1)}% aggregate margin`} /><MetricCard label="Best sales month" value={formatReportMonth(metrics.best.month)} note={`${fmt(metrics.best.sales)} reported sales`} /><MetricCard label="Latest order volume" value={fmt(points.at(-1)!.orders)} note={`${fmt(points.at(-1)!.units)} units sold`} /></div>
      <div className="card chartCard"><div className="cardTitle"><div><small>GOVERNED MONTHLY TREND</small><h3>{metric === "sales" ? "Reported sales" : "Reported profit"}</h3></div><div className="segmented compact"><button className={metric === "sales" ? "active" : ""} onClick={() => setMetric("sales")}>Sales</button><button className={metric === "profit" ? "active" : ""} onClick={() => setMetric("profit")}>Profit</button></div></div><LineChart points={points} metric={metric} /></div>
      <div className="card detailTable"><div className="tableHeading"><h3>Recent monthly detail</h3><span>Latest 8 periods</span></div><div className="detailRow detailHeader"><span>Period</span><span>Sales</span><span>Profit</span><span>Margin</span><span>Orders</span><span>MoM sales</span></div>{points.slice(-8).reverse().map((item) => <div className="detailRow" key={item.month}><b>{formatReportMonth(item.month)}</b><span>{fmt(item.sales)}</span><span className={item.profit < 0 ? "negative" : ""}>{fmt(item.profit)}</span><span>{item.margin.toFixed(1)}%</span><span>{fmt(item.orders)}</span><span className={item.salesMom == null ? "muted" : item.salesMom >= 0 ? "positive" : "negative"}>{item.salesMom == null ? "—" : `${item.salesMom >= 0 ? "+" : ""}${item.salesMom.toFixed(1)}%`}</span></div>)}</div>
    </section>}
  </>;
}

function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return <div className="card kpi"><label>{label}</label><strong>{value}</strong><span>{note}</span></div>;
}
