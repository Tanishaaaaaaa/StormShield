"""
NWS (National Weather Service) Alerts client.
Parses active alerts JSON from api.weather.gov for a given zone.
"""
from __future__ import annotations

import logging
from datetime import datetime

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_last_known: list["NWSAlert"] = []


class NWSAlert(BaseModel):
    event: str
    severity: str   # "Extreme" | "Severe" | "Moderate" | "Minor" | "Unknown"
    headline: str
    onset: datetime
    expires: datetime


def fetch_active_alerts(zone: str = "MDC031") -> list[NWSAlert]:
    """Fetch active NWS alerts for a given zone code."""
    global _last_known
    url = f"https://api.weather.gov/alerts/active?zone={zone}"
    headers = {"User-Agent": "StormShieldAI/2.0 contact@stormshield.local"}
    try:
        resp = httpx.get(url, timeout=10, headers=headers)
        resp.raise_for_status()
        features = resp.json().get("features", [])
        alerts = _parse_alerts(features)
        _last_known = alerts
        return alerts
    except Exception as exc:
        logger.warning("NWS alert fetch failed (%s), returning cached.", exc)
        return _last_known


def _parse_alerts(features: list[dict]) -> list[NWSAlert]:
    """Convert GeoJSON features from NWS alerts API."""
    results = []
    for feat in features:
        props = feat.get("properties", {})
        try:
            onset_raw = props.get("onset") or props.get("effective", "")
            expires_raw = props.get("expires") or props.get("ends", "")
            if not onset_raw or not expires_raw:
                continue
            results.append(
                NWSAlert(
                    event=props.get("event", "Unknown"),
                    severity=props.get("severity", "Unknown"),
                    headline=props.get("headline", ""),
                    onset=datetime.fromisoformat(onset_raw),
                    expires=datetime.fromisoformat(expires_raw),
                )
            )
        except (ValueError, KeyError):
            continue
    return results
