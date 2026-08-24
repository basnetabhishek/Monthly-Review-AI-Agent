from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_sql_requires_warehouse_resource(monkeypatch) -> None:
    monkeypatch.delenv("WAREHOUSE_ID", raising=False)
    response = client.get("/api/connectivity/sql")
    assert response.status_code == 503
    assert "sql-warehouse" in response.json()["detail"]


def test_sql_returns_reporting_span(monkeypatch) -> None:
    monkeypatch.setenv("WAREHOUSE_ID", "test-warehouse")
    statement_response = SimpleNamespace(
        status=SimpleNamespace(state="SUCCEEDED"),
        result=SimpleNamespace(data_array=[["48", "2011-01-01", "2014-12-01"]]),
    )
    workspace = Mock()
    workspace.statement_execution.execute_statement.return_value = statement_response

    with patch("backend.services.connectivity.WorkspaceClient", return_value=workspace):
        response = client.get("/api/connectivity/sql")

    assert response.status_code == 200
    assert response.json()["month_count"] == 48


def test_egress_accepts_unauthorized_as_reachable() -> None:
    with patch("backend.services.connectivity.httpx.get") as get:
        get.return_value = SimpleNamespace(status_code=401)
        response = client.get("/api/connectivity/egress")

    assert response.status_code == 200
    assert response.json()["reachable"] is True
    assert response.json()["credentials_sent"] is False
