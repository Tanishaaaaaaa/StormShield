"""
GET /api/geodata/flood-zones
GET /api/geodata/ema-alerts
"""
from __future__ import annotations

from fastapi import APIRouter
from backend.modules.cache import store as cache

router = APIRouter(prefix="/api/geodata", tags=["geodata"])


@router.get("/flood-zones")
def get_flood_zones():
    data = cache.get("flood_zones")
    if data:
        return data
    # Return stub GeoJSON if not cached
    from backend.modules.ingestion.brightdata_scraper import _stub_flood_zones
    return _stub_flood_zones()


@router.get("/ema-alerts")
def get_ema_alerts():
    data = cache.get("ema_alerts")
    if data:
        return data
    return [{"title": "No active EMA alerts", "body": "All clear at this time."}]
