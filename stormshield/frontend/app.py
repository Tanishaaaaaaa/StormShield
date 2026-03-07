"""
StormShield AI — Streamlit Frontend Entry Point
Montgomery's Smart Flood & Weather Guardian
Run: streamlit run frontend/app.py
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx
import streamlit as st
from streamlit_folium import st_folium

# ── Page config (MUST be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="StormShield AI — Montgomery Flood Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Import frontend modules ────────────────────────────────────────────────
from frontend.config import BACKEND_URL, REFRESH_OPTIONS
from frontend.components.map_view import render_map
from frontend.components.gauge_chart import render_gauge_chart
from frontend.components.alert_card import render_alert_card
from frontend.components.confidence_badge import render_confidence_badge
from frontend.components.simulation_panel import render_simulation_panel
from frontend.components.query_panel import render_query_panel
from frontend.components.weather_panel import render_weather_panel

# ── Global CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif !important; }

.stApp {
    background: linear-gradient(160deg, #020617 0%, #0f172a 40%, #0a0f1e 100%);
    color: #e2e8f0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #1e293b;
}

/* Tab styles */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(30,41,59,0.5);
    border: 1px solid #1e293b;
    border-radius: 8px 8px 0 0;
    color: #94a3b8;
    font-weight: 500;
    font-size: 13px;
    padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
    background: rgba(59,130,246,0.15) !important;
    border-color: #3b82f6 !important;
    color: #60a5fa !important;
}

/* Metrics */
[data-testid="stMetricValue"] {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #f1f5f9 !important;
}

/* Header */
.main-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 0 8px 0;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 16px;
}
.header-title {
    font-size: 26px;
    font-weight: 800;
    background: linear-gradient(90deg, #60a5fa, #818cf8, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}
.header-sub {
    font-size: 12px;
    color: #64748b;
    margin-top: 2px;
}

/* Chat */
.stChatMessage { background: rgba(15,23,42,0.7) !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def fetch_json(url: str) -> dict | list | None:
    try:
        # Increase timeout for the 175MB flood_zones.json file
        resp = httpx.get(url, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def fetch_all_data():
    sensor     = fetch_json(f"{BACKEND_URL}/api/sensor/latest") or {}
    history    = fetch_json(f"{BACKEND_URL}/api/sensor/history?hours=4") or []
    forecast   = fetch_json(f"{BACKEND_URL}/api/forecast/current") or {}
    alert      = fetch_json(f"{BACKEND_URL}/api/alert/current") or {}
    alert_hist = fetch_json(f"{BACKEND_URL}/api/alert/history?limit=20") or []
    geo        = fetch_json(f"{BACKEND_URL}/api/geodata/flood-zones") or {}
    ema        = fetch_json(f"{BACKEND_URL}/api/geodata/ema-alerts") or []
    calls      = fetch_json(f"{BACKEND_URL}/api/geodata/ema-alerts") or []   # reuse for demo
    health     = fetch_json(f"{BACKEND_URL}/health") or {}
    return sensor, history, forecast, alert, alert_hist, geo, ema, calls, health


# ── Sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:16px 0 10px;">
        <div style="font-size:40px;">🛡️</div>
        <div style="font-size:16px; font-weight:700; color:#60a5fa;">StormShield AI</div>
        <div style="font-size:11px; color:#64748b;">Montgomery Flood Guardian</div>
    </div>
    <hr style="border-color:#1e293b;">
    """, unsafe_allow_html=True)

    refresh_label = st.selectbox(
        "🔄 Refresh Interval",
        options=list(REFRESH_OPTIONS.keys()),
        index=1,  # default 60s
    )
    refresh_seconds = REFRESH_OPTIONS[refresh_label]
    st.session_state["refresh_interval"] = refresh_seconds

    st.markdown("---")
    st.markdown("**📍 Address Lookup**")
    address = st.text_input("Enter address to check FEMA zone", placeholder="123 Main St, Montgomery AL")
    if address:
        with st.spinner("Checking FEMA maps..."):
            res = fetch_json(f"{BACKEND_URL}/api/geodata/lookup?address={address}")
            if res and "error" not in res:
                zone = res.get("zone", "X (Minimal Risk)")
                high_risk = res.get("is_high_risk", False)
                
                st.success(f"**Zone: {zone}**")
                if high_risk:
                    st.error("⚠️ This address is in a High-Risk SFHA area.")
                else:
                    st.info("✅ This address is in a Minimal/Moderate risk area.")
                
                st.caption(f"📍 {res.get('address', address)}")
            else:
                st.warning(f"Address not found or error: {res.get('error') if res else 'Unknown'}")

    st.markdown("---")

    # Backend health
    health_data = fetch_json(f"{BACKEND_URL}/health") or {}
    model_ok = health_data.get("model_loaded", False)
    cache_age = health_data.get("cache_age_seconds", 0)

    col_a, col_b = st.columns(2)
    with col_a:
        color = "#22c55e" if model_ok else "#f59e0b"
        st.markdown(f'<div style="font-size:11px; color:{color};">{"✅ Model loaded" if model_ok else "⚠️ Synthetic mode"}</div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(f'<div style="font-size:11px; color:#64748b;">Cache: {cache_age}s ago</div>', unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:10px; color:#475569; margin-top:12px;">Last updated: {datetime.now(timezone.utc).strftime("%H:%M:%S")} UTC</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px; color:#334155;">USGS 01648000 · Sligo Creek · Montgomery, AL</div>', unsafe_allow_html=True)


