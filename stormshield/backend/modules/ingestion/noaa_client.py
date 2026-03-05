"""
NOAA api.weather.gov client.
Fetches hourly precipitation + wind forecasts for a lat/lon point.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_last_known: list["RainfallForecast"] = []


class RainfallForecast(BaseModel):
    timestamp: datetime
    precipitation_mm: float
    wind_speed_mph: float


def fetch_hourly_forecast(lat: float, lon: float) -> list[RainfallForecast]:
    """Resolve lat/lon to a grid point, then fetch hourly forecast periods."""
    global _last_known
    try:
        # Step 1 – resolve point
        points_url = f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}"
        headers = {"User-Agent": "StormShieldAI/2.0 contact@stormshield.local"}
        resp = httpx.get(points_url, timeout=10, headers=headers)
        resp.raise_for_status()
        forecast_url = resp.json()["properties"]["forecastHourly"]

        # Step 2 – fetch hourly periods
        resp2 = httpx.get(forecast_url, timeout=10, headers=headers)
        resp2.raise_for_status()
        periods = resp2.json()["properties"]["periods"]

        forecasts = _parse_periods(periods)
        _last_known = forecasts
        return forecasts
    except Exception as exc:
        logger.warning("NOAA fetch failed (%s), returning cached forecast.", exc)
        return _last_known or _generate_fallback_forecast()


def _parse_periods(periods: list[dict]) -> list[RainfallForecast]:
    """Convert NOAA hourly periods to RainfallForecast objects."""
    results = []
    for p in periods[:24]:  # next 24 hours
        try:
            ts = datetime.fromisoformat(p["startTime"])
            # NOAA gives probabilityOfPrecipitation as a quantitative value
            prob = p.get("probabilityOfPrecipitation", {})
            rain_prob = prob.get("value", 0) or 0
            # Approximate mm from probability (0-100 → 0-25 mm proxy)
            precip_mm = round(rain_prob * 0.25, 2)

            wind_raw = p.get("windSpeed", "0 mph").split(" ")[0]
            wind_mph = float(wind_raw) if wind_raw.isdigit() else 0.0

            results.append(
                RainfallForecast(
                    timestamp=ts,
                    precipitation_mm=precip_mm,
                    wind_speed_mph=wind_mph,
                )
            )
        except (KeyError, ValueError, TypeError):
            continue
    return results


def _generate_fallback_forecast() -> list[RainfallForecast]:
    """Return minimal synthetic forecast."""
    from datetime import timezone
    now = datetime.now(timezone.utc)
    return [
        RainfallForecast(
            timestamp=now,
            precipitation_mm=0.0,
            wind_speed_mph=5.0,
        )
    ]
