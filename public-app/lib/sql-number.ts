/**
 * Convert required numeric fields returned by Databricks' JSON_ARRAY format.
 * A missing value must never masquerade as a valid zero KPI.
 */
export function parseRequiredKpiNumber(value: unknown): number {
  if ((typeof value !== "string" && typeof value !== "number") ||
      (typeof value === "string" && value.trim() === "")) {
    throw new Error("Databricks returned a missing or invalid numeric value");
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    throw new Error("Databricks returned an invalid numeric value");
  }
  return parsed;
}

/** Missing optional comparisons are intentional (e.g. first month MoM). */
export function parseOptionalKpiNumber(value: unknown): number | null {
  if (value == null || value === "") return null;
  return parseRequiredKpiNumber(value);
}
