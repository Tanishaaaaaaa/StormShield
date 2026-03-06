"""
POST /api/query
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.modules.query.query_engine import QueryContext, QueryResponse, answer_query

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    history: Optional[list[dict[str, str]]] = None


@router.post("/query", response_model=QueryResponse)
def post_query(body: QueryRequest) -> QueryResponse:
    from backend.modules.cache import store as cache
    from backend.modules.alert.engine import AlertStatus
    from backend.modules.prediction.model import PredictionResult
    from backend.modules.ingestion.usgs_client import SensorReading
    from datetime import datetime, timezone, timedelta

    # Fetch live context from cache with fallbacks
    sensor: SensorReading = _get_latest_sensor(cache)
    forecast: PredictionResult = cache.get("forecast") or PredictionResult(
        predicted_level_ft=3.85,
        estimated_crest_iso=datetime.now(timezone.utc) + timedelta(minutes=30),
        confidence_score=0.60,
        model_version="2.0-synthetic",
    )
    alert: AlertStatus = cache.get("alert") or AlertStatus(
        level="GREEN",
        predicted_level_ft=3.85,
        rate_of_rise_ft_per_15m=0.0,
        alert_text="System initializing.",
        generated_at=datetime.now(timezone.utc),
    )
    nws_alerts = cache.get("nws_alerts") or []
    flood_zones = cache.get("flood_zones") or {"type": "FeatureCollection", "features": []}

    context = QueryContext(
        sensor=sensor,
        forecast=forecast,
        alert=alert,
        nws_alerts=nws_alerts,
        flood_zones=flood_zones,
    )

    return answer_query(body.question, context, history=body.history)


def _get_latest_sensor(cache):
    from backend.modules.ingestion.usgs_client import SensorReading, _generate_fallback_readings
    readings = cache.get("sensor_readings") or []
    if readings:
        return readings[-1]
    return _generate_fallback_readings()[-1]
