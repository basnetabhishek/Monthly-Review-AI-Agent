import type { ReportData, ReportRow } from "@/lib/report-data";

type StatementResponse = {
  statement_id?: string;
  status?: { state?: string; error?: { message?: string } };
  manifest?: { schema?: { columns?: { name?: string }[] } };
  result?: { data_array?: (string | null)[][] };
};

const REPORT_MONTH = "2014-12-01";
const API_PATH = "/api/2.0/sql/statements";

const queries = {
  executive: `
    SELECT reported_sales, reported_profit, profit_margin_pct, distinct_orders,
           units_sold, negative_profit_orders, sales_mom_pct, profit_mom_pct,
           orders_mom_pct
    FROM workspace.mbr_reporting.vw_monthly_trends
    WHERE report_month = :report_month`,
  trend: `
    SELECT report_month, reported_sales
    FROM workspace.mbr_reporting.vw_monthly_trends
    WHERE report_month BETWEEN ADD_MONTHS(:report_month, -3) AND :report_month
    ORDER BY report_month`,
  markets: `
    SELECT market, region, reported_sales, reported_profit, profit_margin_pct
    FROM workspace.mbr_reporting.vw_market_performance
    WHERE report_month = :report_month
    ORDER BY reported_sales DESC, market, region
    LIMIT 6`,
  categories: `
    SELECT category, sub_category, reported_sales, reported_profit, profit_margin_pct
    FROM workspace.mbr_reporting.vw_category_performance
    WHERE report_month = :report_month
    ORDER BY reported_sales DESC, category, sub_category
    LIMIT 6`,
  targets: `
    SELECT market, CONCAT(region, ' · ', category) AS segment,
           actual_sales, revenue_target, revenue_attainment_pct
    FROM workspace.mbr_reporting.vw_target_attainment
    WHERE report_month = :report_month
    ORDER BY revenue_attainment_pct ASC, market, region, category
    LIMIT 6`,
  exceptions: `
    SELECT order_id, CONCAT(market, ' · ', region) AS location,
           order_reported_sales, order_reported_profit
    FROM workspace.mbr_reporting.vw_negative_profit_orders
    WHERE report_month = :report_month
    ORDER BY order_reported_profit ASC
    LIMIT 6`,
} as const;

function requiredConfig() {
  const hostname = process.env.DATABRICKS_SERVER_HOSTNAME
    ?.replace(/^https?:\/\//, "")
    .replace(/\/$/, "");
  const warehouseId = process.env.DATABRICKS_WAREHOUSE_ID;
  const token = process.env.DATABRICKS_TOKEN;

  if (!hostname || !warehouseId || !token) {
    throw new Error("Databricks connection is not configured");
  }

  return { hostname, warehouseId, token };
}

export function hasDatabricksConfig() {
  return Boolean(
    process.env.DATABRICKS_SERVER_HOSTNAME &&
      process.env.DATABRICKS_WAREHOUSE_ID &&
      process.env.DATABRICKS_TOKEN,
  );
}

async function databricksFetch(path: string, init?: RequestInit) {
  const { hostname, token } = requiredConfig();
  return fetch(`https://${hostname}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...init?.headers,
    },
    cache: "no-store",
    signal: AbortSignal.timeout(55_000),
  });
}

async function waitForResult(statement: StatementResponse) {
  let current = statement;
  const started = Date.now();

  while (["PENDING", "RUNNING"].includes(current.status?.state ?? "")) {
    if (!current.statement_id || Date.now() - started > 90_000) {
      throw new Error("Databricks statement timed out");
    }
    await new Promise((resolve) => setTimeout(resolve, 1_000));
    const response = await databricksFetch(`${API_PATH}/${current.statement_id}`);
    if (!response.ok) throw new Error(`Databricks polling failed (${response.status})`);
    current = (await response.json()) as StatementResponse;
  }

  if (current.status?.state !== "SUCCEEDED") {
    throw new Error(current.status?.error?.message ?? "Databricks statement failed");
  }
  return current;
}

async function execute(statement: string, rowLimit: number) {
  const { warehouseId } = requiredConfig();
  const response = await databricksFetch(API_PATH, {
    method: "POST",
    body: JSON.stringify({
      warehouse_id: warehouseId,
      catalog: "workspace",
      schema: "mbr_reporting",
      statement,
      parameters: [{ name: "report_month", value: REPORT_MONTH, type: "DATE" }],
      wait_timeout: "50s",
      on_wait_timeout: "CONTINUE",
      disposition: "INLINE",
      format: "JSON_ARRAY",
      row_limit: rowLimit,
    }),
  });
  if (!response.ok) throw new Error(`Databricks query failed (${response.status})`);

  const completed = await waitForResult((await response.json()) as StatementResponse);
  const names = completed.manifest?.schema?.columns?.map((column) => column.name ?? "") ?? [];
  const rows = completed.result?.data_array ?? [];
  return rows.map((values) => Object.fromEntries(names.map((name, index) => [name, values[index]])));
}

const number = (value: unknown) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) throw new Error("Databricks returned an invalid numeric value");
  return parsed;
};

const text = (value: unknown) => String(value ?? "");
const month = (value: unknown) => text(value).slice(0, 7);
const row = (values: unknown[], includePercent = true): ReportRow => {
  const base = [text(values[0]), text(values[1]), number(values[2]), number(values[3])] as const;
  return includePercent
    ? [...base, Number(number(values[4]).toFixed(1))]
    : base;
};

export async function getDatabricksReportData(): Promise<ReportData> {
  const [executiveRows, trendRows, marketRows, categoryRows, targetRows, exceptionRows] =
    await Promise.all([
      execute(queries.executive, 1),
      execute(queries.trend, 4),
      execute(queries.markets, 6),
      execute(queries.categories, 6),
      execute(queries.targets, 6),
      execute(queries.exceptions, 6),
    ]);

  const executive = executiveRows[0];
  if (!executive || trendRows.length === 0) throw new Error("Databricks returned no report data");

  return {
    reportMonth: REPORT_MONTH.slice(0, 7),
    current: {
      sales: number(executive.reported_sales),
      profit: number(executive.reported_profit),
      margin: number(executive.profit_margin_pct),
      orders: number(executive.distinct_orders),
      units: number(executive.units_sold),
      negativeOrders: number(executive.negative_profit_orders),
      salesMom: number(executive.sales_mom_pct),
      profitMom: number(executive.profit_mom_pct),
      ordersMom: number(executive.orders_mom_pct),
    },
    trend: trendRows.map((item) => ({
      month: month(item.report_month),
      sales: number(item.reported_sales),
    })),
    markets: marketRows.map((item) =>
      row([item.market, item.region, item.reported_sales, item.reported_profit, item.profit_margin_pct]),
    ),
    categories: categoryRows.map((item) =>
      row([item.category, item.sub_category, item.reported_sales, item.reported_profit, item.profit_margin_pct]),
    ),
    targets: targetRows.map((item) =>
      row([item.market, item.segment, item.actual_sales, item.revenue_target, item.revenue_attainment_pct]),
    ),
    exceptions: exceptionRows.map((item) =>
      row([item.order_id, item.location, item.order_reported_sales, item.order_reported_profit], false),
    ),
  };
}
