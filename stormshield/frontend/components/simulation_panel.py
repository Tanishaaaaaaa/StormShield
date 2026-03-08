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
    <div style="font-size:11px; color:#94a3b8; margin-bottom:4px; letter-spacing:0.2px;">
        🌳 <b style="color:#4ade80;">GREEN SIMULATOR</b>
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
                delta=f"-{runoff_pct:.1f}%",
                delta_color="inverse",
            )
        with col2:
            st.metric(
                "Runoff",
                f"{new_runoff:.1f} mm",
                delta=f"from {base_runoff:.0f}",
                delta_color="inverse",
            )
            
        if display_msg:
            is_dark = st.session_state.get("theme", "dark") == "dark"
            msg_bg = "rgba(59,130,246,0.15)" if is_dark else "rgba(59,130,246,0.1)"
            msg_border = "rgba(59,130,246,0.3)" if is_dark else "rgba(59,130,246,0.2)"
            msg_text = "#ffffff" if is_dark else "#1e3a8a"
            
            st.markdown(f"""
            <div style="background:{msg_bg}; border:1px solid {msg_border}; 
                        border-radius:8px; padding:8px 12px; margin-top:8px; 
                        color:{msg_text}; font-size:12px; line-height:1.4;">
                ℹ️ {display_msg}
            </div>
            """, unsafe_allow_html=True)


        # Visual bar
        efficacy = min(peak_red / 0.5, 1.0)
        bar_html = f"""
        <div style="margin-top:3px;">
            <div style="background:#1e293b; border-radius:3px; height:4px; overflow:hidden;">
                <div style="background:linear-gradient(90deg,#4ade8088,#4ade80);
                    width:{efficacy*100:.1f}%; height:100%; border-radius:3px;"></div>
            </div>
        </div>
        """
        st.markdown(bar_html, unsafe_allow_html=True)

    except Exception as exc:
        st.warning(f"Simulation unavailable: {exc}")
