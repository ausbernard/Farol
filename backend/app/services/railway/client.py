"""
Railway GraphQL client.

Owns one job: Talk to Railway and return a parsed payload (or raise a structured error). Knows nothing about vigia's shape, status mapping, or project rollups - those live in transform.py and status.py

Errors are translated into HTTPException with a `kind` discriminator ('transport' vs 'graphql') so route handlers and logs can distinguish network/auth failures from query-level rejections
"""

from typing import Any

import httpx2 as httpx
from fastapi import HTTPException

from app.config import settings

RAILWAY_API = "https://backboard.railway.com/graphql/v2"
DEFAULT_TIMEOUT = 10.0  # seconds
ERROR_BODY_TRUNCATE = 500  # cap non-JSON error bodies in logs/responses

# --- queries ----------------------------------------------------------------
# Kept as module-level constants, not inline in functions. Easy to diff, easy
# to grep, easy to introspect against the schema when Railway changes a field.

_CATALOG_QUERY = """
query($workspaceId: String!) {
  projects(workspaceId: $workspaceId) {
    edges { node {
      id
      name
      environments { edges { node { id name } } }
      services { edges { node {
        id
        name
        deployments(first: 1) { edges { node {
          id
          status statusUpdatedAt createdAt
          url staticUrl meta
          canRollback canRedeploy
          environmentId
        } } }
      } } }
    } }
  }
}
"""


# --- public API -------------------------------------------------------------
async def fetch_catalog(workspace_id: str) -> dict[str, Any]:
    """Fetch the project/service/deployment catalog for a workspace.

    Returns the raw GraphQL `data` payload. Raises HTTPException(502) on transport or GraphQL errors, with structured `detail` diagnosis.
    """

    return await _execute(query=_CATALOG_QUERY, variables={"workspaceId": workspace_id})


# --- internals ---------------------------------------------------------------
async def _execute(
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    """Single chokepoint for every GraphQL call. Handles transport + GraphQL errors"""
    headers = {"Authorization": f"Bearer {settings.railway_token}"}

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.post(
            RAILWAY_API,
            headers=headers,
            json={
                "query": query,
                "variables": variables,
            },
        )

    # Transport layer first — did the request even reach a GraphQL server?
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=_transport_error(response))

    # Now we know it's 200, so the body should be GraphQL-shaped JSON.
    payload = response.json()

    # Application layer — server reached, but it didn't like it.
    if "errors" in payload:
        raise HTTPException(
            status_code=502,
            detail=_graphql_error(payload["errors"]),
        )

    if "data" not in payload or payload["data"] is None:
        raise HTTPException(
            status_code=502,
            detail={"kind": "graphql", "errors": [{"message": "no data in response"}]},
        )

    return payload["data"]


def _transport_error(response: httpx.Response) -> dict[str, Any]:
    """Structured detail for non-200 responses (network, auth, gateway)"""
    return {
        "kind": "transport",
        "status_code": response.status_code,
        "body": response.text[:ERROR_BODY_TRUNCATE],  # truncate non-json bodies
    }


def _graphql_error(errors: list[dict[str, Any]]) -> dict[str, Any]:
    """Structured detail for 200-OK responses with GraphQL errors (validation, schema)."""
    return {
        "kind": "graphql",
        "errors": [
            {
                "code": e.get("extensions", {}).get("code"),
                "message": e.get("message"),
                "trace_id": e.get("traceId"),
            }
            for e in errors
        ],
    }
