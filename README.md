# Monthly Business Review AI Agent

### [Launch the live executive reporting demo →](https://monthly-review-ai-agent.vercel.app)

This project grew from a challenge I encountered repeatedly in my professional experience: monthly business reporting often requires hours of extracting data, reconciling metrics, investigating performance changes, and translating the results into a clear story for leadership.

I transformed that real-world problem into a demonstrable end-to-end data and AI solution. Using public and synthetic data, the project shows how Databricks, governed SQL, validation controls, generative AI, and a modern web application can work together to produce reliable, executive-ready reports in minutes.

More than a dashboard, this project demonstrates how I approach business problems: understand the decision leaders need to make, establish trusted metrics, automate repetitive work, and use AI only where it adds meaningful value. The concept is inspired by workflows from my previous roles, while the implementation was built independently without using confidential employer data, systems, or intellectual property.

## Intended audience

This solution is designed for three connected groups:

- **Executives and business leaders** who need a concise, trustworthy view of performance, emerging risks, and areas requiring action—without reviewing spreadsheets or running queries themselves.
- **Finance, sales, and operations teams** who spend significant time assembling recurring reports and explaining changes across revenue, profitability, targets, products, and markets.
- **Data and analytics teams** responsible for delivering governed metrics while ensuring that AI-generated insights remain traceable, validated, and grounded in approved business data.

These audiences were selected because monthly reporting sits at the intersection of business decision-making, operational analysis, and data governance. The project demonstrates how one controlled workflow can reduce manual effort for analysts, preserve trust for data teams, and deliver faster insights to leadership.

> **SQL establishes the truth. Validation protects it. AI turns it into a decision-ready narrative.**

## What it demonstrates

- Databricks medallion architecture with Bronze, Silver, and Gold Delta tables
- Governed KPI views served through Databricks SQL
- A controlled report workflow with visible query, validation, and narrative stages
- Grounded AI summaries that receive validated KPI payloads rather than raw data
- A public Next.js experience designed for Vercel deployment
- Dynamic discovery and analysis of all 48 monthly reporting periods
- Interactive trend, market, category, target, and report-history experiences
- A private Databricks App implementation for enterprise architecture proof
- Automated regression checks for business metrics and data quality

## User experience

The public application lets a visitor select any reporting period from August 2022 through July 2026 and generate an executive review. It displays progress while the system queries Databricks, validates the KPI payload, builds the business narrative, and renders:

- Executive summary
- Revenue, profit, margin, orders, and units
- Month-over-month performance
- Market and category performance
- Target attainment
- Negative-profit exceptions
- Twelve-month, twenty-four-month, and full-history performance trends
- Filterable market, region, category, and target-attainment analysis
- A private browser-local archive with downloadable report payloads

When live Databricks access is configured, the application discovers and queries all 48 reporting periods. A sanitized, validated July 2026 KPI snapshot remains available as a resilience fallback. The raw Global Superstore source file and all secrets are intentionally excluded from Git.

For portfolio presentation, the historical source timeline is deterministically shifted forward by 139 months: source January 2011 maps to August 2022 and source December 2014 maps to July 2026. Only dates and embedded order years are relabeled; every commercial KPI and month-over-month relationship remains unchanged. See [`docs/date-rebasing-policy.md`](docs/date-rebasing-policy.md).

## Architecture

```text
Global Superstore source
          |
          v
Databricks Bronze -> Silver -> Gold
          |                    |
          |                    v
          |             Governed KPI views
          |                    |
          +--------------------v
                    Validated report payload
                              |
                  +-----------+-----------+
                  |                       |
                  v                       v
        Private Databricks App    Public Next.js app
                                          |
                                          v
                                OpenAI grounded narrative
                                          |
                                          v
                                      Vercel
```

The model is never responsible for calculating business metrics. SQL produces the numbers, deterministic checks validate them, and the model is limited to explaining the supplied facts. If AI generation is unavailable, the application returns a deterministic fallback narrative.

## Technology

