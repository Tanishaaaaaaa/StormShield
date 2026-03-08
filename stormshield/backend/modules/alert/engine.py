"""
Alert threshold engine.
Evaluates a PredictionResult + rate-of-rise and returns an AlertStatus.
LLM-generated text is attached separately by llm_generator.py.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel


class AlertStatus(BaseModel):
    level: Literal["GREEN", "YELLOW", "RED"]
    predicted_level_ft: float
    rate_of_rise_ft_per_15m: float
    alert_text: str = ""          # populated by llm_generator
    generated_at: datetime


def evaluate_alert(
    prediction: "PredictionResult",  # type: ignore[name-defined]
    rate_of_rise: float,
    flood_stage_ft: float = 8.0,
    rate_threshold: float = 2.0,
) -> AlertStatus:
    """
    Determine alert level from prediction and rate-of-rise.

    Rules:
        RED    – predicted level >= flood_stage_ft
        YELLOW – rate_of_rise > rate_threshold (ft / 15 min) and level below flood stage
        GREEN  – otherwise
    """
    from backend.modules.prediction.model import PredictionResult  # local import to avoid circular

    level: Literal["GREEN", "YELLOW", "RED"]
    if prediction.predicted_level_ft >= flood_stage_ft:
        level = "RED"
    elif rate_of_rise > rate_threshold:
        level = "YELLOW"
    else:
        level = "GREEN"

    return AlertStatus(
        level=level,
        predicted_level_ft=round(prediction.predicted_level_ft, 2),
        rate_of_rise_ft_per_15m=round(rate_of_rise, 3),
        generated_at=datetime.now(timezone.utc),
    )
