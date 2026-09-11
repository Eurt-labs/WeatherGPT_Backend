# WeatherGPT Cloud Backend 🌩️⚡

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI-499848?style=for-the-badge&logo=gunicorn&logoColor=white)](https://www.uvicorn.org/)
[![AI Engine](https://img.shields.io/badge/AI%20Engine-Google%20Gemini%203.6%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Render](https://img.shields.io/badge/Hosted%20on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://weathergpt-backend-m5kk.onrender.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)

The official cloud API backend powering the **[WeatherGPT Android Application](https://github.com/Eurt-labs/WeatherGPT_Android)** with real-time AI reasoning via **Google Gemini 3.6 Flash**, live Open-Meteo meteorological telemetry synthesis, SlowAPI rate limiting, and Supabase database synchronization.

---

## 🚀 Key Features

- **Gemini 3.6 Flash Streaming**: Real-time Server-Sent Events (SSE) token streaming via Google AI Studio provider pinning for low-latency conversational reasoning.
- **Meteorological Grounding**: Dense physics layer integrating barometric pressure trends, dew point proximity, FAO evapotranspiration ($ET_0$), and topsoil volumetric moisture.
- **Conversational Proportionality**: Calibrated system prompts that produce concise 3–4 sentence paragraphs (50–80 words) in standard chat, and 1–2 warm spoken sentences (max 35 words) for voice mode.
- **Proactive Profile Guidance**: Concludes responses with tailored follow-up inquiries based on the user's agricultural crops, acreage, or travel route.
- **SlowAPI Rate Limiting**: Protects against quota exhaustion and abusive bursts.
- **Supabase Authentication & Sync**: Manages user profiles, historical conversations, and preferences.

---

## 📁 Repository Structure

```
WeatherGPT_Backend/
├── main.py                              # FastAPI entry point, SlowAPI rate limiter, CORS, routes
├── services/
│   ├── ai_service.py                    # Gemini 3.6 Flash streaming engine & SSE generator
│   ├── weather_service.py               # Open-Meteo live proxy & telemetry synthesis
│   └── supabase_service.py              # Supabase user authentication & database syncing
├── models/
│   └── schemas.py                       # Pydantic request and response schemas
├── requirements.txt                     # FastAPI, Uvicorn, SlowAPI, httpx, sse-starlette
├── Procfile                             # Render process command (uvicorn main:app)
├── render.yaml                          # Render deployment configuration
├── AGENTS.md                            # Contributor & Agent Guardrails
└── README.md                            # Documentation
```

---

## 🔌 API Endpoints & Contracts

### 1. SSE Real-Time Chat Stream
- **Endpoint:** `POST /api/ai/chat-stream`
- **Content-Type:** `application/json`
- **Response Format:** `text/event-stream` (`data: <token_chunk>\n\n` ending in `data: [DONE]\n\n`)

```json
{
  "message": "Is it safe to irrigate my wheat crop today?",
  "location": "New Delhi, India",
  "weather_context": "Atmosphere: 29°C, Humidity: 68%, Soil Moisture: 0.33 m3/m3, ET0: 4.2 mm/day",
  "sector_focus": "farmer",
  "language": "en",
  "is_voice_mode": false,
  "is_detail_mode": false,
  "history": []
}
```

### 2. Single-Turn Diagnostic Ping
- **Endpoint:** `POST /api/ai/chat`
- **Description:** Fast verification ping utilized by the Android client to test cloud server connectivity.

### 3. Server Health & Metrics
- **Endpoint:** `GET /api/health`
- **Response:**
  ```json
  {
    "status": "online",
    "engine": "Google Gemini 3.6 Flash",
    "version": "1.2.0"
  }
  ```

### 4. Live Meteorological Telemetry Proxy
- **Endpoint:** `POST /api/weather/live`
- **Description:** Proxies and synthesizes Open-Meteo telemetry into structured meteorological analysis layers.

---

## 💻 Local Development Setup

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the root directory:
```env
OPENROUTER_API_KEY=sk-or-v1-...
GEMINI_API_KEY=AIzaSy...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
PORT=8000
HOST=0.0.0.0
```

### 3. Run Locally
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Interactive OpenAPI Swagger docs will be accessible at: **`http://localhost:8000/docs`**

---

## 🚢 Render Deployment

This service is deployed on Render as a Web Service:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Production URL:** `https://weathergpt-backend-m5kk.onrender.com`

---

## 📖 Developer Guardrails

Before submitting changes, review **[`AGENTS.md`](AGENTS.md)** to prevent regressions in SSE streaming protocols, multi-line string escaping, or prompt proportionality rules.
