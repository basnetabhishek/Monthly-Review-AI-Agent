"""Calculate auditable monthly KPI baselines from the profiled source.

This is a local reference implementation, independent of the future Databricks
SQL queries. Its selected fixtures become acceptance-test expectations for the
Bronze/Silver/Gold pipeline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_COLUMNS = [
    "report_month",
    "reported_sales",
    "reported_profit",
    "profit_margin_pct",
    "distinct_orders",
    "units_sold",
    "negative_profit_orders",
    "negative_profit_amount",
    "sales_mom_pct",
    "profit_mom_pct",
    "orders_mom_pct",
]


def load_order_lines(source: Path) -> pd.DataFrame:
    frame = pd.read_csv(source, sep="\t", encoding_errors="replace")
    required = {"Order ID", "Order Date", "Customer ID", "Sales", "Profit", "Quantity"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    cleaned = frame[list(required)].copy()
    cleaned["Order Date"] = pd.to_datetime(cleaned["Order Date"], errors="raise")
    for column in ["Sales", "Profit", "Quantity"]:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="raise")
    cleaned["report_month"] = cleaned["Order Date"].dt.to_period("M").astype(str)
    cleaned["order_key"] = (
        cleaned["Order ID"].astype("string")
        + "||"
        + cleaned["Order Date"].dt.strftime("%Y-%m-%d")
        + "||"
        + cleaned["Customer ID"].astype("string")
    )
    return cleaned


def calculate_monthly_kpis(order_lines: pd.DataFrame) -> pd.DataFrame:
    line_metrics = (
        order_lines.groupby("report_month", as_index=False)
        .agg(
            reported_sales=("Sales", "sum"),
            reported_profit=("Profit", "sum"),
            distinct_orders=("order_key", "nunique"),
            units_sold=("Quantity", "sum"),
        )
        .sort_values("report_month")
    )

    order_metrics = (
        order_lines.groupby(["report_month", "order_key"], as_index=False)
        .agg(order_profit=("Profit", "sum"))
    )
    negative_orders = (
        order_metrics[order_metrics["order_profit"] < 0]
        .groupby("report_month", as_index=False)
        .agg(
            negative_profit_orders=("order_key", "nunique"),
            negative_profit_amount=("order_profit", "sum"),
        )
    )

    result = line_metrics.merge(negative_orders, on="report_month", how="left")
    result["negative_profit_orders"] = result["negative_profit_orders"].fillna(0).astype(int)
    result["negative_profit_amount"] = result["negative_profit_amount"].fillna(0.0)
    result["profit_margin_pct"] = np.where(
        result["reported_sales"] != 0,
        result["reported_profit"] / result["reported_sales"] * 100,
        np.nan,
    )
    result["sales_mom_pct"] = result["reported_sales"].pct_change(fill_method=None) * 100
    result["profit_mom_pct"] = result["reported_profit"].pct_change(fill_method=None) * 100
    result["orders_mom_pct"] = result["distinct_orders"].pct_change(fill_method=None) * 100
    return result[OUTPUT_COLUMNS]


def choose_fixture_months(monthly: pd.DataFrame) -> tuple[list[str], dict[str, str]]:
    first = monthly.iloc[0]
    last = monthly.iloc[-1]
    max_sales = monthly.loc[monthly["reported_sales"].idxmax()]
    max_growth = monthly.loc[monthly["sales_mom_pct"].idxmax()]
    max_loss_orders = monthly.loc[monthly["negative_profit_orders"].idxmax()]
    candidates = [
        (str(first["report_month"]), "first available month; prior-period metrics must be null"),
        (str(max_growth["report_month"]), "largest month-over-month reported-sales increase"),
        (str(max_loss_orders["report_month"]), "highest negative-profit order count"),
        (str(max_sales["report_month"]), "highest reported-sales month"),
        (str(last["report_month"]), "last available month"),
    ]
    reasons = {}
    selected = []
    for month, reason in candidates:
        if month not in reasons:
            reasons[month] = reason
            selected.append(month)
        else:
            reasons[month] += f"; {reason}"

    if len(selected) < 5:
        for month in monthly["report_month"].iloc[::-1]:
            month = str(month)
            if month not in reasons:
                reasons[month] = "additional recent regression-test month"
                selected.append(month)
            if len(selected) == 5:
                break
    return selected, reasons


def format_fixture(monthly: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    fixture = monthly[monthly["report_month"].isin(months)].copy()
    fixture["selection_order"] = fixture["report_month"].map({month: index for index, month in enumerate(months)})
    fixture = fixture.sort_values("selection_order").drop(columns="selection_order")
    currency_columns = ["reported_sales", "reported_profit", "negative_profit_amount"]
    percentage_columns = ["profit_margin_pct", "sales_mom_pct", "profit_mom_pct", "orders_mom_pct"]
    fixture[currency_columns] = fixture[currency_columns].round(6)
    fixture[percentage_columns] = fixture[percentage_columns].round(6)
    return fixture


def build_markdown(monthly: pd.DataFrame, fixture: pd.DataFrame, reasons: dict[str, str]) -> str:
    display = fixture.copy()
    for column in ["reported_sales", "reported_profit", "negative_profit_amount"]:
        display[column] = display[column].map(lambda value: f"{value:,.3f}")
    for column in ["profit_margin_pct", "sales_mom_pct", "profit_mom_pct", "orders_mom_pct"]:
        display[column] = display[column].map(lambda value: "N/A" if pd.isna(value) else f"{value:.3f}%")

    lines = [
        "# MVP KPI Baseline",
        "",
        "These values are calculated locally from the immutable source copy and will be used to test the future Databricks SQL implementation.",
        "",
        "## Definitions",
        "",
        "- Reported sales: sum of source `Sales` values.",
        "- Reported profit: sum of source `Profit` values.",
        "- Profit margin: total profit divided by total sales; row margins are never averaged.",
        "- Orders: distinct composite keys of `Order ID + Order Date + Customer ID`; the source reuses some Order ID strings.",
        "- Negative-profit orders: aggregate profit per order first, then count orders below zero.",
        "- MoM: percentage change from the immediately preceding calendar month.",
        "",
        "## Selected fixture months",
        "",
    ]
    for month in fixture["report_month"]:
        lines.append(f"- `{month}` — {reasons[str(month)]}")
    headers = list(display.columns)
    markdown_rows = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---:" if header != "report_month" else "---" for header in headers) + " |",
    ]
    for row in display.itertuples(index=False, name=None):
        markdown_rows.append("| " + " | ".join(map(str, row)) + " |")
    lines += ["", "## Expected values", "", *markdown_rows, ""]

    first = monthly.iloc[0]
    lines += [
        "## Acceptance rules",
        "",
        f"- The complete monthly output must contain `{len(monthly)}` months.",
        f"- The first month must be `{first['report_month']}` and its MoM fields must be null.",
        "- Databricks monetary results must match within `0.000001` source units.",
        "- Percentage results must match within `0.000001` percentage points.",
        "- Count metrics must match exactly.",
        "- Target attainment is tested separately after synthetic targets are generated.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    work_dir = project_root / "work"
    fixture_dir = project_root / "tests" / "fixtures"
    docs_dir = project_root / "docs"
    for directory in [work_dir, fixture_dir, docs_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    monthly = calculate_monthly_kpis(load_order_lines(args.source.resolve()))
    months, reasons = choose_fixture_months(monthly)
    fixture = format_fixture(monthly, months)

    monthly.to_csv(work_dir / "monthly_kpi_baseline.csv", index=False)
    fixture.to_csv(fixture_dir / "expected_monthly_kpis.csv", index=False)
    (fixture_dir / "fixture_selection.json").write_text(
        json.dumps({"months": months, "reasons": reasons}, indent=2), encoding="utf-8"
    )
    (docs_dir / "kpi-baseline.md").write_text(
        build_markdown(monthly, fixture, reasons), encoding="utf-8"
    )
    print(json.dumps({
        "months_calculated": len(monthly),
        "fixture_months": months,
        "baseline_csv": str(work_dir / "monthly_kpi_baseline.csv"),
        "fixture_csv": str(fixture_dir / "expected_monthly_kpis.csv"),
        "documentation": str(docs_dir / "kpi-baseline.md"),
    }, indent=2))


if __name__ == "__main__":
    main()
