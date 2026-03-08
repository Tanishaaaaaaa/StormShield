"""
FastAPI application entry point.
Mounts all routers, starts background scheduler, and serves /health.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.modules.cache import store as cache
from backend.modules.prediction.model import XGBoostPredictor
from backend.modules.database import init_db, save_flood_zones, get_flood_zones_geojson
from backend.modules.cache.store import DATA_DIR
import json
from backend.scheduler import configure_jobs, job_poll_noaa, job_poll_usgs, scheduler, job_scrape_ema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Global predictor instance (shared with scheduler)
predictor = XGBoostPredictor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load model, seed cache, start scheduler."""
    logger.info("StormShield AI backend starting up…")

    # Load XGBoost model
    predictor.load_model(settings.model_path)

    # Database Initialization & Sync
    init_db()
    
    # Pre-load flood zones into DB if empty or stale
    logger.info("Checking flood zones data layer...")
    fz_path = DATA_DIR / "flood_zones.json"
    if fz_path.exists():
        # Check if DB has data, if not load it
        existing = get_flood_zones_geojson()
        if not existing.get("features"):
            logger.info("Initializing database with flood zones from %s...", fz_path.name)
            with open(fz_path) as f:
                save_flood_zones(json.load(f))
    
    # Seed cache from disk files
    cache.load_json_files()

    # Run initial data pulls in background to prevent blocking startup
    logger.info("Scheduling initial data pulls...")
    scheduler.add_job(job_poll_noaa, id="init_noaa")
    scheduler.add_job(job_scrape_ema, id="init_ema")
    scheduler.add_job(job_poll_usgs, id="init_usgs")

    # Start background scheduler
    configure_jobs()
    scheduler.start()
    logger.info("Scheduler started with %d jobs.", len(scheduler.get_jobs()))

    yield  # Application runs here

    logger.info("Shutting down scheduler…")
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="StormShield AI",
    description="Montgomery's Smart Flood & Weather Guardian — FastAPI Backend",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
from backend.routers import alert, forecast, geodata, query, sensor, simulation

app.include_router(sensor.router)
app.include_router(forecast.router)
app.include_router(alert.router)
app.include_router(simulation.router)
app.include_router(geodata.router)
app.include_router(query.router)


@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "model_loaded": predictor.is_loaded,
        "cache_age_seconds": cache.age_seconds("sensor_readings"),
    }
