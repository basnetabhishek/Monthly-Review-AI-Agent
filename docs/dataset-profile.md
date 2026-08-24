# Dataset Profile

Status: **Source received and profiled**

## Provenance

| Field | Value |
|---|---|
| Dataset name | Global Superstore Dataset |
| Exact filename | `Global Superstore.txt` |
| Original URL | https://www.kaggle.com/datasets/fatihilhan/global-superstore-dataset |
| Publisher/owner | Fatih İlhan and collaborator, Kaggle distribution |
| Download date | 2026-08-23 |
| License | MIT, as listed on the Kaggle dataset page |
| File checksum | `458b28a3f6cb8ab3590d3f2a9be50396156f90c26e81f7fa135069240a536cff` |
| Local source copy | `data/raw/Global Superstore.txt` |
| Format | UTF-8-compatible, tab-delimited text with a header row |

## Verified profile

| Check | Result |
|---|---:|
| Rows | 51,290 |
| Columns | 27 |
| Distinct `Order ID` strings | 25,035 |
| Logical orders (`Order ID + Order Date + Customer ID`) | 25,754 |
| Average lines per order | 2.049 |
| Orders with multiple lines | 12,778 |
| Duplicate complete rows | 0 |
| `Row ID` unique | Yes |
| Order-date coverage | 2011-01-01 through 2014-12-31 |
| Available months | 48 of 48; none missing |
| Null/non-numeric core measures | 0 |
| Distinct-currency column | Not present |

## Decisions and remaining assumptions

### Schema and grain

- Each row is treated as one order line. `Row ID` is unique.
- The source reuses 605 `Order ID` strings across dates or customers. `Order ID` alone is not a reliable global transaction key.
- The approved logical order key is `Order ID + Order Date + Customer ID`, producing 25,754 orders.
- Complete duplicate rows were not found.
- A customer ID never maps to multiple names in this file. The same name can map to multiple IDs, so names must never be treated as customer keys.

### Monetary fields

- `Sales` will be used exactly as the source-provided sales measure. We will not apply `Discount` to it again.
- The empirical price-dispersion check is more consistent with `Sales` already reflecting discount, but this is evidence rather than definitive source documentation.
- `Profit` will be used as the source-provided profit measure; we will not subtract shipping again because its cost composition is undocumented.
- Shipping cost varies across lines in 12,776 of 12,778 multi-line orders, supporting line-level summation for descriptive shipping analysis.
- The file has no currency column. Until stronger documentation is available, cross-market amounts will be labeled `source monetary units`, not asserted to be USD.

### Operational fields

- This distribution contains one tabular file and no Returns table or return indicator.
- Returns-adjusted revenue and return-rate metrics are therefore out of scope.
- Cancellation status is not available.
- Missing ship dates will be excluded from delivery-duration calculations rather than treated as zero.
- Date consistency checks will be enforced in the Silver transformation.

## Empirical checks

The profiling workflow must calculate:

- Row count and distinct order count
- Rows per order distribution
- Duplicate row count
- Null counts for critical fields
- Date range and available months
- Negative/zero sales, quantity, and shipping-cost counts
- Discount value range
- Profit reconciliation summaries
- Shipping-cost consistency within multi-line orders
- Customer ID/name collision checks
- Product price consistency across discount bands

## Approved MVP data policy

- Treat `Sales`, `Profit`, `Quantity`, `Discount`, and `Shipping Cost` as source-provided line measures.
- Do not derive a second net-sales field from `Sales × (1 - Discount)`.
- Recompute aggregate margin as `SUM(Profit) / SUM(Sales)`.
- Compute order-level metrics only after grouping by the approved composite logical order key.
- Clearly disclose that targets are synthetic and returns are unavailable.
- Do not make causal claims about discounts, profit, shipping, or product performance.
