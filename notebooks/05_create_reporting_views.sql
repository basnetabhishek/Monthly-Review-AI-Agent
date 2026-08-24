-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 05 — Create Reporting Views
-- MAGIC
-- MAGIC Update the catalog/schema values in the first command if you did not use the defaults.

-- COMMAND ----------

USE CATALOG workspace;

CREATE SCHEMA IF NOT EXISTS mbr_reporting;

-- COMMAND ----------

CREATE OR REPLACE VIEW mbr_reporting.vw_executive_kpis AS
WITH line_metrics AS (
  SELECT
    report_month,
    SUM(reported_sales) AS reported_sales,
    SUM(reported_profit) AS reported_profit,
    SUM(reported_profit) / NULLIF(SUM(reported_sales), 0) * 100 AS profit_margin_pct,
    SUM(quantity) AS units_sold
  FROM mbr_silver.orders_clean
  GROUP BY report_month
),
order_metrics AS (
  SELECT
    report_month,
    COUNT(*) AS distinct_orders,
    SUM(CASE WHEN is_negative_profit_order THEN 1 ELSE 0 END) AS negative_profit_orders,
    SUM(CASE WHEN is_negative_profit_order THEN order_reported_profit ELSE 0 END) AS negative_profit_amount
  FROM mbr_gold.order_summary
  GROUP BY report_month
)
SELECT
  l.report_month,
  l.reported_sales,
  l.reported_profit,
  l.profit_margin_pct,
  o.distinct_orders,
  l.units_sold,
  o.negative_profit_orders,
  o.negative_profit_amount
FROM line_metrics l
JOIN order_metrics o USING (report_month);

-- COMMAND ----------

CREATE OR REPLACE VIEW mbr_reporting.vw_monthly_trends AS
WITH base AS (
  SELECT * FROM mbr_reporting.vw_executive_kpis
),
comparison AS (
  SELECT
    *,
    LAG(reported_sales) OVER (ORDER BY report_month) AS prior_sales,
    LAG(reported_profit) OVER (ORDER BY report_month) AS prior_profit,
    LAG(distinct_orders) OVER (ORDER BY report_month) AS prior_orders
  FROM base
)
SELECT
  *,
  (reported_sales - prior_sales) / NULLIF(prior_sales, 0) * 100 AS sales_mom_pct,
  (reported_profit - prior_profit) / NULLIF(prior_profit, 0) * 100 AS profit_mom_pct,
  (distinct_orders - prior_orders) / NULLIF(prior_orders, 0) * 100 AS orders_mom_pct
FROM comparison;

-- COMMAND ----------

CREATE OR REPLACE VIEW mbr_reporting.vw_target_attainment AS
WITH actuals AS (
  SELECT
    report_month,
    market,
    region,
    category,
    SUM(reported_sales) AS actual_sales,
    SUM(reported_profit) AS actual_profit,
    COUNT(DISTINCT SHA2(CONCAT_WS('||', order_id, CAST(order_date AS STRING), customer_id), 256)) AS actual_orders
  FROM mbr_silver.orders_clean
  GROUP BY report_month, market, region, category
)
SELECT
  a.report_month,
  a.market,
  a.region,
  a.category,
  a.actual_sales,
  t.revenue_target,
  a.actual_sales / NULLIF(t.revenue_target, 0) * 100 AS revenue_attainment_pct,
  a.actual_sales - t.revenue_target AS revenue_target_gap,
  a.actual_profit,
  t.profit_target,
  CASE
    WHEN t.profit_target = 0 THEN NULL
    ELSE a.actual_profit / t.profit_target * 100
  END AS profit_attainment_pct,
  a.actual_orders,
  t.orders_target,
  a.actual_orders / NULLIF(t.orders_target, 0) * 100 AS orders_attainment_pct,
  t.is_synthetic,
  t.target_method
FROM actuals a
JOIN mbr_gold.monthly_targets t
  ON a.report_month = t.target_month
 AND a.market = t.market
 AND a.region = t.region
 AND a.category = t.category;

-- COMMAND ----------

CREATE OR REPLACE VIEW mbr_reporting.vw_market_performance AS
SELECT
  report_month,
  market,
  region,
  SUM(reported_sales) AS reported_sales,
  SUM(reported_profit) AS reported_profit,
  SUM(reported_profit) / NULLIF(SUM(reported_sales), 0) * 100 AS profit_margin_pct,
  COUNT(DISTINCT SHA2(CONCAT_WS('||', order_id, CAST(order_date AS STRING), customer_id), 256)) AS distinct_orders,
  SUM(quantity) AS units_sold
FROM mbr_silver.orders_clean
GROUP BY report_month, market, region;

-- COMMAND ----------

CREATE OR REPLACE VIEW mbr_reporting.vw_category_performance AS
SELECT
  report_month,
  category,
  sub_category,
  SUM(reported_sales) AS reported_sales,
  SUM(reported_profit) AS reported_profit,
  SUM(reported_profit) / NULLIF(SUM(reported_sales), 0) * 100 AS profit_margin_pct,
  COUNT(DISTINCT SHA2(CONCAT_WS('||', order_id, CAST(order_date AS STRING), customer_id), 256)) AS distinct_orders,
  SUM(quantity) AS units_sold
FROM mbr_silver.orders_clean
GROUP BY report_month, category, sub_category;

-- COMMAND ----------

CREATE OR REPLACE VIEW mbr_reporting.vw_negative_profit_orders AS
SELECT
  report_month,
  order_key,
  order_id,
  order_date,
  market,
  region,
  customer_id,
  order_reported_sales,
  order_reported_profit,
  order_units,
  order_shipping_cost,
  order_lines
FROM mbr_gold.order_summary
WHERE is_negative_profit_order;
