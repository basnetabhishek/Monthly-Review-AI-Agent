import assert from "node:assert/strict";
import { test } from "node:test";
import { parseRequiredKpiNumber, parseOptionalKpiNumber } from "../lib/sql-number.ts";

test("required numeric KPIs accept valid numeric SQL values", () => {
  for (const [value, expected] of [[0, 0], ["0", 0], [-3.5, -3.5], [" 2.75 ", 2.75], ["1e3", 1000]]) {
    assert.equal(parseRequiredKpiNumber(value), expected);
  }
});

test("required numeric KPIs reject missing, nonnumeric, and non-finite values", () => {
  for (const value of [null, undefined, "", " ", "\t", true, false, "abc", "NaN", "Infinity", NaN, Infinity, [], {}]) {
    assert.throws(() => parseRequiredKpiNumber(value), /Databricks returned/);
  }
});

test("optional month-over-month KPIs preserve missing as null without inventing zero", () => {
  assert.equal(parseOptionalKpiNumber(null), null);
  assert.equal(parseOptionalKpiNumber(undefined), null);
  assert.equal(parseOptionalKpiNumber(""), null);
  assert.equal(parseOptionalKpiNumber("0"), 0);
  assert.equal(parseOptionalKpiNumber("-12.5"), -12.5);
  assert.throws(() => parseOptionalKpiNumber(" "), /Databricks returned/);
  assert.throws(() => parseOptionalKpiNumber(false), /Databricks returned/);
});
