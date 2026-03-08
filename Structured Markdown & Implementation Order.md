# StormShield AI — Montgomery's Smart Flood & Weather Guardian

## Overview
StormShield AI is a distributed flood prediction and civic alert architecture consisting of a FastAPI backend and a Streamlit frontend. The system implements a real-time data ingestion pipeline that polls USGS stream gauges and NOAA weather forecasts, applies rolling-window smoothing and Z-score outlier filtering via SciPy, and generates water level predictions for T+30 minutes using a trained XGBoost regressor. Alert metadata is processed by Google Gemini 2.0 Flash to generate plain-language advisory text, while a custom RAG (Retrieval-Augmented Generation) engine handles grounded user queries. The frontend provides a high-fidelity dashboard featuring dual-theme glassmorphism (Midnight Nimbus/Coastal Mist), STRtree-based spatial risk lookups, and a multi-scenario simulation engine for stress-testing flood response.

## Tech Stack

### Backend
The backend is built with Python 3.11+ and FastAPI 0.115.x, providing a high-performance asynchronous REST API.
```python
# Core Infrastructure
fastapi==0.115.6                # REST API framework
uvicorn[standard]==0.34.0       # ASGI server
apscheduler==3.11.0             # Background polling jobs
pydantic==2.10.5                # Schema validation
pydantic-settings==2.7.1        # Env-driven configuration

# Data Science & ML
xgboost==2.1.3                  # Flood level regression
scikit-learn==1.6.1             # Preprocessing & model serialization
pandas==2.2.3                   # Time-series operations
numpy==2.2.1                    # Numerical stats
scipy==1.15.1                   # Z-score outlier detection
joblib==1.4.2                   # Model persistence

# AI & Ingestion
google-generativeai==0.8.4      # Gemini 2.0 Flash SDK
httpx==0.28.1                   # Async HTTP client
beautifulsoup4==4.12.3          # HTML scraping (EMA alerts)
feedparser==6.0.11              # RSS parsing (NWS alerts)
selenium==4.x                   # Browser automation (Bright Data proxy)

# Spatial Geoprocessing
shapely==2.0.6                  # STRtree spatial indexing
geopy==2.4.1                    # Geocoding utilities
```

### Frontend
The frontend uses Streamlit 1.41.x with a custom glassmorphic design system.
```python
streamlit==1.41.1               # Dashboard framework
streamlit-folium==0.26.2        # Folium/Leaflet bridge
folium==0.19.4                  # Map generation
plotly==5.24.1                  # Interactive charts
streamlit-autorefresh==latest   # Non-blocking sync
```

## File Structure
```text
stormshield/
├── .env                     # API keys (GEMINI, BRIGHTDATA, etc.)
├── README.md                # Project setup and developer docs.
├── requirements.txt         # Core dependency list.
├── requirements-dev.txt     # Test and linting tools (pytest, ruff).
├── backend/
│   ├── main.py              # Application lifecycle and router mounting.
│   ├── config.py            # Pydantic BaseSettings-driven configuration.
│   ├── scheduler.py         # APScheduler job definitions and registry.
│   ├── modules/
│   │   ├── alert/           # Threshold evaluators and Gemini text generation.
│   │   ├── cache/           # In-memory + JSON file fallback manager.
│   │   ├── ingestion/       # USGS, NOAA, NWS, and BrightData clients.
│   │   ├── prediction/      # XGBoost model loading, inference, and training.
│   │   ├── processing/      # Smoothing, Z-score filtering, feature engineering.
│   │   ├── query/           # RAG engine for grounded LLM responses.
│   │   └── simulation/      # Hydrological runoff reduction calculators.
│   ├── routers/             # FastAPI endpoint definitions (RESTful).
│   └── data/                # Local cache: flood_zones.json, ema_alerts.json.
├── frontend/
│   ├── app.py               # Theme logic, layout, and tab orchestration.
│   ├── config.py            # Frontend constants (BACKEND_URL, REFRESH_OPTIONS).
│   └── components/          # Modular UI widgets (Map, Charts, Chat, Weather).
```

## Functional Modules

### Module 1: Data Ingestion & Signal Processing
The system uses `APScheduler` to poll USGS and NOAA APIs every 5-15 minutes. Raw stream gauge data is processed through a dual-stage filter: a 15-minute rolling mean to reduce noise, followed by a Z-score outlier filter to drop physically impossible spikes (deltas > 2.0 ft).

