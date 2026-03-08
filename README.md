# 🛡️ StormShield AI — Montgomery's Smart Flood & Weather Guardian
**World Wide Vibes Hackathon Submission**

**StormShield AI — Montgomery's Smart Flood & Weather Guardian** is a real-time flood prediction and civic alert system designed for Montgomery, Alabama. It serves as a smart guardian against weather anomalies, leveraging real-time data ingestion, machine learning, and generative AI to keep citizens safe and informed through a premium glassmorphic interface.

---

## 📄 Documentation

For deep dives into the system architecture, feature breakdown, and developer guides, refer to the following:

*   **[Technical Product Requirement Document (PRD)](./StormShield%20AI%20%E2%80%94%20Technical%20Product%20Requirement%20Document.md)**: Full technical specifications and logic.
*   **[User Interaction Module](./StormShield%20AI%20%E2%80%94%20User%20Interaction%20Module.md)**: Breakdown of UI behaviors and modular code logic.
*   **[Implementation Order & Roadmap](./Structured%20Markdown%20&%20Implementation%20Order.md)**: Step-by-step assembly guide optimized for AI editors.

---

## 🌟 Key Features

*   **Real-Time Data Ingestion:** Constantly polls USGS stream gauge data (Station 01648000), NOAA/NWS alerts, and high-resolution weather telemetry.
*   **Predictive Analytics (XGBoost):** Employs an XGBoost regression model to produce 30-minute water-level forecasts (T+30) with confidence scoring.
*   **Smart Alerting Engine:** Automatically issues **RED**, **YELLOW**, or **GREEN** status based on predicted crests and rate-of-rise thresholds.
*   **Generative AI (Gemini 2.0 Flash):**
    *   **Dynamic Advisories**: Generates plain-language, action-oriented public bulletins.
    *   **Ask StormShield AI**: A RAG-powered conversational interface grounded in live sensor and spatial data.
*   **Premium Glassmorphic Dashboard**:
    *   **Dual-Theme Support**: "Midnight Nimbus" (Dark) and "Coastal Mist" (Light) visual modes.
    *   **4-Tab Navigation**: Live Dashboard, Situation Report, Safety AI Chat, and Detailed Weather Analysis.
    *   **Spatial Lookup Engine**: High-performance address-based flood risk checks using Shapely STRtree indexing.
*   **Multi-Scenario Simulation**: Interactive stress-testing for "Moderate", "High Rainfall", "Heavy Rain", and "Flood" scenarios.

---

## ⚙️ Tech Stack

### Backend
- **Core**: Python 3.11, FastAPI, Uvicorn (ASGI).
- **Processing**: Pandas, NumPy, SciPy (Rolling means & Z-score signal filtering).
- **ML/AI**: XGBoost, Scikit-learn, Google Generative AI (Gemini 2.0 Flash).
- **Spatial**: Shapely (STRtree lookup), Geopy (Nominatim geocoding).
- **Automation**: APScheduler (In-memory job scheduling), Selenium (Bright Data scraping fallback).

### Frontend
- **Framework**: Streamlit 1.41.x.
- **Visuals**: Plotly (Scientific Charts), Folium (Leaflet.js Mapping), Streamlit-Autorefresh.
- **Styling**: Custom CSS injection for glassmorphism and animated theme transitions.

---

## 🚀 Quick Start (Local Setup)

### 1. Set Up Environment
```bash
git clone https://github.com/Tanishaaaaaaa/StormShield.git
cd StormShield
python -m venv venv
source venv/bin/activate  # Mac/Linux: source venv/bin/activate | Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
cd stormshield
pip install -r requirements.txt
```

### 3. Configure `.env`
Create a `.env` in `stormshield/` with your keys:
```ini
GEMINI_API_KEY=your_key
BRIGHTDATA_API_KEY=your_key
USGS_STATION_ID=01648000
FLOOD_STAGE_FT=8.0
BACKEND_URL=http://localhost:8000
```

### 4. Application Components
Run the backend and frontend in separate terminals:

**Terminal 1 (Backend API)**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Frontend Dashboard)**
```bash
streamlit run frontend/app.py
```

---

## 📁 Project Architecture

```text
StormShield/
├── README.md                      # Documentation Hub
└── stormshield/                   # Application Root
    ├── backend/
    │   ├── scheduler.py           # Polling & Ingestion registry
    │   ├── modules/
    │   │   ├── alert/             # Threshold engine & LLM text
    │   │   ├── cache/             # In-memory + JSON persistence
    │   │   ├── ingestion/         # USGS/NOAA/NWS/BrightData clients
    │   │   ├── prediction/        # XGBoost Inference
    │   │   ├── processing/        # Signal smoothing & Filtering
    │   │   ├── query/             # RAG Chat engine
    │   │   └── simulation/        # Runoff & Green-infra calculators
    │   └── routers/               # FastAPI REST endpoints
    ├── frontend/
    │   ├── app.py                 # Theme & Tab Orchestrator
    │   └── components/            # Modular UI Widgets (Map, Gauges, Chat)
    └── data/                      # Local Cache (FEMA Zones, EMA Logs)
```

---

## 🧠 Smart Alerting Logic

| Status | Trigger Condition | Advisor Guidance |
| :--- | :--- | :--- |
| 🟢 **GREEN** | Predicted Level < Threshold | Normal conditions; monitor updates. |
| 🟡 **YELLOW**| Rate of Rise > 2.0 ft/15m | Caution; localized ponding possible. |
| 🔴 **RED**   | Predicted Level ≥ 8.0 ft | Emergency; flooding imminent. Evacuate. |

---

## 🏆 Hackathon Context

This project was built for the **World Wide Vibes Hackathon** to demonstrate how AI can transform raw meteorological and hydrological data into actionable public safety intelligence.

**Team Name:** OmniShield
**Project Name:** StormShield AI
