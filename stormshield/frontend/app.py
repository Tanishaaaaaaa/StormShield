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
    page_title="StormShield AI — Montgomery's Smart Flood & Weather Guardian",
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

# ── Theme Setup & CSS ──────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

def toggle_theme():
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"

DARK_THEME = """
@keyframes pulse-glow {
    0% { box-shadow: 0 0 5px rgba(59, 130, 246, 0.2); }
    50% { box-shadow: 0 0 15px rgba(59, 130, 246, 0.5); }
    100% { box-shadow: 0 0 5px rgba(59, 130, 246, 0.2); }
}

.stApp {
    background: radial-gradient(circle at top right, #1e1b4b 0%, #0f172a 50%, #020617 100%);
    color: #f8fafc;
}
div[data-testid="stWidgetLabel"] p, label p {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #0f172a 100%) !important;
    border-right: 1px solid #1e293b !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #312e81 !important;
}

/* Glassmorphism for Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    background: rgba(15, 23, 42, 0.4);
    padding: 10px 10px 0 10px;
    border-radius: 12px 12px 0 0;
    border-bottom: 2px solid #1e293b;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none !important;
    color: #94a3b8;
    font-weight: 600;
    transition: all 0.3s ease;
}
.stTabs [aria-selected="true"] {
    background: rgba(59, 130, 246, 0.1) !important;
    color: #facc15 !important; /* Lightning Yellow */
    border-bottom: 2px solid #facc15 !important;
}

/* Stunning Metrics */
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 800 !important;
    color: #22d3ee !important; /* Electric Cyan */
    text-shadow: 0 0 10px rgba(34, 211, 238, 0.3);
}
[data-testid="stMetricLabel"] {
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 11px !important;
    color: #94a3b8 !important;
}

.main-header {
    background: rgba(30, 41, 59, 0.4);
    backdrop-filter: blur(8px);
    padding: 20px;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    margin-bottom: 20px;
}
.header-title {
    font-size: 32px;
    font-weight: 900;
    background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #facc15 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.header-sub {
    color: #94a3b8;
    font-weight: 500;
}

@keyframes pulse-live {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.1); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
}
.live-badge {
    background: #ef4444;
    color: white;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 900;
    animation: pulse-live 2s infinite ease-in-out;
    margin-right: 8px;
}
"""

LIGHT_THEME = """
.stApp {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #dbeafe 100%);
    color: #0f172a;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%) !important;
    border-right: 1px solid #e2e8f0 !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255, 255, 255, 0.5);
    padding: 8px 8px 0 8px;
    border-radius: 12px 12px 0 0;
    border-bottom: 2px solid #e2e8f0;
}
.stTabs [data-baseweb="tab"] {
    color: #64748b;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #2563eb !important;
    border-bottom: 2px solid #2563eb !important;
}

[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 800 !important;
    color: #0369a1 !important;
}
[data-testid="stMetricLabel"] {
    color: #64748b !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.main-header {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
}
.header-title {
    font-size: 32px;
    font-weight: 900;
    background: linear-gradient(90deg, #0284c7, #2563eb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stChatMessage { 
    background: white !important; 
    border-radius: 16px !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
}
"""

