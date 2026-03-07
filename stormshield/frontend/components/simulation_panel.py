"""
Green infrastructure simulation panel.
Tree-slider → POST /api/simulation/green → peak reduction display.
"""
from __future__ import annotations

import httpx
import streamlit as st


def render_simulation_panel(backend_url: str, alert: dict | None = None) -> None:
    """Interactive tree-addition slider with live peak reduction calculation."""
    st.markdown("""
    <div style="font-size:13px; color:#94a3b8; margin-bottom:8px; letter-spacing:0.3px;">
        🌳 <b style="color:#4ade80;">GREEN INFRASTRUCTURE SIMULATOR</b>
    </div>
    """, unsafe_allow_html=True)

    trees = st.slider(
        "Add Trees to Watershed",
        min_value=0,
        max_value=500,
        step=10,
        value=100,
        help="Estimate how adding trees reduces peak flood levels",
        key="tree_slider",
    )

    # Determine base runoff from current rainfall or default
    base_runoff = 25.0  # mm default
    if alert and alert.get("level") == "RED":
        base_runoff = 60.0
    elif alert and alert.get("level") == "YELLOW":
        base_runoff = 35.0

    try:
        resp = httpx.post(
            f"{backend_url}/api/simulation/green",
            json={"trees_added": trees, "base_runoff_mm": base_runoff},
            timeout=5,
        )
        resp.raise_for_status()
        result = resp.json()

        peak_red = result.get("peak_level_reduction_ft", 0)
        runoff_pct = result.get("runoff_reduction_pct", 0)
        new_runoff = result.get("new_runoff_mm", base_runoff)
        display_msg = result.get("display_message", "")

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Peak Reduction",
                f"{peak_red:.3f} ft",
                delta=f"-{runoff_pct:.2f}% runoff",
                delta_color="inverse",
            )
        with col2:
            st.metric(
                "Runoff After Trees",
                f"{new_runoff:.1f} mm",
                delta=f"from {base_runoff:.0f} mm",
                delta_color="inverse",
            )
            
        if display_msg:
            st.info(display_msg)


        # Visual bar
        efficacy = min(peak_red / 0.5, 1.0)  # normalise to max 0.5 ft
        bar_html = f"""
        <div style="margin-top:6px;">
            <div style="font-size:11px; color:#64748b; margin-bottom:3px;">Flood Mitigation Efficacy</div>
            <div style="background:#1e293b; border-radius:4px; height:6px; overflow:hidden;">
                <div style="background:linear-gradient(90deg,#4ade8088,#4ade80);
                    width:{efficacy*100:.1f}%; height:100%; border-radius:4px;"></div>
            </div>
        </div>
        """
        st.markdown(bar_html, unsafe_allow_html=True)

    except Exception as exc:
        st.warning(f"Simulation unavailable: {exc}")
