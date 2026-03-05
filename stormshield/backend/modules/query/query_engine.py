"""
Gemini-powered RAG query engine.
Assembles live context from cached state and answers user questions.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

import google.generativeai as genai
from pydantic import BaseModel

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
    zone_summary: str


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

    nws_summary = "; ".join(
        [f"{a.event} ({a.severity})" for a in context.nws_alerts]
    ) or "None"

    context_block = (
        f"Current water level: {context.sensor.water_level_ft} ft\n"
        f"Predicted level (T+30): {context.forecast.predicted_level_ft} ft\n"
        f"Alert level: {context.alert.level}\n"
        f"Rate of rise: {context.alert.rate_of_rise_ft_per_15m} ft/15 min\n"
        f"Active NWS alerts: {nws_summary}\n"
        f"FEMA flood zones in area: {context.zone_summary}\n"
    )

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key":
        answer = _fallback_answer(user_question, context)
        _last_call_time = time.time()
        return QueryResponse(question=user_question, answer=answer, grounded_at=grounded_at)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Build conversation with history
        history_str = ""
        if history:
            for turn in history[-5:]:
                history_str += f"Q: {turn.get('q', '')}\nA: {turn.get('a', '')}\n"

        prompt = (
            "You are StormShield AI, a flood safety assistant for Montgomery, Alabama.\n"
            "Answer the following question using ONLY the provided real-time context.\n"
            "If the answer cannot be determined from context, say so clearly.\n"
            "Keep answers under 80 words. Do not use markdown.\n\n"
            f"CONTEXT:\n{context_block}\n"
            f"{('PREVIOUS CONVERSATION:\n' + history_str) if history_str else ''}"
            f"\nQUESTION: {user_question}"
        )
        response = model.generate_content(prompt)
        answer = response.text.strip()
    except Exception as exc:
        logger.error("Gemini query failed: %s", exc)
        answer = _fallback_answer(user_question, context)

    _last_call_time = time.time()
    return QueryResponse(question=user_question, answer=answer, grounded_at=grounded_at)


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
