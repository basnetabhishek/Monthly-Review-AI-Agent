import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { deterministicSummary, reportData } from "@/lib/report-data";
import { getDatabricksReportData, hasDatabricksConfig } from "@/lib/databricks-report";
import { unstable_cache } from "next/cache";

export const runtime = "nodejs";

const getCachedDatabricksReport = unstable_cache(
  getDatabricksReportData,
  ["monthly-business-review", "2014-12"],
  { revalidate: 3600 },
);

export async function POST() {
  let data = reportData;
  let dataSource = "validated-snapshot";

  if (hasDatabricksConfig()) {
    try {
      data = await getCachedDatabricksReport();
      dataSource = "databricks-live";
    } catch (error) {
      console.error("Databricks report query failed", error instanceof Error ? error.message : "Unknown error");
    }
  }

  const fallback = deterministicSummary(data);
  if (!process.env.OPENAI_API_KEY) {
    return Response.json({ ...data, summary: fallback, narrativeMode: "validated-fallback", dataSource });
  }
  try {
    const { text } = await generateText({
      model: openai("gpt-5.4-mini"),
      system: "You are an executive reporting analyst. Use only supplied facts. Never invent numbers. Write exactly three concise sentences.",
      prompt: `Create an executive summary from this validated KPI payload:\n${JSON.stringify(data.current)}`,
    });
    return Response.json({ ...data, summary: text, narrativeMode: "openai", dataSource });
  } catch {
    return Response.json({ ...data, summary: fallback, narrativeMode: "validated-fallback", dataSource });
  }
}