COMMON_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; }
"""

theme_css = DARK_THEME if st.session_state["theme"] == "dark" else LIGHT_THEME
border_color = "#1e293b" if st.session_state["theme"] == "dark" else "#cbd5e1"
st.markdown(f"<style>\n{COMMON_STYLE}\n{theme_css}\n</style>", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def fetch_json(url: str) -> dict | list | None:
    try:
        resp = httpx.get(url, timeout=8)
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


# ── Clear callback — runs BEFORE script re-renders (most reliable approach) ──
def _clear_lookup():
    """Called by on_click before the next render cycle. State is already clean when sidebar draws."""
    st.session_state.pop("lookup_result", None)
    st.session_state.pop("last_address", None)
    st.session_state["address_input"] = ""


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # ── Compact global CSS ───────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* ── Compact element spacing ─────────────────────────────────────────── */
    section[data-testid="stSidebar"] .block-container { padding-top: 0 !important; }
    section[data-testid="stSidebar"] .element-container { margin-bottom: 2px !important; }
    section[data-testid="stSidebar"] hr { margin: 6px 0 !important; }
    /* Smaller text input */
    section[data-testid="stSidebar"] [data-testid="stTextInput"] input {
        font-size: 11px !important; padding: 5px 8px !important; height: 30px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stTextInput"] label { font-size: 11px !important; }
    /* Smaller selectbox matching text input */
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] label {
        font-size: 11px !important; font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        font-size: 11px !important; min-height: 30px !important; height: 30px !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] div { font-size: 11px !important; }
    /* Clear button — red with visible white text */
    section[data-testid="stSidebar"] .stButton button {
        font-size: 10px !important; padding: 1px 10px !important;
        height: 24px !important; min-height: 24px !important;
        background: #dc2626 !important; color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: none !important; border-radius: 6px !important;
        font-weight: 700 !important; line-height: 22px !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: #991b1b !important; box-shadow: 0 0 6px rgba(220,38,38,0.5) !important;
    }
    section[data-testid="stSidebar"] .stButton button p,
    section[data-testid="stSidebar"] .stButton button span {
        color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; font-size: 10px !important;
    }
    div.stTooltip p { font-size: 10px !important; }
    /* Reduce vertical padding in sidebar sections */
    section[data-testid="stSidebar"] .stSelectbox { margin-bottom: 4px !important; }
    section[data-testid="stSidebar"] .stTextInput { margin-bottom: 2px !important; }
    section[data-testid="stSidebar"] .stMarkdown { margin-bottom: 2px !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Logo ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:8px 0 6px;">
        <div style="font-size:32px;">🛡️</div>
        <div style="font-size:14px; font-weight:700; color:#60a5fa; line-height:1.2;">StormShield AI</div>
        <div style="font-size:10px; color:#64748b;">Montgomery's Smart Flood &amp; Weather Guardian</div>
    </div>
    <hr style="border-color:#1e293b; margin:6px 0;">
    """, unsafe_allow_html=True)

    # ── Refresh Interval ─────────────────────────────────────────────────────
    refresh_label = st.selectbox(
        "🔄 Refresh Interval",
        options=list(REFRESH_OPTIONS.keys()),
        index=2,
        label_visibility="visible",
    )
    refresh_seconds = REFRESH_OPTIONS[refresh_label]
    st.session_state["refresh_interval"] = refresh_seconds

    st.markdown('<hr style="border-color:#1e293b; margin:6px 0;">', unsafe_allow_html=True)

    # ── Simulation Mode ──────────────────────────────────────────────────────
    st.markdown('<div style="font-size:11px; font-weight:700; margin-bottom:3px;">🕹️ Simulation Mode</div>',
                unsafe_allow_html=True)
    sim_mode_val = st.selectbox(
        "Simulation Mode",
        options=["Live Data", "Moderate Rain", "Heavy Rain", "Flood Situation"],
        index=0,
        label_visibility="collapsed",
        key="sim_mode"
    )

    st.markdown('<hr style="border-color:#1e293b; margin:6px 0;">', unsafe_allow_html=True)

    # ── Address Lookup ───────────────────────────────────────────────────────
    st.markdown('<div style="font-size:11px; font-weight:700; margin-bottom:3px;">📍 Address Lookup</div>',
                unsafe_allow_html=True)

    address = st.text_input(
        "Address",
        label_visibility="collapsed",
        placeholder="123 Main St, Montgomery AL",
        key="address_input",
        help="Type an address in Montgomery, AL for flood risk and weather",
    )

    st.markdown("""
    <div style="font-size:9px; color:#64748b; margin-top:-4px; margin-bottom:4px;">
        Examples: <i>101 S Lawrence St</i>, <i>Montgomery Zoo</i>, <i>Maxwell AFB</i>
    </div>
    """, unsafe_allow_html=True)

    if address:
        if "last_address" not in st.session_state or st.session_state["last_address"] != address:
            with st.spinner("📍 Looking up..."):
                try:
                    resp = httpx.post(
                        f"{BACKEND_URL}/api/geodata/lookup",
                        json={"address": address}, timeout=12
                    )
                    if resp.status_code == 200:
                        res = resp.json()
                        if "error" not in res:
                            st.session_state["lookup_result"] = res
                            st.session_state["last_address"] = address
                        else:
                            st.error(res["error"])
                    else:
                        st.error("Lookup service unavailable")
                except Exception:
                    st.error("Lookup timed out. Try again.")

    # ── FIXED POSITION SLOTS (Absolute protection against Streamlit DOM bugs) ──
    button_slot = st.empty()
    content_slot = st.empty()

    # ── Clear button uses on_click callback — fires BEFORE next render ───────
    has_result = (
        "lookup_result" in st.session_state
        and st.session_state["lookup_result"] is not None
    )
    if has_result:
        button_slot.button(
            "🧹 Clear",
            key="clear_lookup_btn",
            help="Resets address input, removes map marker, clears the risk report",
            on_click=_clear_lookup,
        )
    else:
        # Explicitly clear the button slot if there's no result
        button_slot.empty()

    # ── Combine bottom elements into a SINGLE markdown block ────────
    sidebar_html = ""

    if has_result:
        res = st.session_state["lookup_result"]
        zone = res.get("fema_zone", {})
        weather = res.get("weather", {})
        sidebar_html += f"""
        <div style="background:rgba(34,211,238,0.1); border:1px solid #22d3ee;
                    border-radius:12px; padding:12px; margin-top:6px; backdrop-filter:blur(4px);">
            <div style="font-size:11px; font-weight:800; color:#22d3ee; margin-bottom:6px; letter-spacing:0.5px;">⭐ LOCAL RISK REPORT</div>
            <div style="font-size:10px; color:#f1f5f9; margin-bottom:8px; line-height:1.4;">{res.get('address')}</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="font-size:10px; color:#94a3b8;">FEMA Zone</span>
                <span style="font-size:10px; font-weight:700; color:#facc15;">{zone.get('zone')} ({zone.get('risk_level')} Risk)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="font-size:10px; color:#94a3b8;">Forecast</span>
                <span style="font-size:10px; font-weight:700; color:#f8fafc;">{weather.get('summary')}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span style="font-size:10px; color:#94a3b8;">Rain Rate</span>
                <span style="font-size:10px; font-weight:700; color:#34d399;">{weather.get('local_precip_mm', 0)} mm</span>
            </div>
        </div>
        """

    # Model / Health status
    sidebar_html += '<hr style="border-color:#1e293b; margin:6px 0;">'
    health_data = fetch_json(f"{BACKEND_URL}/health") or {}
    model_ok = health_data.get("model_loaded", False)
    cache_age = health_data.get("cache_age_seconds", 0)
    status_color = "#22c55e" if model_ok else "#f59e0b"
    status_label = "✅ Model loaded" if model_ok else "⚠️ Synthetic mode"
    
    sidebar_html += f"""
    <div style="padding:10px 12px; background:rgba(15,23,42,0.6); border-radius:12px; border:1px solid #1e293b; margin-top:8px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <span style="font-size:10px; color:{status_color}; font-weight:700;">{status_label}</span>
            <span style="font-size:9px; color:#64748b;">Cache: {cache_age}s</span>
        </div>
        <div style="font-size:9px; color:#475569; letter-spacing:0.5px;">SYNC: {datetime.now(timezone.utc).strftime("%H:%M:%S")} UTC</div>
    </div>
    """

    # Always write into the fixed slot
    content_slot.markdown(sidebar_html, unsafe_allow_html=True)


