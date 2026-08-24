import type { DataSource } from "@/lib/analytics-types";

export function StatusPill({ source }: { source: DataSource }) {
  const live = source === "databricks-live";
  return <span className={`statusPill ${live ? "live" : "snapshot"}`}><i />{live ? "DATABRICKS LIVE" : "VALIDATED SNAPSHOT"}</span>;
}
