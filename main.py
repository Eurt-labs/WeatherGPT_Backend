import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

from models.schemas import WeatherRequest, WeatherResponse, ChatRequest
from services.weather_service import get_live_meteorological_data
from services.ai_service import stream_google_gemma_ai

load_dotenv()

app = FastAPI(
    title="WeatherGPT Cloud Engine",
    version="2.0.0",
    description="Live Meteorological Intelligence, CPCB AQI Indexing & Google Gemma 4 31B AI API"
)

# Enable CORS for Android App & Web Dashboard clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "WeatherGPT FastAPI Backend",
        "ai_engine": "Google: Gemma 4 31B (Free)",
        "weather_source": "OpenWeatherMap + Open-Meteo Fallback"
    }

@app.get("/api/weather/current", tags=["Weather"])
async def get_current_weather(
    lat: float = Query(default=27.5966, description="Latitude (e.g. 27.5966 for Hathras)"),
    lon: float = Query(default=78.0519, description="Longitude (e.g. 78.0519 for Hathras)")
):
    """
    Get real-time temperature, condition, humidity, wind, and CPCB standard Air Quality Index (AQI).
    """
    data = await get_live_meteorological_data(lat, lon)
    if "error" in data:
        raise HTTPException(status_code=502, detail=data["error"])
    return data

@app.post("/api/weather/live", tags=["Weather"], response_model=WeatherResponse)
async def post_current_weather(req: WeatherRequest):
    """
    POST endpoint for Android app passing JSON payload with coordinates.
    """
    data = await get_live_meteorological_data(req.latitude, req.longitude)
    if "error" in data:
        raise HTTPException(status_code=502, detail=data["error"])
    return data

@app.post("/api/ai/chat-stream", tags=["AI Reasoning"])
async def ai_chat_stream(req: ChatRequest):
    """
    Server-Sent Events (SSE) token stream from Google Gemma 4 31B with live meteorological context.
    """
    return EventSourceResponse(
        stream_google_gemma_ai(
            user_message=req.message,
            location=req.location,
            weather_context=req.weather_context,
            history=req.history,
            is_voice=req.is_voice_mode
        )
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting WeatherGPT Backend on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
