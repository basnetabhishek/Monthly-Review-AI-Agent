import assert from "node:assert/strict";
import { test } from "node:test";
import {
  fallbackMonthOptions,
  isSupportedReportMonth,
  toDisplayReportMonth,
  toSourceReportMonth,
} from "../lib/report-months.ts";

test("source-to-display date rebasing is reversible at documented boundaries", () => {
  assert.equal(toDisplayReportMonth("2011-01"), "2022-08");
  assert.equal(toDisplayReportMonth("2014-12"), "2026-07");
  assert.equal(toSourceReportMonth("2022-08"), "2011-01");
  assert.equal(toSourceReportMonth("2026-07"), "2014-12");
});

test("offline month discovery does not offer unavailable historical reports", () => {
  const months = fallbackMonthOptions();
  assert.deepEqual(months, [{ value: "2026-07", label: "July 2026" }]);
});

test("supported report months reject out-of-range and malformed requests", () => {
  for (const value of ["2022-08", "2026-07", "2024-12"]) {
    assert.equal(isSupportedReportMonth(value), true);
  }
  for (const value of ["2022-07", "2026-08", "2026-13", "2026-7", null, false, 202607]) {
    assert.equal(isSupportedReportMonth(value), false);
  }
});
