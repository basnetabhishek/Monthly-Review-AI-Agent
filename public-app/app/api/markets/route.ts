import { getDatabricksMarketAnalysis, hasDatabricksConfig } from "@/lib/databricks-report";
import { reportData } from "@/lib/report-data";
import { isSupportedReportMonth } from "@/lib/report-months";
import { unstable_cache } from "next/cache";

export const runtime = "nodejs";

const getCachedMarketAnalysis = unstable_cache(
  getDatabricksMarketAnalysis,
  ["monthly-business-review", "market-analysis", "date-rebased-v3"],
  { revalidate: 3600 },
);

export async function GET(request: Request) {
  const reportMonth = new URL(request.url).searchParams.get("month") ?? reportData.reportMonth;
  if (!isSupportedReportMonth(reportMonth)) {
    return Response.json({ error: "Select a valid reporting month." }, { status: 400 });
  }

  if (hasDatabricksConfig()) {
    try {
      const data = await getCachedMarketAnalysis(reportMonth);
      return Response.json({ ...data, dataSource: "databricks-live" });
    } catch (error) {
      console.error("Databricks market query failed", error instanceof Error ? error.message : "Unknown error");
    }
  }

  if (reportMonth !== reportData.reportMonth) {
    return Response.json({ error: "Live Databricks data is temporarily unavailable for this period." }, { status: 503 });
  }

  return Response.json({
    reportMonth,
    markets: reportData.markets.map((item) => ({
      group: item[0], segment: item[1], sales: item[2], profit: item[3], margin: item[4] ?? 0,
    })),
    categories: reportData.categories.map((item) => ({
      group: item[0], segment: item[1], sales: item[2], profit: item[3], margin: item[4] ?? 0,
    })),
    targets: reportData.targets.map((item) => ({
      market: item[0], segment: item[1], actual: item[2], target: item[3], attainment: item[4] ?? 0,
    })),
    dataSource: "validated-snapshot",
  });
}
