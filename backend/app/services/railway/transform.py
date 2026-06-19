"""
Railway GraphQL response -> vigia fleet payload

Each transform function owns one node type. Composition runs top-down: fleet -> project -> service. Status rollup is computed here, not in the route handler and not in the frontend.
"""

from typing import Any

from .status import map_deployment_status, relative_age, roll_up_worst


def _transform_service(service_node: dict[str, Any]) -> dict[str, Any]:
    """One Railway project noce -> one vigia service row"""

    name = service_node.get("name", "unknown")

    # Latest deployment (we ask for first: 1, may be empty if never deployed)
    deployments = service_node.get("deployments", {}).get("edges", [])
    if not deployments:
        return {
            "id": name,  # use name as stable ID for now
            "name": name,
            "status": "unknown",
            "source": "no deployments",
            "age": "",
        }

    deploy = deployments[0]["node"]
    meta = deploy.get("meta") or {}
    status = map_deployment_status(deploy.get("status"))
    age = relative_age(deploy.get("statusUpdatedAt"))

    # Detect service kind: if there's a commitHash, it's an app deploy.
    # Otherwise it's a managed / template servce (Postgres, Reis, etc).

    commit_hash = meta.get("commitHash")
    if commit_hash:
        return {
            "id": name,  # use name as stable ID for now
            "name": name,
            "status": status,
            "ref": commit_hash[:7],  # short-sha, like git's default
            "branch": meta.get("branch", "main"),
            "age": age,
            "url": deploy.get("staticUrl") or deploy.get("url"),
        }

    else:
        return {
            "id": name,  # use name as stable ID for now
            "name": name,
            "status": status,
            "source": "managed",
            "age": age,
        }


def _transform_project(project_node: dict[str, Any]) -> dict[str, Any]:
    """One Railway project node → one vigia project group, with rollup."""
    name = project_node.get("name", "unknown")
    service_edges = project_node.get("services", {}).get("edges", [])

    # Empty services case: project exists but nothing has been deployed yet.
    # Render honestly - not green, not red, not a fake "healthy" badge.

    if not service_edges:
        return {
            "id": name,  # use name as stable ID for now
            "name": name,
            "found": True,
            "empty": True,
            "services": [],
            "status": "unknown",
        }

    services = [_transform_service(edge["node"]) for edge in service_edges]

    # Try to get and surface the project's publi domain from any service that has one.
    domain = next((s.get("url") for s in services if s.get("url")), None)

    return {
        "id": name,  # use name as stable ID for now
        "name": name,
        "found": True,
        "domain": domain,
        "services": services,
        "status": roll_up_worst(s["status"] for s in services),
    }


def transform_to_vigia_state(
    graphql_response: dict[str, Any],
    expected_projects: list[str] | None = None,
) -> dict[str, Any]:
    """
    Railway GraphQL catalog response -> vigia fleet shape.

    `expected_projects` is the list of project names you expect to see (ie. from a config file). Any project in the list that railway didn't return gets emitted as `found: false` - the grey "verify source" row.

    Without this, missing projects would silently vanish. Safeguard this.

    """
    edges = graphql_response.get("projects", {}).get("edges", [])
    projects = [_transform_project(edge["node"]) for edge in edges]

    if expected_projects:
        returned_names = {p["name"] for p in projects}
        for expected in expected_projects:
            if expected not in returned_names:
                projects.append(
                    {
                        "id": expected,
                        "name": expected,
                        "found": False,
                        "note": "not found on railyway - verify source.",
                        "services": [],
                    }
                )

    return {
        "refreshedAgo": "just now",
        "projects": projects,
        "activity": [],
    }
