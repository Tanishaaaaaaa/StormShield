"""
Open-Meteo API client for current weather and daily summary.
Provides better context for the Query Engine/AI.
"""
from __future__ import annotations

import logging
from typing import Any, Optional
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class WeatherStatus(BaseModel):
    temperature: float
    precipitation: float
    humidity: int
    wind_speed: float
    condition: str
    daily_precip_sum: float  # Today's total rain so far

def fetch_current_weather(lat: float, lon: float) -> Optional[WeatherStatus]:
    """Fetch current status and today's summary from open-meteo."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code"
        f"&daily=weather_code,precipitation_sum&timezone=America%2FChicago&forecast_days=1"
    )
    
    try:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        current = data.get("current", {})
        daily = data.get("daily", {})
        
        code = current.get("weather_code", 0)
        condition = _map_code_to_text(code)
        
        return WeatherStatus(
            temperature=current.get("temperature_2m", 0.0),
            precipitation=current.get("precipitation", 0.0),
            humidity=current.get("relative_humidity_2m", 0),
            wind_speed=current.get("wind_speed_10m", 0.0),
            condition=condition,
            daily_precip_sum=daily.get("precipitation_sum", [0.0])[0],
        )
    except Exception as exc:
        logger.warning("Open-Meteo fetch failed: %s", exc)
        return None

def _map_code_to_text(code: int) -> str:
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return mapping.get(code, "Cloudy")
