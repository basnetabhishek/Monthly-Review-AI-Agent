# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Ingest Bronze
# MAGIC
# MAGIC Loads the immutable tab-delimited Global Superstore source into a Bronze Delta table.
# MAGIC All source values remain strings. Column names are normalized, and ingestion metadata is added.

# COMMAND ----------

from pyspark.sql import functions as F

dbutils.widgets.text("catalog_name", "workspace", "Unity Catalog catalog")
dbutils.widgets.text("bronze_schema", "mbr_bronze", "Bronze schema")
dbutils.widgets.text(
    "source_path",
    "/Volumes/workspace/mbr_bronze/landing/Global Superstore.txt",
    "Uploaded source path",
)

catalog_name = dbutils.widgets.get("catalog_name").strip()
bronze_schema = dbutils.widgets.get("bronze_schema").strip()
source_path = dbutils.widgets.get("source_path").strip()

if not catalog_name or not bronze_schema or not source_path:
    raise ValueError("catalog_name, bronze_schema, and source_path are required")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog_name}`.`{bronze_schema}`")
spark.sql(
    f"CREATE VOLUME IF NOT EXISTS `{catalog_name}`.`{bronze_schema}`.`landing`"
)

# COMMAND ----------

raw = (
    spark.read.format("csv")
    .option("header", "true")
    .option("sep", "\t")
    .option("quote", '"')
    .option("escape", '"')
    .option("multiLine", "false")
    .option("inferSchema", "false")
    .load(source_path)
)

expected_source_columns = {
    "Category",
    "City",
    "Country",
    "Customer ID",
    "Customer Name",
    "Discount",
    "Market",
    "Order Date",
    "Order ID",
    "Order Priority",
    "Product ID",
    "Product Name",
    "Profit",
    "Quantity",
    "Region",
    "Row ID",
    "Sales",
    "Segment",
    "Ship Date",
    "Ship Mode",
    "Shipping Cost",
    "State",
    "Sub-Category",
}
missing_columns = sorted(expected_source_columns - set(raw.columns))
if missing_columns:
    raise ValueError(f"Source is missing required columns: {missing_columns}")

column_mapping = {
    "Category": "category",
    "City": "city",
    "Country": "country",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Discount": "discount",
    "Market": "market",
    "记录数": "record_count",
    "Order Date": "order_date",
    "Order ID": "order_id",
    "Order Priority": "order_priority",
    "Product ID": "product_id",
    "Product Name": "product_name",
    "Profit": "profit",
    "Quantity": "quantity",
    "Region": "region",
    "Row ID": "row_id",
    "Sales": "sales",
    "Segment": "segment",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Shipping Cost": "shipping_cost",
    "State": "state",
    "Sub-Category": "sub_category",
    "Year": "source_year",
    "Market2": "market_group",
    "weeknum": "source_week_number",
}

bronze = raw.select(
    *[
        F.col(f"`{source_name}`").alias(column_mapping.get(source_name, source_name))
        for source_name in raw.columns
    ]
)

source_value_columns = bronze.columns
bronze = (
    bronze.withColumn("_source_file", F.lit(source_path))
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn(
        "_row_hash",
        F.sha2(
            F.concat_ws(
                "||",
                *[F.coalesce(F.col(column).cast("string"), F.lit("∅")) for column in source_value_columns],
            ),
            256,
        ),
    )
)

target_table = f"`{catalog_name}`.`{bronze_schema}`.`raw_orders`"
(
    bronze.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(target_table)
)

# COMMAND ----------

summary = spark.sql(
    f"""
    SELECT
      COUNT(*) AS row_count,
      COUNT(DISTINCT row_id) AS distinct_row_ids,
      COUNT(DISTINCT order_id) AS distinct_orders,
      SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS null_order_ids
    FROM {target_table}
    """
).first()

if summary.row_count != 51290:
    raise AssertionError(f"Expected 51,290 Bronze rows, found {summary.row_count:,}")
if summary.distinct_row_ids != 51290:
    raise AssertionError("Bronze Row ID values are not unique")
if summary.distinct_orders != 25035:
    raise AssertionError(f"Expected 25,035 orders, found {summary.distinct_orders:,}")
if summary.null_order_ids != 0:
    raise AssertionError("Bronze contains null Order IDs")

display(spark.createDataFrame([summary.asDict()]))
