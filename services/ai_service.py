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
    is_voice: bool = False,
    language: str = "en"
) -> AsyncGenerator[str, None]:
    """
    Multi-Sector Google Gemini 2.5 Flash Streaming Reasoning Engine.
    Handles Natural Language queries for Farmers, Disaster Managers, Pilots, Fishermen & Researchers
    across Indian languages (Hindi, Marathi, Bengali, Tamil, Telugu, Gujarati, English).
    """
    if history is None:
        history = []

    lang_name_map = {
        "hi": "Hindi (हिन्दी)",
        "mr": "Marathi (मराठी)",
        "bn": "Bengali (বাংলা)",
        "ta": "Tamil (தமிழ்)",
        "te": "Telugu (తెలుగు)",
        "gu": "Gujarati (ગુજરાતી)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
        "en": "Indian English"
    }
    target_lang_name = lang_name_map.get((language or "en").lower(), "Hindi or English")

    if is_voice:
        system_prompt = (
            f"You are WeatherGPT Voice powered by Google Gemini 2.5 Flash.\n"
            f"Location: {location}\n"
            f"Live Multi-Sector Meteorological Context: {weather_context}\n"
            f"User Preferred Language: {target_lang_name} ({language})\n\n"
            f"VOICE & MULTILINGUAL INTELLIGENCE INSTRUCTIONS:\n"
            f"1. Detect the user's spoken language or use the target preferred language ({target_lang_name}).\n"
            f"2. RESPOND DIRECTLY IN THAT EXACT LANGUAGE.\n"
            f"   - If Hindi, or if user query is in Hindi/Hinglish: Respond in pure, natural, conversational spoken Hindi in Devanagari script (e.g., 'नमस्ते! आज दिल्ली में आसमान साफ रहेगा और तापमान 32 डिग्री रहेगा।').\n"
            f"   - If Marathi: Respond in fluent conversational Marathi in Devanagari script (मराठी).\n"
            f"   - If Bengali: Respond in fluent conversational Bengali script (বাংলা).\n"
            f"   - If Tamil: Respond in fluent conversational Tamil script (தமிழ்).\n"
            f"   - If Telugu: Respond in fluent conversational Telugu script (తెలుగు).\n"
            f"   - If English: Respond in natural Indian conversational English.\n"
            f"3. Keep your response strictly to 1 to 2 spoken conversational sentences.\n"
            f"4. NEVER use asterisks (*), markdown formatting, emojis, bullet points, or numbers in digits that cannot be read aloud easily.\n"
            f"5. Speak warmly and informatively, perfectly optimized for natural text-to-speech audio readout."
        )
    else:
        system_prompt = (
            f"You are WeatherGPT, India's premier Conversational Weather & Climate Intelligence Platform powered by Google Gemini 2.5 Flash.\n"
            f"Location: {location}\n"
            f"Sector Focus: {sector_focus.upper()}\n"
            f"Preferred Language: {target_lang_name} ({language})\n"
            f"Live Multi-Sector Meteorological Context: {weather_context}\n\n"
            f"CAPABILITIES & GUIDELINES:\n"
            f"- **Agriculture (Kisan AI)**: Provide precise crop-weather advisories, irrigation timing based on soil moisture, and pesticide spray suitability.\n"
            f"- **Disaster & Flood**: Alert on river discharge risks, severe heatwaves, lightning, and emergency safety guidelines.\n"
            f"- **Aviation & Travel**: Advise on cloud ceilings, visibility (km), crosswinds, and turbulence.\n"
            f"- **Climate Trends**: Explain temperature anomalies, past 7-day rainfall patterns, and monsoon behavior.\n"
            f"- **Multilingual**: Respond fluently in {target_lang_name} or the user's chosen language. Keep formatting clean and helpful."
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
        "model": "google/gemini-2.5-flash",
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
