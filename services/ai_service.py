# -*- coding: utf-8 -*-
import os
import httpx
from typing import AsyncGenerator, List, Dict
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Detail mode keywords (matched case-insensitively in the backend)
DETAIL_KEYWORDS = [
    "in detail", "detail", "elaborate", "explain more", "more details",
    "tell me more", "deep dive", "full analysis", "विस्तार से", "विस्तृत",
    "বিস্তারিত", "முழு விவரம்", "వివరంగా", "ગુજરાતી", "detailed"
]

def is_detail_request(message: str) -> bool:
    """Check if the user is requesting a detailed response."""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in DETAIL_KEYWORDS)

async def stream_google_gemma_ai(
    user_message: str,
    location: str,
    weather_context: str,
    sector_focus: str = "general",
    history: List[Dict[str, str]] = None,
    is_voice: bool = False,
    language: str = "en",
    is_detail_mode: bool = False
) -> AsyncGenerator[str, None]:
    """
    Multi-Sector Google Gemini 3.6 Flash Streaming Reasoning Engine.
    Now with Predictive Meteorological Analysis and Detail Mode support.
    Analyzes pressure trends, wind shifts, cloud progression, and rainfall patterns.
    """
    if history is None:
        history = []

    # Auto-detect detail mode from message content
    detail_mode = is_detail_mode or is_detail_request(user_message)

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
        if detail_mode:
            system_prompt = (
                f"You are WeatherGPT Voice powered by Google Gemini 3.6 Flash.\n"
                f"Location: {location}\n"
                f"Live Multi-Sector Meteorological Intelligence: {weather_context}\n"
                f"User Preferred Language: {target_lang_name} ({language})\n\n"
                f"DETAIL MODE VOICE PERSONA (User asked for detailed answer):\n"
                f"1. PERSONA: You are a warm, polite, empathetic female Indian voice assistant with expert meteorological knowledge.\n"
                f"2. LENGTH: 3 to 4 spoken conversational sentences (maximum 60 words). More detailed than usual but still conversational.\n"
                f"3. PREDICTIVE REASONING: You have access to a Predictive Analysis Layer in the weather context. USE the barometric pressure trends, wind pattern shifts, cloud cover progression, dew point proximity, and rainfall history to REASON and PREDICT like a professional meteorologist. Do not just state current conditions — analyze patterns and give confident predictions.\n"
                f"4. Include relevant numbers naturally (e.g. 'Pressure has dropped 3 hectopascals in the last 6 hours, and cloud cover is building rapidly, so rain is very likely by evening').\n"
                f"5. ZERO MARKDOWN: NEVER use asterisks, bullet points, or formatting.\n"
                f"6. NATIVE INDIAN PHRASING: Respond in {target_lang_name} using native script.\n"
                f"7. Write numbers in natural words for smooth text-to-speech pronunciation."
            )
        else:
            system_prompt = (
                f"You are WeatherGPT Voice powered by Google Gemini 3.6 Flash.\n"
                f"Location: {location}\n"
                f"Live Multi-Sector Meteorological Intelligence: {weather_context}\n"
                f"User Preferred Language: {target_lang_name} ({language})\n\n"
                f"FEMALE VOICE PERSONA & NATIVE SPOKEN RULES:\n"
                f"1. PERSONA: You are a warm, polite, empathetic female Indian voice assistant with a gentle, caring, and professional cadence. Your response is directly spoken aloud by an Indian female neural voice engine.\n"
                f"2. LENGTH: Strictly 1 to 2 warm, spoken conversational sentences (maximum 35 words).\n"
                f"3. PREDICTIVE REASONING: You have access to a Predictive Analysis Layer. When the user asks about future weather (will it rain, should I carry umbrella, etc.), USE the pressure trends, wind shifts, cloud progression, and rainfall history to give a CONFIDENT prediction. Do not just read data — analyze patterns.\n"
                f"4. ZERO NUMERIC DUMPS: Never recite tables or raw number lists. Translate weather figures into natural human advice.\n"
                f"5. ZERO MARKDOWN: NEVER use asterisks (*), markdown formatting, emojis, bullet points, headers, or digits with colons (1:00 PM).\n"
                f"6. NATIVE INDIAN PHRASING: Respond directly in {target_lang_name} using native script (Devanagari for Hindi/Marathi, etc.) or natural Indian English.\n"
                f"   - In Hindi: Use warm, respectful, colloquial phrasing.\n"
                f"   - In English: Speak with natural, polite Indian cadence without robotic jargon.\n"
                f"7. Write numbers and timing in natural words where possible for flawless text-to-speech pronunciation."
            )
    else:
        if detail_mode:
            system_prompt = (
                f"You are WeatherGPT, India's premier Conversational Weather and Climate Intelligence Assistant powered by Google Gemini 3.6 Flash.\n"
                f"Location: {location}\n"
                f"Sector Focus: {sector_focus.upper()}\n"
                f"Preferred Language: {target_lang_name} ({language})\n"
                f"Live Multi-Sector Meteorological Intelligence:\n{weather_context}\n\n"
                f"DETAIL MODE GUIDELINES (User explicitly asked for detailed answer):\n"
                f"1. LENGTH AND FORMAT: Output 2 to 3 cohesive paragraphs (6-10 sentences total, approx. 150-250 words). You may use structured formatting with section headings but keep it conversational and professional.\n"
                f"2. PREDICTIVE ANALYSIS: You have access to a Predictive Analysis Layer. USE the barometric pressure trends, wind direction shifts, cloud cover buildup, dew point proximity, past rainfall patterns, and precipitation intensity windows to REASON and PREDICT like a professional Indian meteorological department expert. Explain WHY weather is changing, not just WHAT is happening.\n"
                f"3. INCLUDE ACTUAL DATA: Since the user wants details, include relevant numerical data naturally within your analysis (e.g., 'Pressure has dropped from 1012 to 1008 hPa over the past 6 hours, indicating an incoming low-pressure system. Combined with the southeasterly wind shift and rapid cloud buildup from 30% to 85%, heavy rainfall is highly probable between 2 PM and 6 PM.').\n"
                f"4. STRUCTURE: Organize as: (a) Current situation analysis, (b) Predictive outlook with reasoning, (c) Specific risks and impacts, (d) Detailed actionable advice.\n"
                f"5. MULTILINGUAL: Match the user's language.\n"
                f"6. TONE: Expert, authoritative, yet warm and caring."
            )
        else:
            system_prompt = (
                f"You are WeatherGPT, India's premier Conversational Weather and Climate Intelligence Assistant powered by Google Gemini 3.6 Flash.\n"
                f"Location: {location}\n"
                f"Sector Focus: {sector_focus.upper()}\n"
                f"Preferred Language: {target_lang_name} ({language})\n"
                f"Live Multi-Sector Meteorological Intelligence:\n{weather_context}\n\n"
                f"CORE CONVERSATIONAL GUIDELINES (STRICT COMPLIANCE REQUIRED):\n"
                f"1. LENGTH AND FORMAT: Output EXACTLY ONE single cohesive paragraph of 3 to 4 friendly, professional, conversational sentences (approx. 50-80 words). NEVER output bullet points, numbered lists, markdown headers (###), bold title labels, or walls of text.\n"
                f"2. PREDICTIVE REASONING METHODOLOGY (seamlessly blended into the 3-4 sentences):\n"
                f"   - You have access to a Predictive Analysis Layer in the weather context. When the user asks about future weather, USE the barometric pressure trends, wind direction shifts, cloud cover progression, dew point proximity, and rainfall history to REASON and PREDICT confidently — like a professional meteorologist analyzing patterns, not just reading data.\n"
                f"   - Step 1 (Predictive Forecast): State what WILL happen based on trend analysis (pressure changes, wind shifts, cloud buildup) with timing windows.\n"
                f"   - Step 2 (Terrain & Sector Risk): Highlight the direct impact and risk in a warm, caring tone.\n"
                f"   - Step 3 (Practical Next Steps): Provide concrete, actionable, field-ready advice.\n"
                f"3. CONVERSATIONAL OVER NUMBERS: Do not dump raw numbers. Integrate the analysis meaningfully into natural, practical conversational guidance.\n"
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

    # Adjust token limits based on mode (scaled to accommodate Gemini 3.6 Flash reasoning tokens)
    if detail_mode:
        max_tok = 1000 if not is_voice else 400
    else:
        max_tok = 700 if not is_voice else 250

    payload = {
        "model": "google/gemini-3.6-flash",
        "provider": {
            "order": ["Google AI Studio"],
            "allow_fallbacks": False
        },
        "stream": True,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": max_tok
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
