# 🛡️ StormShield AI
**World Wide Vibes Hackathon Submission**

**StormShield AI** is a real-time flood prediction and civic alert system designed for Montgomery, Alabama. It serves as a smart guardian against weather anomalies, leveraging real-time data ingestion, machine learning, and generative AI to keep citizens safe and informed.

---

## 🌟 Key Features

*   **Real-Time Data Ingestion:** Constantly polls USGS stream gauge data (e.g., Sligo Creek), NOAA/NWS alerts, and supplementary local weather data.
*   **Predictive Analytics (XGBoost):** Employs an XGBoost machine learning model trained on historical data to predict water levels 30 minutes into the future (T+30).
*   **Smart Alerting Engine:** Automatically issues **RED**, **YELLOW**, or **GREEN** zone alerts based on current predictions and rate-of-rise metrics.
*   **Generative AI Integration (Gemini 2.0 Flash):**
    *   Generates dynamic, non-panicky, action-oriented public alert bulletins.
    *   Powers **Ask StormShield AI**, a conversational RAG interface where users can ask questions about current flood conditions, road closures, and evacuation staging areas.
*   **Live Interactive Dashboard:** A stunning, responsive Streamlit dashboard featuring:
    *   Live telemetry (Water Level, Discharge, Rate of Rise, Predictive Forecasting).
    *   **Dark/Light Mode** support with beautifully styled widgets.
    *   Interactive flood zone maps with live sensor markers.
    *   A "Green Infrastructure" simulator to estimate how many trees are needed to offset local water runoff.

---

## ⚙️ Tech Stack

*   **Backend:** Python, FastAPI, APScheduler (Background Jobs), Uvicorn.
*   **Frontend:** Streamlit, Folium (Mapping), Plotly (Interactive Charts).
*   **AI / ML:** XGBoost (Time-series forecasting), Google Gemini 2.0 Flash (Alert generation & RAG Q&A).
*   **Data Sources:** USGS Water Services API, NWS/NOAA Alerts, Bright Data (for auxiliary web scraping tasks).

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/Tanishaaaaaaa/StormShield.git
cd StormShield
python -m venv venv

# Activate Virtual Environment
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows
```

### 2. Install Dependencies
```bash
cd stormshield
pip install -r requirements.txt
```

### 3. Environment Variables (`.env`)
Ensure you have a `.env` file in the `stormshield/` directory with the following keys:
```ini
GEMINI_API_KEY=your_gemini_api_key
BRIGHTDATA_API_KEY=your_brightdata_api_key  # Optional for scraping
USGS_STATION_ID=01648000
FLOOD_STAGE_FT=8.0
BACKEND_URL=http://localhost:8000
DEFAULT_REFRESH_SECONDS=60
```

### 4. Train the ML Model (First time only)
```bash
python backend/modules/prediction/train.py
```

### 5. Run the Application
You will need two terminal windows to run both the API backend and the Streamlit frontend.

**Terminal 1 (Backend API):**
```bash
cd stormshield
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
*   **API Docs:** http://localhost:8000/docs
*   **Health Check:** http://localhost:8000/health

**Terminal 2 (Frontend Dashboard):**
```bash
cd stormshield
streamlit run frontend/app.py
```
*   **Live Dashboard:** http://localhost:8501

---

## 📁 Project Architecture

```
StormShield/
├── README.md                     # You are here!
└── stormshield/                  # Main Application Directory
    ├── backend/
    │   ├── main.py               # FastAPI App & Endpoints
    │   ├── scheduler.py          # Background polling jobs
    │   ├── modules/
    │   │   ├── ingestion/        # USGS / NOAA data fetching
    │   │   ├── processing/       # Data smoothing & filtering
    │   │   ├── prediction/       # XGBoost Inference & Training
    │   │   ├── alert/            # Threshold Logic + Gemini Integration
    │   │   ├── simulation/       # Green Infrastructure logic
    │   │   └── query/            # RAG Chatbot Engine
    │   └── data/                 # JSON caches & ML model weights
    ├── frontend/
    │   ├── app.py                # Streamlit Dashboard Entry Point
    │   └── components/           # UI Components (Map, Alerts, Weather, Chat)
    ├── .env                      # Secrets & Config
    └── requirements.txt          # Python Dependencies
```

---

## 🧠 Smart Alerting Logic

| Status | Trigger Condition | Dashboard Indicator |
| :--- | :--- | :--- |
| 🟢 **GREEN** | Normal conditions, low water level. | Safe / Normal Operations |
| 🟡 **YELLOW**| Rate of rise > 2.0 ft/15 min. | Caution / Prepare |
| 🔴 **RED**   | Predicted level ≥ 8.0 ft (Flood Stage). | Action Required / Evacuate |

---

## 🏆 Hackathon Context

This project was built for the **World Wide Vibes Hackathon**. The goal was to build a highly responsive, AI-driven civic application capable of assisting local emergency management agencies and keeping citizens informed during extreme weather events.

**Team Name:** MoCo-Sentinel
**Project Name:** StormShield AI
