# -*- coding: utf-8 -*-
import os
import hmac
import hashlib
import time
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

HMAC_SECRET = os.getenv("APP_CLIENT_SECRET", "weathergpt_prod_client_auth_secret_2026")
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(
    title="WeatherGPT Multi-Sector Cloud Engine",
    version="3.0.0",
    description="Conversational Weather & Climate Intelligence API (Agriculture, Flood, Aviation, Marine, Climate & Google Gemma 4)"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_hmac_or_token(
    request: Request,
    x_weathergpt_key: str = Header(default=None),
    x_timestamp: str = Header(default=None),
    x_signature: str = Header(default=None)
):
    if x_timestamp and x_signature and HMAC_SECRET:
        try:
            req_time = int(x_timestamp)
            current_time = int(time.time())
            if abs(current_time - req_time) > 60:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthorized: Request timestamp expired."
                )
            message = f"{x_timestamp}:{request.url.path}".encode("utf-8")
            expected_sig = hmac.new(HMAC_SECRET.encode("utf-8"), message, hashlib.sha256).hexdigest()
            if hmac.compare_digest(expected_sig, x_signature):
                return True
        except ValueError:
            pass

    if HMAC_SECRET and x_weathergpt_key == HMAC_SECRET:
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Invalid HMAC signature or client key."
    )

@app.get("/", tags=["Health"])
@limiter.limit("120/minute")
def health_check(request: Request):
    return {
        "status": "online",
        "service": "WeatherGPT Multi-Sector FastAPI Engine",
        "version": "3.0.0",
        "ai_engine": "Google: Gemma 4 31B (Free)",
        "datasets": [
            "Open-Meteo High-Resolution NWP (ECMWF/GFS)",
            "Global Flood & River Discharge API",
            "CPCB Standard Air Quality Index",
            "Agri-Soil Moisture (0-7cm) & Evapotranspiration",
            "80-Year Climate Archive (1940-Present)"
        ]
    }

@app.get("/api/weather/comprehensive", tags=["Weather & Sectors"], response_model=WeatherResponse)
@limiter.limit("60/minute")
async def get_comprehensive_weather(
    request: Request,
    lat: float = Query(default=27.5966, description="Latitude (e.g. 27.5966 for Hathras)"),
    lon: float = Query(default=78.0519, description="Longitude (e.g. 78.0519 for Hathras)"),
    auth: bool = Depends(verify_hmac_or_token)
):
    data = await get_live_meteorological_data(lat, lon)
    if "error" in data:
        raise HTTPException(status_code=502, detail=data["error"])
    return data

@app.post("/api/weather/live", tags=["Weather & Sectors"], response_model=WeatherResponse)
@limiter.limit("60/minute")
async def post_live_weather(
    request: Request,
    req: WeatherRequest,
    auth: bool = Depends(verify_hmac_or_token)
):
    data = await get_live_meteorological_data(req.latitude, req.longitude)
    if "error" in data:
        raise HTTPException(status_code=502, detail=data["error"])
    return data

@app.get("/api/advisory/agri", tags=["Agriculture - Kisan AI"])
@limiter.limit("60/minute")
async def get_agri_advisory(
    request: Request,
    lat: float = Query(default=27.5966),
    lon: float = Query(default=78.0519),
    auth: bool = Depends(verify_hmac_or_token)
):
    data = await get_live_meteorological_data(lat, lon)
    if "error" in data:
        raise HTTPException(status_code=502, detail=data["error"])
    return {
        "location": data.get("location_name"),
        "temperature": data.get("temperature"),
        "humidity": data.get("humidity"),
        "agriculture": data.get("agriculture"),
        "climate_trends": data.get("climate_trends")
    }

@app.get("/api/disaster/alerts", tags=["Disaster & Early Warning"])
@limiter.limit("60/minute")
async def get_disaster_alerts(
    request: Request,
    lat: float = Query(default=27.5966),
    lon: float = Query(default=78.0519),
    auth: bool = Depends(verify_hmac_or_token)
):
    data = await get_live_meteorological_data(lat, lon)
    if "error" in data:
        raise HTTPException(status_code=502, detail=data["error"])
    return {
        "location": data.get("location_name"),
        "aqi": data.get("aqi"),
        "disaster_alerts": data.get("disaster_alerts")
    }

@app.post("/api/ai/chat-stream", tags=["AI Reasoning"])
@limiter.limit("30/minute")
async def ai_chat_stream(
    request: Request,
    req: ChatRequest,
    auth: bool = Depends(verify_hmac_or_token)
):
    return EventSourceResponse(
        stream_google_gemma_ai(
            user_message=req.message,
            location=req.location,
            weather_context=req.weather_context,
            sector_focus=req.sector_focus,
            history=req.history,
            is_voice=req.is_voice_mode
        )
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting WeatherGPT Multi-Sector Backend on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