- **Data platform:** Databricks Free Edition, Unity Catalog, Delta Lake, SQL Warehouse
- **Data processing:** PySpark and SQL
- **Public application:** Next.js 16, React 19, TypeScript
- **AI layer:** Vercel AI SDK with the OpenAI provider
- **Hosting target:** Vercel
- **Private application:** Databricks Apps with Python
- **Testing:** Pytest and KPI regression fixtures

## Repository layout

```text
notebooks/          Databricks profiling, ingestion, transformation, and validation
sql/kpis/           Controlled KPI queries
backend/            Typed payload and validation services
deploy/             Databricks application packages
public-app/         Public Next.js portfolio application
docs/               Architecture, dataset profile, KPI baseline, and metric dictionary
tests/              Data quality and KPI regression tests
data/targets/       Synthetic planning targets with a documented policy
data/raw/           Local-only source location; contents are ignored by Git
```

## Run the public application locally

Requirements: Node.js 20.9 or newer and pnpm.

```powershell
cd public-app
pnpm install
pnpm dev
```

Open `http://localhost:3000` and click **Generate report**.

The application works without an API key by using its validated fallback summary. To enable generated OpenAI narratives, copy `public-app/.env.example` to `public-app/.env.local` and set:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.6-luna
```

`gpt-5.6-luna` is the default cost-efficient model for this short executive-writing workload. Generated narratives are cached for one hour, while the deterministic summary remains available whenever OpenAI is unavailable or unconfigured.

Never commit `.env.local` or an API key. The repository already ignores both.

## Connect the live Databricks warehouse

The report endpoint can query the governed reporting views directly through the Databricks SQL Statement Execution API. Configure these server-only variables locally or in Vercel:

```text
DATABRICKS_SERVER_HOSTNAME=dbc-example.cloud.databricks.com
DATABRICKS_WAREHOUSE_ID=your_warehouse_id
DATABRICKS_TOKEN=your_short_lived_token
```

Find the hostname and HTTP path under **SQL Warehouses → your warehouse → Connection details**. The warehouse ID is the final value in an HTTP path such as `/sql/1.0/warehouses/<warehouse-id>`.

The integration uses only hard-coded, parameterized `SELECT` statements against the `workspace.mbr_reporting` views. Presented months are translated back to governed source months before each query and returned dates are shifted forward by the same documented offset. Results are cached for one hour to protect Free Edition quotas. If the warehouse is sleeping, unavailable, or not configured, the application clearly falls back to its validated July 2026 KPI snapshot; it never presents fallback data as another month.

For a portfolio prototype, use a short-lived Databricks personal access token stored only as a sensitive Vercel environment variable. In a production account, replace the personal identity with a least-privilege service principal using OAuth machine-to-machine authentication.

## Deploy to Vercel

1. Import this GitHub repository into Vercel.
2. Set the project root directory to `public-app`.
3. Add the Databricks variables as sensitive, server-side environment variables; never prefix them with `NEXT_PUBLIC_`.
4. Add `OPENAI_API_KEY` as a sensitive production variable and optionally set `OPENAI_MODEL`; the application caches generated narratives for one hour and retains a deterministic fallback.
5. Keep the raw dataset and all credential values outside Git and browser code.

## Data and metric governance

The source is a 51,290-row, 27-column, tab-delimited Global Superstore dataset with an original 2011–2014 chronology, presented in the portfolio as August 2022–July 2026 under the documented date-rebasing policy. Currency normalization, returns, and cancellations are documented limitations. Synthetic monthly targets are clearly labeled and are generated from a documented prior-year policy.

Metric definitions and validation evidence are available in:

- `docs/metric-dictionary.md`
- `docs/kpi-baseline.md`
- `docs/dataset-profile-results.md`
- `docs/architecture.md`

## Privacy and security

- No raw customer-level dataset is committed
- No Databricks token or OpenAI key is committed
- Public hosting returns only aggregated KPI results from governed reporting views
- The report archive uses a versioned browser-local store, so no shared write database or additional cloud account is required for the portfolio release
- Generated narratives are constrained to supplied facts
- The Databricks workspace remains private and governed
