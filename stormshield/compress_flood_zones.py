
import json
from pathlib import Path

DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "flood_zones.json"
OUTPUT_FILE = DATA_DIR / "flood_zones_light.json"

def round_coords(obj, precision=4):
    if isinstance(obj, list):
        return [round_coords(x, precision) for x in obj]
    if isinstance(obj, float):
        return round(obj, precision)
    return obj

def main():
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Loading {INPUT_FILE} ({INPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB)...")
    with open(INPUT_FILE) as f:
        data = json.load(f)

    print(f"Processing features...")
    # Round coordinates and simplify properties if needed
    for feature in data.get("features", []):
        if "geometry" in feature and "coordinates" in feature["geometry"]:
            feature["geometry"]["coordinates"] = round_coords(feature["geometry"]["coordinates"])
        
        # Keep only essential properties to save even more space
        props = feature.get("properties", {})
        essential_props = {
            "fld_zone": props.get("fld_zone"),
            "sfha_tf": props.get("sfha_tf"),
            "zone_subty": props.get("zone_subty"),
            "name": props.get("name") or f"Zone {props.get('fld_zone')}"
        }
        feature["properties"] = essential_props

    print(f"Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, separators=(",", ":")) # No extra whitespace

    print(f"Finished. New size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB.")

if __name__ == "__main__":
    main()
