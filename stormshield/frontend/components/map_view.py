"""
Folium/Leaflet choropleth map renderer.
Shows FEMA flood zone polygons coloured by zone type + active alert markers.
"""
from __future__ import annotations

import folium
import streamlit as st
from streamlit_folium import st_folium

# Colour mapping for FEMA flood zone codes
ZONE_COLORS = {
    "AE": "#e74c3c",   # High-risk (SFHA) — red
    "AO": "#e67e22",   # High-risk (shalllow flooding) — orange
    "AH": "#e67e22",
    "A": "#e74c3c",
    "VE": "#8e44ad",   # Coastal high-risk — purple
    "X": "#27ae60",    # Minimal risk — green
    "D": "#95a5a6",    # Undetermined
}


def render_map(flood_zones: dict, ema_alerts: list[dict], calls_911: list[dict]) -> None:
    """Render the Leaflet choropleth flood map with zone overlays."""
    m = folium.Map(
        location=[32.3768, -86.3006],
        zoom_start=12,
        tiles="CartoDB positron",
    )

    # FEMA flood zone GeoJSON overlay
    if flood_zones and flood_zones.get("features"):
        # Normalize property keys to lowercase so both stub and live data work
        for feature in flood_zones["features"]:
            props = feature.get("properties", {})
            # Create a lowercase version of all keys
            new_props = {k.lower(): v for k, v in props.items()}
            # Specific fallback for 'name' which might be missing in live ArcGIS data
            if "name" not in new_props:
                new_props["name"] = f"Zone {new_props.get('fld_zone', 'Unknown')}"
            feature["properties"] = new_props

        def style_function(feature):
            zone = feature["properties"].get("fld_zone", "X")
            color = ZONE_COLORS.get(zone, "#95a5a6")
            return {
                "fillColor": color,
                "color": color,
                "weight": 1.5,
                "fillOpacity": 0.35,
            }

        folium.GeoJson(
            flood_zones,
            name="FEMA Flood Zones",
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=["fld_zone", "sfha_tf", "name"],
                aliases=["Zone:", "SFHA:", "Area:"],
                style="background-color: #1a1a2e; color: #eee; font-size: 12px;",
            ),
        ).add_to(m)

    # EMA alert markers
    for i, alert in enumerate(ema_alerts or []):
        if alert.get("title", "").lower() != "no active ema alerts":
            folium.CircleMarker(
                location=[32.3768 + i * 0.005, -86.3006],
                radius=8,
                color="#f39c12",
                fill=True,
                fill_color="#f39c12",
                fill_opacity=0.8,
                tooltip=f"EMA: {alert.get('title', 'Alert')}",
            ).add_to(m)

    # 911 call markers
    district_coords = {
        "North": [32.3950, -86.3000],
        "Downtown": [32.3668, -86.3000],
        "East": [32.3768, -86.2800],
        "South": [32.3500, -86.3006],
    }
    for call in calls_911 or []:
        if call.get("count", 0) > 0:
            district = call.get("district", "North")
            loc = district_coords.get(district, [32.3768, -86.3006])
            folium.CircleMarker(
                location=loc,
                radius=6,
                color="#e74c3c",
                fill=True,
                fill_color="#e74c3c",
                fill_opacity=0.9,
                tooltip=f"911: {call.get('incident_type','Incident')} × {call.get('count',0)} ({district})",
            ).add_to(m)

    # Legend
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
         background: rgba(15,15,35,0.92); padding: 12px 16px; border-radius: 10px;
         border: 1px solid #333; color: #eee; font-size: 12px; font-family: sans-serif;">
      <b style="color:#00d4ff;">FEMA Flood Zones</b><br>
      <span style="color:#e74c3c;">&#9632;</span> AE — High Risk (SFHA)<br>
      <span style="color:#e67e22;">&#9632;</span> AO/AH — Shallow<br>
      <span style="color:#27ae60;">&#9632;</span> X — Minimal Risk<br>
      <span style="color:#f39c12;">&#9679;</span> EMA Alert<br>
      <span style="color:#e74c3c;">&#9679;</span> 911 Incident
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl().add_to(m)

    st_folium(m, width=None, height=420, returned_objects=[])
