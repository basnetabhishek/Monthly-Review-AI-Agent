import assert from "node:assert/strict";
import { test } from "node:test";
import { deterministicSummary, reportData } from "../lib/report-data.ts";

test("offline report trajectory includes only sales values established by regression fixtures", () => {
  assert.deepEqual(reportData.trend, [
    { month: "2026-05", sales: 422785 }, // source October 2014
    { month: "2026-06", sales: 555312 }, // source November 2014
    { month: "2026-07", sales: 503154 }, // source December 2014
  ]);
  assert.equal(reportData.current.sales, reportData.trend.at(-1).sales);
});

test("offline summary describes the validated current period without invented currency", () => {
  const summary = deterministicSummary(reportData);
  assert.match(summary, /Sales declined/);
  assert.match(summary, /source monetary units/);
  assert.doesNotMatch(summary, /\$|USD|EUR|GBP/);
});
