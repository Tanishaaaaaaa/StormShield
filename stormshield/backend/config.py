from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        extra="ignore",
    )

    # API Keys
    gemini_api_key: str = ""
    brightdata_api_key: str = ""

    # USGS
    usgs_station_id: str = "01648000"
    usgs_period_hours: int = 4

    # NOAA / NWS
    location_lat: float = 32.3768
    location_lon: float = -86.3006
    nws_zone: str = "MDC031"

    # Alert thresholds
    flood_stage_ft: float = 8.0
    rate_of_rise_threshold: float = 2.0

    # Model
    model_path: str = "backend/modules/prediction/artifacts/xgb_model.joblib"

    # Scheduler intervals (seconds)
    poll_usgs_interval: int = 300
    poll_noaa_interval: int = 900
    scrape_ema_interval: int = 900
    run_prediction_interval: int = 300

    # Frontend
    backend_url: str = "http://localhost:8000"
    default_refresh_seconds: int = 300


settings = Settings()
