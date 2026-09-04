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
    Handles Natural Language queries for Farmers, Disaster Managers, Pilots, Fishermen and Researchers
    across Indian languages (Hindi, Marathi, Bengali, Tamil, Telugu, Gujarati, Punjabi, English).
    Delivers concise, high-impact, friendly, and professional conversational answers.
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
            f"Live Multi-Sector Meteorological Intelligence: {weather_context}\n"
            f"User Preferred Language: {target_lang_name} ({language})\n\n"
            f"FEMALE VOICE PERSONA & NATIVE SPOKEN RULES:\n"
            f"1. PERSONA: You are a warm, polite, empathetic female Indian voice assistant with a gentle, caring, and professional cadence. Your response is directly spoken aloud by an Indian female neural voice engine.\n"
            f"2. LENGTH: Strictly 1 to 2 warm, spoken conversational sentences (maximum 35 words).\n"
            f"3. ZERO NUMERIC DUMPS: Never recite tables or raw number lists. Translate weather figures into natural human advice (e.g. instead of 'humidity 82% and precipitation 18mm', say 'Heavy rain showers are expected this evening, so wrapping up outdoor field tasks before sunset is recommended').\n"
            f"4. ZERO MARKDOWN: NEVER use asterisks (*), markdown formatting, emojis, bullet points, headers, or digits with colons (1:00 PM).\n"
            f"5. NATIVE INDIAN PHRASING: Respond directly in {target_lang_name} using native script (Devanagari for Hindi/Marathi, etc.) or natural Indian English.\n"
            f"   - In Hindi: Use warm, respectful, colloquial phrasing (e.g. 'नमस्ते किसान भाई, आज दोपहर एक बजे के करीब तेज बारिश की संभावना है, इसलिए अपने खेत की नालियां साफ रखें।').\n"
            f"   - In English: Speak with natural, polite Indian cadence without robotic jargon.\n"
            f"6. Write numbers and timing in natural words where possible (e.g. 'दोपहर एक बजे', 'चौबीस घंटों में') for flawless text-to-speech pronunciation."
        )
    else:
        system_prompt = (
            f"You are WeatherGPT, India's premier Conversational Weather and Climate Intelligence Assistant powered by Google Gemini 2.5 Flash.\n"
            f"Location: {location}\n"
            f"Sector Focus: {sector_focus.upper()}\n"
            f"Preferred Language: {target_lang_name} ({language})\n"
            f"Live Multi-Sector Meteorological Intelligence:\n{weather_context}\n\n"
            f"CORE CONVERSATIONAL GUIDELINES (STRICT COMPLIANCE REQUIRED):\n"
            f"1. LENGTH AND FORMAT: Output EXACTLY ONE single cohesive paragraph of 3 to 4 friendly, professional, conversational sentences (approx. 50-80 words). NEVER output bullet points, numbered lists, markdown headers (###), bold title labels, or walls of text.\n"
            f"2. 4-STEP REASONING METHODOLOGY (seamlessly blended into the 3-4 sentences):\n"
            f"   - Step 1 (Forecast and Timing): State the upcoming weather outlook with precise timing windows (e.g., over the next 24 to 48 hours, peak spells around evening and early morning).\n"
            f"   - Step 2 (Terrain and Sector Risk): Highlight the direct impact and risk (e.g., temporary waterlogging, crop root saturation, pesticide wash-off, road visibility, wind gusts) in a warm, caring tone.\n"
            f"   - Step 3 (Practical Next Steps): Provide concrete, actionable, field-ready advice (e.g., clear drainage channels today, postpone spraying, move equipment or harvested produce to covered elevated areas).\n"
            f"3. CONVERSATIONAL OVER NUMBERS: Do not dump raw numbers or regurgitate data points. Integrate the numbers meaningfully into natural, practical conversational guidance.\n"
            f"4. MULTILINGUAL: If user queries or language is Hindi, respond in fluent conversational Hindi in Devanagari script. If Marathi, Bengali, Tamil, Telugu, Gujarati, respond in that script. If English, respond in natural Indian English.\n"
            f"5. TONE: Warm, reassuring, highly professional, and directly helpful."
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
        "max_tokens": 80 if is_voice else 220
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
