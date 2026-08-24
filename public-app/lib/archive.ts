import type { ArchiveRecord, ReportResponse } from "@/lib/analytics-types";

const STORAGE_KEY = "northstar-report-archive-v2";

export function listArchive(): ArchiveRecord[] {
  if (typeof window === "undefined") return [];
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "[]") as ArchiveRecord[];
    return Array.isArray(parsed) ? parsed.sort((a, b) => b.generatedAt.localeCompare(a.generatedAt)) : [];
  } catch {
    return [];
  }
}

export function saveReportToArchive(report: ReportResponse) {
  const record: ArchiveRecord = {
    id: `${report.reportMonth}-${Date.now()}`,
    reportMonth: report.reportMonth,
    generatedAt: new Date().toISOString(),
    report,
  };
  const remaining = listArchive().filter((item) => item.reportMonth !== report.reportMonth);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify([record, ...remaining].slice(0, 24)));
  return record;
}

export function deleteArchiveRecord(id: string) {
  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(listArchive().filter((item) => item.id !== id)),
  );
}
