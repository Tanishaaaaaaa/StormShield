"""
Gemini-powered RAG query engine.
Assembles live context from cached state and answers user questions.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

import google.generativeai as genai
from pydantic import BaseModel

from backend.config import settings

from backend.modules.alert.engine import AlertStatus
from backend.modules.ingestion.nws_client import NWSAlert
from backend.modules.ingestion.usgs_client import SensorReading
from backend.modules.prediction.model import PredictionResult
from backend.modules.ingestion.weather_client import WeatherStatus

logger = logging.getLogger(__name__)

_last_call_time: float = 0.0
RATE_LIMIT_SECONDS = 3.0


class QueryContext(BaseModel):
    sensor: SensorReading
    forecast: PredictionResult
    alert: AlertStatus
    nws_alerts: list[NWSAlert]
    flood_zone_summary: str  # Summarized text instead of 175MB GeoJSON
    ema_alerts: list[dict] = []
    calls_911: list[dict] = []
    weather: Optional[WeatherStatus] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    grounded_at: datetime


def answer_query(
    user_question: str,
    context: QueryContext,
    history: Optional[list[dict[str, str]]] = None,
) -> QueryResponse:
    """
    RAG query handler: assembles a grounded context block and calls Gemini.
    Rate-limited to 1 call per RATE_LIMIT_SECONDS.
    """
    global _last_call_time

    # Enforce rate limit
    elapsed = time.time() - _last_call_time
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)

    grounded_at = datetime.now(timezone.utc)

    # 1. Summarise NWS alerts
    nws_summary = "; ".join(
        [f"{a.event} ({a.severity})" for a in context.nws_alerts]
    ) or "None"

    # 2. Road Closures and Incidents Summary
    ema_summary = "; ".join(
        [f"{a.get('title', 'Alert')}: {a.get('body', '')[:60]}..." for a in context.ema_alerts[:3]]
    ) or "No active road closure reports."
    
    call_summary = ", ".join(
        [f"{c.get('incident_type', 'Incident')} ({c.get('count', 0)})" for c in context.calls_911]
    ) or "0 reported incidents."

    # 3. Weather sub-summary
    weather_info = "Status: Unknown"
    if context.weather:
        weather_info = (
            f"{context.weather.condition}, {context.weather.temperature}°C. "
            f"Rain today so far: {context.weather.daily_precip_sum} mm."
        )

    # 4. Build context block
    context_block = (
        f"--- CURRENT SENSORS ---\n"
        f"Water Level: {context.sensor.water_level_ft:.2f} ft\n"
        f"Rate of Rise: {context.alert.rate_of_rise_ft_per_15m:+.3f} ft/15 min\n"
        f"Alert Level: {context.alert.level}\n\n"
        f"--- FORECAST (T+30) ---\n"
        f"Predicted Level: {context.forecast.predicted_level_ft:.2f} ft\n"
        f"Estimated Crest: {context.forecast.estimated_crest_iso.strftime('%H:%M:%S')} UTC\n\n"
        f"--- EMERGENCY SERVICES ---\n"
        f"Weather: {weather_info}\n"
        f"NWS Alerts: {nws_summary}\n"
        f"Road Closures (EMA): {ema_summary}\n"
        f"911 Reports: {call_summary}\n"
        f"Area Flood Risk: {context.flood_zone_summary}\n"
    )

    api_key = settings.gemini_api_key
    if not api_key or api_key == "your_gemini_api_key":
        logger.warning("Gemini API key missing or default; using fallback.")
        answer = _fallback_answer(user_question, context)
        _last_call_time = time.time()
        return QueryResponse(question=user_question, answer=answer, grounded_at=grounded_at)

    try:
        genai.configure(api_key=api_key)
        
        # Multi-model fallback logic for maximum reliability
        model_names = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash", "gemini-pro"]
        model = None
        last_error = ""

        # Build conversation history
        history_str = ""
        if history and isinstance(history, list):
            for turn in history[-5:]:
                q_hist = turn.get("q", turn.get("question", ""))
                a_hist = turn.get("a", turn.get("answer", ""))
                if q_hist:
                    history_str += f"User: {q_hist}\nAssistant: {a_hist}\n"

        prompt = (
            "You are StormShield AI, a highly local flood safety expert for Montgomery, Alabama.\n"
            "Use the real-time sensor, weather, and geographic context below to answer accurately.\n"
            "Rules:\n"
            "1. If the question is about safety, reference the current alert level immediately.\n"
            "2. If the user is in a 'High-Risk SFHA' area, advise extreme caution.\n"
            "3. For questions about rain history, refer to 'Current Weather' in the context. If 'Rain today so far' is 0.0mm, it has not rained yet today.\n"
            "4. Keep the response under 70 words and very professional.\n"
            "5. Do NOT use markdown symbols like * or #.\n\n"
            f"CONTEXT:\n{context_block}\n"
            f"{'CHAT HISTORY:' + history_str if history_str else ''}\n"
            f"USER QUERY: {user_question}"
        )

        for m_name in model_names:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(prompt)
                answer = response.text.strip()
                if answer:
                    break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Model {m_name} failed: {e}")
                continue
        
        if not answer:
            raise Exception(f"All models failed. Last error: {last_error}")

    except Exception as exc:
        logger.error("Gemini query failed: %s", exc)
        answer = _fallback_answer(user_question, context)

    _last_call_time = time.time()
    return QueryResponse(**{"question": user_question, "answer": answer, "grounded_at": grounded_at})


def _fallback_answer(user_question: str, ctx: QueryContext) -> str:
    """Rule-based fallback answers when Gemini is unavailable."""
    q = user_question.lower()
    level = ctx.sensor.water_level_ft
    alert = ctx.alert.level

    if any(w in q for w in ("flood", "flooding", "water level")):
        return (
            f"Current water level is {level:.1f} ft with alert status {alert}. "
            f"Predicted level in 30 minutes: {ctx.forecast.predicted_level_ft:.1f} ft."
        )
    if any(w in q for w in ("safe", "evacuate", "leave")):
        if alert == "RED":
            return "Current alert is RED. Evacuation is recommended for areas near Sligo Creek."
        elif alert == "YELLOW":
            return "Alert is YELLOW. Be prepared to evacuate and avoid creek crossings."
        return "Alert is GREEN. No immediate action needed."
    return (
        f"StormShield AI — Alert: {alert}. "
        f"Water level: {level:.1f} ft. "
        f"Rate of rise: {ctx.alert.rate_of_rise_ft_per_15m:.2f} ft/15 min."
    )
