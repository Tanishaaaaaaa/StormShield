
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parents[1]))

# Mock settings or import them
try:
    from backend.config import settings
    api_key = settings.brightdata_api_key
except Exception:
    api_key = os.getenv("BRIGHTDATA_API_KEY", "1aeade8c-91f8-48d0-b533-4568906daa10")

from backend.modules.ingestion.brightdata_scraper import scrape_flood_zones, scrape_ema_alerts, scrape_911_calls

def main():
    print(f"Starting Bright Data scrape with API key: {api_key[:5]}...")
    
    print("\n--- Scraping Flood Zones ---")
    try:
        data = scrape_flood_zones(password=api_key, force=True)
        print(f"Flood Zones: {len(data.get('features', []))} features.")
    except Exception as e:
        print(f"Flood scrape failed: {e}")

    print("\n--- Scraping EMA Alerts ---")
    try:
        ema = scrape_ema_alerts(password=api_key)
        print(f"EMA Alerts: {len(ema)} items.")
    except Exception as e:
        print(f"EMA scrape failed: {e}")

    print("\n--- Scraping 911 Calls ---")
    try:
        calls = scrape_911_calls(password=api_key)
        print(f"911 Calls: {len(calls)} items.")
    except Exception as e:
        print(f"911 scrape failed: {e}")

if __name__ == "__main__":
    main()