# ── Page Header ────────────────────────────────────────────────────────────

sensor, history, forecast, alert, alert_hist, geo, ema, calls, health = fetch_all_data()

# ── Apply Simulation Overrides ──────────────────────────────────────────────
sim_mode = st.session_state.get("sim_mode", "Live Data")
if sim_mode != "Live Data":
    from datetime import datetime, timezone, timedelta
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()
    
    if sim_mode == "Moderate Rain":
        alert = {"level": "YELLOW", "alert_text": "Montgomery River level is normal but rising slowly. Expect runoff from moderate rain.", "predicted_level_ft": 145.9, "rate_of_rise_ft_per_15m": 0.2}
        sensor = {"water_level_ft": 145.5, "rate_of_rise_ft_per_15m": 0.2, "timestamp": now_iso, "discharge_cfs": 4500}
        forecast = {"current": {"precip_mm": 15.0, "summary": "Moderate Rain", "temp_c": 19.5}, "hourly": forecast.get("hourly", [])}
        alert_hist = [{"level": "YELLOW", "predicted_level_ft": 145.5, "rate_of_rise_ft_per_15m": 0.2, "generated_at": now_iso}] + alert_hist[:4]
        ema = [{"title": "Weather Advisory", "body": "Moderate rainfall expected throughout the day. Minor ponding on roads possible."}]
        calls = [{"district": "North", "incident_type": "Traffic Hazard", "count": 1}]
        
    elif sim_mode == "Heavy Rain":
        alert = {"level": "YELLOW", "alert_text": "Heavy rain in effect. Rising river levels and localized street flooding expected.", "predicted_level_ft": 149.1, "rate_of_rise_ft_per_15m": 0.8}
        sensor = {"water_level_ft": 147.5, "rate_of_rise_ft_per_15m": 0.8, "timestamp": now_iso, "discharge_cfs": 18500}
        forecast = {"current": {"precip_mm": 45.0, "summary": "Heavy Rain", "temp_c": 18.0}, "hourly": forecast.get("hourly", [])}
        alert_hist = [{"level": "YELLOW", "predicted_level_ft": 147.5, "rate_of_rise_ft_per_15m": 0.8, "generated_at": now_iso}] + alert_hist[:4]
        ema = [{"title": "Flash Flood Watch", "body": "A flash flood watch is in effect for Montgomery county until 8 PM."}]
        calls = [{"district": "Downtown", "incident_type": "Water Rescue", "count": 2}, {"district": "East", "incident_type": "Flooded Roadway", "count": 3}]
        
    elif sim_mode == "Flood Situation":
        alert = {"level": "RED", "alert_text": "CRITICAL: Major river flooding identified. Evacuation warnings in effect for low-lying areas.", "predicted_level_ft": 155.0, "rate_of_rise_ft_per_15m": 1.5}
        sensor = {"water_level_ft": 152.0, "rate_of_rise_ft_per_15m": 1.5, "timestamp": now_iso, "discharge_cfs": 65000}
        forecast = {"current": {"precip_mm": 80.0, "summary": "Torrential Downpours", "temp_c": 17.5}, "hourly": forecast.get("hourly", [])}
        alert_hist = [{"level": "RED", "predicted_level_ft": 152.0, "rate_of_rise_ft_per_15m": 1.5, "generated_at": now_iso}] + alert_hist[:4]
        ema = [{"title": "Flash Flood Warning", "body": "Flash flood warning for Montgomery. Seek higher ground immediately."}]
        calls = [
            {"district": "North", "incident_type": "Water Rescue", "count": 15},
            {"district": "Downtown", "incident_type": "Flooded Roadway", "count": 12},
            {"district": "South", "incident_type": "Evacuation", "count": 7}
        ]
        
    # Generate realistic historical chart data sloping upwards to current level
    history = [
        {
            "timestamp": (now_utc - timedelta(minutes=15 * i)).isoformat(), 
            "water_level_ft": round(sensor["water_level_ft"] - (i * sensor["rate_of_rise_ft_per_15m"]), 2)
        } 
        for i in range(16)
    ]

