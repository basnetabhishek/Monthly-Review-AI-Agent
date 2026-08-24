# Dataset Profile Results

Generated: `2026-08-24T03:56:33.761724+00:00`

## Source evidence

- Filename: `Global Superstore.txt`
- SHA-256: `458b28a3f6cb8ab3590d3f2a9be50396156f90c26e81f7fa135069240a536cff`
- Size: `15639131` bytes
- Format: `txt`
- Selected orders sheet: `None`
- Returns sheet candidates: `none`

## Schema and grain

- Rows: `51290`
- Columns: `27`
- Duplicate rows: `0`
- Distinct orders: `25035`
- Mean rows per order: `2.04873177551428`
- Multi-line orders: `12778`
- Unique row ID: `True`
- Missing core columns: `none`

## Date coverage

- Order dates: `{'parsed_rows': 51290, 'unparsed_rows': 0, 'minimum': '2011-01-01T00:00:00', 'maximum': '2014-12-31T00:00:00', 'distinct_months': 48, 'missing_calendar_months': []}`
- Ship dates: `{'parsed_rows': 51290, 'unparsed_rows': 0, 'minimum': '2011-01-03T00:00:00', 'maximum': '2015-01-07T00:00:00', 'distinct_months': 49, 'missing_calendar_months': []}`

## Numeric checks

- **sales**: `{'valid_rows': 51290, 'null_or_non_numeric_rows': 0, 'minimum': 0, 'maximum': 22638, 'zero_rows': 1, 'negative_rows': 0, 'sum': 12642905}`
- **profit**: `{'valid_rows': 51290, 'null_or_non_numeric_rows': 0, 'minimum': -6599.978, 'maximum': 8399.976, 'zero_rows': 668, 'negative_rows': 12544, 'sum': 1467457.2912800002}`
- **quantity**: `{'valid_rows': 51290, 'null_or_non_numeric_rows': 0, 'minimum': 1, 'maximum': 14, 'zero_rows': 0, 'negative_rows': 0, 'sum': 178312}`
- **discount**: `{'valid_rows': 51290, 'null_or_non_numeric_rows': 0, 'minimum': 0.0, 'maximum': 0.85, 'zero_rows': 29009, 'negative_rows': 0, 'sum': 7329.727999999999}`
- **shipping_cost**: `{'valid_rows': 51290, 'null_or_non_numeric_rows': 0, 'minimum': 0.002, 'maximum': 933.57, 'zero_rows': 0, 'negative_rows': 0, 'sum': 1352815.7034}`

## Semantic evidence

