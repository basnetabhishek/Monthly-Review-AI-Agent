import type { MonthOption } from "@/lib/analytics-types";

export const REPORT_MONTH_PATTERN = /^20\d{2}-(0[1-9]|1[0-2])$/;

export function formatReportMonth(value: string) {
  const [year, month] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(year, month - 1, 1)));
}

export function fallbackMonthOptions(): MonthOption[] {
  const months: MonthOption[] = [];
  for (let year = 2014; year >= 2011; year -= 1) {
    for (let month = 12; month >= 1; month -= 1) {
      const value = `${year}-${String(month).padStart(2, "0")}`;
      months.push({ value, label: formatReportMonth(value) });
    }
  }
  return months;
}

export function isSupportedReportMonth(value: unknown): value is string {
  if (typeof value !== "string" || !REPORT_MONTH_PATTERN.test(value)) return false;
  return value >= "2011-01" && value <= "2014-12";
}
