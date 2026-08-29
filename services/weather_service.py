# -*- coding: utf-8 -*-
import os
import httpx
from datetime import datetime
from typing import Dict, Any, List

def wmo_code_to_condition(code: int) -> str:
    """Decodes WMO weather codes into user-friendly conditions."""
    mapping = {
        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Mostly Cloudy",
        45: "Foggy",
        48: "Depositing Rime Fog",
        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",
        61: "Slight Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",
        71: "Slight Snow Fall",
        73: "Moderate Snow Fall",
        75: "Heavy Snow Fall",
        80: "Slight Rain Showers",
        81: "Moderate Rain Showers",
        82: "Violent Rain Showers",
        95: "Thunderstorm",
        96: "Thunderstorm with Slight Hail",
        99: "Thunderstorm with Heavy Hail"
    }
    return mapping.get(code, "Partly Cloudy")

async def get_live_meteorological_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Pure 100% Open-Meteo Meteorological & Air Quality Engine.
    Zero API keys required, 10,000 requests/day, ECMWF/GFS global models,
    including soil moisture, rain probabilities, and past 3 days trends.
    """
    async with httpx.AsyncClient(timeout=12.0) as client:
        try:
            # 1. Open-Meteo Weather Forecast & Historical Past Days API
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,precipitation"
                f"&hourly=temperature_2m,weather_code,precipitation_probability,soil_moisture_0_to_1cm"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,uv_index_max"
                f"&past_days=3&timezone=auto"
            )

            # 2. Open-Meteo Air Quality API
            pollution_url = (
                f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}"
                f"&current=us_aqi,pm2_5,pm10,ozone"
            )

            weather_res = await client.get(weather_url)
            pollution_res = await client.get(pollution_url)

            if weather_res.status_code != 200:
                return {"error": f"Open-Meteo HTTP {weather_res.status_code}"}

            w_data = weather_res.json()
            curr = w_data.get("current", {})
            daily = w_data.get("daily", {})
            hourly = w_data.get("hourly", {})

            temp_c = round(curr.get("temperature_2m", 32.0))
            humidity = f"{round(curr.get('relative_humidity_2m', 60))}%"
            wind_speed = f"{round(curr.get('wind_speed_10m', 6.0))} km/h"
            condition = wmo_code_to_condition(curr.get("weather_code", 3))

            # Daily High / Low for Today (index 3 because past_days=3)
            today_idx = 3 if len(daily.get("time", [])) > 3 else 0
            max_t = round(daily.get("temperature_2m_max", [temp_c + 2])[today_idx])
            min_t = round(daily.get("temperature_2m_min", [temp_c - 5])[today_idx])
            uv_val = daily.get("uv_index_max", [7.0])[today_idx]
            uv_str = f"{round(uv_val)} ({'Low' if uv_val <= 2 else ('Moderate' if uv_val <= 5 else 'High')})"

            # Calculate Standard AQI from Open-Meteo Air Quality API
            aqi_str = "64 (Moderate)"
            if pollution_res.status_code == 200:
                pol_data = pollution_res.json().get("current", {})
                pm25 = pol_data.get("pm2_5", 20.0)
                pm10 = pol_data.get("pm10", 60.0)
                aqi_val = max(int(pm25 * 2.5), int(pm10 * 1.0))
                aqi_val = min(max(aqi_val, 15), 500)
                cat = "Good" if aqi_val <= 50 else ("Moderate" if aqi_val <= 100 else ("Poor" if aqi_val <= 200 else "Hazardous"))
                aqi_str = f"{aqi_val} ({cat})"

            # Parse Sequential Hourly Forecast
            hourly_times = hourly.get("time", [])
            hourly_temps = hourly.get("temperature_2m", [])
            hourly_codes = hourly.get("weather_code", [])

            hourly_list: List[Dict[str, str]] = []
            hourly_list.append({"time": "Now", "temp": f"{temp_c}°", "condition": condition})

            # Find index closest to now
            now_iso = datetime.now().strftime("%Y-%m-%dT%H:00")
            start_i = 0
            for i, t in enumerate(hourly_times):
                if t >= now_iso:
                    start_i = i
                    break

            for i in range(start_i + 1, min(start_i + 7, len(hourly_times))):
                dt_str = hourly_times[i]
                try:
                    dt_obj = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
                    time_label = dt_obj.strftime("%I:%M %p").lstrip("0").lower()
                except Exception:
                    time_label = dt_str.split("T")[-1]

                item_temp = f"{round(hourly_temps[i])}°"
                item_cond = wmo_code_to_condition(hourly_codes[i])
                hourly_list.append({"time": time_label, "temp": item_temp, "condition": item_cond})

            # Parse Multi-Day Forecast (Today, Tomorrow, and upcoming days)
            daily_times = daily.get("time", [])
            daily_maxs = daily.get("temperature_2m_max", [])
            daily_mins = daily.get("temperature_2m_min", [])
            daily_codes = daily.get("weather_code", [])

            daily_list: List[Dict[str, str]] = []
            for i in range(today_idx, len(daily_times)):
                dt_str = daily_times[i]
                day_offset = i - today_idx
                if day_offset == 0:
                    label = "Today"
                elif day_offset == 1:
                    label = "Tomorrow"
                else:
                    try:
                        label = datetime.strptime(dt_str, "%Y-%m-%d").strftime("%a")
                    except Exception:
                        label = dt_str

                daily_list.append({
                    "day": label,
                    "min_temp": f"{round(daily_mins[i])}°",
                    "max_temp": f"{round(daily_maxs[i])}°",
                    "condition": wmo_code_to_condition(daily_codes[i])
                })

            # Historical / Agricultural Context (for AI reasoning)
            past_rain = sum(daily.get("precipitation_sum", [])[:today_idx])
            soil_moist = hourly.get("soil_moisture_0_to_1cm", [0.33])[start_i] if hourly.get("soil_moisture_0_to_1cm") else 0.33

            return {
                "temperature": f"{temp_c}°",
                "condition": condition,
                "high_low": f"H: {max_t}°  L: {min_t}°",
                "humidity": humidity,
                "wind_speed": wind_speed,
                "aqi": aqi_str,
                "location_name": "Live Location",
                "hourly_forecast": hourly_list,
                "daily_forecast": daily_list,
                "soil_moisture": f"{soil_moist:.3f} m³/m³",
                "past_3days_rainfall": f"{past_rain:.1f} mm"
            }
        except Exception as e:
            return {"error": f"Failed to fetch Open-Meteo data: {str(e)}"}
