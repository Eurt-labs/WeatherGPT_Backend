# -*- coding: utf-8 -*-
import os
import httpx
from typing import AsyncGenerator, List, Dict
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

async def stream_google_gemma_ai(
    user_message: str,
    location: str,
    weather_context: str,
    sector_focus: str = "general",
    history: List[Dict[str, str]] = None,
    is_voice: bool = False
) -> AsyncGenerator[str, None]:
    """
    Multi-Sector Google Gemma 4 31B Streaming Reasoning Engine.
    Handles Natural Language queries for Farmers, Disaster Managers, Pilots, Fishermen & Researchers
    across Indian languages (Hindi, Marathi, Bengali, Tamil, Telugu, English).
    """
    if history is None:
        history = []

    if is_voice:
        system_prompt = (
            f"You are WeatherGPT Voice powered by Google Gemma 4.\n"
            f"Location: {location}\n"
            f"Live Multi-Sector Meteorological Context: {weather_context}\n\n"
            f"CRITICAL RULES:\n"
            f"1. Answer concisely in 1 to 2 spoken sentences in the exact language spoken by the user (Hindi, Marathi, Bengali, Tamil, Telugu, or English).\n"
            f"2. Never use bullet points, asterisks, or markdown formatting.\n"
            f"3. Be natural, direct, and actionable for farmers, citizens, and travelers."
        )
    else:
        system_prompt = (
            f"You are WeatherGPT, India's premier Conversational Weather & Climate Intelligence Platform powered by Google Gemma 4.\n"
            f"Location: {location}\n"
            f"Sector Focus: {sector_focus.upper()}\n"
            f"Live Multi-Sector Meteorological Context: {weather_context}\n\n"
            f"CAPABILITIES & GUIDELINES:\n"
            f"- **Agriculture (Kisan AI)**: Provide precise crop-weather advisories, irrigation timing based on soil moisture, and pesticide spray suitability.\n"
            f"- **Disaster & Flood**: Alert on river discharge risks, severe heatwaves, lightning, and emergency safety guidelines.\n"
            f"- **Aviation & Travel**: Advise on cloud ceilings, visibility (km), crosswinds, and turbulence.\n"
            f"- **Climate Trends**: Explain temperature anomalies, past 7-day rainfall patterns, and monsoon behavior.\n"
            f"- **Multilingual**: Respond fluently in the user's language (Hindi, English, Marathi, Bengali, Tamil, Telugu, etc.). Keep formatting clean and helpful."
        )

    messages = [{"role": "system", "content": system_prompt}]
    for item in history[-4:]:
        messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": "https://weathergpt.ai",
        "X-Title": "WeatherGPT Multi-Sector AI Engine"
    }
    if OPENROUTER_API_KEY:
        headers["Authorization"] = f"Bearer {OPENROUTER_API_KEY}"

    payload = {
        "model": "google/gemma-4-31b-it:free",
        "stream": True,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 120 if is_voice else 500
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            async with client.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status_code != 200:
                    yield f"data: Error HTTP {response.status_code}\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        yield f"{line}\n\n"
        except Exception as e:
            yield f"data: Connection error: {str(e)}\n\n"
