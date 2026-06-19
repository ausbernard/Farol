from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)

_EMPTY_CATALOG = {"projects": {"edges": []}}

_VIGIA_STATE = {
    "refreshedAgo": "just now",
    "projects": [],
    "activity": [],
}


# --- GET /api/state ----------------------------------------------------------

def test_get_vigia_state_success():
    with patch("app.routes.vigia.fetch_catalog", new_callable=AsyncMock, return_value=_EMPTY_CATALOG):
        resp = client.get("/api/state")
    assert resp.status_code == 200
    body = resp.json()
    assert "projects" in body
    assert "refreshedAgo" in body

def test_get_vigia_state_propagates_502():
    exc = HTTPException(status_code=502, detail={"kind": "transport"})
    with patch("app.routes.vigia.fetch_catalog", new_callable=AsyncMock, side_effect=exc):
        resp = client.get("/api/state")
    assert resp.status_code == 502

def test_get_vigia_state_returns_missing_projects():
    with (
        patch("app.routes.vigia.fetch_catalog", new_callable=AsyncMock, return_value=_EMPTY_CATALOG),
        patch("app.routes.vigia.settings") as mock_settings,
    ):
        mock_settings.railway_workspace_id = "ws-test"
        mock_settings.expected_projects = ["ghost-project"]
        resp = client.get("/api/state")
    assert resp.status_code == 200
    projects = resp.json()["projects"]
    assert any(p["name"] == "ghost-project" and not p["found"] for p in projects)


# --- GET /api/raw ------------------------------------------------------------

def test_get_raw_catalog_success():
    raw = {"projects": {"edges": [{"node": {"name": "myproj"}}]}}
    with patch("app.routes.vigia.fetch_catalog", new_callable=AsyncMock, return_value=raw):
        resp = client.get("/api/raw")
    assert resp.status_code == 200
    assert resp.json() == raw

def test_get_raw_catalog_propagates_502():
    exc = HTTPException(status_code=502, detail={"kind": "graphql"})
    with patch("app.routes.vigia.fetch_catalog", new_callable=AsyncMock, side_effect=exc):
        resp = client.get("/api/raw")
    assert resp.status_code == 502
