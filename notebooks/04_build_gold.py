# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Build Gold
# MAGIC
# MAGIC Builds two physical facts and transparent synthetic targets:
# MAGIC
# MAGIC - `monthly_performance`: additive line measures at month × market × region × category × subcategory
# MAGIC - `order_summary`: one row per order
# MAGIC - `monthly_targets`: prior-year actuals converted into explicitly synthetic planning targets

# COMMAND ----------

dbutils.widgets.text("catalog_name", "workspace", "Unity Catalog catalog")
dbutils.widgets.text("silver_schema", "mbr_silver", "Silver schema")
dbutils.widgets.text("gold_schema", "mbr_gold", "Gold schema")

catalog_name = dbutils.widgets.get("catalog_name").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog_name}`.`{gold_schema}`")
silver_orders = f"`{catalog_name}`.`{silver_schema}`.`orders_clean`"

# COMMAND ----------

spark.sql(
    f"""
    CREATE OR REPLACE TABLE `{catalog_name}`.`{gold_schema}`.`monthly_performance`
    USING DELTA
    AS
    SELECT
      report_month,
      market,
      region,
      category,
      sub_category,
      SUM(reported_sales) AS reported_sales,
      SUM(reported_profit) AS reported_profit,
      SUM(quantity) AS units_sold,
      SUM(shipping_cost) AS shipping_cost,
      SUM(CASE WHEN reported_profit < 0 THEN reported_profit ELSE 0 END) AS negative_profit_line_amount,
      SUM(CASE WHEN reported_profit < 0 THEN 1 ELSE 0 END) AS negative_profit_lines,
      COUNT(*) AS order_lines
    FROM {silver_orders}
    GROUP BY report_month, market, region, category, sub_category
    """
)

# COMMAND ----------

spark.sql(
    f"""
    CREATE OR REPLACE TABLE `{catalog_name}`.`{gold_schema}`.`order_summary`
    USING DELTA
    AS
    SELECT
      report_month,
      SHA2(CONCAT_WS('||', order_id, CAST(order_date AS STRING), customer_id), 256) AS order_key,
      order_id,
      order_date,
      MAX(ship_date) AS final_ship_date,
      MAX(days_to_ship) AS maximum_days_to_ship,
      customer_id,
      MIN(market) AS market,
      MIN(region) AS region,
      SUM(reported_sales) AS order_reported_sales,
      SUM(reported_profit) AS order_reported_profit,
      SUM(quantity) AS order_units,
      SUM(shipping_cost) AS order_shipping_cost,
      COUNT(*) AS order_lines,
      SUM(reported_profit) < 0 AS is_negative_profit_order
    FROM {silver_orders}
    GROUP BY report_month, order_id, order_date, customer_id
    """
)

# COMMAND ----------

# Synthetic target policy:
# - Each month from 2012 onward targets the same month one year earlier.
# - Sales target: prior-year actual × 1.08.
# - Profit target: prior-year actual × 1.05, with break-even (0) as the minimum target.
# - Order target: ceiling(prior-year distinct orders × 1.05).
# This is demonstration planning data, never historical company guidance.
spark.sql(
    f"""
    CREATE OR REPLACE TABLE `{catalog_name}`.`{gold_schema}`.`monthly_targets`
    USING DELTA
    AS
    WITH prior_year_actuals AS (
      SELECT
        ADD_MONTHS(report_month, 12) AS target_month,
        market,
        region,
        category,
        SUM(reported_sales) AS prior_year_sales,
        SUM(reported_profit) AS prior_year_profit,
        COUNT(DISTINCT SHA2(CONCAT_WS('||', order_id, CAST(order_date AS STRING), customer_id), 256)) AS prior_year_orders
      FROM {silver_orders}
      WHERE report_month < DATE '2014-01-01'
      GROUP BY report_month, market, region, category
    )
    SELECT
      target_month,
      market,
      region,
      category,
      ROUND(prior_year_sales * 1.08, 6) AS revenue_target,
      ROUND(GREATEST(prior_year_profit * 1.05, 0), 6) AS profit_target,
      CAST(CEIL(prior_year_orders * 1.05) AS BIGINT) AS orders_target,
      CAST(true AS BOOLEAN) AS is_synthetic,
      'PRIOR_YEAR_PLUS_GROWTH' AS target_method,
      CAST(0.08 AS DECIMAL(9,6)) AS revenue_growth_assumption,
      CAST(0.05 AS DECIMAL(9,6)) AS profit_growth_assumption,
      CAST(0.05 AS DECIMAL(9,6)) AS order_growth_assumption
    FROM prior_year_actuals
    """
)

# COMMAND ----------

quality = spark.sql(
    f"""
    SELECT
      (SELECT COUNT(*) FROM `{catalog_name}`.`{gold_schema}`.`monthly_performance`) AS performance_rows,
      (SELECT COUNT(*) FROM `{catalog_name}`.`{gold_schema}`.`order_summary`) AS order_rows,
      (SELECT COUNT(*) FROM `{catalog_name}`.`{gold_schema}`.`monthly_targets`) AS target_rows,
      (SELECT COUNT(DISTINCT report_month) FROM `{catalog_name}`.`{gold_schema}`.`monthly_performance`) AS performance_months,
      (SELECT COUNT(DISTINCT target_month) FROM `{catalog_name}`.`{gold_schema}`.`monthly_targets`) AS target_months
    """
).first()

if quality.order_rows != 25754:
    raise AssertionError(f"Expected 25,754 logical Gold orders, found {quality.order_rows:,}")
if quality.performance_months != 48:
    raise AssertionError(f"Expected 48 performance months, found {quality.performance_months}")
if quality.target_months != 36:
    raise AssertionError(f"Expected 36 synthetic target months, found {quality.target_months}")
if quality.target_rows <= 0 or quality.performance_rows <= 0:
    raise AssertionError("Gold tables unexpectedly contain no rows")

display(spark.createDataFrame([quality.asDict()]))
