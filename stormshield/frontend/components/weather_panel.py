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

import plotly.express as px
import plotly.graph_objects as go

def render_weather_panel() -> None:
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h4 style="margin:0; background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🌤️ Weather & Rainfall Analysis</h4>
            <div style="font-size: 13px; color: #94a3b8;">Live meteorological data and precise rainfall projections for Montgomery, AL</div>
        </div>
    """, unsafe_allow_html=True)
    
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
        
        # 1. Glassmorphic Current Weather Card
        st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 20px; backdrop-filter: blur(10px); margin-bottom: 25px;">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="font-size: 48px;">{condition.split()[0] if 'cloudy' not in condition.lower() else '☁️'}</div>
                    <div>
                        <div style="font-size: 14px; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Current Condition</div>
                        <div style="font-size: 24px; font-weight: 800; color: #f8fafc;">{condition}</div>
                        <div style="font-size: 13px; color: #60a5fa;">Montgomery, AL • Live Update</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🌡️ Temperature", f"{temp} °C")
        with col2:
            st.metric("💧 Precipitation", f"{precip} mm")
        with col3:
            st.metric("💨 Wind Speed", f"{wind} km/h")
        with col4:
            st.metric("🌫️ Humidity", f"{humidity} %")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. Daily Forecast Table (Themed and Center Aligned)
        st.markdown("##### 📅 7-Day Forecast (Montgomery)")
        daily = data.get("daily", {})
        if daily:
            df_daily = pd.DataFrame({
                "Date": daily.get("time", []),
                "Condition": [get_weather_desc(c) for c in daily.get("weather_code", [])],
                "Max Temp (°C)": daily.get("temperature_2m_max", []),
                "Min Temp (°C)": daily.get("temperature_2m_min", []),
                "Rainfall (mm)": daily.get("precipitation_sum", [])
            })
            
            # CSS for center-aligning table text
            st.markdown("""
                <style>
                    [data-testid="stDataFrame"] td { text-align: center !important; }
                    [data-testid="stDataFrame"] th { text-align: center !important; }
                </style>
            """, unsafe_allow_html=True)
            
            st.dataframe(df_daily, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. Two Charts Arrangement
        st.markdown("##### 🕒 Hourly Precipitation & Temperature")
        hourly = data.get("hourly", {})
        if hourly:
            times = [t.replace("T", " ") for t in hourly.get("time", [])[:24]]
            precips = hourly.get("precipitation", [])[:24]
            probs = hourly.get("precipitation_probability", [])[:24]
            temps = hourly.get("temperature_2m", [])[:24]

            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                # Rainfall Probability & Amount (Bar + Line)
                fig_precip = go.Figure()
                fig_precip.add_trace(go.Bar(
                    x=times, y=precips, name="Rain (mm)", 
                    marker_color="#22d3ee", opacity=0.7
                ))
                fig_precip.add_trace(go.Scatter(
                    x=times, y=probs, name="Prob (%)", 
                    line=dict(color="#facc15", width=2), yaxis="y2"
                ))
                fig_precip.update_layout(
                    title="Rainfall Forecast",
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis=dict(title="Rainfall (mm)", gridcolor="rgba(255,255,255,0.05)"),
                    yaxis2=dict(title="Probability (%)", overlaying="y", side="right", range=[0, 100], showgrid=False)
                )
                st.plotly_chart(fig_precip, use_container_width=True, config={'displayModeBar': False})

            with chart_col2:
                # Temperature Trend
                fig_temp = px.line(
                    x=times, y=temps, 
                    labels={"x": "Time", "y": "Temp (°C)"},
                    title="Temperature Trend"
                )
                fig_temp.update_traces(line_color="#60a5fa", line_width=3, fill='tozeroy', fillcolor='rgba(96,165,250,0.1)')
                fig_temp.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig_temp, use_container_width=True, config={'displayModeBar': False})
            
    except Exception as e:
        st.error(f"⚠️ Could not load weather data: {e}")
