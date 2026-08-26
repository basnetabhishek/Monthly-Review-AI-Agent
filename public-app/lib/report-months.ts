import type { MonthOption } from "@/lib/analytics-types";

export const REPORT_MONTH_PATTERN = /^20\d{2}-(0[1-9]|1[0-2])$/;
export const DATE_SHIFT_MONTHS = 139;
export const SOURCE_START_MONTH = "2011-01";
export const SOURCE_END_MONTH = "2014-12";
export const DISPLAY_START_MONTH = "2022-08";
export const DISPLAY_END_MONTH = "2026-07";

function shiftReportMonth(value: string, delta: number) {
  if (!REPORT_MONTH_PATTERN.test(value)) throw new Error("Invalid report month");
  const [year, month] = value.split("-").map(Number);
  const shiftedIndex = year * 12 + month - 1 + delta;
  const shiftedYear = Math.floor(shiftedIndex / 12);
  const shiftedMonth = (shiftedIndex % 12) + 1;
  return `${shiftedYear}-${String(shiftedMonth).padStart(2, "0")}`;
}

export function toDisplayReportMonth(sourceMonth: string) {
  return shiftReportMonth(sourceMonth, DATE_SHIFT_MONTHS);
}

export function toSourceReportMonth(displayMonth: string) {
  return shiftReportMonth(displayMonth, -DATE_SHIFT_MONTHS);
}

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
  for (let offset = 0; offset < 48; offset += 1) {
    const value = shiftReportMonth(DISPLAY_END_MONTH, -offset);
    months.push({ value, label: formatReportMonth(value) });
  }
  return months;
}

export function isSupportedReportMonth(value: unknown): value is string {
  if (typeof value !== "string" || !REPORT_MONTH_PATTERN.test(value)) return false;
  return value >= DISPLAY_START_MONTH && value <= DISPLAY_END_MONTH;
}
