# Monthly Business Review AI Agent

A portfolio project that converts governed Databricks SQL metrics into an executive monthly business review.

Core principle: **SQL calculates the facts; AI explains the facts.**

## Current status

Phase 1 — dataset acquisition, verification, metric definitions, and KPI regression fixtures completed. Next: Databricks Bronze ingestion design.

The exact source is a 51,290-row, 27-column tab-delimited Global Superstore file covering 2011–2014. The project uses source-provided Sales and Profit without inventing additional cost or discount calculations. Currency, returns, and cancellations are explicitly documented limitations.

## MVP scope

- Global Superstore source data plus clearly labeled synthetic monthly targets generated from a documented prior-year policy
- Bronze, Silver, and minimal Gold Delta tables
- Controlled SQL catalog for eight core KPIs
- Typed KPI payload
- Deterministic materiality rules
- Structured AI narrative with metric references
- Numerical, entity, and causal-language validation
- SQL-only fallback if narrative generation is unavailable
- Executive report UI and basic report history

## MVP KPIs

1. Revenue
2. Profit
3. Profit margin
4. Distinct orders
5. Units sold
6. Month-over-month change
7. Target attainment
8. Negative-profit exceptions

## Repository layout

```text
data/raw/          Local source files; ignored by Git
data/targets/      Optional target templates for a later externally supplied planning process
docs/              Architecture, dataset profile, and metric definitions
notebooks/         Databricks ingestion and transformation notebooks
sql/kpis/          Controlled reporting SQL
backend/           Report orchestration and validation service
frontend/          Executive report application
tests/             KPI and narrative-grounding tests
```

## Immediate next step

Place the exact Global Superstore CSV or Excel workbook in `data/raw/`. Record its original URL, publisher, download date, and license in `docs/dataset-profile.md`. Then run the profiling workflow before implementing transformations.

Run the profiler with the bundled Python runtime or any local Python environment containing pandas:

```powershell
python notebooks/00_profile_source.py data/raw/<global-superstore-file>
```

It writes a detailed Markdown result to `docs/dataset-profile-results.md` and machine-readable evidence to `work/dataset_profile.json`.

