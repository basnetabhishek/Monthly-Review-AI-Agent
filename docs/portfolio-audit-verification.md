# Portfolio audit: reporting integrity verification

This checklist accompanies the unmerged audit branch. It records expected behavior, not proof that the tests have already passed.

## Local checks

From `public-app/` with dependencies installed:

```bash
pnpm test
pnpm typecheck
pnpm build
```

From the repository root, in a Python environment with the project's requirements:

```bash
python -m pytest -q tests/test_connectivity.py tests/test_kpi_payload.py tests/test_source_profiler.py
```

The CI workflow `.github/workflows/portfolio-validation.yml` runs these checks on pull requests (Node 22, Python 3.12). The source-data-dependent `tests/test_mvp_baseline.py` cannot run in CI because `data/raw/Global Superstore.txt` is intentionally excluded from the repository. Run that test separately with a licensed local source copy. The Databricks notebook `notebooks/06_validate_databricks_kpis.py` additionally requires a configured workspace and access to the reporting views.

## Manual regression scenarios

1. **No Databricks environment variables:** Start the public application. `/api/months` must list only July 2026 with `dataSource: "validated-snapshot"`. The report for that month should succeed; an earlier-month report should return HTTP 503 rather than silently reuse July data.
2. **Offline trends:** `/api/trends` must return exactly one July 2026 point with all metrics drawn from the validated snapshot (no historical zero-filled profits, margins, or orders). The Trends page must explicitly explain that history is unavailable and avoid drawing a one-point trend line.
3. **Offline report sales:** Only May–July 2026 sales figures (422,785; 555,312; 503,154) should appear in the snapshot chart, matching the October–December 2014 baseline fixtures; no unverified April 2026 amount should appear.
4. **Missing numeric SQL values:** In a test Databricks environment, feed null, empty-string, whitespace-only, and Boolean values into required KPI columns and verify the query-to-report conversion raises an error rather than substituting zero. Genuine numeric zero must remain valid. First-month month-over-month fields may still be null.
5. **Live Databricks:** With working server-side credentials, `/api/months` should discover the available shifted reporting months and `/api/trends` should load actual view-derived history. The Trends page should allow 12-, 24-, and 48-month range choices.
6. **Failover:** If configured Databricks becomes unavailable, the snapshot must be visibly labeled as fallback. No requested historical month should be presented as July.
7. **Narrative:** With no OpenAI key, the deterministic narrative should work. With OpenAI enabled, generated text must not invent currency or unsupported explanations.
8. **Security:** Confirm private Databricks credentials and model API keys never appear in browser responses or committed files.

## Scope and limits

The loading indicator must not claim individually tracked stages; it is a generic progress indicator. Live Databricks values are cached for up to one hour and are labeled accordingly.

These changes improve reporting integrity and offline transparency. They do **not** validate a live Databricks deployment, prove the accuracy of every historical KPI, or establish that a full production test suite passes. The branch should not be merged until the checks above have been executed and reviewed.
