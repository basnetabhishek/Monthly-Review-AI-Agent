"use client";

import { useEffect, useState } from "react";
import { MonthPicker } from "@/app/components/month-picker";
import { ReportView } from "@/app/components/report-view";
import { useReportMonths } from "@/app/hooks/use-report-months";
import { saveReportToArchive } from "@/lib/archive";
import type { ReportResponse } from "@/lib/analytics-types";

export default function Page() {
  const { months, dataSource: monthsDataSource, loading: monthsLoading } = useReportMonths();
  const [selectedMonth, setSelectedMonth] = useState("");
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { if (!selectedMonth && months[0]) setSelectedMonth(months[0].value); }, [months, selectedMonth]);

  async function generate() {
    if (!selectedMonth) return;
    setLoading(true); setReport(null); setError("");
    try {
      const response = await fetch("/api/report", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ month: selectedMonth }) });
      const payload = (await response.json()) as ReportResponse | { error?: string };
      if (!response.ok || !("reportMonth" in payload)) throw new Error("error" in payload ? payload.error ?? "The report could not be generated." : "The report could not be generated.");
      setReport(payload); saveReportToArchive(payload);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "The report could not be generated."); }
    finally { setLoading(false); }
  }

  return <>
    <header className="pageHeader"><div><span className="sectionLabel">01 / EXECUTIVE REPORTING</span><h1>Monthly Business Review</h1><p>Decision-ready performance intelligence, grounded in governed data.</p></div><div className="actions"><MonthPicker months={months} value={selectedMonth} onChange={setSelectedMonth} disabled={loading || monthsLoading} /><button className="primaryButton" onClick={generate} disabled={loading || !selectedMonth}>{loading ? "Generating…" : "Generate report"}<span>→</span></button></div></header>
    {loading && <div className="generationPanel animateIn"><div className="spinner" /><div><small>REPORT GENERATION</small><b>Preparing the report</b><span>Loading available KPI data and preparing the executive summary. Individual processing stages are not tracked.</span></div></div>}
    {error && <div className="errorBanner" role="alert"><b>Report generation paused.</b><span>{error}</span></div>}
    {!report && !loading && <div className="emptyState"><span>MONTHLY BUSINESS REVIEW AGENT</span><h2>From governed data to executive clarity.</h2><p>{monthsDataSource === "databricks-live" ? "Choose a reporting month. Live Databricks SQL provides the metrics for this report." : "Live Databricks history is unavailable. You can generate the validated July 2026 snapshot; historical reporting requires a live warehouse connection."}</p><button className="textButton" onClick={generate} disabled={!selectedMonth}>Generate the first report →</button><div className="processRail"><i>01<small>QUERY</small></i><b /><i>02<small>VALIDATE</small></i><b /><i>03<small>EXPLAIN</small></i><b /><i>04<small>ARCHIVE</small></i></div></div>}
    {report && <ReportView report={report} />}
  </>;
}
