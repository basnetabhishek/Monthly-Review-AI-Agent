SELECT
  report_month,
  order_key,
  order_id,
  order_date,
  market,
  region,
  order_reported_sales,
  order_reported_profit,
  order_units,
  order_shipping_cost,
  order_lines
FROM workspace.mbr_reporting.vw_negative_profit_orders
WHERE report_month = CAST(:report_month AS DATE)
ORDER BY order_reported_profit ASC
LIMIT 10

