"""
Live Weather and Rainfall Prediction Panel for Montgomery, AL.
Uses open-meteo API.
"""
from __future__ import annotations

import httpx
import streamlit as st
import pandas as pd
import datetime

def get_weather_desc(code: int) -> str:
    """Map WMO weather codes to human-readable strings."""
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return mapping.get(code, "Cloudy")

def render_weather_panel() -> None:
    st.markdown("#### 🌤️ Live Weather & Rainfall Forecast (Montgomery, AL)")
    
    # Montgomery coordinates
    lat = 32.3668
    lon = -86.3000
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code&hourly=temperature_2m,precipitation_probability,precipitation&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=America%2FChicago"
    
    try:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        current = data.get("current", {})
        temp = current.get("temperature_2m", "--")
        precip = current.get("precipitation", "--")
        humidity = current.get("relative_humidity_2m", "--")
        wind = current.get("wind_speed_10m", "--")
        code = current.get("weather_code", 0)
        condition = get_weather_desc(code)
        
        # Today's Prediction Sentence
        st.markdown(f"**Today's Outlook:** {condition} with a temperature of {temp}°C.")

        # Custom CSS to brighten metric labels
        st.markdown("""
        <style>
        [data-testid="stMetricLabel"] {
            color: #ffffff !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            opacity: 1 !important;
        }
        [data-testid="stMetricValue"] {
            color: #00d4ff !important;
        }
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🌡️ Temp", f"{temp} °C")
        with col2:
            st.metric("💧 Precip", f"{precip} mm")
        with col3:
            st.metric("💨 Wind", f"{wind} km/h")
        with col4:
            st.metric("🌫️ Humidity", f"{humidity} %")
            
        st.markdown("---")
        st.markdown("##### 📅 7-Day Forecast")
        
        daily = data.get("daily", {})
        if daily:
            dates = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            precip_sums = daily.get("precipitation_sum", [])
            codes = daily.get("weather_code", [])
            descs = [get_weather_desc(c) for c in codes]
            
            df_daily = pd.DataFrame({
                "Date": dates,
                "Condition": descs,
                "Max (°C)": max_temps,
                "Min (°C)": min_temps,
                "Rain (mm)": precip_sums
            })
            st.dataframe(df_daily, use_container_width=True, hide_index=True)
            
        st.markdown("##### 🕒 24-Hour Rainfall Prediction")
        hourly = data.get("hourly", {})
        if hourly:
            times = hourly.get("time", [])[:24]
            precips = hourly.get("precipitation", [])[:24]
            probs = hourly.get("precipitation_probability", [])[:24]
            
            df_hourly = pd.DataFrame({
                "Time": [t.replace("T", " ") for t in times],
                "Rainfall (mm)": precips,
                "Probability (%)": probs
            })
            st.line_chart(df_hourly.set_index("Time")["Rainfall (mm)"])
            
    except Exception as e:
        st.warning(f"Could not load weather data: {e}")
