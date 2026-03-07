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
    ema_alerts = cache.get("ema_alerts") or []
    calls_911 = cache.get("calls_911") or []
    weather = cache.get("weather_status")
    flood_summary = _get_flood_summary(cache)

    context = QueryContext(
        sensor=sensor,
        forecast=forecast,
        alert=alert,
        nws_alerts=nws_alerts,
        flood_zone_summary=flood_summary,
        ema_alerts=ema_alerts,
        calls_911=calls_911,
        weather=weather,
    )

    return answer_query(body.question, context, history=body.history)


def _get_latest_sensor(cache):
    from backend.modules.ingestion.usgs_client import SensorReading, _generate_fallback_readings
    readings = cache.get("sensor_readings") or []
    if readings:
        return readings[-1]
    return _generate_fallback_readings()[-1]


def _get_flood_summary(cache) -> str:
    """Return a lightweight summary of flood zones to avoid processing 175MB GeoJSON."""
    summary = cache.get("flood_zone_summary_text")
    if summary:
        return summary
    
    # Default Montgomery context for RAG grounding
    summary = "AE (High Risk SFHA), X (Minimal Risk), 0.2 PCT (Moderate Risk)"
    cache.set("flood_zone_summary_text", summary, ttl_seconds=86400)
    return summary