lookup_pnt = st.session_state.get("lookup_result")

level = alert.get("level", "GREEN")
level_emoji = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}.get(level, "🟢")

header_col, toggle_col = st.columns([0.80, 0.20], vertical_alignment="center")

with header_col:
    st.markdown(f"""
    <div class="main-header" style="display:flex; align-items:center; justify-content:space-between;">
        <div style="display:flex; align-items:center; gap:20px;">
            <div style="font-size:54px; filter: drop-shadow(0 0 10px rgba(96, 165, 250, 0.5));">🛡️</div>
            <div>
                <div style="display:flex; align-items:center; gap:12px;">
                    <span class="header-title">StormShield AI</span>
                    <span class="live-badge">● LIVE</span>
                </div>
                <div class="header-sub">Montgomery's Smart Flood & Weather Guardian</div>
            </div>
        </div>
        <div style="text-align:right; background:rgba(15,23,42,0.4); padding:10px 18px; border-radius:12px; border:1px solid rgba(255,255,255,0.05);">
            <div style="font-size:12px; font-weight:800; color:#facc15; letter-spacing:1px;">{level} STATUS</div>
            <div style="font-size:10px; color:#64748b; margin-top:2px;">{datetime.now(timezone.utc).strftime("%b %d, %H:%M:%S")} UTC</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with toggle_col:
    # Flex container to align everything top-right
    st.markdown("""
    <style>
    /* target the standard toggle widget to force it right */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stHorizontalBlock"] {
        align-items: flex-start !important;
    }
    .top-right-panel {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        justify-content: center;
        gap: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    is_light = st.session_state["theme"] == "light"
    mode_label = "☀️ Light Mode" if is_light else "🌙 Dark Mode"
    
    st.markdown('<div class="top-right-panel">', unsafe_allow_html=True)
    st.toggle(mode_label, key="theme_toggle", value=is_light, on_change=toggle_theme)
    
    st.markdown(f"""
        <div style="text-align: center; line-height: 1.1; margin-right: 20px;">
            <div style="font-size:24px;">{level_emoji}</div>
            <div style="font-size:11px; color:#64748b; font-weight:bold; margin-top: 3px;">{level} ALERT</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"<hr style='margin-top: 0; margin-bottom: 16px; border-color: {border_color}; border-width: 1px 0 0 0; font-weight: bold;'>", unsafe_allow_html=True)


tab1, tab2, tab3, tab4 = st.tabs(["🗺️ **Live Dashboard**", "📋 **Situation Report**", "💬 **Ask StormShield AI**", "🌤️ **Weather & Rainfall Analysis**"])


# ════════════════════════════════════════════════════════════
# TAB 1 — LIVE DASHBOARD
# ════════════════════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns([2, 1], gap="large")

    # LEFT COLUMN — Map + Chart
    with col1:
        st.markdown("##### 🗺️ Montgomery Flood Zone Map")
        render_map(geo, ema, calls, highlight_point=lookup_pnt)

        st.markdown("##### 📈 Water Level History & Forecast")
        render_gauge_chart(history, forecast)

    # RIGHT COLUMN — Alert + Confidence + Simulation
    with col2:
        st.markdown("##### ⚠️ Current Alert Status")
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
            st.metric("**💧 Water Level**", f"{wl:.2f} ft")
            st.metric("**📉 Rate of Rise**", f"{ror:+.3f} ft/15m")
        with m2:
            st.metric("**🌊 Discharge**", f"{dis:.0f} cfs")
            st.metric("**🔮 Predicted (T+30)**", f"{pred:.2f} ft")

        st.markdown("---")
        render_simulation_panel(BACKEND_URL, alert)


# ════════════════════════════════════════════════════════════
# TAB 2 — SITUATION REPORT
# ════════════════════════════════════════════════════════════
with tab2:
    st.markdown("##### 📋 Alert History (last 20 records)")

    # Header styling
    # st.markdown("""
    # <style>
    # [data-testid="stDataFrame"] thead th {
    #     text-align: center !important;
    #     font-weight: 700 !important;
    # }
    # [data-testid="stDataFrame"] td {
    #     text-align: left !important;
    # }
    # </style>
    # """, unsafe_allow_html=True)

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
    st.markdown("##### 📢 Current Alert Bulletin")
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
    st.markdown("##### 🌩️ Active NWS Alerts")
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
    st.markdown("##### 💬 Ask StormShield AI")
    render_query_panel(BACKEND_URL)


# ════════════════════════════════════════════════════════════
# TAB 4 — WEATHER & RAINFALL
# ════════════════════════════════════════════════════════════
with tab4:
    render_weather_panel()

# ── Auto-rerun loop ────────────────────────────────────────────────────────
refresh = st.session_state.get("refresh_interval", 60)
from streamlit_autorefresh import st_autorefresh
# st_autorefresh runs non-blocking, so the script finishes instantly and the 
# browser triggers the rerun. This prevents the "greyed out" stale element bug.
st_autorefresh(interval=refresh * 1000, key="data_refresh")

