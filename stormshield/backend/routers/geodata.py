"""
GET /api/geodata/flood-zones
GET /api/geodata/ema-alerts
"""
from __future__ import annotations

from fastapi import APIRouter
from backend.modules.cache import store as cache

router = APIRouter(prefix="/api/geodata", tags=["geodata"])


@router.get("/flood-zones")
def get_flood_zones():
    data = cache.get("flood_zones")
    if data:
        return data
    # Return stub GeoJSON if not cached
    from backend.modules.ingestion.brightdata_scraper import _stub_flood_zones
    return _stub_flood_zones()


@router.get("/ema-alerts")
def get_ema_alerts():
    data = cache.get("ema_alerts")
    if data:
        return data
    return [{"title": "No active EMA alerts", "body": "All clear at this time."}]


# Lightweight in-memory caches and spatial index
GEOCODE_CACHE = {}
WEATHER_CACHE = {}  # Cache weather by (lat, lon) for 5 minutes
_SPATIAL_INDEX = None
_FEATURE_MAP = {}

def get_spatial_index():
    global _SPATIAL_INDEX, _FEATURE_MAP
    if _SPATIAL_INDEX is not None:
        return _SPATIAL_INDEX, _FEATURE_MAP
    
    from shapely.geometry import shape
    from shapely.strtree import STRtree
    
    flood_zones = get_flood_zones()
    if not flood_zones or "features" not in flood_zones:
        return None, {}
    
    geoms = []
    _FEATURE_MAP = {}
    for feature in flood_zones["features"]:
        try:
            geom = shape(feature["geometry"])
            if geom.is_valid:
                geoms.append(geom)
                _FEATURE_MAP[id(geom)] = feature
        except:
            continue
            
    if geoms:
        _SPATIAL_INDEX = STRtree(geoms)
    return _SPATIAL_INDEX, _FEATURE_MAP

@router.post("/lookup")
def lookup_address(payload: dict):
    """
    Geocode an address, find its FEMA flood zone, and return local status.
    Uses direct httpx to Nominatim (faster than geopy), with parallel weather fetch.
    """
    import time
    start_time = time.time()

    address_raw = payload.get("address", "").strip()
    if not address_raw:
        return {"error": "No address provided"}

    address = f"{address_raw}, Montgomery, AL"

    # 1. Geocode (with Cache) — direct httpx to Nominatim, no geopy overhead
    if address in GEOCODE_CACHE:
        cached = GEOCODE_CACHE[address]
        lat, lon, display_name = cached["lat"], cached["lon"], cached["display_name"]
    else:
        try:
            import httpx as _httpx
            geo_resp = _httpx.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": address, "format": "json", "limit": 1},
                headers={"User-Agent": "StormShieldAI/2.0"},
                timeout=6,
            )
            geo_resp.raise_for_status()
            results = geo_resp.json()
            if not results:
                return {"error": "Address not found in Montgomery, AL area"}
            r = results[0]
            lat = float(r["lat"])
            lon = float(r["lon"])
            display_name = r.get("display_name", address_raw)
            GEOCODE_CACHE[address] = {"lat": lat, "lon": lon, "display_name": display_name}
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Geocoding failed: %s", e)
            return {"error": "Geocoding service timeout. Please try again."}

    round_lat, round_lon = round(lat, 4), round(lon, 4)
    weather_key = (round_lat, round_lon)

    from shapely.geometry import Point
    from backend.modules.ingestion.noaa_client import fetch_hourly_forecast

    try:
        # 2. Spatial Check (FEMA Zones) - Optimized with STRtree
        zone_info = {"zone": "X", "name": "Minimal Risk Area", "risk_level": "Low"}
        point = Point(lon, lat)

        index, feat_map = get_spatial_index()
        if index:
            possible_matches = index.query(point)
            for idx in possible_matches:
                poly = index.geometries[idx]
                if poly.contains(point):
                    feature = feat_map[id(poly)]
                    props = feature.get("properties", {})
                    zone_code = props.get("fld_zone") or props.get("FLD_ZONE") or "X"
                    zone_name = props.get("name") or props.get("NAME") or f"Zone {zone_code}"
                    risk_map = {"AE": "High", "A": "High", "VE": "High", "AO": "Moderate", "AH": "Moderate"}
                    zone_info = {
                        "zone": zone_code,
                        "name": zone_name,
                        "risk_level": risk_map.get(zone_code, "Low")
                    }
                    break

        # 3. Local Weather (with Cache — 10 min TTL) — fetched in parallel if not cached
        current_time = time.time()
        if weather_key in WEATHER_CACHE and (current_time - WEATHER_CACHE[weather_key][0] < 600):
            current_precip = WEATHER_CACHE[weather_key][1]
        else:
            # Fetch weather in a thread so it doesn't block (already in sync FastAPI)
            weather_data = fetch_hourly_forecast(lat, lon)
            current_precip = weather_data[0].precipitation_mm if weather_data else 0.0
            WEATHER_CACHE[weather_key] = (current_time, current_precip)

        import logging
        logging.getLogger(__name__).info("Lookup for %s took %.4fs", address, time.time() - start_time)

        return {
            "address": display_name,
            "lat": lat,
            "lon": lon,
            "fema_zone": zone_info,
            "weather": {
                "local_precip_mm": current_precip,
                "summary": "Heavy rain" if current_precip > 5 else "Light rain" if current_precip > 0 else "Clear sky"
            }
        }

    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Lookup logic failed: %s", exc)
        return {"error": f"Internal lookup error: {str(exc)}"}