- Discount semantics: `{'status': 'evidence_only', 'warning': 'Lower price dispersion is evidence, not proof, because products may change price over time.', 'products_tested': 25, 'median_observed_unit_sales_cv': 0.3256227203421187, 'median_grossed_up_unit_sales_cv': 0.2064845318779323, 'sample': [{'product_id': 'OFF-ST-10002714', 'rows': 18, 'discount_levels': 7, 'observed_unit_sales_cv': 0.6794625017353118, 'grossed_up_unit_sales_cv': 0.6044736215295407}, {'product_id': 'OFF-EN-10002700', 'rows': 13, 'discount_levels': 7, 'observed_unit_sales_cv': 0.7774331576717728, 'grossed_up_unit_sales_cv': 0.7323480433035625}, {'product_id': 'TEC-CO-10000660', 'rows': 12, 'discount_levels': 7, 'observed_unit_sales_cv': 0.251122574764428, 'grossed_up_unit_sales_cv': 0.1458515946768719}, {'product_id': 'OFF-BI-10004140', 'rows': 25, 'discount_levels': 6, 'observed_unit_sales_cv': 0.49299966071899337, 'grossed_up_unit_sales_cv': 0.18389805203193543}, {'product_id': 'OFF-BI-10003650', 'rows': 24, 'discount_levels': 6, 'observed_unit_sales_cv': 1.5907969108991142, 'grossed_up_unit_sales_cv': 1.344736731535944}, {'product_id': 'OFF-BI-10001249', 'rows': 22, 'discount_levels': 6, 'observed_unit_sales_cv': 0.3912115623542412, 'grossed_up_unit_sales_cv': 0.0517554813623305}, {'product_id': 'OFF-ST-10001554', 'rows': 18, 'discount_levels': 6, 'observed_unit_sales_cv': 0.6652373446425278, 'grossed_up_unit_sales_cv': 0.6410211898974865}, {'product_id': 'OFF-ST-10003306', 'rows': 18, 'discount_levels': 6, 'observed_unit_sales_cv': 0.22058595987780025, 'grossed_up_unit_sales_cv': 0.05278029195660818}, {'product_id': 'OFF-PA-10002479', 'rows': 17, 'discount_levels': 6, 'observed_unit_sales_cv': 0.8009579478690857, 'grossed_up_unit_sales_cv': 0.7766954486377036}, {'product_id': 'FUR-CH-10004095', 'rows': 16, 'discount_levels': 6, 'observed_unit_sales_cv': 0.6177755488127517, 'grossed_up_unit_sales_cv': 0.5452039831466022}, {'product_id': 'FUR-BO-10001934', 'rows': 14, 'discount_levels': 6, 'observed_unit_sales_cv': 0.15575898348290948, 'grossed_up_unit_sales_cv': 0.00044301236976095466}, {'product_id': 'FUR-BO-10003103', 'rows': 12, 'discount_levels': 6, 'observed_unit_sales_cv': 0.4781585643469956, 'grossed_up_unit_sales_cv': 0.38224770540896863}, {'product_id': 'FUR-CH-10001797', 'rows': 12, 'discount_levels': 6, 'observed_unit_sales_cv': 0.2968570658979878, 'grossed_up_unit_sales_cv': 0.21787697699021183}, {'product_id': 'FUR-TA-10003473', 'rows': 12, 'discount_levels': 6, 'observed_unit_sales_cv': 0.19784009479826026, 'grossed_up_unit_sales_cv': 0.00033523837570711073}, {'product_id': 'OFF-AR-10001850', 'rows': 12, 'discount_levels': 6, 'observed_unit_sales_cv': 0.3256227203421187, 'grossed_up_unit_sales_cv': 0.2676669217849932}, {'product_id': 'OFF-BI-10004224', 'rows': 12, 'discount_levels': 6, 'observed_unit_sales_cv': 0.8897691568095376, 'grossed_up_unit_sales_cv': 0.6070267165571662}, {'product_id': 'OFF-SU-10001382', 'rows': 12, 'discount_levels': 6, 'observed_unit_sales_cv': 0.2440511459551812, 'grossed_up_unit_sales_cv': 0.2064845318779323}, {'product_id': 'FUR-TA-10001889', 'rows': 11, 'discount_levels': 6, 'observed_unit_sales_cv': 0.5777000236762673, 'grossed_up_unit_sales_cv': 0.3972293167250473}, {'product_id': 'TEC-PH-10002597', 'rows': 11, 'discount_levels': 6, 'observed_unit_sales_cv': 0.2039433908136035, 'grossed_up_unit_sales_cv': 0.03013901318460794}, {'product_id': 'OFF-LA-10000668', 'rows': 10, 'discount_levels': 6, 'observed_unit_sales_cv': 0.2399040398921287, 'grossed_up_unit_sales_cv': 0.005516520582423822}, {'product_id': 'FUR-BO-10001155', 'rows': 9, 'discount_levels': 6, 'observed_unit_sales_cv': 0.19254382573389442, 'grossed_up_unit_sales_cv': 0.0018270405157253793}, {'product_id': 'FUR-BO-10002545', 'rows': 8, 'discount_levels': 6, 'observed_unit_sales_cv': 0.21004178209289512, 'grossed_up_unit_sales_cv': 0.00033571773300002794}, {'product_id': 'FUR-BO-10004834', 'rows': 8, 'discount_levels': 6, 'observed_unit_sales_cv': 0.5718221658902665, 'grossed_up_unit_sales_cv': 0.5588032340312936}, {'product_id': 'FUR-CH-10001802', 'rows': 8, 'discount_levels': 6, 'observed_unit_sales_cv': 0.27301561324533935, 'grossed_up_unit_sales_cv': 0.03056095960363423}, {'product_id': 'FUR-CH-10002061', 'rows': 8, 'discount_levels': 6, 'observed_unit_sales_cv': 0.18856958565807738, 'grossed_up_unit_sales_cv': 0.0002694002270418665}]}`
- Shipping grain: `{'status': 'evidence_only', 'multiline_orders': 12778, 'multiline_orders_with_one_repeated_cost': 2, 'multiline_orders_with_varying_cost': 12776, 'warning': 'Repeated values suggest possible order-level duplication but do not prove source allocation semantics.'}`
- Currency: `{'currency_column_present': False, 'values': None, 'decision': 'verify_from_source_documentation'}`
- Customer identity: `{'ids_linked_to_multiple_names': 0, 'names_linked_to_multiple_ids': 795}`

## Metric readiness

- revenue: **ready**
- profit: **ready**
- orders: **ready**
- units: **ready**
- targets: **not ready**
- returns_adjusted_metrics: **not ready**

## Required human decisions

- Confirm the source URL, publisher, license, and download date.
- Confirm whether `Sales` is pre- or post-discount using source documentation plus the empirical evidence above.
- Confirm whether monetary fields use one comparable currency.
- Confirm whether shipping cost is line-level or order-level before aggregation.
- Decide whether returns are available and how they affect official KPIs.
