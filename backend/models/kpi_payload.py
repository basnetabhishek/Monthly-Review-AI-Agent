from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReportMetadata(ContractModel):
    report_month: date
    comparison_month: date | None = None
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    currency_label: str = "source monetary units"
    data_snapshot: str
    schema_version: str = "1.0.0"
    limitations: list[str]


class ExecutiveKpis(ContractModel):
    reported_sales: Decimal
    reported_profit: Decimal
    profit_margin_pct: Decimal
    distinct_orders: int = Field(ge=0)
    units_sold: int = Field(ge=0)
    negative_profit_orders: int = Field(ge=0)
    negative_profit_amount: Decimal
    sales_mom_pct: Decimal | None = None
    profit_mom_pct: Decimal | None = None
    orders_mom_pct: Decimal | None = None
    prior_profit_margin_pct: Decimal | None = None
    margin_change_points: Decimal | None = None


class TrendPoint(ContractModel):
    report_month: date
    reported_sales: Decimal
    reported_profit: Decimal
    profit_margin_pct: Decimal
    distinct_orders: int = Field(ge=0)
    units_sold: int = Field(ge=0)


class TargetAttainment(ContractModel):
    market: str
    region: str
    category: str
    actual_sales: Decimal
    revenue_target: Decimal
    revenue_attainment_pct: Decimal | None
    revenue_target_gap: Decimal
    actual_profit: Decimal
    profit_target: Decimal
    profit_attainment_pct: Decimal | None
    actual_orders: int = Field(ge=0)
    orders_target: int = Field(ge=0)
    orders_attainment_pct: Decimal | None
    is_synthetic: bool
    target_method: str


class DimensionPerformance(ContractModel):
    dimension_type: Literal["market_region", "category_subcategory"]
    primary_label: str
    secondary_label: str
    reported_sales: Decimal
    reported_profit: Decimal
    profit_margin_pct: Decimal
    distinct_orders: int = Field(ge=0)
    units_sold: int = Field(ge=0)


class NegativeProfitException(ContractModel):
    order_key: str
    order_id: str
    order_date: date
    market: str
    region: str
    order_reported_sales: Decimal
    order_reported_profit: Decimal = Field(lt=0)
    order_units: int = Field(ge=0)
    order_shipping_cost: Decimal
    order_lines: int = Field(gt=0)


class MaterialChange(ContractModel):
    flag_id: str
    severity: Literal["high", "medium", "low"]
    observation: str
    metric_refs: list[str] = Field(min_length=1)
    rule_id: str


class KpiPayload(ContractModel):
    metadata: ReportMetadata
    executive: ExecutiveKpis
    monthly_trend: list[TrendPoint]
    target_attainment: list[TargetAttainment]
    market_performance: list[DimensionPerformance]
    category_performance: list[DimensionPerformance]
    negative_profit_exceptions: list[NegativeProfitException]
    material_changes: list[MaterialChange]

    @model_validator(mode="after")
    def report_month_is_present_in_trend(self) -> "KpiPayload":
        if not any(point.report_month == self.metadata.report_month for point in self.monthly_trend):
            raise ValueError("monthly_trend must include the selected report month")
        if any(not row.is_synthetic for row in self.target_attainment):
            raise ValueError("MVP target rows must be explicitly marked synthetic")
        return self

