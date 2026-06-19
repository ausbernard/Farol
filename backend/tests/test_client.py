from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.railway.client import (
    _execute,
    _graphql_error,
    _transport_error,
    fetch_catalog,
)

# --- sync helpers ------------------------------------------------------------


def test_transport_error_structure():
    resp = MagicMock()
    resp.status_code = 401
    resp.text = "Unauthorized"
    result = _transport_error(resp)
    assert result["kind"] == "transport"
    assert result["status_code"] == 401
    assert result["body"] == "Unauthorized"


def test_transport_error_truncates_long_body():
    resp = MagicMock()
    resp.status_code = 500
    resp.text = "x" * 1000
    result = _transport_error(resp)
    assert len(result["body"]) == 500  # ERROR_BODY_TRUNCATE constant


def test_graphql_error_structure():
    errors = [
        {"message": "not found", "extensions": {"code": "NOT_FOUND"}, "traceId": "abc"}
    ]
    result = _graphql_error(errors)
    assert result["kind"] == "graphql"
    assert result["errors"][0]["code"] == "NOT_FOUND"
    assert result["errors"][0]["message"] == "not found"
    assert result["errors"][0]["trace_id"] == "abc"


def test_graphql_error_missing_extensions():
    errors = [{"message": "oops"}]
    result = _graphql_error(errors)
    assert result["errors"][0]["code"] is None
    assert result["errors"][0]["trace_id"] is None


# --- async _execute ----------------------------------------------------------


def _mock_http_client(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text

    mock_client = AsyncMock()
    mock_client.post.return_value = resp

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


async def test_execute_success():
    payload = {"data": {"projects": {"edges": []}}}
    ctx = _mock_http_client(200, payload)
    with patch("app.services.railway.client.httpx.AsyncClient", return_value=ctx):
        result = await _execute("query {}", {})
    assert result == {"projects": {"edges": []}}


async def test_execute_non_200_raises_502():
    ctx = _mock_http_client(401, text="Unauthorized")
    with patch("app.services.railway.client.httpx.AsyncClient", return_value=ctx):
        with pytest.raises(HTTPException) as exc_info:
            await _execute("query {}", {})
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["kind"] == "transport"


async def test_execute_graphql_errors_raises_502():
    payload = {"errors": [{"message": "bad query"}]}
    ctx = _mock_http_client(200, payload)
    with patch("app.services.railway.client.httpx.AsyncClient", return_value=ctx):
        with pytest.raises(HTTPException) as exc_info:
            await _execute("query {}", {})
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["kind"] == "graphql"


async def test_execute_null_data_raises_502():
    payload = {"data": None}
    ctx = _mock_http_client(200, payload)
    with patch("app.services.railway.client.httpx.AsyncClient", return_value=ctx):
        with pytest.raises(HTTPException) as exc_info:
            await _execute("query {}", {})
    assert exc_info.value.status_code == 502


async def test_execute_missing_data_key_raises_502():
    ctx = _mock_http_client(200, {})
    with patch("app.services.railway.client.httpx.AsyncClient", return_value=ctx):
        with pytest.raises(HTTPException) as exc_info:
            await _execute("query {}", {})
    assert exc_info.value.status_code == 502


# --- fetch_catalog -----------------------------------------------------------


async def test_fetch_catalog_delegates_with_workspace_id():
    payload = {"data": {"projects": {"edges": []}}}
    ctx = _mock_http_client(200, payload)
    with patch("app.services.railway.client.httpx.AsyncClient", return_value=ctx):
        await fetch_catalog("ws-123")
    call_kwargs = ctx.__aenter__.return_value.post.call_args
    assert "ws-123" in str(call_kwargs)
