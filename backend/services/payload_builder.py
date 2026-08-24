from __future__ import annotations

from datetime import date
from typing import Any

from backend.models.kpi_payload import (
    DimensionPerformance,
    ExecutiveKpis,
    KpiPayload,
    NegativeProfitException,
    ReportMetadata,
    TargetAttainment,
    TrendPoint,
)
from backend.services.materiality import identify_material_changes


REQUIRED_QUERY_NAMES = {
    "executive_kpis",
    "monthly_trend",
    "target_attainment",
    "market_performance",
    "category_performance",
    "negative_profit_exceptions",
}


def _month(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def build_kpi_payload(
    report_month: date,
    query_results: dict[str, list[dict[str, Any]]],
    *,
    data_snapshot: str,
) -> KpiPayload:
    missing_queries = REQUIRED_QUERY_NAMES - set(query_results)
    if missing_queries:
        raise ValueError(f"Missing controlled query results: {sorted(missing_queries)}")

    executive_rows = query_results["executive_kpis"]
    if len(executive_rows) != 1:
        raise ValueError(f"Expected exactly one executive KPI row, found {len(executive_rows)}")
    executive_row = executive_rows[0]
    row_month = _month(executive_row["report_month"])
    if row_month != report_month:
        raise ValueError(f"Executive KPI row is for {row_month}, expected {report_month}")

    executive = ExecutiveKpis(**{
        key: executive_row.get(key)
        for key in ExecutiveKpis.model_fields
    })
    targets = [
        TargetAttainment(**{
            key: row.get(key)
            for key in TargetAttainment.model_fields
        })
        for row in query_results["target_attainment"]
    ]

    trend = [
        TrendPoint(
            report_month=_month(row["report_month"]),
            **{key: row.get(key) for key in TrendPoint.model_fields if key != "report_month"},
        )
        for row in query_results["monthly_trend"]
    ]
    market = [
        DimensionPerformance(
            dimension_type="market_region",
            primary_label=row["market"],
            secondary_label=row["region"],
            **{key: row.get(key) for key in ["reported_sales", "reported_profit", "profit_margin_pct", "distinct_orders", "units_sold"]},
        )
        for row in query_results["market_performance"]
    ]
    category = [
        DimensionPerformance(
            dimension_type="category_subcategory",
            primary_label=row["category"],
            secondary_label=row["sub_category"],
            **{key: row.get(key) for key in ["reported_sales", "reported_profit", "profit_margin_pct", "distinct_orders", "units_sold"]},
        )
        for row in query_results["category_performance"]
    ]
    exceptions = [
        NegativeProfitException(**{
            key: row.get(key)
            for key in NegativeProfitException.model_fields
        })
        for row in query_results["negative_profit_exceptions"]
    ]

    comparison_month = date(report_month.year - 1, report_month.month, 1) if report_month.year > 1 else None
    metadata = ReportMetadata(
        report_month=report_month,
        comparison_month=comparison_month,
        data_snapshot=data_snapshot,
        limitations=[
            "The source file does not identify a reporting currency; amounts are labeled source monetary units.",
            "Returns and cancellations are unavailable in the supplied source.",
            "Targets are synthetic and generated from prior-year actuals.",
            "Observed relationships are descriptive and do not establish causality.",
        ],
    )

    return KpiPayload(
        metadata=metadata,
        executive=executive,
        monthly_trend=trend,
        target_attainment=targets,
        market_performance=market,
        category_performance=category,
        negative_profit_exceptions=exceptions,
        material_changes=identify_material_changes(executive, targets),
    )

