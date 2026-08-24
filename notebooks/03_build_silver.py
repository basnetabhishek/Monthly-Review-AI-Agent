# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Build Silver
# MAGIC
# MAGIC Casts, cleans, deduplicates, and validates the order-line source. The Silver grain is one row per `row_id`.

# COMMAND ----------

from pyspark.sql import Window
from pyspark.sql import functions as F

dbutils.widgets.text("catalog_name", "workspace", "Unity Catalog catalog")
dbutils.widgets.text("bronze_schema", "mbr_bronze", "Bronze schema")
dbutils.widgets.text("silver_schema", "mbr_silver", "Silver schema")

catalog_name = dbutils.widgets.get("catalog_name").strip()
bronze_schema = dbutils.widgets.get("bronze_schema").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog_name}`.`{silver_schema}`")
source_table = f"`{catalog_name}`.`{bronze_schema}`.`raw_orders`"
target_table = f"`{catalog_name}`.`{silver_schema}`.`orders_clean`"

# COMMAND ----------

bronze = spark.table(source_table)
dedupe_window = Window.partitionBy(F.col("row_id")).orderBy(F.col("_ingested_at").desc())

silver = (
    bronze.withColumn("_dedupe_rank", F.row_number().over(dedupe_window))
    .filter(F.col("_dedupe_rank") == 1)
    .select(
        F.col("row_id").cast("long").alias("order_line_id"),
        F.trim("order_id").alias("order_id"),
        F.to_date("order_date").alias("order_date"),
        F.to_date("ship_date").alias("ship_date"),
        F.trim("ship_mode").alias("ship_mode"),
        F.trim("order_priority").alias("order_priority"),
        F.trim("customer_id").alias("customer_id"),
        F.trim("customer_name").alias("customer_name"),
        F.trim("segment").alias("segment"),
        F.trim("market").alias("market"),
        F.trim("market_group").alias("market_group"),
        F.trim("region").alias("region"),
        F.trim("country").alias("country"),
        F.trim("state").alias("state"),
        F.trim("city").alias("city"),
        F.trim("product_id").alias("product_id"),
        F.trim("product_name").alias("product_name"),
        F.trim("category").alias("category"),
        F.trim("sub_category").alias("sub_category"),
        F.col("sales").cast("decimal(18,6)").alias("reported_sales"),
        F.col("profit").cast("decimal(18,6)").alias("reported_profit"),
        F.col("quantity").cast("int").alias("quantity"),
        F.col("discount").cast("decimal(9,6)").alias("discount_rate"),
        F.col("shipping_cost").cast("decimal(18,6)").alias("shipping_cost"),
        F.col("_source_file"),
        F.col("_row_hash"),
        F.current_timestamp().alias("_silver_processed_at"),
    )
    .withColumn("report_month", F.trunc("order_date", "month"))
    .withColumn("days_to_ship", F.datediff("ship_date", "order_date"))
    .withColumn("is_negative_profit_line", F.col("reported_profit") < 0)
)

(
    silver.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(target_table)
)

# COMMAND ----------

checks = spark.sql(
    f"""
    SELECT
      COUNT(*) AS row_count,
      COUNT(DISTINCT order_line_id) AS distinct_line_ids,
      COUNT(DISTINCT order_id) AS distinct_orders,
      SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS null_order_ids,
      SUM(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END) AS null_order_dates,
      SUM(CASE WHEN reported_sales IS NULL THEN 1 ELSE 0 END) AS null_sales,
      SUM(CASE WHEN reported_profit IS NULL THEN 1 ELSE 0 END) AS null_profit,
      SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) AS null_quantity,
      SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END) AS nonpositive_quantities,
      SUM(CASE WHEN discount_rate < 0 OR discount_rate >= 1 THEN 1 ELSE 0 END) AS invalid_discounts,
      SUM(CASE WHEN ship_date < order_date THEN 1 ELSE 0 END) AS invalid_ship_dates,
      MIN(order_date) AS minimum_order_date,
      MAX(order_date) AS maximum_order_date
    FROM {target_table}
    """
).first()

expected = {
    "row_count": 51290,
    "distinct_line_ids": 51290,
    "distinct_orders": 25035,
    "null_order_ids": 0,
    "null_order_dates": 0,
    "null_sales": 0,
    "null_profit": 0,
    "null_quantity": 0,
    "nonpositive_quantities": 0,
    "invalid_discounts": 0,
    "invalid_ship_dates": 0,
}
for field, value in expected.items():
    actual = checks[field]
    if actual != value:
        raise AssertionError(f"Silver check failed for {field}: expected {value}, found {actual}")

if str(checks.minimum_order_date) != "2011-01-01" or str(checks.maximum_order_date) != "2014-12-31":
    raise AssertionError("Silver order-date range does not match the profiled source")

display(spark.createDataFrame([checks.asDict()]))

