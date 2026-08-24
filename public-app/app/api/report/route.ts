import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { deterministicSummary, reportData } from "@/lib/report-data";

export async function POST() {
  const fallback = deterministicSummary();
  if (!process.env.OPENAI_API_KEY) return Response.json({ ...reportData, summary: fallback, narrativeMode: "validated-fallback" });
  try {
    const { text } = await generateText({
      model: openai("gpt-5.4-mini"),
      system: "You are an executive reporting analyst. Use only supplied facts. Never invent numbers. Write exactly three concise sentences.",
      prompt: `Create an executive summary from this validated KPI payload:\n${JSON.stringify(reportData.current)}`,
    });
    return Response.json({ ...reportData, summary: text, narrativeMode: "openai" });
  } catch {
    return Response.json({ ...reportData, summary: fallback, narrativeMode: "validated-fallback" });
  }
}
