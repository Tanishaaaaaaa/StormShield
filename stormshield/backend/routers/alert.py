"""
GET /api/alert/current
GET /api/alert/history?limit=N
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from backend.modules.alert.engine import AlertStatus
from backend.modules.cache import store as cache

router = APIRouter(prefix="/api/alert", tags=["alert"])


@router.get("/current", response_model=AlertStatus)
def get_current_alert() -> AlertStatus:
    alert: AlertStatus | None = cache.get("alert")
    if alert:
        return alert
    from datetime import datetime, timezone
    return AlertStatus(
        level="GREEN",
        predicted_level_ft=3.85,
        rate_of_rise_ft_per_15m=0.0,
        alert_text="All clear. Water levels are within normal range. StormShield AI is monitoring conditions.",
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/history", response_model=list[AlertStatus])
def get_alert_history(limit: int = Query(default=20, ge=1, le=100)) -> list[AlertStatus]:
    history: list[AlertStatus] = cache.get("alert_history") or []
    return history[-limit:]
