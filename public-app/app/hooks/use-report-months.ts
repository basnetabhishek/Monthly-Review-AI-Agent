"use client";

import { useEffect, useState } from "react";
import type { MonthsResponse } from "@/lib/analytics-types";
import { fallbackMonthOptions } from "@/lib/report-months";

let request: Promise<MonthsResponse> | null = null;

function loadMonths() {
  request ??= fetch("/api/months")
    .then(async (response) => {
      if (!response.ok) throw new Error("Reporting periods could not be loaded.");
      return (await response.json()) as MonthsResponse;
    })
    .catch(() => ({ months: fallbackMonthOptions(), dataSource: "validated-snapshot" }));
  return request;
}

export function useReportMonths() {
  const [result, setResult] = useState<MonthsResponse>({
    months: [],
    dataSource: "validated-snapshot",
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    loadMonths().then((value) => {
      if (active) {
        setResult(value);
        setLoading(false);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  return { ...result, loading };
}
