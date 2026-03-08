"""
XGBoostPredictor: loads a trained model and runs predictions.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from pydantic import BaseModel

logger = logging.getLogger(__name__)

MODEL_VERSION = "2.0"


class PredictionResult(BaseModel):
    predicted_level_ft: float
    estimated_crest_iso: datetime
    confidence_score: float   # 0.0 – 1.0
    model_version: str = MODEL_VERSION


class XGBoostPredictor:
    def __init__(self) -> None:
        self._model = None
        self._baseline_var: float = 1.0

    def load_model(self, path: str) -> None:
        """Load a serialised XGBoost model from disk."""
        p = Path(path)
        if not p.exists():
            logger.warning("Model file not found at %s; predictions will be synthetic.", path)
            return
        try:
            self._model = joblib.load(p)
            logger.info("XGBoost model loaded from %s", path)
        except Exception as exc:
            logger.error("Failed to load model: %s", exc)
            self._model = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def predict(self, features: np.ndarray) -> PredictionResult:
        """Run inference and return a PredictionResult."""
        now = datetime.now(timezone.utc)
        crest_time = now + timedelta(minutes=30)

        if self._model is None:
            # Synthetic prediction when model isn't available
            current_level = float(features[0][0]) if features.size > 0 else 3.5
            predicted = round(current_level + np.random.uniform(-0.1, 0.3), 2)
            return PredictionResult(
                predicted_level_ft=predicted,
                estimated_crest_iso=crest_time,
                confidence_score=0.60,
                model_version=f"{MODEL_VERSION}-synthetic",
            )

        predicted_raw = float(self._model.predict(features)[0])
        predicted = round(predicted_raw, 2)

        # Confidence: 1 - (residual variance / baseline variance), clamped [0, 1]
        try:
            residual_var = getattr(self._model, "best_score", None)
            if residual_var is not None and self._baseline_var > 0:
                conf = float(np.clip(1.0 - (residual_var / self._baseline_var), 0.0, 1.0))
            else:
                conf = 0.85
        except Exception:
            conf = 0.85

        return PredictionResult(
            predicted_level_ft=predicted,
            estimated_crest_iso=crest_time,
            confidence_score=conf,
            model_version=MODEL_VERSION,
        )
