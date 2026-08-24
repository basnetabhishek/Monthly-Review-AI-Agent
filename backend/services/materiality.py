from __future__ import annotations

from decimal import Decimal

from backend.models.kpi_payload import ExecutiveKpis, MaterialChange, TargetAttainment


def _absolute(value: Decimal | None) -> Decimal:
    return abs(value) if value is not None else Decimal("0")


def identify_material_changes(
    executive: ExecutiveKpis,
    targets: list[TargetAttainment],
) -> list[MaterialChange]:
    """Apply deterministic, versioned materiality rules.

    The LLM is never asked to decide whether a movement is material.
    """

    changes: list[MaterialChange] = []

    if _absolute(executive.sales_mom_pct) >= Decimal("15"):
        direction = "increased" if executive.sales_mom_pct >= 0 else "decreased"
        changes.append(
            MaterialChange(
                flag_id="sales_mom_material",
                severity="high",
                observation=f"Reported sales {direction} materially month over month.",
                metric_refs=["executive.reported_sales", "executive.sales_mom_pct"],
                rule_id="SALES_MOM_ABS_GTE_15_V1",
            )
        )

    if _absolute(executive.margin_change_points) >= Decimal("2"):
        direction = "improved" if executive.margin_change_points >= 0 else "declined"
        changes.append(
            MaterialChange(
                flag_id="margin_change_material",
                severity="high",
                observation=f"Profit margin {direction} materially from the previous month.",
                metric_refs=["executive.profit_margin_pct", "executive.margin_change_points"],
                rule_id="MARGIN_CHANGE_ABS_GTE_2PTS_V1",
            )
        )

    if executive.distinct_orders and (
        Decimal(executive.negative_profit_orders) / Decimal(executive.distinct_orders)
    ) >= Decimal("0.20"):
        changes.append(
            MaterialChange(
                flag_id="negative_order_share_high",
                severity="high",
                observation="At least 20% of logical orders generated negative reported profit.",
                metric_refs=["executive.negative_profit_orders", "executive.distinct_orders"],
                rule_id="NEGATIVE_ORDER_SHARE_GTE_20PCT_V1",
            )
        )

    at_risk = [
        row
        for row in targets
        if row.revenue_attainment_pct is not None and row.revenue_attainment_pct < Decimal("85")
    ]
    if at_risk:
        changes.append(
            MaterialChange(
                flag_id="revenue_targets_at_risk",
                severity="medium",
                observation=f"{len(at_risk)} market-region-category target rows are below 85% revenue attainment.",
                metric_refs=["target_attainment"],
                rule_id="REVENUE_ATTAINMENT_LT_85_V1",
            )
        )

    return changes

