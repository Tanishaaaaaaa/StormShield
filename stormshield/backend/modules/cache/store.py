"""
In-memory + JSON file cache manager for StormShield AI.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parents[3] / "data"

_store: dict[str, dict] = {}   # {"key": {"value": ..., "expires_at": float}}


def set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Store a value with an expiry time."""
    _store[key] = {
        "value": value,
        "expires_at": time.monotonic() + ttl_seconds,
        "stored_at": time.time(),
    }


def get(key: str) -> Optional[Any]:
    """Retrieve a value if it hasn't expired. Returns None if absent or expired."""
    entry = _store.get(key)
    if entry is None:
        return None
    if time.monotonic() > entry["expires_at"]:
        del _store[key]
        return None
    return entry["value"]


def age_seconds(key: str) -> int:
    """Return how many seconds ago `key` was stored (0 if not found)."""
    entry = _store.get(key)
    if entry is None:
        return 0
    return int(time.time() - entry.get("stored_at", time.time()))


def load_json_files() -> None:
    """
    On startup, populate in-memory cache from JSON files
    if the in-memory cache is empty for those keys.
    """
    files = {
        "flood_zones": "flood_zones.json",
        "ema_alerts": "ema_alerts.json",
        "calls_911": "calls_911.json",
    }
    for key, filename in files.items():
        if get(key) is None:
            path = DATA_DIR / filename
            if path.exists():
                try:
                    with open(path) as f:
                        data = json.load(f)
                    set(key, data, ttl_seconds=24 * 3600)
                    logger.info("Loaded %s from disk into cache.", filename)
                except Exception as exc:
                    logger.warning("Could not load %s: %s", filename, exc)
