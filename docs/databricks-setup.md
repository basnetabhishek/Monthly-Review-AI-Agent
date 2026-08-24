# Databricks Free Edition Setup

## What Codex prepared

The local project contains the complete first-pass Databricks pipeline:

1. `02_ingest_bronze.py`
2. `03_build_silver.py`
3. `04_build_gold.py`
4. `05_create_reporting_views.sql`
5. `06_validate_databricks_kpis.py`

## User actions required when running the pipeline

### 1. Sign in to Databricks Free Edition

No separate AWS, Azure, or Google Cloud account is required.

### 2. Create the Bronze schema and landing volume

Run in a Databricks SQL editor or notebook:

```sql
CREATE SCHEMA IF NOT EXISTS workspace.mbr_bronze;
CREATE VOLUME IF NOT EXISTS workspace.mbr_bronze.landing;
```

If your Free Edition workspace does not provide a `workspace` catalog, replace it consistently with the catalog shown in Catalog Explorer.

### 3. Upload the source file

Upload the unchanged file to:

```text
/Volumes/workspace/mbr_bronze/landing/Global Superstore.txt
```

Do not convert or edit it first.

### 4. Import the notebooks

Import or create notebooks using the files in the local `notebooks/` directory. Keep the numeric order.

### 5. Run in order

Run notebooks 02 through 06. Each notebook stops with a specific error if an expected count or metric differs.

## Where Databricks stores the data

```text
workspace.mbr_bronze.raw_orders
workspace.mbr_silver.orders_clean
workspace.mbr_gold.monthly_performance
workspace.mbr_gold.order_summary
workspace.mbr_gold.monthly_targets
workspace.mbr_reporting.vw_executive_kpis
workspace.mbr_reporting.vw_monthly_trends
workspace.mbr_reporting.vw_target_attainment
workspace.mbr_reporting.vw_market_performance
workspace.mbr_reporting.vw_category_performance
workspace.mbr_reporting.vw_negative_profit_orders
```

The data files behind managed Delta tables live in Databricks-managed default storage. They are not placed in GitHub.

`Order ID` is not globally unique in the supplied source. Gold order metrics use a SHA-256 key built from `Order ID + Order Date + Customer ID`, resulting in 25,754 logical orders.

## Synthetic target policy

Targets exist from 2012 through 2014 and are calculated from the same month in the previous year:

- Sales target: prior-year sales plus 8%
- Profit target: prior-year profit plus 5%, with break-even as the minimum
- Order target: prior-year distinct orders plus 5%, rounded upward

Every target row contains `is_synthetic = true` and the generation method. The application must display this limitation.
