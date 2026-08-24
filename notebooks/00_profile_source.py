"""Profile the exact Global Superstore source before defining business metrics.

Run locally:
    python notebooks/00_profile_source.py data/raw/<file.csv-or-xlsx>

The script writes machine-readable evidence to work/dataset_profile.json and a
human-readable report to docs/dataset-profile-results.md. It does not transform
or overwrite the source file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ALIASES = {
    "row_id": {"row_id", "rowid"},
    "order_id": {"order_id", "orderid"},
    "order_date": {"order_date", "orderdate"},
    "ship_date": {"ship_date", "shipdate"},
    "customer_id": {"customer_id", "customerid"},
    "customer_name": {"customer_name", "customername"},
    "product_id": {"product_id", "productid"},
    "product_name": {"product_name", "productname"},
    "sales": {"sales", "sale", "revenue"},
    "profit": {"profit"},
    "quantity": {"quantity", "qty"},
    "discount": {"discount", "discount_rate"},
    "shipping_cost": {"shipping_cost", "shippingcost", "freight"},
    "market": {"market"},
    "region": {"region"},
    "category": {"category"},
    "sub_category": {"sub_category", "subcategory"},
    "currency": {"currency", "currency_code"},
}


def slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_source(path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        workbook = pd.ExcelFile(path)
        sheets = {}
        frames = {}
        for name in workbook.sheet_names:
            frame = pd.read_excel(path, sheet_name=name)
            frames[name] = frame
            sheets[name] = {"rows": int(len(frame)), "columns": list(map(str, frame.columns))}

        def order_score(item: tuple[str, pd.DataFrame]) -> tuple[int, int]:
            name, frame = item
            cols = {slug(column) for column in frame.columns}
            signals = sum(alias in cols for alias in {"order_id", "orderid", "sales", "profit", "quantity"})
            return signals, len(frame)

        selected_name, selected = max(frames.items(), key=order_score)
        return selected, {
            "format": suffix.lstrip("."),
            "sheet_inventory": sheets,
            "selected_orders_sheet": selected_name,
            "returns_sheet_candidates": [name for name in workbook.sheet_names if "return" in name.lower()],
        }
    if suffix in {".csv", ".txt", ".tsv"}:
        separator = "\t" if suffix == ".tsv" else None
        frame = pd.read_csv(path, sep=separator, engine="python", encoding_errors="replace")
        return frame, {
            "format": suffix.lstrip("."),
            "sheet_inventory": None,
            "selected_orders_sheet": None,
            "returns_sheet_candidates": [],
        }
    raise ValueError(f"Unsupported source type: {suffix}. Use CSV, TSV, XLS, or XLSX.")


def resolve_columns(frame: pd.DataFrame) -> dict[str, str]:
    by_slug = {slug(column): str(column) for column in frame.columns}
    resolved = {}
    for canonical, alternatives in ALIASES.items():
        match = next((by_slug[name] for name in alternatives if name in by_slug), None)
        if match:
            resolved[canonical] = match
    return resolved


def numeric_series(frame: pd.DataFrame, column: str | None) -> pd.Series | None:
    if not column:
        return None
    return pd.to_numeric(frame[column], errors="coerce")


def date_profile(frame: pd.DataFrame, column: str | None) -> dict[str, Any] | None:
    if not column:
        return None
    values = pd.to_datetime(frame[column], errors="coerce")
    months = values.dropna().dt.to_period("M")
    return {
        "parsed_rows": int(values.notna().sum()),
        "unparsed_rows": int(values.isna().sum()),
        "minimum": json_value(values.min()),
        "maximum": json_value(values.max()),
        "distinct_months": int(months.nunique()),
        "missing_calendar_months": missing_months(months),
    }


def missing_months(months: pd.Series) -> list[str]:
    if months.empty:
        return []
    expected = pd.period_range(months.min(), months.max(), freq="M")
    observed = set(months.unique())
    return [str(month) for month in expected if month not in observed]


def numeric_profile(values: pd.Series | None) -> dict[str, Any] | None:
    if values is None:
        return None
    valid = values.dropna()
    return {
        "valid_rows": int(values.notna().sum()),
        "null_or_non_numeric_rows": int(values.isna().sum()),
        "minimum": json_value(valid.min()) if not valid.empty else None,
        "maximum": json_value(valid.max()) if not valid.empty else None,
        "zero_rows": int((valid == 0).sum()),
        "negative_rows": int((valid < 0).sum()),
        "sum": json_value(valid.sum()) if not valid.empty else None,
    }


def ratio_cv(values: pd.Series) -> float | None:
    values = values.replace([np.inf, -np.inf], np.nan).dropna()
    if len(values) < 2 or values.mean() == 0:
        return None
    return float(values.std(ddof=0) / abs(values.mean()))


def discount_evidence(frame: pd.DataFrame, columns: dict[str, str]) -> dict[str, Any]:
    required = {"sales", "quantity", "discount", "product_id"}
    if not required.issubset(columns):
        return {"status": "insufficient_columns", "missing": sorted(required - set(columns))}

    probe = pd.DataFrame({
        "product": frame[columns["product_id"]].astype("string"),
        "sales": numeric_series(frame, columns["sales"]),
        "quantity": numeric_series(frame, columns["quantity"]),
        "discount": numeric_series(frame, columns["discount"]),
    }).dropna()
    probe = probe[(probe["quantity"] > 0) & (probe["discount"] >= 0) & (probe["discount"] < 1)]
    probe["observed_unit_sales"] = probe["sales"] / probe["quantity"]
    probe["grossed_up_unit_sales"] = probe["sales"] / ((1 - probe["discount"]) * probe["quantity"])

    results = []
    for product, group in probe.groupby("product"):
        if group["discount"].nunique() < 2 or len(group) < 3:
            continue
        results.append({
            "product_id": str(product),
            "rows": int(len(group)),
            "discount_levels": int(group["discount"].nunique()),
            "observed_unit_sales_cv": ratio_cv(group["observed_unit_sales"]),
            "grossed_up_unit_sales_cv": ratio_cv(group["grossed_up_unit_sales"]),
        })
    results = sorted(results, key=lambda item: (-item["discount_levels"], -item["rows"]))[:25]
    observed_scores = [item["observed_unit_sales_cv"] for item in results if item["observed_unit_sales_cv"] is not None]
    grossed_scores = [item["grossed_up_unit_sales_cv"] for item in results if item["grossed_up_unit_sales_cv"] is not None]
    return {
        "status": "evidence_only",
        "warning": "Lower price dispersion is evidence, not proof, because products may change price over time.",
        "products_tested": len(results),
        "median_observed_unit_sales_cv": json_value(np.median(observed_scores)) if observed_scores else None,
        "median_grossed_up_unit_sales_cv": json_value(np.median(grossed_scores)) if grossed_scores else None,
        "sample": results,
    }


def shipping_evidence(frame: pd.DataFrame, columns: dict[str, str]) -> dict[str, Any]:
    if not {"order_id", "shipping_cost"}.issubset(columns):
        return {"status": "insufficient_columns"}
    probe = pd.DataFrame({
        "order_id": frame[columns["order_id"]].astype("string"),
        "shipping_cost": numeric_series(frame, columns["shipping_cost"]),
    }).dropna()
    grouped = probe.groupby("order_id").agg(rows=("shipping_cost", "size"), unique_costs=("shipping_cost", "nunique"))
    multiline = grouped[grouped["rows"] > 1]
    return {
        "status": "evidence_only",
        "multiline_orders": int(len(multiline)),
        "multiline_orders_with_one_repeated_cost": int((multiline["unique_costs"] == 1).sum()),
        "multiline_orders_with_varying_cost": int((multiline["unique_costs"] > 1).sum()),
        "warning": "Repeated values suggest possible order-level duplication but do not prove source allocation semantics.",
    }


def build_profile(path: Path) -> dict[str, Any]:
    frame, source_meta = load_source(path)
    columns = resolve_columns(frame)
    order_id = columns.get("order_id")
    customer_id = columns.get("customer_id")
    customer_name = columns.get("customer_name")
    row_count = len(frame)
    duplicate_rows = int(frame.astype("string").duplicated().sum())

    critical_names = ["order_id", "order_date", "sales", "profit", "quantity"]
    critical_nulls = {
        name: int(frame[column].isna().sum())
        for name in critical_names
        if (column := columns.get(name)) is not None
    }

    customer_collisions = None
    if customer_id and customer_name:
        pairs = frame[[customer_id, customer_name]].dropna().drop_duplicates()
        by_id = pairs.groupby(customer_id)[customer_name].nunique()
        by_name = pairs.groupby(customer_name)[customer_id].nunique()
        customer_collisions = {
            "ids_linked_to_multiple_names": int((by_id > 1).sum()),
            "names_linked_to_multiple_ids": int((by_name > 1).sum()),
        }

    currency = columns.get("currency")
    currency_values = None if not currency else sorted(map(str, frame[currency].dropna().unique().tolist()))

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "filename": path.name,
            "absolute_path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            **source_meta,
        },
        "schema": {
            "row_count": int(row_count),
            "column_count": int(len(frame.columns)),
            "original_columns": list(map(str, frame.columns)),
            "resolved_columns": columns,
            "missing_core_columns": sorted(set(critical_names) - set(columns)),
            "duplicate_rows": duplicate_rows,
            "critical_nulls": critical_nulls,
        },
        "grain": {
            "distinct_orders": int(frame[order_id].nunique(dropna=True)) if order_id else None,
            "rows_per_order_mean": float(row_count / frame[order_id].nunique(dropna=True)) if order_id and frame[order_id].nunique(dropna=True) else None,
            "orders_with_multiple_rows": int((frame.groupby(order_id).size() > 1).sum()) if order_id else None,
            "row_id_unique": bool(frame[columns["row_id"]].is_unique) if "row_id" in columns else None,
        },
        "dates": {
            "order_date": date_profile(frame, columns.get("order_date")),
            "ship_date": date_profile(frame, columns.get("ship_date")),
        },
        "numeric_fields": {
            name: numeric_profile(numeric_series(frame, columns.get(name)))
            for name in ["sales", "profit", "quantity", "discount", "shipping_cost"]
        },
        "currency": {
            "currency_column_present": bool(currency),
            "values": currency_values,
            "decision": "verify_from_source_documentation" if not currency else "inspect_values",
        },
        "customer_identity": customer_collisions,
        "discount_semantics_evidence": discount_evidence(frame, columns),
        "shipping_grain_evidence": shipping_evidence(frame, columns),
        "metric_readiness": {
            "revenue": all(name in columns for name in ["sales", "order_date"]),
            "profit": all(name in columns for name in ["profit", "order_date"]),
            "orders": all(name in columns for name in ["order_id", "order_date"]),
            "units": all(name in columns for name in ["quantity", "order_date"]),
            "targets": False,
            "returns_adjusted_metrics": bool(source_meta["returns_sheet_candidates"]),
        },
    }


def markdown(profile: dict[str, Any]) -> str:
    source = profile["source"]
    schema = profile["schema"]
    grain = profile["grain"]
    dates = profile["dates"]
    numeric = profile["numeric_fields"]
    lines = [
        "# Dataset Profile Results",
        "",
        f"Generated: `{profile['generated_at_utc']}`",
        "",
        "## Source evidence",
        "",
        f"- Filename: `{source['filename']}`",
        f"- SHA-256: `{source['sha256']}`",
        f"- Size: `{source['bytes']}` bytes",
        f"- Format: `{source['format']}`",
        f"- Selected orders sheet: `{source['selected_orders_sheet']}`",
        f"- Returns sheet candidates: `{', '.join(source['returns_sheet_candidates']) or 'none'}`",
        "",
        "## Schema and grain",
        "",
        f"- Rows: `{schema['row_count']}`",
        f"- Columns: `{schema['column_count']}`",
        f"- Duplicate rows: `{schema['duplicate_rows']}`",
        f"- Distinct orders: `{grain['distinct_orders']}`",
        f"- Mean rows per order: `{grain['rows_per_order_mean']}`",
        f"- Multi-line orders: `{grain['orders_with_multiple_rows']}`",
        f"- Unique row ID: `{grain['row_id_unique']}`",
        f"- Missing core columns: `{', '.join(schema['missing_core_columns']) or 'none'}`",
        "",
        "## Date coverage",
        "",
        f"- Order dates: `{dates['order_date']}`",
        f"- Ship dates: `{dates['ship_date']}`",
        "",
        "## Numeric checks",
        "",
    ]
    for name, evidence in numeric.items():
        lines.append(f"- **{name}**: `{evidence}`")
    lines += [
        "",
        "## Semantic evidence",
        "",
        f"- Discount semantics: `{profile['discount_semantics_evidence']}`",
        f"- Shipping grain: `{profile['shipping_grain_evidence']}`",
        f"- Currency: `{profile['currency']}`",
        f"- Customer identity: `{profile['customer_identity']}`",
        "",
        "## Metric readiness",
        "",
    ]
    for metric, ready in profile["metric_readiness"].items():
        lines.append(f"- {metric}: **{'ready' if ready else 'not ready'}**")
    lines += [
        "",
        "## Required human decisions",
        "",
        "- Confirm the source URL, publisher, license, and download date.",
        "- Confirm whether `Sales` is pre- or post-discount using source documentation plus the empirical evidence above.",
        "- Confirm whether monetary fields use one comparable currency.",
        "- Confirm whether shipping cost is line-level or order-level before aggregation.",
        "- Decide whether returns are available and how they affect official KPIs.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to the exact CSV, TSV, XLS, or XLSX source")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    source = args.source.resolve()
    if not source.exists():
        raise SystemExit(f"Source file does not exist: {source}")

    project_root = args.project_root.resolve()
    work_dir = project_root / "work"
    docs_dir = project_root / "docs"
    work_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    profile = build_profile(source)
    (work_dir / "dataset_profile.json").write_text(
        json.dumps(profile, indent=2, default=json_value), encoding="utf-8"
    )
    (docs_dir / "dataset-profile-results.md").write_text(markdown(profile), encoding="utf-8")
    print(json.dumps({
        "source": str(source),
        "rows": profile["schema"]["row_count"],
        "columns": profile["schema"]["column_count"],
        "profile_json": str(work_dir / "dataset_profile.json"),
        "profile_markdown": str(docs_dir / "dataset-profile-results.md"),
    }, indent=2))


if __name__ == "__main__":
    main()
