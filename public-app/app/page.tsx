"use client";

import { useEffect, useState } from "react";
import { MonthPicker } from "@/app/components/month-picker";
import { ReportView } from "@/app/components/report-view";
import { useReportMonths } from "@/app/hooks/use-report-months";
import { saveReportToArchive } from "@/lib/archive";
import type { ReportResponse } from "@/lib/analytics-types";

const stages = [["Running governed SQL", "Querying approved Databricks reporting views"], ["Validating KPI payload", "Checking completeness and metric consistency"], ["Identifying material changes", "Comparing performance to the prior month"], ["Generating executive narrative", "Turning governed facts into decision-ready context"]] as const;

export default function Page() {
  const { months, loading: monthsLoading } = useReportMonths();
  const [selectedMonth, setSelectedMonth] = useState("");
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => { if (!selectedMonth && months[0]) setSelectedMonth(months[0].value); }, [months, selectedMonth]);

  async function generate() {
    if (!selectedMonth) return;
    setLoading(true); setReport(null); setError(""); setStep(0);
    const timer = window.setInterval(() => setStep((current) => Math.min(current + 1, 3)), 900);
    try {
      const response = await fetch("/api/report", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ month: selectedMonth }) });
      const payload = (await response.json()) as ReportResponse | { error?: string };
      if (!response.ok || !("reportMonth" in payload)) throw new Error("error" in payload ? payload.error ?? "The report could not be generated." : "The report could not be generated.");
      setStep(3); setReport(payload); saveReportToArchive(payload);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "The report could not be generated."); }
    finally { window.clearInterval(timer); setLoading(false); }
  }

  return <>
    <header className="pageHeader"><div><span className="sectionLabel">01 / EXECUTIVE REPORTING</span><h1>Monthly Business Review</h1><p>Decision-ready performance intelligence, grounded in governed data.</p></div><div className="actions"><MonthPicker months={months} value={selectedMonth} onChange={setSelectedMonth} disabled={loading || monthsLoading} /><button className="primaryButton" onClick={generate} disabled={loading || !selectedMonth}>{loading ? "Generating…" : "Generate report"}<span>→</span></button></div></header>
    {loading && <div className="generationPanel animateIn"><div className="spinner" /><div><small>AGENT WORKFLOW · STEP {step + 1} OF 4</small><b>{stages[step][0]}</b><span>{stages[step][1]}</span></div><div className="stepTrack">{stages.map((stage, index) => <i className={index <= step ? "done" : ""} key={stage[0]} />)}</div></div>}
    {error && <div className="errorBanner" role="alert"><b>Report generation paused.</b><span>{error}</span></div>}
    {!report && !loading && <div className="emptyState"><span>MONTHLY BUSINESS REVIEW AGENT</span><h2>From governed data to executive clarity.</h2><p>Select any month in the four-year dataset. The agent runs controlled SQL, validates the KPI payload, and produces a traceable executive report.</p><button className="textButton" onClick={generate} disabled={!selectedMonth}>Generate the first report →</button><div className="processRail"><i>01<small>QUERY</small></i><b /><i>02<small>VALIDATE</small></i><b /><i>03<small>EXPLAIN</small></i><b /><i>04<small>ARCHIVE</small></i></div></div>}
    {report && <ReportView report={report} />}
  </>;
}
