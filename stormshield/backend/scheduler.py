"""
APScheduler background polling jobs.
Registered here, started from main.py on app startup.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from backend.config import settings

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def job_poll_usgs() -> None:
    """Poll USGS, smooth readings, run prediction, evaluate alert, store to cache."""
    from backend.modules.ingestion.usgs_client import fetch_gauge_readings
    from backend.modules.processing.smoother import apply_rolling_mean, remove_outliers_zscore
    from backend.modules.processing.feature_builder import build_feature_vector, compute_rate_of_rise
    from backend.modules.alert.engine import evaluate_alert
    from backend.modules.alert.llm_generator import generate_alert_text
    from backend.modules.cache import store as cache
    from backend.modules.ingestion.noaa_client import fetch_hourly_forecast

    logger.info("[Scheduler] Polling USGS…")
    raw = fetch_gauge_readings(settings.usgs_station_id, settings.usgs_period_hours)
    smoothed = apply_rolling_mean(raw)
    cleaned = remove_outliers_zscore(smoothed)
    cache.set("sensor_readings", cleaned, ttl_seconds=600)

    # Also fetch rainfall for feature building
    rainfall = cache.get("rainfall_forecast") or []
    features = build_feature_vector(cleaned, rainfall)
    rate = compute_rate_of_rise(cleaned)

    # Predict
    from backend.main import predictor
    prediction = predictor.predict(features)
    cache.set("forecast", prediction, ttl_seconds=300)

    # Alert
    old_alert = cache.get("alert")
    alert = evaluate_alert(prediction, rate, settings.flood_stage_ft, settings.rate_of_rise_threshold)
    alert.alert_text = generate_alert_text(alert, prediction)
    cache.set("alert", alert, ttl_seconds=300)

    # SMS Broadcast for ANY status change (RED, YELLOW, or return to GREEN)
    if not old_alert or old_alert.level != alert.level:
        from backend.modules.alert.sms import broadcast_alert
        subscribers = cache.get_subscribers()
        
        emoji = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}.get(alert.level, "📢")
        status_name = "ALL CLEAR" if alert.level == "GREEN" else f"{alert.level} ALERT"
        
        sms_msg = f"StormShield AI {emoji}: {status_name}! Predicted: {alert.predicted_level_ft}ft. {alert.alert_text[:120]}"
        broadcast_alert(sms_msg, subscribers)

    # Maintain alert history (max 200)
    history = cache.get("alert_history") or []
    history.append(alert)
    history = history[-200:]
    cache.set("alert_history", history, ttl_seconds=86400)
    logger.info("[Scheduler] USGS cycle complete. Alert: %s @ %.2f ft", alert.level, prediction.predicted_level_ft)


def job_poll_noaa() -> None:
    """Poll NOAA hourly forecast and NWS alerts."""
    from backend.modules.ingestion.noaa_client import fetch_hourly_forecast
    from backend.modules.ingestion.nws_client import fetch_active_alerts
    from backend.modules.cache import store as cache

    logger.info("[Scheduler] Polling NOAA & NWS…")
    rainfall = fetch_hourly_forecast(settings.location_lat, settings.location_lon)
    cache.set("rainfall_forecast", rainfall, ttl_seconds=settings.poll_noaa_interval + 60)

    nws = fetch_active_alerts(settings.nws_zone)
    cache.set("nws_alerts", nws, ttl_seconds=settings.poll_noaa_interval + 60)
    logger.info("[Scheduler] NOAA/NWS cycle complete.")


def job_scrape_ema() -> None:
    """Scrape EMA alerts and 911 calls via Bright Data."""
    from backend.modules.ingestion.brightdata_scraper import scrape_ema_alerts, scrape_911_calls
    from backend.modules.cache import store as cache

    logger.info("[Scheduler] Scraping EMA & 911…")
    ema = scrape_ema_alerts(settings.brightdata_api_key)
    cache.set("ema_alerts", ema, ttl_seconds=settings.scrape_ema_interval + 60)

    calls = scrape_911_calls(settings.brightdata_api_key)
    cache.set("calls_911", calls, ttl_seconds=settings.scrape_ema_interval + 60)
    logger.info("[Scheduler] EMA/911 scrape complete.")


def configure_jobs() -> None:
    """Register all background jobs with APScheduler."""
    scheduler.add_job(
        job_poll_usgs,
        "interval",
        seconds=settings.poll_usgs_interval,
        id="poll_usgs",
        replace_existing=True,
    )
    scheduler.add_job(
        job_poll_noaa,
        "interval",
        seconds=settings.poll_noaa_interval,
        id="poll_noaa",
        replace_existing=True,
    )
    scheduler.add_job(
        job_scrape_ema,
        "interval",
        seconds=settings.scrape_ema_interval,
        id="scrape_ema",
        replace_existing=True,
    )
