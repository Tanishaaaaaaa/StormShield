
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

from backend.modules.ingestion.brightdata_scraper import scrape_flood_zones

def main():
    print(f"Starting flood zone scrape with API key: {api_key[:5]}...")
    try:
        data = scrape_flood_zones(password=api_key, force=True)
        num_features = len(data.get("features", []))
        print(f"Successfully scraped {num_features} features.")
        if num_features <= 2:
            print("WARNING: Only scraped stub data (2 features). Check proxy/connectivity.")
    except Exception as e:
        print(f"Scrape failed: {e}")

if __name__ == "__main__":
    main()
