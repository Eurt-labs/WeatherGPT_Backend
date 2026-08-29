# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI, HTTPException, Query, Header, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from models.schemas import WeatherRequest, WeatherResponse, ChatRequest
from services.weather_service import get_live_meteorological_data
from services.ai_service import stream_google_gemma_ai

load_dotenv()

# Client Secret Token for authenticating mobile requests
CLIENT_SECRET = os.getenv("APP_CLIENT_SECRET", "weathergpt_prod_client_auth_secret_2026")

# Rate Limiter setup (60 requests per minute per IP)
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(
    title="WeatherGPT Cloud Engine",
    version="2.1.0",
    description="Live Meteorological Intelligence & Secure Google Gemma 4 31B AI API"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_client_token(x_weathergpt_key: str = Header(default=None)):
    """
    Security Dependency: Validates the custom client authentication header.
    """
    if CLIENT_SECRET and CLIENT_SECRET != "":
        if not x_weathergpt_key or x_weathergpt_key != CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Invalid or missing X-WeatherGPT-Key authentication header."
            )
    return True

@app.get("/", tags=["Health"])
@limiter.limit("120/minute")
def health_check(request: Request):
    return {
        "status": "online",
        "service": "WeatherGPT FastAPI Backend",
        "ai_engine": "Google: Gemma 4 31B (Free)",
        "security": "Rate Limiting & Client Auth Active",
        "weather_source": "OpenWeatherMap + Open-Meteo Fallback"
    }

@app.get("/api/weather/current", tags=["Weather"])
@limiter.limit("60/minute")
async def get_current_weather(
    request: Request,
    lat: float = Query(default=27.5966, description="Latitude (e.g. 27.5966 for Hathras)"),
    lon: float = Query(default=78.0519, description="Longitude (e.g. 78.0519 for Hathras)"),
    auth: bool = Depends(verify_client_token)
):
    """
    Protected endpoint: Fetches real-time weather and CPCB AQI. Requires X-WeatherGPT-Key header.
    """
    data = await get_live_meteorological_data(lat, lon)
    if "error" in data:
        raise HTTPException(status_code=502, detail=data["error"])
    return data

@app.post("/api/weather/live", tags=["Weather"], response_model=WeatherResponse)
@limiter.limit("60/minute")
async def post_current_weather(
    request: Request,
    req: WeatherRequest,
    auth: bool = Depends(verify_client_token)
):
    """
    Protected POST endpoint for Android app passing JSON payload with coordinates.
    """
    data = await get_live_meteorological_data(req.latitude, req.longitude)
    if "error" in data:
        raise HTTPException(status_code=502, detail=data["error"])
    return data

@app.post("/api/ai/chat-stream", tags=["AI Reasoning"])
@limiter.limit("30/minute")
async def ai_chat_stream(
    request: Request,
    req: ChatRequest,
    auth: bool = Depends(verify_client_token)
):
    """
    Protected Server-Sent Events (SSE) stream from Google Gemma 4 31B.
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
    print(f"Starting Secure WeatherGPT Backend on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
