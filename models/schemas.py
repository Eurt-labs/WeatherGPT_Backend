from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class WeatherRequest(BaseModel):
    latitude: float = Field(default=27.5966, description="Latitude coordinate (e.g. 27.5966 for Hathras)")
    longitude: float = Field(default=78.0519, description="Longitude coordinate (e.g. 78.0519 for Hathras)")

class HourlyItem(BaseModel):
    time: str
    temp: str
    condition: str

class DayItem(BaseModel):
    day: str
    min_temp: str
    max_temp: str
    condition: str

class WeatherResponse(BaseModel):
    temperature: str
    condition: str
    high_low: str
    humidity: str
    wind_speed: str
    aqi: str
    location_name: str
    hourly_forecast: List[HourlyItem]
    daily_forecast: List[DayItem]

class ChatRequest(BaseModel):
    message: str = Field(..., description="User question or voice transcript")
    location: str = Field(default="Hathras, Uttar Pradesh", description="Location name")
    weather_context: str = Field(default="32°C, Mostly Cloudy, Wind 6 km/h, Humidity 59%, AQI 64", description="Atmospheric context")
    history: List[Dict[str, str]] = Field(default_factory=list, description="Recent conversation history")
    is_voice_mode: bool = Field(default=False, description="True if prompt comes from Voice AI")
