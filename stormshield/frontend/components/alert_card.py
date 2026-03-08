"""
RED / YELLOW / GREEN alert card widget.
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime

LEVEL_CONFIG = {
    "RED": {
        "emoji": "🔴",
        "label": "FLOOD WARNING",
        "bg": "linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)",
        "border": "#ef4444",
        "text": "#fecaca",
        "badge_bg": "#ef4444",
    },
    "YELLOW": {
        "emoji": "🟡",
        "label": "FLOOD WATCH",
        "bg": "linear-gradient(135deg, #451a03 0%, #78350f 100%)",
        "border": "#f59e0b",
        "text": "#fef3c7",
        "badge_bg": "#f59e0b",
    },
    "GREEN": {
        "emoji": "🟢",
        "label": "ALL CLEAR",
        "bg": "linear-gradient(135deg, #052e16 0%, #14532d 100%)",
        "border": "#22c55e",
        "text": "#bbf7d0",
        "badge_bg": "#22c55e",
    },
}


def render_alert_card(alert: dict, forecast: dict | None) -> None:
    """Render the colour-coded alert card with LLM-generated text."""
    level = alert.get("level", "GREEN")
    cfg = LEVEL_CONFIG.get(level, LEVEL_CONFIG["GREEN"])
    pred_ft = alert.get("predicted_level_ft", 0.0)
    ror = alert.get("rate_of_rise_ft_per_15m", 0.0)
    alert_text = alert.get("alert_text", "Monitoring conditions…")
    gen_at = alert.get("generated_at", "")

    card_html = f"""
    <div style="
        background: {cfg['bg']};
        border: 1.2px solid {cfg['border']};
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 6px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    ">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
            <span style="font-size:18px;">{cfg['emoji']}</span>
            <div>
                <div style="font-size:13px; font-weight:700; color:{cfg['border']}; letter-spacing:0.3px; line-height:1.2;">
                    {cfg['label']}
                </div>
                <div style="font-size:10px; color:#94a3b8; margin-top:0px;">
                    Level: {level}
                </div>
            </div>
        </div>
        <div style="display:flex; gap:12px; margin-bottom:8px; justify-content:center; align-items:center;">
            <div style="text-align:center;">
                <div style="font-size:20px; font-weight:800; color:{cfg['border']};">{pred_ft:.2f} ft</div>
                <div style="font-size:9px; color:#94a3b8;">Predicted T+30</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:20px; font-weight:800; color:{cfg['text']};">{ror:+.3f}</div>
                <div style="font-size:9px; color:#94a3b8;">ft / 15 min</div>
            </div>
        </div>
        <div style="
            background: rgba(0,0,0,0.25);
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 11.5px;
            color: {cfg['text']};
            line-height: 1.4;
            font-style: italic;
        ">
            {alert_text}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    if forecast:
        conf = forecast.get("confidence_score", 0)
        mv = forecast.get("model_version", "2.0")
        st.caption(f"Model: `{mv}` · Confidence: {conf*100:.0f}% · Updated: {gen_at[:19] if gen_at else '—'} UTC")
