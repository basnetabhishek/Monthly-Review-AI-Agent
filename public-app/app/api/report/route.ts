import { openai, type OpenAILanguageModelResponsesOptions } from "@ai-sdk/openai";
import { generateText } from "ai";
import { unstable_cache } from "next/cache";
import type { DataSource } from "@/lib/analytics-types";
import { getDatabricksReportData, hasDatabricksConfig } from "@/lib/databricks-report";
import { deterministicSummary, reportData, type ReportData } from "@/lib/report-data";
import { isSupportedReportMonth } from "@/lib/report-months";

export const runtime = "nodejs";

const getCachedDatabricksReport = unstable_cache(
  getDatabricksReportData,
  ["monthly-business-review", "report", "v2"],
  { revalidate: 3600 },
);

const getCachedOpenAiNarrative = unstable_cache(
  async (data: ReportData) => {
    const { text } = await generateText({
      model: openai(process.env.OPENAI_MODEL ?? "gpt-5.6-luna"),
      system:
        "You are an executive reporting analyst. Use only the supplied facts. Never invent numbers, causes, forecasts, currencies, or recommendations unsupported by the payload. Currency is unspecified: never use a currency symbol or name a currency; refer to sales and profit as reported amounts. Write exactly three concise sentences for senior leadership.",
      prompt: `Create an executive summary from this governed monthly KPI payload:\n${JSON.stringify({
        monetaryUnit: "unspecified source monetary units",
        reportMonth: data.reportMonth,
        current: data.current,
        trend: data.trend,
        targetWatchlist: data.targets.slice(0, 3),
        topProfitExceptionsIncluded: data.exceptions.length,
      })}`,
      maxOutputTokens: 220,
      providerOptions: {
        openai: { reasoningEffort: "none" } satisfies OpenAILanguageModelResponsesOptions,
      },
    });
    return text.trim();
  },
  ["monthly-business-review", "openai-narrative", "v2"],
  { revalidate: 3600 },
);

export async function POST(request: Request) {
  let body: { month?: unknown } = {};
  try {
    body = (await request.json()) as { month?: unknown };
  } catch {
    // An empty body intentionally falls back to the validated snapshot month.
  }

  const reportMonth = body.month ?? reportData.reportMonth;
  if (!isSupportedReportMonth(reportMonth)) {
    return Response.json({ error: "Select a valid reporting month." }, { status: 400 });
  }

  let data: ReportData = reportData;
  let dataSource: DataSource = "validated-snapshot";

  if (hasDatabricksConfig()) {
    try {
      data = await getCachedDatabricksReport(reportMonth);
      dataSource = "databricks-live";
    } catch (error) {
      console.error("Databricks report query failed", error instanceof Error ? error.message : "Unknown error");
    }
  }

  if (dataSource !== "databricks-live" && reportMonth !== reportData.reportMonth) {
    return Response.json(
      { error: "Live Databricks data is temporarily unavailable for this reporting period." },
      { status: 503 },
    );
  }

  const fallback = deterministicSummary(data);
  if (!process.env.OPENAI_API_KEY) {
    return Response.json({ ...data, summary: fallback, narrativeMode: "validated-fallback", dataSource });
  }

  try {
    const summary = await getCachedOpenAiNarrative(data);
    return Response.json({ ...data, summary, narrativeMode: "openai", dataSource });
  } catch (error) {
    console.error("OpenAI narrative generation failed", error instanceof Error ? error.message : "Unknown error");
    return Response.json({ ...data, summary: fallback, narrativeMode: "validated-fallback", dataSource });
  }
}
