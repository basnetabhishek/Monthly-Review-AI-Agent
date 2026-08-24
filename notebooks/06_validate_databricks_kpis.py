# Databricks notebook source
# MAGIC %md
# MAGIC # 06 — Validate Databricks KPI Results
# MAGIC
# MAGIC Compares Databricks views against five immutable local regression fixtures.

# COMMAND ----------

from decimal import Decimal

from pyspark.sql import functions as F

dbutils.widgets.text("catalog_name", "workspace", "Unity Catalog catalog")
dbutils.widgets.text("reporting_schema", "mbr_reporting", "Reporting schema")

catalog_name = dbutils.widgets.get("catalog_name").strip()
reporting_schema = dbutils.widgets.get("reporting_schema").strip()
view_name = f"`{catalog_name}`.`{reporting_schema}`.`vw_monthly_trends`"

# COMMAND ----------

fixture_rows = [
    ("2011-01-01", Decimal("98902"), Decimal("8321.800960"), Decimal("8.414189"), 216, 1463, 61, Decimal("-9538.709740"), None, None, None),
    ("2012-08-01", Decimal("303158"), Decimal("43573.878580"), Decimal("14.373323"), 524, 3818, 122, Decimal("-13817.593540"), Decimal("108.718941"), Decimal("179.581602"), Decimal("61.230769")),
    ("2014-12-01", Decimal("503154"), Decimal("46916.520680"), Decimal("9.324485"), 1102, 7513, 284, Decimal("-41627.492500"), Decimal("-9.392558"), Decimal("-25.359422"), Decimal("1.848429")),
    ("2014-11-01", Decimal("555312"), Decimal("62856.587900"), Decimal("11.319148"), 1082, 7706, 265, Decimal("-38259.343040"), Decimal("31.346193"), Decimal("7.982763"), Decimal("33.580247")),
    ("2014-10-01", Decimal("422785"), Decimal("58209.834760"), Decimal("13.768188"), 810, 5876, 197, Decimal("-24696.628980"), Decimal("-12.136887"), Decimal("-14.371426"), Decimal("-20.743640")),
]

fixture_schema = """
  report_month_string STRING,
  expected_sales DECIMAL(18,6),
  expected_profit DECIMAL(18,6),
  expected_margin_pct DECIMAL(18,6),
  expected_orders BIGINT,
  expected_units BIGINT,
  expected_negative_orders BIGINT,
  expected_negative_amount DECIMAL(18,6),
  expected_sales_mom_pct DECIMAL(18,6),
  expected_profit_mom_pct DECIMAL(18,6),
  expected_orders_mom_pct DECIMAL(18,6)
"""
fixtures = spark.createDataFrame(fixture_rows, fixture_schema).withColumn(
    "report_month", F.to_date("report_month_string")
)

actual = spark.table(view_name)
if actual.count() != 48:
    raise AssertionError(f"Expected 48 monthly rows in {view_name}, found {actual.count()}")

comparison = (
    fixtures.join(actual, on="report_month", how="left")
    .select(
        "report_month",
        (F.abs(F.col("reported_sales") - F.col("expected_sales")) <= Decimal("0.000001")).alias("sales_ok"),
        (F.abs(F.col("reported_profit") - F.col("expected_profit")) <= Decimal("0.000001")).alias("profit_ok"),
        (F.abs(F.col("profit_margin_pct") - F.col("expected_margin_pct")) <= Decimal("0.000001")).alias("margin_ok"),
        (F.col("distinct_orders") == F.col("expected_orders")).alias("orders_ok"),
        (F.col("units_sold") == F.col("expected_units")).alias("units_ok"),
        (F.col("negative_profit_orders") == F.col("expected_negative_orders")).alias("negative_orders_ok"),
        (F.abs(F.col("negative_profit_amount") - F.col("expected_negative_amount")) <= Decimal("0.000001")).alias("negative_amount_ok"),
        F.when(
            F.col("expected_sales_mom_pct").isNull(), F.col("sales_mom_pct").isNull()
        ).otherwise(F.abs(F.col("sales_mom_pct") - F.col("expected_sales_mom_pct")) <= Decimal("0.000001")).alias("sales_mom_ok"),
        F.when(
            F.col("expected_profit_mom_pct").isNull(), F.col("profit_mom_pct").isNull()
        ).otherwise(F.abs(F.col("profit_mom_pct") - F.col("expected_profit_mom_pct")) <= Decimal("0.000001")).alias("profit_mom_ok"),
        F.when(
            F.col("expected_orders_mom_pct").isNull(), F.col("orders_mom_pct").isNull()
        ).otherwise(F.abs(F.col("orders_mom_pct") - F.col("expected_orders_mom_pct")) <= Decimal("0.000001")).alias("orders_mom_ok"),
    )
)

boolean_columns = [column for column in comparison.columns if column != "report_month"]
failed = comparison.filter(
    ~F.expr(" AND ".join([f"COALESCE({column}, false)" for column in boolean_columns]))
)
if failed.count() > 0:
    display(failed)
    raise AssertionError("Databricks KPI results do not match the approved local fixtures")

display(comparison)
print("PASS: all five regression months and all KPI fields match the approved local baseline")
