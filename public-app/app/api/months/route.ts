import { getAvailableReportMonths, hasDatabricksConfig } from "@/lib/databricks-report";
import { fallbackMonthOptions } from "@/lib/report-months";
import { unstable_cache } from "next/cache";

export const runtime = "nodejs";

const getCachedMonths = unstable_cache(
  getAvailableReportMonths,
  ["monthly-business-review", "available-months", "date-rebased-v3"],
  { revalidate: 3600 },
);

export async function GET() {
  if (hasDatabricksConfig()) {
    try {
      const months = await getCachedMonths();
      if (months.length > 0) {
        return Response.json({ months, dataSource: "databricks-live" });
      }
    } catch (error) {
      console.error("Databricks month discovery failed", error instanceof Error ? error.message : "Unknown error");
    }
  }

  return Response.json({ months: fallbackMonthOptions(), dataSource: "validated-snapshot" });
}
