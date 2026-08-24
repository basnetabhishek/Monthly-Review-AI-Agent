import { StatusPill } from "@/app/components/status-pill";
import type { ReportResponse } from "@/lib/analytics-types";
import type { ReportRow } from "@/lib/report-data";
import { formatReportMonth } from "@/lib/report-months";

const fmt = (value: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);

export function ReportView({ report }: { report: ReportResponse }) {
  const c = report.current;
  const max = Math.max(...report.trend.map((item) => item.sales), 1);
  return (
    <section className="report animateIn">
      <div className="reportHead"><div><small>EXECUTIVE PERFORMANCE REPORT</small><h2>{formatReportMonth(report.reportMonth)}</h2></div><StatusPill source={report.dataSource} /></div>
      <div className="kpis">
        <Kpi label="Reported sales" value={fmt(c.sales)} delta={c.salesMom} /><Kpi label="Reported profit" value={fmt(c.profit)} delta={c.profitMom} /><Kpi label="Logical orders" value={fmt(c.orders)} delta={c.ordersMom} />
        <div className="card kpi"><label>Profit margin</label><strong>{c.margin.toFixed(1)}%</strong><span>{fmt(c.units)} units sold</span></div>
      </div>
      <div className="heroGrid">
        <div className="card"><div className="cardTitle"><div><small>4-MONTH VIEW</small><h3>Sales trajectory</h3></div><b>{fmt(c.sales)}</b></div><div className="bars">{report.trend.map((item) => <div key={item.month} style={{ height: `${Math.max((item.sales / max) * 100, 5)}%` }} title={`${formatReportMonth(item.month)}: ${fmt(item.sales)}`} />)}</div><div className="axis"><span>{formatReportMonth(report.trend[0].month)}</span><span>{formatReportMonth(report.trend.at(-1)!.month)}</span></div></div>
        <article className="card summary"><small>EXECUTIVE SUMMARY · {report.narrativeMode === "openai" ? "OPENAI" : "CONTROLLED FALLBACK"}</small><p>{report.summary}</p><footer>{report.dataSource === "databricks-live" ? "Every number was queried from governed Databricks views." : "Every number is sourced from the validated KPI snapshot."}</footer></article>
      </div>
      <div className="tables">
        <DataTable title="Market performance" rows={report.markets} headings={["Market / region", "Sales", "Profit", "Margin"]} /><DataTable title="Category performance" rows={report.categories} headings={["Category / segment", "Sales", "Profit", "Margin"]} /><DataTable title="Target watchlist" rows={report.targets} headings={["Market / segment", "Actual", "Target", "Attain."]} percentTone /><DataTable title="Profit exceptions" rows={report.exceptions} headings={["Order / location", "Sales", "Profit", ""]} />
      </div>
    </section>
  );
}

function Kpi({ label, value, delta }: { label: string; value: string; delta: number | null }) {
  return <div className="card kpi"><label>{label}</label><strong>{value}</strong><span className={delta == null ? "muted" : delta >= 0 ? "positive" : "negative"}>{delta == null ? "No prior-month comparison" : `${delta >= 0 ? "+" : ""}${delta.toFixed(1)}% vs prior month`}</span></div>;
}

function DataTable({ title, rows, headings, percentTone = false }: { title: string; rows: readonly ReportRow[]; headings: string[]; percentTone?: boolean }) {
  return <div className="card table"><div className="tableHeading"><h3>{title}</h3><span>{rows.length} records</span></div><div className="row rowHeader">{headings.map((heading) => <span key={heading}>{heading}</span>)}</div>{rows.map((row, index) => <div className="row" key={`${row[0]}-${row[1]}-${index}`}><span><b>{row[0]}</b><small>{row[1]}</small></span><span>{fmt(row[2])}</span><span className={row[3] < 0 ? "negative" : ""}>{fmt(row[3])}</span><span className={percentTone && (row[4] ?? 100) < 80 ? "negative" : ""}>{row[4] !== undefined ? `${row[4].toFixed(1)}%` : "—"}</span></div>)}</div>;
}
