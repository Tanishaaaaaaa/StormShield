"""
GET /api/geodata/flood-zones
GET /api/geodata/ema-alerts
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse
from backend.modules.cache import store as cache

router = APIRouter(prefix="/api/geodata", tags=["geodata"])


@router.get("/flood-zones")
def get_flood_zones():
    """Serve the 175MB flood zone GeoJSON directly as a file to prevent serialization timeouts."""
    path = cache.DATA_DIR / "flood_zones.json"
    if path.exists():
        return FileResponse(path, media_type="application/geo+json")
    
    # Return stub GeoJSON if file doesn't exist
    from backend.modules.ingestion.brightdata_scraper import _stub_flood_zones
    return _stub_flood_zones()


@router.get("/ema-alerts")
def get_ema_alerts():
    data = cache.get("ema_alerts")
    if data:
        return data
    return [{"title": "No active EMA alerts", "body": "All clear at this time."}]


@router.get("/lookup")
async def lookup_address_zone(address: str):
    """Geocode address and return which FEMA flood zone it resides in."""
    import httpx
    import json
    
    # 1. Geocode via Nominatim
    headers = {"User-Agent": "StormShieldAI/2.0"}
    geo_url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(geo_url, headers=headers, timeout=5.0)
            geo_data = resp.json()
            if not geo_data:
                return {"error": "Address not found."}
            
            lat = float(geo_data[0]["lat"])
            lon = float(geo_data[0]["lon"])
            display_name = geo_data[0]["display_name"]
    except Exception as exc:
        return {"error": f"Geocoding failed: {exc}"}

    # 2. Check zones (Winding Number / Ray Casting)
    # Use cache or load from disk
    from backend.modules.cache import store as cache
    zones_collection = cache.get("flood_zones")
    if not zones_collection:
        # Try to load if missing
        path = cache.DATA_DIR / "flood_zones.json"
        if path.exists():
            with open(path) as f:
                zones_collection = json.load(f)

    if not zones_collection or "features" not in zones_collection:
        return {"error": "Flood zone data unavailable."}

    matched_zone = "X (Minimal Risk)"
    is_sfha = False

    def point_in_poly(x, y, poly):
        n = len(poly)
        inside = False
        p1x, p1y = poly[0]
        for i in range(1, n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    for feat in zones_collection["features"]:
        geom = feat.get("geometry", {})
        props = feat.get("properties", {})
        if geom.get("type") == "Polygon":
            # Just handle first ring for performance
            for ring in geom.get("coordinates", []):
                if point_in_poly(lon, lat, ring):
                    matched_zone = props.get("fld_zone", "Unknown")
                    is_sfha = props.get("sfha_tf", "F") == "T"
                    return {
                        "address": display_name,
                        "zone": matched_zone,
                        "is_high_risk": is_sfha,
                        "lat": lat,
                        "lon": lon
                    }
        elif geom.get("type") == "MultiPolygon":
            for poly in geom.get("coordinates", []):
                for ring in poly:
                    if point_in_poly(lon, lat, ring):
                        matched_zone = props.get("fld_zone", "Unknown")
                        is_sfha = props.get("sfha_tf", "F") == "T"
                        return {
                            "address": display_name,
                            "zone": matched_zone,
                            "is_high_risk": is_sfha,
                            "lat": lat,
                            "lon": lon
                        }

    return {
        "address": display_name,
        "zone": matched_zone,
        "is_high_risk": False,
        "lat": lat,
        "lon": lon
    }
