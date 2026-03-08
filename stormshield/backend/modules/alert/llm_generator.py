"""
Gemini 2.0 Flash LLM alert text generator.
Generates plain-language public alerts based on AlertStatus + PredictionResult.
Caches output to avoid unnecessary Gemini calls.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import google.generativeai as genai

from backend.modules.alert.engine import AlertStatus
from backend.modules.prediction.model import PredictionResult

logger = logging.getLogger(__name__)

_last_alert_level: Optional[str] = None
_last_predicted_ft: Optional[float] = None
_last_generated_text: str = ""
_LEVEL_CHANGE_THRESHOLD_FT = 0.5


def _api_key_configured() -> bool:
    key = os.getenv("GEMINI_API_KEY", "")
    return bool(key and key != "your_gemini_api_key")


def generate_alert_text(alert: AlertStatus, forecast: PredictionResult) -> str:
    """
    Call Gemini 2.0 Flash to produce a ≤60-word plain-language public alert.

    Cached unless:
        - Alert level changed, OR
        - Predicted level delta > 0.5 ft from last generation
    """
    global _last_alert_level, _last_predicted_ft, _last_generated_text

    # Check cache
    level_changed = alert.level != _last_alert_level
    level_delta = abs(forecast.predicted_level_ft - (_last_predicted_ft or 0.0))
    if not level_changed and level_delta <= _LEVEL_CHANGE_THRESHOLD_FT and _last_generated_text:
        return _last_generated_text

    # Fallback if Gemini not configured
    if not _api_key_configured():
        text = _fallback_alert_text(alert, forecast)
        _update_cache(alert, forecast, text)
        return text

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = (
            f"You are an emergency alert system for Montgomery, Alabama.\n"
            f"Current alert level: {alert.level}\n"
            f"Predicted water level: {forecast.predicted_level_ft} ft "
            f"at {forecast.estimated_crest_iso.isoformat()}\n"
            f"Rate of rise: {alert.rate_of_rise_ft_per_15m} ft/15 min\n"
            "Generate a single-paragraph plain-language public alert under 60 words.\n"
            "Include: which roads/areas to avoid, expected timing, recommended actions.\n"
            "Do not include any markdown formatting."
        )
        response = model.generate_content(prompt)
        text = response.text.strip()
        _update_cache(alert, forecast, text)
        return text

    except Exception as exc:
        logger.error("Gemini alert generation failed: %s", exc)
        text = _fallback_alert_text(alert, forecast)
        _update_cache(alert, forecast, text)
        return text


def _update_cache(alert: AlertStatus, forecast: PredictionResult, text: str) -> None:
    global _last_alert_level, _last_predicted_ft, _last_generated_text
    _last_alert_level = alert.level
    _last_predicted_ft = forecast.predicted_level_ft
    _last_generated_text = text


def _fallback_alert_text(alert: AlertStatus, forecast: PredictionResult) -> str:
    level = alert.level
    ft = forecast.predicted_level_ft
    ror = alert.rate_of_rise_ft_per_15m

    if level == "RED":
        return (
            f"FLOOD WARNING: Water levels at Sligo Creek projected to reach {ft:.1f} ft, "
            "exceeding flood stage. Avoid low-lying roads, move vehicles to higher ground, "
            "and follow EMA evacuation guidance immediately."
        )
    elif level == "YELLOW":
        return (
            f"FLOOD WATCH: Water levels rising at {ror:.2f} ft/15 min. "
            f"Predicted level: {ft:.1f} ft. Avoid underpasses and creek crossings. "
            "Monitor EMA updates and be ready to move quickly."
        )
    else:
        return (
            f"All clear. Current predicted water level is {ft:.1f} ft, "
            "well below flood stage. Continue to monitor StormShield AI for updates."
        )
