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

logger = logging.getLogger(__name__)

_last_call_time: float = 0.0
RATE_LIMIT_SECONDS = 3.0


class QueryContext(BaseModel):
    sensor: SensorReading
    forecast: PredictionResult
    alert: AlertStatus
    nws_alerts: list[NWSAlert]
    flood_zones: dict[str, Any]  # Changed from zone_summary


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

    # 2. Derive zone summary from flood_zones GeoJSON
    zone_names = set()
    high_risk = False
    for feat in context.flood_zones.get("features", []):
        props = feat.get("properties", {})
        sfha = props.get("sfha_tf", "F") == "T"
        zone_names.add(props.get("name", "Unknown Zone"))
        if sfha:
            high_risk = True

    zone_summary = f"{', '.join(list(zone_names)[:3])}"
    if high_risk:
        zone_summary += " (High-Risk SFHA Areas Found)"
    else:
        zone_summary += " (Minimal Risk Areas)"

    # 3. Build context block
    context_block = (
        f"Current water level: {context.sensor.water_level_ft:.2f} ft\n"
        f"Predicted level (T+30): {context.forecast.predicted_level_ft:.2f} ft\n"
        f"Alert level: {context.alert.level}\n"
        f"Rate of rise: {context.alert.rate_of_rise_ft_per_15m:+.3f} ft/15 min\n"
        f"Active NWS alerts: {nws_summary}\n"
        f"FEMA flood zones in area: {zone_summary}\n"
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
            "Use the real-time sensor and geographic context below to answer accurately.\n"
            "Rules:\n"
            "1. If the question is about safety, reference the current alert level immediately.\n"
            "2. If the user is in a 'High-Risk SFHA' area, advise extreme caution.\n"
            "3. Keep the response under 70 words and very professional.\n"
            "4. Do NOT use markdown symbols like * or #.\n\n"
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
