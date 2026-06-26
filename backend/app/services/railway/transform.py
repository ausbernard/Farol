"""
Railway GraphQL response -> vigia fleet payload

Each transform function owns one node type. Composition runs top-down: fleet -> project -> service. Status rollup is computed here, not in the route handler and not in the frontend.
"""

from typing import Any

from .status import VigiaStatus, map_deployment_status, relative_age, roll_up_worst


def _transform_service(service_node: dict[str, Any], env_names: dict[str, str]) -> dict[str, Any]:
    """One Railway project noce -> one vigia service row"""
    service_id = service_node.get("id") or service_node.get("name", "unknown")
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
    env_id = deploy.get("environmentId")


    # Detect service kind: if there's a commitHash, it's an app deploy.
    # Otherwise it's a managed / template servce (Postgres, Reis, etc).

    base = {
        "id": service_id, 
        "name": name,
        "status": map_deployment_status(deploy.get("status")),
        "age": relative_age(deploy.get("statusUpdatedAt")),
        "deploymentId": deploy.get("id"),
        "canRollback": deploy.get("canRollback", False),
        "canRedeploy": deploy.get("canRedeploy", False),
        "environment": env_names.get(env_id),
        "environmentId": env_id,
    }

    commit_hash = meta.get("commitHash")
    if commit_hash:
        return {
            **base,
            "ref": commit_hash[:7],  # short-sha, like git's default
            "branch": meta.get("branch", "main"),
            "url": deploy.get("staticUrl") or deploy.get("url"),
        }

    return {**base, "source": "managed"}


def _transform_project(project_node: dict[str, Any]) -> dict[str, Any]:
    """One Railway project node → one vigia project group, with rollup."""
    name = project_node.get("name", "unknown")
    service_edges = project_node.get("services", {}).get("edges", [])
    env_edges = project_node.get("environments", {}).get("edges", [])
    env_names = {e["node"]["id"]: e["node"]["name"] for e in env_edges}
    # Empty services case: project exists but nothing has been deployed yet.
    # Render honestly - not green, not red, not a fake "healthy" badge.

    if not service_edges:
        return {
            "id": name,  # use name as stable ID for now
            "name": name,
            "found": True,
            "empty": True,
            "services": [],
            "status": "degraded",
        }

    services = [_transform_service(edge["node"], env_names) for edge in service_edges]

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
        "summary": _summarize(projects),
        "projects": projects,
        "activity": [],
    }


def _summarize(projects: list[dict[str, Any]]) -> dict[str, Any]:
    missing = sum(1 for p in projects if not p.get("found", True))
    statuses: list[VigiaStatus] = [p["status"] for p in projects if "status" in p]
    counts: dict[str, int] = {"healthy": 0, "building": 0, "down": 0, "unknown": 0, "degraded":0}
    for s in statuses:
        counts[s] = counts.get(s, 0) + 1
    return {
        "overall": roll_up_worst(statuses),
        "total": len(projects),
        "healthy": counts["healthy"],
        "building": counts["building"],
        "down": counts["down"],
        "unknown": counts["unknown"],
        "degraded": counts["degraded"],
        "missing": missing,
    }
