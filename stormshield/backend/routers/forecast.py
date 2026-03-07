"""
GET /api/forecast/current
"""
from __future__ import annotations

from fastapi import APIRouter
from backend.modules.prediction.model import PredictionResult
from backend.modules.cache import store as cache

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.get("/current", response_model=PredictionResult)
def get_current_forecast() -> PredictionResult:
    forecast: PredictionResult | None = cache.get("forecast")
    if forecast:
        return forecast
    # Fallback synthetic result
    from datetime import datetime, timezone, timedelta
    return PredictionResult(
        predicted_level_ft=3.85,
        estimated_crest_iso=datetime.now(timezone.utc) + timedelta(minutes=30),
        confidence_score=0.60,
        model_version="2.0-synthetic",
    )