### Module 2: Flood Prediction Engine
The prediction pipeline constructs a 9-dimensional feature vector containing historical water levels, discharge rates, and rainfall proxies. This vector is fed into an XGBoost regressor to predict values at T+30 minutes. A confidence score is derived by comparing model residual variance against a baseline.

### Module 3: Advisory & Query Systems (LLM)
Alert levels are evaluated against Montgomery's flood stage thresholds. If a threat is detected, the system uses Gemini 2.0 Flash to generate a plain-language alert. The system also includes a RAG-powered query engine that grounding user questions in the latest sensor and spatial data context.

### Module 4: Spatial Analytics (Address Lookup)
Users can input any address in Montgomery to receive a localized risk report. The backend geocodes the address and performs a high-speed point-in-polygon search using a `Shapely.STRtree` index over FEMA GeoJSON features.

## Data Models

### Sensor and Forecast Schemas
```python
class SensorReading(BaseModel):
    timestamp: datetime
    water_level_ft: float
    discharge_cfs: float

class RainfallForecast(BaseModel):
    timestamp: datetime
    precipitation_mm: float
    wind_speed_mph: float

class PredictionResult(BaseModel):
    predicted_level_ft: float
    estimated_crest_iso: datetime
    confidence_score: float         # 0.0 – 1.0 logic
```

### Alert and Query Schemas
```python
class AlertStatus(BaseModel):
    level: Literal["RED", "YELLOW", "GREEN"]
    predicted_level_ft: float
    rate_of_rise_ft_per_15m: float
    alert_text: str                 # LLM-generated string
    generated_at: datetime

class QueryResponse(BaseModel):
    question: str
    answer: str
    grounded_at: datetime           # Context snapshot timestamp
```

## UI Components

### Dashboard Layout
The Dashboard is built as a responsive 4-tab interface with dual-theme support (Dark/Light mode).
- **Tab 1: Live Dashboard**: Integrated Folium map with FEMA polygons and Plotly dual-axis charts showing actual vs predicted trends.
- **Tab 2: Situation Report**: A data-dense filterable table showing historical alert cycles and the full text of latest advisories.
- **Tab 3: Ask StormShield AI**: A RAG-powered chat interface using Streamlit's native `st.chat_message` components.
- **Tab 4: Weather Analysis**: Detailed weather breakdown using Open-Meteo data, focusing on precipitation probability and temperature trends.

### Theme & Interaction
The application implements a unique glassmorphic injection system for themes.
- **Midnight Nimbus**: A deep navy/black theme with electric cyan metrics.
- **Coastal Mist**: A high-contrast light theme using soft azure gradients.
- **Simulation Sidebar**: Allows users to stress-test the UI by injecting "Moderate", "High", or "Flood" scenarios.

## Constraints and Out of Scope
The system relies on a local JSON file cache system instead of a persistent external database to minimize latency and hosting costs for the hackathon MVP. Map rendering is strictly limited to Folium/Leaflet.js to avoid Mapbox or Google Maps licensing fees. Direct ArcGIS REST API calls are excluded; all spatial data must pass through the Bright Data scraper or the local GeoJSON cache. Real-time SMS notifications and user authentication are currently out of scope.

## Implementation Order

### Phase 1: Core Foundation & Configuration
1. Build `config.py` (Backend/Frontend) to handle `.env` loading.
2. Implement `backend/modules/cache/store.py` for the TTL-based in-memory and JSON storage.

### Phase 2: Ingestion & Processing
1. Implement USGS and NOAA clients using `httpx`.
2. Build `smoother.py` and `feature_builder.py` for signal conditioning.
3. Configure `scheduler.py` to orchestrate background data pulls.

### Phase 3: Prediction & Alert Logic
1. Load and wrap the XGBoost model in `modules/prediction/model.py`.
2. Implement threshold evaluation logic in `modules/alert/engine.py`.
3. Build the Gemini 2.0 Flash alert generator.

### Phase 4: Spatial & Query Engines
1. Build the STRtree lookup engine in `routers/geodata.py`.
2. Implement the RAG system in `modules/query/query_engine.py`.

### Phase 5: UI Construction
1. Create frontend components (`map_view.py`, `gauge_chart.py`, `query_panel.py`) in isolation.
2. Assemble the final `app.py` with tab-based navigation and the auto-refresh loop.
