"""
Offline training script for XGBoost water-level predictor.
Run once before first launch:
    python backend/modules/prediction/train.py

Generates: backend/modules/prediction/artifacts/xgb_model.joblib
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import joblib
import numpy as np
from xgboost import XGBRegressor

# Allow running as a script from anywhere
ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT / "stormshield"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "xgb_model.joblib"

N_FEATURES = 9  # must match feature_builder.py


def _generate_synthetic_training_data(n_samples: int = 5000):
    """
    Generate synthetic training data that approximates realistic gauge behaviour.
    In a production setup this would load real historical USGS CSV exports.
    """
    rng = np.random.default_rng(42)
    X_rows = []
    y_rows = []

    base_level = 3.5
    for i in range(n_samples):
        trend = rng.uniform(-0.02, 0.04)
        noise = rng.normal(0, 0.05)
        t0 = max(0.1, base_level + noise)
        t_minus_15 = max(0.1, t0 - trend - rng.normal(0, 0.03))
        t_minus_30 = max(0.1, t_minus_15 - trend - rng.normal(0, 0.03))
        t_minus_60 = max(0.1, t_minus_30 - trend - rng.normal(0, 0.04))
        discharge = t0 * 35 + rng.normal(0, 5)
        ror = t0 - t_minus_15
        roll_1h = (t0 + t_minus_15 + t_minus_30 + t_minus_60) / 4
        roll_4h = roll_1h + rng.normal(0, 0.1)
        rainfall = max(0.0, rng.exponential(1.5) if rng.random() < 0.3 else 0.0)

        X_rows.append([t0, t_minus_15, t_minus_30, t_minus_60, discharge, ror, roll_1h, roll_4h, rainfall])

        # Target: T+30 prediction
        future_noise = rng.normal(0, 0.04)
        y = t0 + trend * 6 + rainfall * 0.02 + future_noise
        y_rows.append(max(0.1, y))

        # Drift the base level
        base_level = t0 + rng.uniform(-0.02, 0.02)
        base_level = np.clip(base_level, 0.5, 12.0)

    return np.array(X_rows, dtype=np.float32), np.array(y_rows, dtype=np.float32)


def train_and_save():
    logger.info("Generating synthetic training data…")
    X, y = _generate_synthetic_training_data(n_samples=5000)

    logger.info("Training XGBoost on %d samples with %d features…", len(X), X.shape[1])
    model = XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        objective="reg:squarederror",
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X, y, eval_set=[(X, y)], verbose=False)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    logger.info("Model saved to %s", MODEL_PATH)

    # Quick sanity check
    sample = X[:5]
    preds = model.predict(sample)
    logger.info("Sample predictions: %s", preds.round(3))


if __name__ == "__main__":
    train_and_save()
