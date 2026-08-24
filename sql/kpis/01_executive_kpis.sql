SELECT
  report_month,
  reported_sales,
  reported_profit,
  profit_margin_pct,
  distinct_orders,
  units_sold,
  negative_profit_orders,
  negative_profit_amount,
  prior_sales,
  prior_profit,
  prior_orders,
  sales_mom_pct,
  profit_mom_pct,
  orders_mom_pct,
  prior_profit / NULLIF(prior_sales, 0) * 100 AS prior_profit_margin_pct,
  profit_margin_pct - (prior_profit / NULLIF(prior_sales, 0) * 100) AS margin_change_points
FROM workspace.mbr_reporting.vw_monthly_trends
WHERE report_month = CAST(:report_month AS DATE)

