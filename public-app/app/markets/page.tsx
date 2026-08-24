"use client";

import { useEffect, useMemo, useState } from "react";
import { MonthPicker } from "@/app/components/month-picker";
import { StatusPill } from "@/app/components/status-pill";
import { useReportMonths } from "@/app/hooks/use-report-months";
import type { MarketAnalysisResponse, PerformanceItem } from "@/lib/analytics-types";
import { formatReportMonth } from "@/lib/report-months";

const fmt = (value: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);

export default function MarketsPage() {
  const { months } = useReportMonths();
  const [selectedMonth, setSelectedMonth] = useState("");
  const [data, setData] = useState<MarketAnalysisResponse | null>(null);
  const [view, setView] = useState<"markets" | "categories">("markets");
  const [group, setGroup] = useState("All");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { if (!selectedMonth && months[0]) setSelectedMonth(months[0].value); }, [months, selectedMonth]);
  useEffect(() => {
    if (!selectedMonth) return;
    let active = true;
    setLoading(true); setError(""); setGroup("All");
    fetch(`/api/markets?month=${encodeURIComponent(selectedMonth)}`).then(async (response) => {
      const payload = await response.json() as MarketAnalysisResponse | { error?: string };
      if (!response.ok || !("markets" in payload)) throw new Error("error" in payload ? payload.error ?? "Market analysis could not be loaded." : "Market analysis could not be loaded.");
      return payload;
    }).then((payload) => { if (active) setData(payload); }).catch((caught) => { if (active) setError(caught instanceof Error ? caught.message : "Market analysis could not be loaded."); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [selectedMonth]);

  const source = data?.[view] ?? [];
  const groups = useMemo(() => ["All", ...Array.from(new Set(source.map((item) => item.group)))], [source]);
  const visible = useMemo(() => (group === "All" ? source : source.filter((item) => item.group === group)).slice().sort((a, b) => b.sales - a.sales), [source, group]);
  const totalSales = visible.reduce((sum, item) => sum + item.sales, 0);
  const totalProfit = visible.reduce((sum, item) => sum + item.profit, 0);
  const best = visible.reduce<PerformanceItem | null>((winner, item) => !winner || item.profit > winner.profit ? item : winner, null);
  const max = Math.max(...visible.map((item) => item.sales), 1);

  return <>
    <header className="pageHeader"><div><span className="sectionLabel">03 / PORTFOLIO DIAGNOSTICS</span><h1>Market Analysis</h1><p>Compare geographic and product performance, then isolate target risk.</p></div><MonthPicker months={months} value={selectedMonth} onChange={setSelectedMonth} disabled={loading} /></header>
    {error && <div className="errorBanner" role="alert"><b>Analysis unavailable.</b><span>{error}</span></div>}
    {loading && <div className="loadingState"><div className="spinner" /><span>Querying market and category performance…</span></div>}
    {data && !loading && <section className="analyticsPage animateIn">
      <div className="analyticsMeta"><StatusPill source={data.dataSource} /><span>{formatReportMonth(data.reportMonth)}</span></div>
      <div className="analysisControls"><div className="segmented"><button className={view === "markets" ? "active" : ""} onClick={() => { setView("markets"); setGroup("All"); }}>Markets</button><button className={view === "categories" ? "active" : ""} onClick={() => { setView("categories"); setGroup("All"); }}>Categories</button></div><label>Filter group<select value={group} onChange={(event) => setGroup(event.target.value)}>{groups.map((item) => <option key={item}>{item}</option>)}</select></label></div>
      <div className="kpis trendKpis"><MetricCard label="Selected sales" value={fmt(totalSales)} note={`${visible.length} performance segments`} /><MetricCard label="Selected profit" value={fmt(totalProfit)} note={`${totalSales ? ((totalProfit / totalSales) * 100).toFixed(1) : "0.0"}% weighted margin`} /><MetricCard label="Strongest profit segment" value={best?.segment ?? "—"} note={best ? `${fmt(best.profit)} profit` : "No data"} /><MetricCard label="Target risks" value={String(data.targets.filter((item) => item.attainment < 80).length)} note="segments below 80% attainment" /></div>
      <div className="marketGrid"><div className="card ranking"><div className="tableHeading"><h3>{view === "markets" ? "Geographic performance" : "Product performance"}</h3><span>Sorted by reported sales</span></div>{visible.slice(0, 14).map((item) => <div className="rankRow" key={`${item.group}-${item.segment}`}><span><b>{item.segment}</b><small>{item.group} · {item.margin.toFixed(1)}% margin</small></span><div><i style={{ width: `${Math.max((item.sales / max) * 100, 2)}%` }} /></div><strong>{fmt(item.sales)}</strong><em className={item.profit < 0 ? "negative" : "positive"}>{fmt(item.profit)}</em></div>)}</div><div className="card watchlist"><div className="tableHeading"><h3>Target watchlist</h3><span>Lowest attainment first</span></div>{data.targets.slice().sort((a, b) => a.attainment - b.attainment).slice(0, 10).map((item) => <div className="targetRow" key={`${item.market}-${item.segment}`}><span><b>{item.segment}</b><small>{item.market}</small></span><strong className={item.attainment < 80 ? "negative" : "positive"}>{item.attainment.toFixed(0)}%</strong><div><i style={{ width: `${Math.min(item.attainment, 100)}%` }} /></div><small>{fmt(item.actual)} / {fmt(item.target)}</small></div>)}</div></div>
    </section>}
  </>;
}

function MetricCard({ label, value, note }: { label: string; value: string; note: string }) { return <div className="card kpi"><label>{label}</label><strong>{value}</strong><span>{note}</span></div>; }
