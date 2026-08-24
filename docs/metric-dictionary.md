# MVP Metric Dictionary

Status: **MVP definitions approved against the profiled source**

| Metric | Grain | Definition | Important rules |
|---|---|---|---|
| Reported sales | Order line, aggregated | `SUM(sales)` | Uses the source field without applying discount again. Display in source monetary units until currency is verified. |
| Reported profit | Order line, aggregated | `SUM(profit)` | Uses the source field without subtracting shipping again. Not returns-adjusted. |
| Profit margin | Requested reporting grain | `SUM(profit) / NULLIF(SUM(sales), 0)` | Never average row-level margins. |
| Orders | Logical order | Count distinct `Order ID + Order Date + Customer ID` keys | The source reuses 605 Order ID strings; never count Order ID alone. |
| Units sold | Order line, aggregated | `SUM(quantity)` | Profile found values from 1 to 14 with no zero or negative quantities. |
| MoM change | Same metric and grain in adjacent months | `(current - prior) / NULLIF(prior, 0)` | Return unavailable when no prior period exists. |
| Target attainment | Target-defined grain | `actual / NULLIF(target, 0)` | Targets are synthetic and must be labeled. No subcategory attainment without subcategory targets. |
| Negative-profit orders | Logical order | Aggregate profit by the composite order key, then filter `order_profit < 0` | Keep separate from negative-profit lines. |

## Source limitations attached to every report

- Monetary currency is not identified in the supplied file.
- Returns and cancellations are unavailable.
- Synthetic targets are illustrative rather than historical company plans.
- Discount analysis is descriptive and cannot establish causality.

## Regression-test months

The future Databricks implementation must match the locally calculated baseline for:

- `2011-01`: first available month; MoM values must be unavailable.
- `2012-08`: largest reported-sales MoM increase.
- `2014-12`: highest negative-profit order count and final available month.
- `2014-11`: highest reported-sales month.
- `2014-10`: additional recent comparison month.

Exact expected values and tolerances are documented in `docs/kpi-baseline.md` and stored in `tests/fixtures/expected_monthly_kpis.csv`.

## Deferred metrics

- Margin by discount band: descriptive relationship only; no causal claim.
- Shipping-cost ratio and delivery duration: separate measures after source grain is verified.
- Customer concentration: calculate directly from customer-level facts, never summed distinct counts.
- Repeat purchasing: requires a precise lookback-window definition.
