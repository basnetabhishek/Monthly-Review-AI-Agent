SELECT
  report_month,
  market,
  region,
  reported_sales,
  reported_profit,
  profit_margin_pct,
  distinct_orders,
  units_sold
FROM workspace.mbr_reporting.vw_market_performance
WHERE report_month = CAST(:report_month AS DATE)
ORDER BY reported_sales DESC, market, region

