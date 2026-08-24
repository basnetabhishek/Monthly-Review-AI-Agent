# MVP KPI Baseline

These values are calculated locally from the immutable source copy and will be used to test the future Databricks SQL implementation.

## Definitions

- Reported sales: sum of source `Sales` values.
- Reported profit: sum of source `Profit` values.
- Profit margin: total profit divided by total sales; row margins are never averaged.
- Orders: distinct composite keys of `Order ID + Order Date + Customer ID`; the source reuses some Order ID strings.
- Negative-profit orders: aggregate profit per order first, then count orders below zero.
- MoM: percentage change from the immediately preceding calendar month.

## Selected fixture months

- `2011-01` — first available month; prior-period metrics must be null
- `2012-08` — largest month-over-month reported-sales increase
- `2014-12` — highest negative-profit order count; last available month
- `2014-11` — highest reported-sales month
- `2014-10` — additional recent regression-test month

## Expected values

| report_month | reported_sales | reported_profit | profit_margin_pct | distinct_orders | units_sold | negative_profit_orders | negative_profit_amount | sales_mom_pct | profit_mom_pct | orders_mom_pct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2011-01 | 98,902.000 | 8,321.801 | 8.414% | 216 | 1463 | 61 | -9,538.710 | N/A | N/A | N/A |
| 2012-08 | 303,158.000 | 43,573.879 | 14.373% | 524 | 3818 | 122 | -13,817.594 | 108.719% | 179.582% | 61.231% |
| 2014-12 | 503,154.000 | 46,916.521 | 9.324% | 1102 | 7513 | 284 | -41,627.493 | -9.393% | -25.359% | 1.848% |
| 2014-11 | 555,312.000 | 62,856.588 | 11.319% | 1082 | 7706 | 265 | -38,259.343 | 31.346% | 7.983% | 33.580% |
| 2014-10 | 422,785.000 | 58,209.835 | 13.768% | 810 | 5876 | 197 | -24,696.629 | -12.137% | -14.371% | -20.744% |

## Acceptance rules

- The complete monthly output must contain `48` months.
- The first month must be `2011-01` and its MoM fields must be null.
- Databricks monetary results must match within `0.000001` source units.
- Percentage results must match within `0.000001` percentage points.
- Count metrics must match exactly.
- Target attainment is tested separately after synthetic targets are generated.
