import { generateText } from "ai";
import { openai, type OpenAILanguageModelResponsesOptions } from "@ai-sdk/openai";
import { deterministicSummary, reportData, type ReportData } from "@/lib/report-data";
import { getDatabricksReportData, hasDatabricksConfig } from "@/lib/databricks-report";
import { unstable_cache } from "next/cache";

export const runtime = "nodejs";

const getCachedDatabricksReport = unstable_cache(
  getDatabricksReportData,
  ["monthly-business-review", "2014-12"],
  { revalidate: 3600 },
);

const getCachedOpenAiNarrative = unstable_cache(
  async (data: ReportData) => {
    const { text } = await generateText({
      model: openai(process.env.OPENAI_MODEL ?? "gpt-5.6-luna"),
      system:
        "You are an executive reporting analyst. Use only the supplied facts. Never invent numbers, causes, forecasts, or recommendations unsupported by the payload. Write exactly three concise sentences for senior leadership.",
      prompt: `Create an executive summary from this governed monthly KPI payload:\n${JSON.stringify({
        current: data.current,
        trend: data.trend,
        targetWatchlist: data.targets.slice(0, 3),
        profitExceptions: data.exceptions.length,
      })}`,
      maxOutputTokens: 220,
      providerOptions: {
        openai: {
          reasoningEffort: "none",
        } satisfies OpenAILanguageModelResponsesOptions,
      },
    });

    return text.trim();
  },
  ["monthly-business-review", "openai-narrative"],
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
    const summary = await getCachedOpenAiNarrative(data);
    return Response.json({ ...data, summary, narrativeMode: "openai", dataSource });
  } catch (error) {
    console.error("OpenAI narrative generation failed", error instanceof Error ? error.message : "Unknown error");
    return Response.json({ ...data, summary: fallback, narrativeMode: "validated-fallback", dataSource });
  }
}

