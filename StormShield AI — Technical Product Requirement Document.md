# StormShield AI — Montgomery's Smart Flood & Weather Guardian | Technical Product Requirements Document
**Version**: 2.1 | **Audience**: Developers & AI Code Editors | **Stack**: Python / Streamlit / FastAPI / XGBoost

## 1. Project Overview
StormShield AI is a distributed flood prediction and civic alert architecture consisting of a FastAPI backend and a Streamlit frontend. The system implements a real-time data ingestion pipeline that polls USGS stream gauges and NOAA weather forecasts, applies rolling-window smoothing and Z-score outlier filtering via SciPy, and generates water level predictions for T+30 minutes using a trained XGBoost regressor. Alert metadata is processed by Google Gemini 2.0 Flash to generate plain-language advisory text, while a custom RAG (Retrieval-Augmented Generation) engine handles grounded user queries. The frontend provides a high-fidelity dashboard featuring dual-theme glassmorphism (Midnight Nimbus/Coastal Mist), STRtree-based spatial risk lookups, and a multi-scenario simulation engine for stress-testing flood response.

## 2. Tech Stack

### Backend
| Package | Version | Justification |
| :--- | :--- | :--- |
| **Python** | 3.11.0+ | Runtime environment for backend and frontend. |
| **FastAPI** | 0.115.x | High-performance asynchronous REST API framework. |
| **Uvicorn** | 0.34.x | ASGI server for production-grade reliability. |
| **XGBoost** | 2.1.x | Gradient boosting for time-series water level regression. |
| **Pandas / NumPy** | 2.2 / 2.2 | Vectorized data manipulation and rolling statistics. |
| **SciPy** | 1.15.x | Statistical signal processing and Z-score outlier detection. |
| **Google Generative AI**| 0.8.x | Gemini 2.0 Flash SDK for alert generation and RAG. |
| **APScheduler** | 3.11.0 | Reliable background polling for ingestion jobs. |
| **Shapely** | 2.0.x | STRtree spatial indexing for O(log n) flood zone lookups. |
| **Pydantic / Settings** | 2.10 / 2.7 | Schema validation and env-driven configuration. |
| **Httpx** | 0.28.x | Async HTTP client for USGS, NOAA, and API internal calls. |
| **BS4 / LXML** | 4.12 / 5.3 | HTML/XML parsing for EMA alerts and RSS feeds. |
| **Feedparser** | 6.0.x | RSS parsing for National Weather Service (NWS) alerts. |
| **Selenium** | 4.x | Browser automation (via Bright Data) for dynamic Montgomery portal scraping. |
| **Python-Dotenv** | 1.0.x | Environment variable management for API keys. |
| **Geopy** | 2.4.x | Fallback geocoding and coordinate utilities. |

### Frontend
| Package | Version | Justification |
| :--- | :--- | :--- |
| **Streamlit** | 1.41.x | Reactive dashboard framework with custom glassmorphic styling. |
| **Streamlit-Folium** | 0.26.x | Bridge for Leaflet.js rendering with GeoJSON support. |
| **Folium** | 0.19.x | Leaflet.js Python wrapper for map generation. |
| **Plotly** | 5.24.x | Interactive dual-axis charts for time-series visualization. |
| **Httpx** | 0.28.x | Modern async HTTP client for backend REST communication. |
| **Streamlit-Autorefresh** | latest | Non-blocking UI synchronization to ensure fresh data state. |

## 3. File and Folder Structure
```text
stormshield/
├── .env                     # API keys (GEMINI, BRIGHTDATA, etc.)
├── README.md                # Project setup and developer docs.
├── requirements.txt         # Core dependency list.
├── requirements-dev.txt     # Test and linting tools (pytest, ruff).
├── backend/
│   ├── main.py              # Application lifecycle, middleware, and router mounting.
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
│   └── data/                # Local cache storage: flood_zones.json, ema_alerts.json.
├── frontend/
│   ├── app.py               # Theme logic, layout, and tab orchestration.
│   ├── config.py            # Frontend constants (BACKEND_URL, REFRESH_OPTIONS).
│   └── components/          # Modular UI widgets (Map, Charts, Chat, Weather).
```

## 4. Core Functional Modules

