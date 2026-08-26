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

  const points = reportData.trend.map((item, index) => ({
    month: item.month,
    sales: item.sales,
    profit: index === reportData.trend.length - 1 ? reportData.current.profit : 0,
    margin: index === reportData.trend.length - 1 ? reportData.current.margin : 0,
    orders: index === reportData.trend.length - 1 ? reportData.current.orders : 0,
    units: index === reportData.trend.length - 1 ? reportData.current.units : 0,
    negativeOrders: index === reportData.trend.length - 1 ? reportData.current.negativeOrders : 0,
    salesMom: index === reportData.trend.length - 1 ? reportData.current.salesMom : null,
    profitMom: index === reportData.trend.length - 1 ? reportData.current.profitMom : null,
    ordersMom: index === reportData.trend.length - 1 ? reportData.current.ordersMom : null,
  }));

  return Response.json({ points, dataSource: "validated-snapshot" });
}
