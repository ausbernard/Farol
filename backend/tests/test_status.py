import os
import sys

# Ensure backend app is importable from repo root
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from app.services.railway import status


def test_map_deployment_status_known():
    assert status.map_deployment_status("SUCCESS") == "healthy"
    assert status.map_deployment_status("CRASHED") == "down"
    assert status.map_deployment_status(None) == "unknown"
    assert status.map_deployment_status("NON_EXISTENT") == "unknown"


def test_roll_up_worst_basic():
    assert status.roll_up_worst([]) == "unknown"
    assert status.roll_up_worst(["healthy", "building"]) == "building"
    assert status.roll_up_worst(["healthy", "unknown"]) == "unknown"
    assert status.roll_up_worst(["healthy", "typo"]) == "unknown"
    assert status.roll_up_worst(("healthy", "down")) == "down"
    assert status.roll_up_worst(["unknown", "building"]) == "building"
