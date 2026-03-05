"""
GET /api/sensor/latest
GET /api/sensor/history?hours=4
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from backend.modules.ingestion.usgs_client import SensorReading
from backend.modules.cache import store as cache

router = APIRouter(prefix="/api/sensor", tags=["sensor"])


@router.get("/latest", response_model=SensorReading)
def get_latest_sensor() -> SensorReading:
    readings: list[SensorReading] = cache.get("sensor_readings") or []
    if readings:
        return readings[-1]
    # Return synthetic fallback
    from backend.modules.ingestion.usgs_client import _generate_fallback_readings
    return _generate_fallback_readings()[-1]


@router.get("/history", response_model=list[SensorReading])
def get_sensor_history(hours: int = Query(default=4, ge=1, le=72)) -> list[SensorReading]:
    readings: list[SensorReading] = cache.get("sensor_readings") or []
    if readings:
        return readings
    from backend.modules.ingestion.usgs_client import _generate_fallback_readings
    return _generate_fallback_readings()
