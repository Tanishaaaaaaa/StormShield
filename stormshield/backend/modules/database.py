"""
Database layer for StormShield AI.
Handles persistence for flood zones, subscribers, and system logs using SQLite.
"""
import sqlite3
import json
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parents[2] / "data" / "stormshield.db"

def get_connection():
    """Create a database connection to the SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Flood Zones Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flood_zones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fema_id TEXT UNIQUE,
        zone_code TEXT,
        risk_level TEXT,
        properties_json TEXT,
        geometry_json TEXT
    )
    """)
    
    # Index for faster geocoding lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_zone_code ON flood_zones(zone_code)")
    
    # Subscribers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", DB_PATH)

def save_flood_zones(geojson_data: Dict[str, Any]):
    """Sync GeoJSON features into the SQLite database with geometry simplification."""
    from shapely.geometry import shape, mapping
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Optional: Clear existing data for a clean re-sync with simplified geometries
    cursor.execute("DELETE FROM flood_zones")
    
    features = geojson_data.get("features", [])
    count = 0
    
    for feat in features:
        props = feat.get("properties", {})
        geom_raw = feat.get("geometry", {})
        
        # Determine internal keys
        fema_id = str(props.get("OBJECTID") or props.get("fid") or count)
        zone_code = props.get("fld_zone") or props.get("FLD_ZONE") or "X"
        
        risk_map = {"AE": "High", "A": "High", "VE": "High", "AO": "Moderate", "AH": "Moderate"}
        risk_level = risk_map.get(zone_code, "Low")
        
        # Simplify geometry to reduce size (0.001 degrees is ~100m, perfect for map view)
        try:
            s = shape(geom_raw)
            # Simplify and reduce coordinate precision to 5 decimal places
            s_simple = s.simplify(0.001, preserve_topology=True)
            geom_simplified = mapping(s_simple)
            
            cursor.execute("""
            INSERT OR REPLACE INTO flood_zones (fema_id, zone_code, risk_level, properties_json, geometry_json)
            VALUES (?, ?, ?, ?, ?)
            """, (fema_id, zone_code, risk_level, json.dumps(props), json.dumps(geom_simplified)))
            count += 1
        except Exception as e:
            logger.warning("Failed to process feature %s: %s", fema_id, e)
            
    conn.commit()
    conn.close()
    logger.info("Synced and simplified %d flood zone features to database.", count)

def get_flood_zones_geojson() -> Dict[str, Any]:
    """Reconstruct a FeatureCollection from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT properties_json, geometry_json FROM flood_zones")
    rows = cursor.fetchall()
    
    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "properties": json.loads(row["properties_json"]),
            "geometry": json.loads(row["geometry_json"])
        })
    
    conn.close()
    return {
        "type": "FeatureCollection",
        "features": features
    }

def add_subscriber(phone: str) -> bool:
    """Persistent subscriber addition."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subscribers (phone_number) VALUES (?)", (phone,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return False # Explicit fallback

def get_subscribers() -> List[str]:
    """Retrieve all subscriber phone numbers."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT phone_number FROM subscribers")
    phones = [row["phone_number"] for row in cursor.fetchall()]
    conn.close()
    return phones
