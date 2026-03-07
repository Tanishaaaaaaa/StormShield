"""
Signal smoother: rolling mean + Z-score outlier removal.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from scipy import stats

if TYPE_CHECKING:
    from backend.modules.ingestion.usgs_client import SensorReading

logger = logging.getLogger(__name__)

MAX_STEP_DELTA_FT = 2.0  # physically impossible single-step change


def apply_rolling_mean(
    readings: list["SensorReading"],
    window_minutes: int = 15,
) -> list["SensorReading"]:
    """Apply rolling mean with `window_minutes` width to smooth water level data."""
    if not readings:
        return readings

    from backend.modules.ingestion.usgs_client import SensorReading

    df = pd.DataFrame([r.model_dump() for r in readings])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Infer frequency (readings may be every 5 or 15 minutes)
    if len(df) > 1:
        freq_min = (df["timestamp"].diff().dropna().dt.total_seconds() / 60).median()
        freq_min = max(1, int(freq_min))
    else:
        freq_min = 5

    window = max(1, window_minutes // freq_min)
    df["water_level_ft"] = df["water_level_ft"].rolling(window=window, min_periods=1).mean()
    df["discharge_cfs"] = df["discharge_cfs"].rolling(window=window, min_periods=1).mean()

    return [SensorReading(**row) for row in df.to_dict("records")]


def remove_outliers_zscore(
    readings: list["SensorReading"],
    threshold: float = 2.0,
) -> list["SensorReading"]:
    """Remove readings whose water_level Z-score exceeds threshold, plus hard-delta filter."""
    if len(readings) < 3:
        return readings

    from backend.modules.ingestion.usgs_client import SensorReading

    df = pd.DataFrame([r.model_dump() for r in readings])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Z-score filter
    z_scores = np.abs(stats.zscore(df["water_level_ft"].to_numpy()))
    df = df[z_scores <= threshold].reset_index(drop=True)

    # Hard-floor: reject impossible single-step deltas
    deltas = df["water_level_ft"].diff().abs()
    df = df[deltas.isna() | (deltas <= MAX_STEP_DELTA_FT)].reset_index(drop=True)

    return [SensorReading(**row) for row in df.to_dict("records")]
