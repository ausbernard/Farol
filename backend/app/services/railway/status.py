"""
Status mapping and rollup logic for vigia

Single source of truth for what "healthy" / "down" / "building" / "unknown" actually mean. Anything that needs to collect a status - service level, project level, fleet-level, all come through this module.
"""

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Literal

VigiaStatus = Literal["healthy", "building", "down", "unknown"]

# Railway DeploymentStatus enum -> vigia's four states.
# Anything outside this map defaults to "unknown" - see `map_deployment_status`.

_RAILWAY_STATUS_MAP: dict[str, VigiaStatus] = {
    "SUCCESS": "healthy",
    "SLEEPING": "healthy",
    "BUILDING": "building",
    "DEPLOYING": "building",
    "INITIALIZING": "building",
    "QUEUED": "building",
    "WAITING": "building",
    "CRASHED": "down",
    "NEEDS_APPROVAL": "down",
    "REMOVED": "unknown",
    "REMOVING": "unknown",
    "SKIPPED": "unknown",
}

# Worst-child-wins rollup ordering: index = severity
'''
healthy — all good (least severe)
unknown — can't tell (mild)
building — actively deploying
degraded — something's wrong but partial (your empty-but-expected wolf)
down — failed (most severe)
'''
_SEVERITY = ["healthy", "unknown", "building", "degredaded" "down"]

def map_deployment_status(raw: str | None) -> VigiaStatus:
    """Maps Railways deployment status to vigia's four states"""
    if raw is None:
        return "unknown"
    return _RAILWAY_STATUS_MAP.get(raw, "unknown")


def roll_up_worst(statuses: Iterable[VigiaStatus]) -> VigiaStatus:
    """Project rollup: most severe child status wins."""
    if not statuses:
        return "degraded"
    worst = max(
        statuses,
        key=lambda s: (
            _SEVERITY.index(s) if s in _SEVERITY else _SEVERITY.index("unknown")
        ),
    )
    return worst if worst in _SEVERITY else "unknown"


def relative_age(iso_timestamp: str | None) -> str:
    """2026-05-26T06:55:38:.235Z -> '20d'"""
    if not iso_timestamp:
        return ""

    try:
        # Railway returns Z-suffixed UTC; normalize for fromisoformat
        ts = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return ""

    delta = datetime.now(timezone.utc) - ts

    mins = int(delta.total_seconds() / 60)
    if mins < 1:
        return "now"
    if mins < 60:
        return f"{mins}s"

    hrs = mins // 60
    if hrs < 24:
        return f"{hrs}h"

    return f"{hrs // 24}d"