# ── Page Header ────────────────────────────────────────────────────────────

sensor, history, forecast, alert, alert_hist, geo, ema, calls, health = fetch_all_data()

level = alert.get("level", "GREEN")
level_emoji = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}.get(level, "🟢")

st.markdown(f"""
<div class="main-header">
    <div style="font-size:48px;">🛡️</div>
    <div>
        <div class="header-title">StormShield AI</div>
        <div class="header-sub">Montgomery's Smart Flood & Weather Guardian · USGS Sligo Creek Station 01648000</div>
    </div>
    <div style="margin-left:auto; text-align:right;">
        <div style="font-size:28px;">{level_emoji}</div>
        <div style="font-size:11px; color:#64748b;">{level} ALERT</div>
    </div>
</div>
""", unsafe_allow_html=True)


tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Live Dashboard", "📋 Situation Report", "💬 Ask StormShield AI", "🌤️ Weather & Rainfall Analysis"])


# ════════════════════════════════════════════════════════════
# TAB 1 — LIVE DASHBOARD
# ════════════════════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns([2, 1], gap="large")

    # LEFT COLUMN — Map + Chart
    with col1:
        st.markdown("#### 🗺️ Montgomery Flood Zone Map")
        render_map(geo, ema, calls)

        st.markdown("#### 📈 Water Level History & Forecast")
        render_gauge_chart(history, forecast)

    # RIGHT COLUMN — Alert + Confidence + Simulation
    with col2:
        st.markdown("#### ⚠️ Current Alert Status")
        render_alert_card(alert, forecast)

        if forecast:
            render_confidence_badge(forecast.get("confidence_score", 0.6))

        st.markdown("---")

        # Live metrics row
        wl = sensor.get("water_level_ft", 0)
        dis = sensor.get("discharge_cfs", 0)
        pred = alert.get("predicted_level_ft", 0)
        ror  = alert.get("rate_of_rise_ft_per_15m", 0)

        m1, m2 = st.columns(2)
        with m1:
            st.metric("💧 Water Level", f"{wl:.2f} ft")
            st.metric("📉 Rate of Rise", f"{ror:+.3f} ft/15m")
        with m2:
            st.metric("🌊 Discharge", f"{dis:.0f} cfs")
            st.metric("🔮 Predicted (T+30)", f"{pred:.2f} ft")

        st.markdown("---")
        render_simulation_panel(BACKEND_URL, alert)


# ════════════════════════════════════════════════════════════
# TAB 2 — SITUATION REPORT
# ════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### 📋 Alert History (last 20 records)")

    if alert_hist:
        import pandas as pd
        rows = []
        for a in alert_hist:
            rows.append({
                "Timestamp": a.get("generated_at", "")[:19],
                "Level": a.get("level", "—"),
                "Predicted (ft)": round(a.get("predicted_level_ft", 0), 2),
                "Rise (ft/15m)": round(a.get("rate_of_rise_ft_per_15m", 0), 3),
            })
        df = pd.DataFrame(rows[::-1])

        def highlight_level(row):
            styles = {
                "RED":    "background-color:#450a0a; color:#fca5a5",
                "YELLOW": "background-color:#451a03; color:#fcd34d",
                "GREEN":  "background-color:#052e16; color:#86efac",
            }
            return [styles.get(row["Level"], "")] * len(row)

        st.dataframe(
            df.style.apply(highlight_level, axis=1),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No alert history yet — data is collected on each scheduler cycle (every 5 min).")

    st.markdown("---")
    st.markdown("#### 📢 Current Alert Bulletin")
    alert_text = alert.get("alert_text", "No alert text available.")
    level_color = {"RED": "#ef4444", "YELLOW": "#f59e0b", "GREEN": "#22c55e"}.get(level, "#22c55e")
    st.markdown(f"""
    <div style="border-left: 4px solid {level_color}; padding: 12px 20px;
                background: rgba(30,41,59,0.6); border-radius: 0 10px 10px 0;
                font-size: 14px; color: #e2e8f0; line-height: 1.7;">
        {alert_text}
    </div>
    """, unsafe_allow_html=True)

    # NWS Alerts
    st.markdown("---")
    st.markdown("#### 🌩️ Active NWS Alerts")
    nws_alerts = fetch_json(f"{BACKEND_URL}/api/geodata/ema-alerts") or []
    for a in nws_alerts:
        title = a.get("title", "Alert")
        body  = a.get("body", "")
        if "no active" in title.lower():
            st.success(f"✅ {title}")
        else:
            st.warning(f"⚠️ **{title}** — {body}")


# ════════════════════════════════════════════════════════════
# TAB 3 — ASK STORMSHIELD AI
# ════════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### 💬 Ask StormShield AI")
    render_query_panel(BACKEND_URL)


# ════════════════════════════════════════════════════════════
# TAB 4 — WEATHER & RAINFALL
# ════════════════════════════════════════════════════════════
with tab4:
    render_weather_panel()

# ── Auto-rerun loop ────────────────────────────────────────────────────────
refresh = st.session_state.get("refresh_interval", 60)
time.sleep(refresh)
st.rerun()
