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

    badge_html = f"""
    <div style="margin: 6px 0 10px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <span style="font-size:12px; color:#94a3b8; font-weight:600; letter-spacing:0.5px;">
                SYSTEM CONFIDENCE SCORE
            </span>
            <span style="
                background:{color};
                color:#000;
                font-size:11px;
                font-weight:700;
                padding:2px 8px;
                border-radius:20px;
            ">{label} · {pct}%</span>
        </div>
        <div style="background:#1e293b; border-radius:6px; height:8px; overflow:hidden; margin-bottom:4px;">
            <div style="
                background: linear-gradient(90deg, {color}88, {color});
                width:{pct}%;
                height:100%;
                border-radius:6px;
                transition: width 0.5s ease;
            "></div>
        </div>
        <div style="font-size:10px; color:#64748b; line-height:1.4;">
            <b>Based on:</b><br/>
            • Model residual variance<br/>
            • Trend consistency
        </div>
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)