### Module 1: Data Ingestion & Signal Processing
- **Poller**: `APScheduler` runs background jobs every 5-15 mins.
- **USGS Client**: Fetches stage and discharge via Waterservices JSON API.
- **Smoother**: Applies 15-min rolling mean.
- **Outlier Filter**: Drops signals with $|Z| > 2.0$ or single-step deltas $> 2.0$ ft.

### Module 2: Flood Prediction Engine
- **Predictor**: Loads serialised `XGBoost` model via `joblib`.
- **Feature Vector**: (t0, t-15, t-30, t-60 water levels) + (discharge) + (rain proxy) + (rate of rise).
- **Confidence Scoring**: 1.0 - (residual variance / baseline variance), clamped to $[0,1]$.

### Module 3: Advisory & Query Systems
- **Alert Engine**: Evaluates current level + rate of rise against RED/YELLOW thresholds.
- **Gemini Generator**: Single-paragraph, plain-language advisory (<60 words).
- **Query Engine (RAG)**: Injects live system state (sensor, forecast, zone) into a "Search-Augmented" prompt for the LLM.

### Module 4: Spatial Analytics
- **Address Lookup**: Geocodes via Nominatim, then queries a `Shapely.STRtree` for point-in-polygon verification against FEMA GeoJSON features.

## 5. Data Models & State Management

### Backend Schemas (Pydantic v2)
- `SensorReading`: `timestamp: datetime`, `water_level_ft: float`, `discharge_cfs: float`.
- `PredictionResult`: `predicted_level_ft: float`, `confidence_score: float`, `estimated_crest: datetime`.
- `AlertStatus`: `level: Literal["RED", "YELLOW", "GREEN"]`, `alert_text: str`.

### Frontend State Management
Streamlit `st.session_state` is used for non-persistent UI state:
- `theme`: Current visual mode ("dark" / "light").
- `sim_mode`: Active scenario ("Live" / "Moderate" / "Heavy" / "Flood").
- `lookup_result`: Geocoded coordinates and localized risk for the sidebar.
- `query_history`: Last 5 turns of conversation for LLM context window.

## 6. API Endpoints & Data Flow
| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/sensor/latest` | GET | Returns the most recent filtered USGS reading. |
| `/api/forecast/current` | GET | Returns the XGBoost T+30 prediction object. |
| `/api/alert/current` | GET | Returns the current system alert and Gemini text. |
| `/api/geodata/lookup` | POST | Performs spatial intersection search for a given address. |
| `/api/query` | POST | Submits user prompt to the RAG engine. |
| `/health` | GET | Returns model load status and cache age. |

**Data Flow**: `USGS -> Smoother -> Predictor -> Alert Engine -> Cache -> Frontend`.

## 7. UI Component Hierarchy
- **`app.py`**: Root layout with `st.tabs`.
    - **Tab 1: Live Dashboard**: 
        - `render_map()`: Folium map with zone overlays.
        - `render_gauge_chart()`: Plotly trend lines.
        - `render_alert_card()`: Status metrics.
    - **Tab 2: Situation Report**: 
        - Log table and full-text advisory.
    - **Tab 3: Ask StormShield AI**: 
        - Chat interface (`st.chat_message`).
    - **Tab 4: Weather Analysis**: 
        - Open-Meteo forecast grid and bar charts.
- **Sidebar**: Theme toggle, Simulation scenario selector, Address lookup port.

## 8. Theme & Simulation Systems 
### Dual-Theme Architecture
Implemented via a custom CSS injection block in `app.py`.
- **Midnight Nimbus**: Deep radial gradients (`#1e1b4b` -> `#020617`), cyan metrics, and glassmorphic blurs.
- **Coastal Mist**: Azure/Blue gradients, high-contrast borders, and clean white chat bubbles.

### Multi-Scenario Simulation
Front-end interceptor that injects synthetic state (RED/YELLOW) into the session.
- **Moderate Rain**: Rising trend (0.2 ft/15m), YELLOW status.
- **High Rainfall / Heavy Rain**: Significant rainfall intensity, rapid rise (0.8 ft/15m), YELLOW status.
- **Flood Situation**: Extreme levels (150+ ft), RED status, evacuation advice.

## 9. Explicit Constraints & Out-of-Scope
- **Constraints**: 
    - No external persistent DB (JSON file cache only).
    - Mapbox GL JS/ArcGIS API keys are restricted; use Folium/OSM.
    - Rate limit: 1 LLM call per 3 seconds.
- **Out-of-Scope**:
    - User authentication/Session persistence.
    - SMS/Push notifications.
