"""Safe connectivity checks for Databricks SQL and the future LLM API."""

from __future__ import annotations

import os
from typing import Any

import httpx
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from fastapi import HTTPException

REPORTING_CHECK_SQL = """
SELECT
  COUNT(*) AS month_count,
  MIN(report_month) AS first_month,
  MAX(report_month) AS last_month
FROM workspace.mbr_reporting.vw_monthly_trends
""".strip()

OPENAI_MODELS_URL = "https://api.openai.com/v1/models"


def _first_row(response: Any) -> list[Any]:
    result = getattr(response, "result", None)
    rows = getattr(result, "data_array", None)
    if not rows:
        raise RuntimeError("The reporting query returned no rows.")
    return rows[0]


def check_reporting_sql() -> dict[str, object]:
    """Execute a controlled query through the app's assigned SQL warehouse."""
    warehouse_id = os.getenv("WAREHOUSE_ID")
    if not warehouse_id:
        raise HTTPException(
            status_code=503,
            detail="WAREHOUSE_ID is missing. Add a SQL warehouse app resource with key 'sql-warehouse'.",
        )

    try:
        response = WorkspaceClient().statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=REPORTING_CHECK_SQL,
            wait_timeout="30s",
        )
        state = getattr(getattr(response, "status", None), "state", None)
        if state != StatementState.SUCCEEDED:
            state_label = getattr(state, "value", str(state))
            raise RuntimeError(f"SQL statement did not succeed (state={state_label}).")

        month_count, first_month, last_month = _first_row(response)
        return {
            "status": "ok",
            "warehouse_configured": True,
            "reporting_view": "workspace.mbr_reporting.vw_monthly_trends",
            "month_count": int(month_count),
            "first_month": str(first_month),
            "last_month": str(last_month),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Databricks SQL check failed: {exc}") from exc


def check_openai_egress() -> dict[str, object]:
    """Reach a fixed OpenAI endpoint; 401 means networking works but no key was sent."""
    try:
        response = httpx.get(OPENAI_MODELS_URL, timeout=10.0, follow_redirects=False)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI network check failed: {exc}") from exc

    reachable = response.status_code in {200, 401, 403, 429}
    if not reachable:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI returned unexpected HTTP status {response.status_code}.",
        )
    return {
        "status": "ok",
        "provider": "OpenAI",
        "reachable": True,
        "http_status": response.status_code,
        "credentials_sent": False,
    }
