"""
Plotly time-series gauge level chart.
Shows actual water level history + T+30 prediction + flood-stage line.
"""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime


def render_gauge_chart(
    history: list[dict],
    forecast: dict | None,
    flood_stage_ft: float = 8.0,
) -> None:
    """Render the Plotly scatter chart with actual, predicted, and threshold lines."""
    if not history:
        st.info("No sensor history available yet.")
        return

    timestamps = [h.get("timestamp") for h in history]
    levels = [h.get("water_level_ft", 0) for h in history]

    fig = go.Figure()

    # Actual water level line
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=levels,
        mode="lines",
        name="Actual Level",
        line=dict(color="#3b82f6", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.08)",
        hovertemplate="%{x}<br>%{y:.2f} ft<extra>Actual</extra>",
    ))

    # Predicted T+30 point
    if forecast:
        pred_time = forecast.get("estimated_crest_iso")
        pred_level = forecast.get("predicted_level_ft", 0)
        conf = forecast.get("confidence_score", 0.8)
        error_bar = round((1 - conf) * pred_level * 0.15, 3)

        fig.add_trace(go.Scatter(
            x=[pred_time],
            y=[pred_level],
            mode="markers",
            name="T+30 Prediction",
            marker=dict(
                color="#f97316",
                size=14,
                symbol="diamond",
                line=dict(color="#fff", width=2),
            ),
            error_y=dict(
                type="data",
                array=[error_bar],
                arrayminus=[error_bar],
                color="#f97316",
                thickness=2,
            ),
            hovertemplate=f"T+30 Prediction<br>%{{y:.2f}} ft ±{error_bar:.2f} ft<extra></extra>",
        ))

    # Flood stage threshold line
    if timestamps:
        fig.add_hline(
            y=flood_stage_ft,
            line=dict(color="#ef4444", dash="dash", width=1.5),
            annotation_text=f"Flood Stage ({flood_stage_ft} ft)",
            annotation_position="top right",
            annotation_font=dict(color="#ef4444", size=11),
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,12,30,0.6)",
        font=dict(color="#e2e8f0", family="Inter, sans-serif", size=12),
        margin=dict(l=0, r=0, t=30, b=0),
        height=280,
        xaxis=dict(
            title="Time",
            gridcolor="rgba(255,255,255,0.06)",
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="Water Level (ft)",
            gridcolor="rgba(255,255,255,0.06)",
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
