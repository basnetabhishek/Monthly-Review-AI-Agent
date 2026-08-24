import type { ReportData } from "@/lib/report-data";

export type DataSource = "databricks-live" | "validated-snapshot";

export type ReportResponse = ReportData & {
  summary: string;
  narrativeMode: "openai" | "validated-fallback";
  dataSource: DataSource;
};

export type MonthOption = {
  value: string;
  label: string;
};

export type MonthsResponse = {
  months: MonthOption[];
  dataSource: DataSource;
};

export type TrendPoint = {
  month: string;
  sales: number;
  profit: number;
  margin: number;
  orders: number;
  units: number;
  negativeOrders: number;
  salesMom: number | null;
  profitMom: number | null;
  ordersMom: number | null;
};

export type TrendsResponse = {
  points: TrendPoint[];
  dataSource: DataSource;
};

export type PerformanceItem = {
  group: string;
  segment: string;
  sales: number;
  profit: number;
  margin: number;
};

export type TargetItem = {
  market: string;
  segment: string;
  actual: number;
  target: number;
  attainment: number;
};

export type MarketAnalysisResponse = {
  reportMonth: string;
  markets: PerformanceItem[];
  categories: PerformanceItem[];
  targets: TargetItem[];
  dataSource: DataSource;
};

export type ArchiveRecord = {
  id: string;
  reportMonth: string;
  generatedAt: string;
  report: ReportResponse;
};
