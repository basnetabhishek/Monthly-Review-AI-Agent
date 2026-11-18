import { getDatabricksTrendData, hasDatabricksConfig } from "@/lib/databricks-report";
import { reportData } from "@/lib/report-data";
import { unstable_cache } from "next/cache";

export const runtime = "nodejs";

const getCachedTrends = unstable_cache(
  getDatabricksTrendData,
  ["monthly-business-review", "performance-trends", "date-rebased-v3"],
  { revalidate: 3600 },
);

export async function GET() {
  if (hasDatabricksConfig()) {
    try {
      const points = await getCachedTrends();
      return Response.json({ points, dataSource: "databricks-live" });
    } catch (error) {
      console.error("Databricks trend query failed", error instanceof Error ? error.message : "Unknown error");
    }
  }

  // The snapshot only validates the final month's full KPI set.
  // Earlier fallback sales figures do not include validated profit, margin,
  // or order data, so do not fabricate those values as zeros.
  const points = [{
    month: reportData.reportMonth,
    sales: reportData.current.sales,
    profit: reportData.current.profit,
    margin: reportData.current.margin,
    orders: reportData.current.orders,
    units: reportData.current.units,
    negativeOrders: reportData.current.negativeOrders,
    salesMom: reportData.current.salesMom,
    profitMom: reportData.current.profitMom,
    ordersMom: reportData.current.ordersMom,
  }];

  return Response.json({ points, dataSource: "validated-snapshot" });
}
