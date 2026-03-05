"""
Frontend configuration — API base URL and refresh settings.
"""
import os

BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
DEFAULT_REFRESH_SECONDS: int = int(os.getenv("DEFAULT_REFRESH_SECONDS", "60"))

REFRESH_OPTIONS = {
    "30 seconds": 30,
    "60 seconds": 60,
    "5 minutes": 300,
}
