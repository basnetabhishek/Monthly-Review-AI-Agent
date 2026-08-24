SELECT
  report_month,
  category,
  sub_category,
  reported_sales,
  reported_profit,
  profit_margin_pct,
  distinct_orders,
  units_sold
FROM workspace.mbr_reporting.vw_category_performance
WHERE report_month = CAST(:report_month AS DATE)
ORDER BY reported_profit ASC, category, sub_category

