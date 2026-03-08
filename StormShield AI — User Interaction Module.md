# StormShield AI — User Interaction Modules

This document defines the core user-driven interactions within the StormShield AI ecosystem, formatted to enable independent module implementation.

---

## 1. Spatial Risk Lookup
**User Action**: Types a street address into the sidebar input field and presses `Enter`.
**System Response**: A spinner appears while the system geocodes the address, performs an spatial search, and then renders a "Local Risk Report" card showing FEMA zone type, local rainfall intensity, and risk level (High/Moderate/Low). The map automatically zooms to the resulting location with a marker.
**Module Name**: `AddressLookupComponent`
**Dependencies**: `httpx` (API call), `Folium` (Map markers), `Shapely` (Backend STRtree).
**State Changes**: Updates `st.session_state["lookup_result"]` with geocoordinates and risk metadata.

## 2. Dynamic Theme Switching
**User Action**: Clicks the "Light Mode" or "Dark Mode" toggle in the top-right header.
**System Response**: The entire dashboard background, text colors, and glassmorphic blurs transition immediately without refreshing the core data state.
**Module Name**: `ThemeController`
**Dependencies**: Custom CSS injection block (`st.markdown`), `st.session_state["theme"]`.
**State Changes**: `st.session_state["theme"]` toggles between `"dark"` and `"light"`.

## 3. Hydrological Impact Simulation
**User Action**: Drags the "Add Trees to Watershed" slider in the sidebar or Simulation Panel.
**System Response**: Triggers a non-blocking `POST` request. The "Peak Reduction" and "Runoff" metrics update in real-time to show the estimated percentage reduction in flood crest height based on green infrastructure.
**Module Name**: `SimulationPanel`
**Dependencies**: FastAPI Endpoint `/api/simulation/green`, `httpx`.
**State Changes**: Updates component-local response data; no global state side effects.

## 4. RAG-Powered Safety Chat
**User Action**: Types a question about current conditions (e.g., "Is it safe to drive near Sligo Creek?") into the `st.chat_input` field in the "Ask StormShield AI" tab.
**System Response**: A chat history bubble appears for the user. A spinner indicates the LLM is processing. The system returns a conversational answer grounded in real-time sensor data, followed by a "timestamp: grounded at..." caption.
**Module Name**: `ChatQueryModule`
**Dependencies**: FastAPI Endpoint `/api/query`, Google Gemini 2.0 Flash SDK, `st.chat_message`.
**State Changes**: Appends new Q&A pairs to `st.session_state["query_history"]` (limited to last 5 entries).

## 5. Scenario Stress-Testing
**User Action**: Selects a scenario from the "Simulation Mode" dropdown (e.g., "Flood Situation").
**System Response**: The UI immediately overrides live API data with extreme synthetic values (e.g., 150+ ft water level, RED alert status). The map highlights potential floodways and the Gemini alert text regenerates with critical evacuation advice.
**Module Name**: `ScenarioManager`
**Dependencies**: Frontend dictionary overrides in `app.py`.
**State Changes**: `st.session_state["sim_mode"]` resets current local `sensor`, `alert`, and `forecast` variables for the rendering cycle.

## 6. Real-Time Synchronization Control
**User Action**: Selects a refresh frequency (30s / 1m / 5m) from the sidebar selectbox.
**System Response**: The browser-level `st_autorefresh` timer interval is updated.
**Module Name**: `SyncController`
**Dependencies**: `streamlit-autorefresh` library.
**State Changes**: `st.session_state["refresh_interval"]` updates, defining the next trigger for the `st.rerun()` loop.

## 7. Interactive Geospatial Exploration
**User Action**: Hovers over or clicks on a shaded polygon in the Folium map.
**System Response**: A floating tooltip (on hover) or persistent popup (on click) appears showing the FEMA Zone ID (e.g., "Zone AE"), Special Flood Hazard Area (SFHA) status, and specific area name.
**Module Name**: `FloodMapRenderer`
**Dependencies**: `folium.GeoJson`, `streamlit-folium`, FEMA GeoJSON cache.
**State Changes**: None (Stateless visual feedback).

## 8. Time-Series Trend Analysis
**User Action**: Hovers over the data points in the water level history chart.
**System Response**: Plotly crosshairs appear, showing the high-precision water level in feet and the corresponding timestamp for both historical readings and future predictions.
**Module Name**: `GaugeHistoryChart`
**Dependencies**: `Plotly.graph_objects`, `Pandas` (for time-axis formatting).
**State Changes**: None (Stateless visual feedback).
