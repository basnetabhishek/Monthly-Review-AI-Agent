SELECT
  report_month,
  reported_sales,
  reported_profit,
  profit_margin_pct,
  distinct_orders,
  units_sold
FROM workspace.mbr_reporting.vw_monthly_trends
WHERE report_month BETWEEN ADD_MONTHS(CAST(:report_month AS DATE), -11) AND CAST(:report_month AS DATE)
ORDER BY report_month

