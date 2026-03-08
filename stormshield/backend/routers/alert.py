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


@router.post("/send-otp")
def trigger_otp(payload: dict):
    """Trigger an OTP for verification."""
    phone = payload.get("phone")
    if not phone or len(phone) < 10:
        return {"status": "error", "message": "Invalid phone number"}
    
    # Check if already registered
    from backend.modules.cache.store import get_subscribers
    if phone in get_subscribers():
        return {"status": "error", "message": "already_registered"}
    
    from backend.modules.alert.sms import send_otp
    session_id = send_otp(phone)
    if session_id:
        return {"status": "success", "session_id": session_id}
    else:
        return {"status": "error", "message": "Failed to send OTP. Please check your number."}


@router.post("/verify-otp")
def verify_and_subscribe(payload: dict):
    """Verify OTP and then subscribe the user."""
    phone = payload.get("phone")
    session_id = payload.get("session_id")
    otp = payload.get("otp")
    
    if not all([phone, session_id, otp]):
        return {"status": "error", "message": "Missing required fields"}
    
    from backend.modules.alert.sms import verify_otp, send_sms_alert
    if verify_otp(session_id, otp):
        added = cache.add_subscriber(phone)
        if added:
            send_sms_alert(phone, "Verification successful! Welcome to StormShield AI Alerts.")
            return {"status": "success", "message": "Verified and Subscribed successfully"}
        else:
            return {"status": "success", "message": "Verification success! You are already in our alert system."}
    else:
        return {"status": "error", "message": "Invalid OTP. Please try again."}


@router.post("/subscribe")
def subscribe_to_alerts(payload: dict):
    """Fallback legacy subscribe (direct)."""
    phone = payload.get("phone")
    if not phone or len(phone) < 10:
        return {"status": "error", "message": "Invalid phone number"}
    
    added = cache.add_subscriber(phone)
    if added:
        return {"status": "success", "message": "Subscribed successfully"}
    else:
        return {"status": "info", "message": "Already subscribed"}
