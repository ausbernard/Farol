from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.services.railway import status

# --- map_deployment_status ---------------------------------------------------


def test_map_deployment_status_healthy():
    for raw in ("SUCCESS", "SLEEPING"):
        assert status.map_deployment_status(raw) == "healthy"


def test_map_deployment_status_building():
    for raw in ("BUILDING", "DEPLOYING", "INITIALIZING", "QUEUED", "WAITING"):
        assert status.map_deployment_status(raw) == "building"


def test_map_deployment_status_down():
    for raw in ("CRASHED", "NEEDS_APPROVAL"):
        assert status.map_deployment_status(raw) == "down"


def test_map_deployment_status_unknown_mapped():
    for raw in ("REMOVED", "REMOVING", "SKIPPED"):
        assert status.map_deployment_status(raw) == "unknown"


def test_map_deployment_status_none():
    assert status.map_deployment_status(None) == "unknown"


def test_map_deployment_status_unmapped():
    assert status.map_deployment_status("NOT_A_REAL_STATUS") == "unknown"


# --- roll_up_worst -----------------------------------------------------------


def test_roll_up_worst_empty_list():
    assert status.roll_up_worst([]) == "unknown"


def test_roll_up_worst_single():
    assert status.roll_up_worst(["healthy"]) == "healthy"
    assert status.roll_up_worst(["down"]) == "down"


def test_roll_up_worst_down_wins():
    assert status.roll_up_worst(["healthy", "down"]) == "down"
    assert status.roll_up_worst(["building", "down"]) == "down"
    assert status.roll_up_worst(["unknown", "down"]) == "down"


def test_roll_up_worst_building_over_healthy_and_unknown():
    assert status.roll_up_worst(["healthy", "building"]) == "building"
    assert status.roll_up_worst(["unknown", "building"]) == "building"


def test_roll_up_worst_unknown_over_healthy():
    assert status.roll_up_worst(["healthy", "unknown"]) == "unknown"


def test_roll_up_worst_bad_status_treated_as_unknown():
    # typo status isn't in _SEVERITY, falls back to unknown index
    assert status.roll_up_worst(["healthy", "typo"]) == "unknown"


def test_roll_up_worst_tuple_input():
    assert status.roll_up_worst(("healthy", "down")) == "down"


# --- relative_age ------------------------------------------------------------

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _age(delta: timedelta) -> str:
    ts = (_NOW - delta).isoformat().replace("+00:00", "Z")
    with patch("app.services.railway.status.datetime") as mock_dt:
        mock_dt.now.return_value = _NOW
        mock_dt.fromisoformat = datetime.fromisoformat
        return status.relative_age(ts)


def test_relative_age_none():
    assert status.relative_age(None) == ""


def test_relative_age_invalid():
    assert status.relative_age("not-a-date") == ""


def test_relative_age_now():
    assert _age(timedelta(seconds=30)) == "now"


def test_relative_age_minutes():
    assert _age(timedelta(minutes=5)) == "5s"  # code uses "s" suffix for minutes


def test_relative_age_hours():
    assert _age(timedelta(hours=3)) == "3h"


def test_relative_age_days():
    assert _age(timedelta(days=20)) == "20d"
