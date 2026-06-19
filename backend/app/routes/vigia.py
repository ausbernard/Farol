"""
Routes are thin: fetch, transform, return. No business logic here.
"""

from fastapi import APIRouter

from app.config import settings
from app.services.railway.client import fetch_catalog
from app.services.railway.transform import transform_to_vigia_state

router = APIRouter()

RAILWAY_API = "https://backboard.railway.com/graphql/v2"


@router.get("/api/state")
async def get_vigia_state():
    raw = await fetch_catalog(settings.railway_workspace_id)

    return transform_to_vigia_state(raw, expected_projects=settings.expected_projects)


@router.get("/api/raw")
async def get_raw_catalog():
    """Debug endoing - raw Railway response, no transform. Keep for verification."""
    return await fetch_catalog(settings.railway_workspace_id)
