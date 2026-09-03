# -*- coding: utf-8 -*-
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

class AgriMetrics(BaseModel):
    soil_moisture_surface: str
    soil_temperature: str
    evapotranspiration: str
    irrigation_advice: str

class DisasterAlerts(BaseModel):
    flood_risk_level: str
    river_discharge_m3s: str
    heatwave_alert: str
    storm_warning: str

class AviationMetrics(BaseModel):
    visibility_km: str
    cloud_cover_pct: str
    wind_gusts_kmh: str
    freezing_level_m: str

class ClimateTrends(BaseModel):
    past_7days_rain_mm: str
    temp_anomaly: str
    drought_risk: str

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
    agriculture: Optional[AgriMetrics] = None
    disaster_alerts: Optional[DisasterAlerts] = None
    aviation: Optional[AviationMetrics] = None
    climate_trends: Optional[ClimateTrends] = None

class ChatRequest(BaseModel):
    message: str = Field(..., description="User query or voice transcript in any Indian language")
    location: str = Field(default="Hathras, Uttar Pradesh", description="Location name")
    weather_context: str = Field(default="32°C, Mostly Cloudy, Wind 6 km/h, Humidity 59%, AQI 64", description="Atmospheric context")
    sector_focus: str = Field(default="general", description="Focus area: general, agriculture, disaster, aviation, marine, climate")
    history: List[Dict[str, str]] = Field(default_factory=list, description="Recent conversation history")
    is_voice_mode: bool = Field(default=False, description="True if prompt comes from Voice AI")


class AuthSendOtpRequest(BaseModel):
    contact: str = Field(..., description='Email address or phone number (with country code)')
    channel: str = Field(default='email', description='email or phone')

class AuthVerifyOtpRequest(BaseModel):
    contact: str = Field(..., description='Email address or phone number')
    token: str = Field(..., description='6-digit OTP token')
    channel: str = Field(default='email', description='email or phone')

class UserProfileRequest(BaseModel):
    user_id: str
    name: str
    contact: str
    contact_type: str = 'email'
    sector: str = 'farmer' # farmer, disaster, commuter, aviation
    language: str = 'en'
    crops: Optional[str] = None
    land_area: Optional[str] = None
    monitored_region: Optional[str] = None

class AuthResponse(BaseModel):
    status: str
    message: str
    user_id: Optional[str] = None
    session_token: Optional[str] = None
    is_new_user: bool = False
    profile: Optional[Dict[str, Any]] = None
