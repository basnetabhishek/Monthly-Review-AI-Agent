"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { deleteArchiveRecord, listArchive } from "@/lib/archive";
import type { ArchiveRecord } from "@/lib/analytics-types";
import { formatReportMonth } from "@/lib/report-months";

const fmt = (value: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);

export default function ArchivePage() {
  const [records, setRecords] = useState<ArchiveRecord[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  useEffect(() => setRecords(listArchive()), []);

  function remove(id: string) {
    if (!window.confirm("Remove this generated report from your browser archive?")) return;
    deleteArchiveRecord(id); setRecords(listArchive());
  }
  function download(record: ArchiveRecord) {
    const blob = new Blob([JSON.stringify(record, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob); const link = document.createElement("a");
    link.href = url; link.download = `northstar-report-${record.reportMonth}.json`; link.click(); URL.revokeObjectURL(url);
  }

  return <>
    <header className="pageHeader"><div><span className="sectionLabel">04 / REPORT HISTORY</span><h1>Report Archive</h1><p>A private, browser-local history of the reports you generated.</p></div><Link className="primaryButton linkButton" href="/">Generate new report <span>→</span></Link></header>
    <div className="privacyNote"><i>LOCAL</i><span><b>Private by design.</b> This archive stays in this browser. Existing v2 reports are automatically date-rebased, and credentials are never stored here.</span></div>
    {records.length === 0 ? <div className="emptyState archiveEmpty"><span>NO REPORTS SAVED YET</span><h2>Your decision history starts here.</h2><p>Generate a monthly review and it will automatically appear in this private archive.</p><Link className="textButton" href="/">Generate a report →</Link></div> : <section className="archiveList animateIn">{records.map((record) => { const open = expanded === record.id; return <article className="card archiveCard" key={record.id}><button className="archiveSummary" onClick={() => setExpanded(open ? null : record.id)} aria-expanded={open}><span><small>MONTHLY BUSINESS REVIEW</small><b>{formatReportMonth(record.reportMonth)}</b><em>Generated {new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(record.generatedAt))}</em></span><span className="archiveKpi"><small>SALES</small><b>{fmt(record.report.current.sales)}</b></span><span className="archiveKpi"><small>PROFIT</small><b>{fmt(record.report.current.profit)}</b></span><i>{open ? "−" : "+"}</i></button>{open && <div className="archiveDetail"><p>{record.report.summary}</p><div><span><small>MARGIN</small><b>{record.report.current.margin.toFixed(1)}%</b></span><span><small>ORDERS</small><b>{fmt(record.report.current.orders)}</b></span><span><small>NEGATIVE PROFIT ORDERS</small><b>{fmt(record.report.current.negativeOrders)}</b></span><span><small>SOURCE</small><b>{record.report.dataSource === "databricks-live" ? "Databricks live" : "Validated snapshot"}</b></span></div><footer><button onClick={() => download(record)}>Download JSON</button><button className="dangerButton" onClick={() => remove(record.id)}>Remove</button></footer></div>}</article>; })}</section>}
  </>;
}
