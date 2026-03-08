# 🛡️ StormShield AI — Montgomery's Smart Flood & Weather Guardian

**Version 2.0** | Python / FastAPI / Streamlit / XGBoost / Gemini 2.0 Flash

StormShield AI is a real-time flood prediction and civic alert system for Montgomery, Alabama. It polls USGS stream gauge data, applies ML-based water-level prediction, issues RED/YELLOW/GREEN alerts with LLM-generated text, and provides an interactive Streamlit dashboard with flood zone mapping.

---

## 🚀 Quick Start (Local)

### 1. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows
```

### 2. Install dependencies
```bash
cd stormshield
pip install -r requirements.txt
```

### 3. Configure environment
```bash
# .env is pre-configured in stormshield/.env
# Update GEMINI_API_KEY and BRIGHTDATA_API_KEY if needed
```

### 4. Train the XGBoost model (run once)
```bash
python backend/modules/prediction/train.py
```

### 5. Start the backend (Terminal 1)
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Start the frontend (Terminal 2)
```bash
streamlit run frontend/app.py
```

- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📁 Project Structure

```
stormshield/
├── .env                          # API keys & config
├── requirements.txt
├── backend/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Pydantic BaseSettings
│   ├── scheduler.py              # APScheduler background jobs
│   ├── modules/
│   │   ├── ingestion/            # USGS, NOAA, NWS, Bright Data clients
│   │   ├── processing/           # Rolling mean smoother + Z-score filter
│   │   ├── prediction/           # XGBoost model + training script
│   │   ├── alert/                # Threshold engine + Gemini alert generator
│   │   ├── simulation/           # Green infrastructure tree calculator
│   │   ├── cache/                # In-memory + JSON cache manager
│   │   └── query/                # Gemini RAG query engine
│   ├── routers/                  # FastAPI route handlers
│   └── data/                     # JSON cache files (auto-populated)
└── frontend/
    ├── app.py                    # Streamlit entry point
    ├── config.py
    └── components/               # Map, chart, alert card, simulation, query panel
```

---

## 🔑 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | Google AI Studio API key (required for LLM features) |
| `BRIGHTDATA_API_KEY` | — | Bright Data account key (for scraping; stubs provided) |
| `USGS_STATION_ID` | `01648000` | USGS Sligo Creek gauge station |
| `FLOOD_STAGE_FT` | `8.0` | Water level (ft) that triggers RED alert |
| `BACKEND_URL` | `http://localhost:8000` | FastAPI backend URL (update for cloud deploy) |
| `DEFAULT_REFRESH_SECONDS` | `60` | Streamlit auto-refresh interval |

---

## 🧠 Alert Levels

| Level | Condition |
|---|---|
| 🔴 **RED** | Predicted level ≥ flood stage (8.0 ft) |
| 🟡 **YELLOW** | Rate of rise > 2.0 ft/15 min |
| 🟢 **GREEN** | Normal conditions |

---

## 📡 Key API Endpoints

```
GET  /api/sensor/latest         Latest smoothed USGS reading
GET  /api/sensor/history?hours=4  Historical readings (up to 72h)
GET  /api/forecast/current      XGBoost T+30 prediction
GET  /api/alert/current         Current alert with LLM text
GET  /api/alert/history         Last 20 alert records
POST /api/simulation/green      Green infrastructure simulation
GET  /api/geodata/flood-zones   FEMA flood zone GeoJSON
GET  /api/geodata/ema-alerts    EMA alert objects
POST /api/query                 RAG query (Gemini-powered)
GET  /health                    Backend health check
```

---

## ☁️ Cloud Deployment

**Backend → Railway**: Set start command to `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

**Frontend → Streamlit Community Cloud**: Set main file to `frontend/app.py`, add secrets via Streamlit dashboard.
