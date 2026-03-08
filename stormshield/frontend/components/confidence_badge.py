"""
Confidence score display component.
Renders a progress bar + percentage badge for the model's confidence.
"""
from __future__ import annotations

import streamlit as st


def render_confidence_badge(confidence_score: float) -> None:
    """Show model confidence as a styled progress bar and caption."""
    pct = int(confidence_score * 100)

    if confidence_score >= 0.80:
        color = "#22c55e"
        label = "High"
    elif confidence_score >= 0.60:
        color = "#f59e0b"
        label = "Moderate"
    else:
        color = "#ef4444"
        label = "Low"

    is_light = st.session_state.get("theme", "dark") == "light"
    text_color = "#000000" if is_light else "#ffffff"

    badge_html = f"""
    <div style="margin: 4px 0 6px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
            <span style="font-size:10.5px; color:{text_color}; font-weight:800; letter-spacing:0.3px;">
                SYSTEM CONFIDENCE SCORE
            </span>
            <span style="
                background:{color};
                color:#000;
                font-size:10px;
                font-weight:700;
                padding:1px 6px;
                border-radius:10px;
            ">{label} · {pct}%</span>
        </div>
        <div style="background:#1e293b; border-radius:4px; height:6px; overflow:hidden;">
            <div style="
                background: linear-gradient(90deg, {color}88, {color});
                width:{pct}%;
                height:100%;
                border-radius:4px;
                transition: width 0.5s ease;
            "></div>
        </div>
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)
