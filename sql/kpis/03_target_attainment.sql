SELECT
  report_month,
  market,
  region,
  category,
  actual_sales,
  revenue_target,
  revenue_attainment_pct,
  revenue_target_gap,
  actual_profit,
  profit_target,
  profit_attainment_pct,
  actual_orders,
  orders_target,
  orders_attainment_pct,
  is_synthetic,
  target_method
FROM workspace.mbr_reporting.vw_target_attainment
WHERE report_month = CAST(:report_month AS DATE)
ORDER BY revenue_target_gap ASC, market, region, category

