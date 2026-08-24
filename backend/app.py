"""HTTP entry point for the Monthly Business Review Databricks App."""

from fastapi import FastAPI

from backend.services.connectivity import check_openai_egress, check_reporting_sql

app = FastAPI(
    title="Monthly Business Review Agent",
    version="0.1.0",
    description="Read-only connectivity proof for the reporting agent.",
)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Confirm that the application process is running."""
    return {"status": "ok", "service": "monthly-business-review-agent"}


@app.get("/api/connectivity/sql")
def sql_connectivity() -> dict[str, object]:
    """Run one fixed, read-only query against the reporting layer."""
    return check_reporting_sql()


@app.get("/api/connectivity/egress")
def egress_connectivity() -> dict[str, object]:
    """Confirm that the app can reach OpenAI without sending a secret."""
    return check_openai_egress()
