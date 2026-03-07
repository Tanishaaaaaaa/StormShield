"""
Feature builder: constructs an (1, 8) numpy feature vector for XGBoostPredictor.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from backend.modules.ingestion.usgs_client import SensorReading
    from backend.modules.ingestion.noaa_client import RainfallForecast


def build_feature_vector(
    readings: list["SensorReading"],
    rainfall: list["RainfallForecast"],
) -> np.ndarray:
    """
    Build shape (1, 9) feature vector.

    Features:
        0  water_level_t0
        1  water_level_t-15   (15 min ago)
        2  water_level_t-30   (30 min ago)
        3  water_level_t-60   (60 min ago)
        4  discharge_t0
        5  rate_of_rise       (ft per 15 min)
        6  rolling_1hr_mean
        7  rolling_4hr_mean
        8  rainfall_proxy     (next-hour NOAA precipitation_mm)
    """
    if not readings:
        return np.zeros((1, 9))

    df = pd.DataFrame([r.model_dump() for r in readings])
    df = df.sort_values("timestamp").reset_index(drop=True)

    levels = df["water_level_ft"].to_numpy()

    def _at_offset(minutes: int) -> float:
        """Get water level approximately `minutes` ago."""
        # Assume readings every 5 min; 15 min = 3 steps back
        steps = minutes // 5
        idx = max(0, len(levels) - 1 - steps)
        return float(levels[idx])

    t0 = float(levels[-1]) if len(levels) > 0 else 0.0
    t_minus_15 = _at_offset(15)
    t_minus_30 = _at_offset(30)
    t_minus_60 = _at_offset(60)

    discharge_t0 = float(df["discharge_cfs"].iloc[-1]) if len(df) > 0 else 0.0
    rate_of_rise = t0 - t_minus_15  # ft per 15 minutes

    # Rolling means (last 12 readings = 1 hr; last 48 = 4 hr at 5-min resolution)
    rolling_1hr = float(pd.Series(levels[-12:]).mean()) if len(levels) >= 1 else t0
    rolling_4hr = float(pd.Series(levels[-48:]).mean()) if len(levels) >= 1 else t0

    # Rainfall proxy: next-hour precipitation
    rainfall_proxy = 0.0
    if rainfall:
        rainfall_proxy = float(rainfall[0].precipitation_mm)

    features = np.array(
        [[t0, t_minus_15, t_minus_30, t_minus_60, discharge_t0,
          rate_of_rise, rolling_1hr, rolling_4hr, rainfall_proxy]],
        dtype=np.float32,
    )
    return features


def compute_rate_of_rise(readings: list["SensorReading"]) -> float:
    """Return the rate of rise (ft per 15 min) from the latest readings."""
    if len(readings) < 2:
        return 0.0
    df = pd.DataFrame([r.model_dump() for r in readings]).sort_values("timestamp")
    levels = df["water_level_ft"].to_numpy()
    steps = min(3, len(levels) - 1)  # 3 × 5-min steps = 15 min
    if steps == 0:
        return 0.0
    return float(levels[-1] - levels[-1 - steps])
