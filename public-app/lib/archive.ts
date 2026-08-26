import type { ArchiveRecord, ReportResponse } from "@/lib/analytics-types";
import { toDisplayReportMonth } from "@/lib/report-months";

const STORAGE_KEY = "northstar-report-archive-v3";
const LEGACY_STORAGE_KEY = "northstar-report-archive-v2";

function migrateLegacyArchive() {
  const legacy = window.localStorage.getItem(LEGACY_STORAGE_KEY);
  if (!legacy) return [];
  try {
    const records = JSON.parse(legacy) as ArchiveRecord[];
    if (!Array.isArray(records)) return [];
    const migrated = records.map((record) => {
      const reportMonth = toDisplayReportMonth(record.reportMonth);
      return {
        ...record,
        id: `${reportMonth}-${record.generatedAt}`,
        reportMonth,
        report: {
          ...record.report,
          reportMonth,
          trend: record.report.trend.map((point) => ({
            ...point,
            month: toDisplayReportMonth(point.month),
          })),
        },
      } satisfies ArchiveRecord;
    });
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(migrated));
    return migrated;
  } catch {
    return [];
  }
}

export function listArchive(): ArchiveRecord[] {
  if (typeof window === "undefined") return [];
  try {
    const current = window.localStorage.getItem(STORAGE_KEY);
    const parsed = current ? JSON.parse(current) as ArchiveRecord[] : migrateLegacyArchive();
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
