from app.services.railway.transform import (
    _transform_service,
    _transform_project,
    transform_to_vigia_state,
)


# --- helpers -----------------------------------------------------------------

def _service_node(name="svc", status="SUCCESS", commit=None, branch="main",
                  url=None, static_url=None, ts="2026-01-01T00:00:00Z"):
    deploy = {
        "status": status,
        "statusUpdatedAt": ts,
        "url": url,
        "staticUrl": static_url,
        "meta": {"commitHash": commit, "branch": branch} if commit else {},
    }
    return {
        "name": name,
        "deployments": {"edges": [{"node": deploy}]},
    }

def _project_node(name="proj", service_nodes=None):
    edges = [{"node": s} for s in (service_nodes or [])]
    return {"name": name, "services": {"edges": edges}}

def _graphql_response(project_nodes):
    return {"projects": {"edges": [{"node": p} for p in project_nodes]}}


# --- _transform_service ------------------------------------------------------

def test_service_no_deployments():
    node = {"name": "empty-svc", "deployments": {"edges": []}}
    result = _transform_service(node)
    assert result["status"] == "unknown"
    assert result["source"] == "no deployments"
    assert result["name"] == "empty-svc"

def test_service_app_deploy():
    node = _service_node(name="api", status="SUCCESS", commit="abc1234567", branch="main", static_url="https://api.example.com")
    result = _transform_service(node)
    assert result["status"] == "healthy"
    assert result["ref"] == "abc1234"   # short-sha (7 chars)
    assert result["branch"] == "main"
    assert result["url"] == "https://api.example.com"
    assert "source" not in result

def test_service_app_deploy_prefers_static_url():
    node = _service_node(commit="abc1234567", url="https://raw.example.com", static_url="https://static.example.com")
    result = _transform_service(node)
    assert result["url"] == "https://static.example.com"

def test_service_app_deploy_falls_back_to_url():
    node = _service_node(commit="abc1234567", url="https://raw.example.com", static_url=None)
    result = _transform_service(node)
    assert result["url"] == "https://raw.example.com"

def test_service_managed():
    node = _service_node(name="postgres", status="SUCCESS", commit=None)
    result = _transform_service(node)
    assert result["source"] == "managed"
    assert "ref" not in result
    assert "branch" not in result

def test_service_crashed_status():
    node = _service_node(status="CRASHED", commit="deadbeef01")
    result = _transform_service(node)
    assert result["status"] == "down"

def test_service_missing_name_defaults():
    node = {"deployments": {"edges": []}}
    result = _transform_service(node)
    assert result["name"] == "unknown"


# --- _transform_project ------------------------------------------------------

def test_project_empty_services():
    node = _project_node(name="empty-proj", service_nodes=[])
    result = _transform_project(node)
    assert result["found"] is True
    assert result["empty"] is True
    assert result["services"] == []
    assert result["status"] == "unknown"

def test_project_with_services():
    svcs = [
        _service_node(name="api", status="SUCCESS", commit="aaa0000000"),
        _service_node(name="worker", status="CRASHED", commit="bbb0000000"),
    ]
    node = _project_node(name="myapp", service_nodes=svcs)
    result = _transform_project(node)
    assert result["found"] is True
    assert result["status"] == "down"   # CRASHED rolls up to down
    assert len(result["services"]) == 2

def test_project_domain_from_first_service_with_url():
    svcs = [
        _service_node(name="db", status="SUCCESS"),        # managed, no url
        _service_node(name="api", status="SUCCESS", commit="abc1234567", static_url="https://app.example.com"),
    ]
    node = _project_node(name="proj", service_nodes=svcs)
    result = _transform_project(node)
    assert result["domain"] == "https://app.example.com"

def test_project_no_domain_when_no_service_has_url():
    svcs = [_service_node(name="worker", status="SUCCESS", commit="abc1234567", url=None, static_url=None)]
    node = _project_node(name="proj", service_nodes=svcs)
    result = _transform_project(node)
    assert result.get("domain") is None

def test_project_missing_name_defaults():
    node = {"services": {"edges": []}}
    result = _transform_project(node)
    assert result["name"] == "unknown"


# --- transform_to_vigia_state ------------------------------------------------

def test_fleet_empty_workspace():
    raw = _graphql_response([])
    result = transform_to_vigia_state(raw)
    assert result["projects"] == []
    assert result["refreshedAgo"] == "just now"
    assert result["activity"] == []

def test_fleet_projects_present():
    raw = _graphql_response([
        _project_node("proj-a", [_service_node(commit="abc1234567")]),
        _project_node("proj-b"),
    ])
    result = transform_to_vigia_state(raw)
    names = [p["name"] for p in result["projects"]]
    assert "proj-a" in names
    assert "proj-b" in names

def test_fleet_missing_expected_project():
    raw = _graphql_response([_project_node("exists")])
    result = transform_to_vigia_state(raw, expected_projects=["exists", "ghost"])
    ghost = next(p for p in result["projects"] if p["name"] == "ghost")
    assert ghost["found"] is False
    assert "note" in ghost

def test_fleet_no_missing_when_all_present():
    raw = _graphql_response([_project_node("a"), _project_node("b")])
    result = transform_to_vigia_state(raw, expected_projects=["a", "b"])
    missing = [p for p in result["projects"] if not p.get("found", True)]
    assert missing == []

def test_fleet_no_expected_projects():
    raw = _graphql_response([_project_node("proj")])
    result = transform_to_vigia_state(raw, expected_projects=None)
    assert len(result["projects"]) == 1
