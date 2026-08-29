# ??? WeatherGPT Backend

Production-grade FastAPI Cloud Engine powering **WeatherGPT Android** with real-time meteorological intelligence, CPCB standard Air Quality Index (AQI) calculations, and Google Gemma 4 31B AI streaming.

---

## ?? Features

- **Live Meteorological Aggregator**: Queries OpenWeatherMap with automatic keyless Open-Meteo fallback.
- **CPCB Standard AQI Calculation**: Precise breakpoint calculation using live particulate matter ({2.5}$, {10}$, $).
- **Google Gemma 4 31B AI Streaming**: Real-time Server-Sent Events (SSE) token streaming proxy with multilingual Indic support (English, Hindi, Marathi, Bengali, Tamil, Telugu).
- **FastAPI & Uvicorn**: High-throughput async API with interactive Swagger UI documentation.

---

## ??? Quick Start

### 1. Install Dependencies
`ash
pip install -r requirements.txt
`

### 2. Configure Environment Variables
Copy .env.example to .env and add your API keys:
`env
OPENWEATHER_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
PORT=8000
HOST=0.0.0.0
`

### 3. Run Server
`ash
# Windows 1-Click
run_server.bat

# Or CLI
python main.py
`

---

## ?? API Documentation

Once the server is running, access the interactive Swagger documentation at:
**[http://localhost:8000/docs](http://localhost:8000/docs)**

- GET / — Health check endpoint
- GET /api/weather/current?lat=27.5966&lon=78.0519 — Live meteorological and AQI payload
- POST /api/weather/live — Weather request with JSON coordinates
- POST /api/ai/chat-stream — Real-time Server-Sent Events (SSE) AI stream
