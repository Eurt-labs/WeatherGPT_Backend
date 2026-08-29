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
    history: List[Dict[str, str]] = None,
    is_voice: bool = False
) -> AsyncGenerator[str, None]:
    """
    Streams tokens in real time from Google Gemma 4 31B (Free) via OpenRouter.
    """
    if history is None:
        history = []

    if is_voice:
        system_prompt = (
            f"You are WeatherGPT Voice, an ultra-fast AI meteorologist powered by Google Gemma 4.\n"
            f"Location: {location}\n"
            f"Live Weather: {weather_context}\n\n"
            f"CRITICAL INSTRUCTIONS FOR LOW LATENCY:\n"
            f"- Give a direct, punchy, 1-to-2 sentence answer in the user's language (English, Hindi, Marathi, Bengali, Tamil, Telugu, etc.).\n"
            f"- Never use markdown formatting or bullet points.\n"
            f"- Speak naturally for immediate voice playback."
        )
    else:
        system_prompt = (
            f"You are WeatherGPT, an advanced AI meteorologist powered by Google Gemma 4.\n"
            f"Location: {location}\n"
            f"Live Weather: {weather_context}\n\n"
            f"Guidelines:\n"
            f"- Provide actionable, concise weather advice in the user's language (English, Hindi, Marathi, Bengali, Tamil, Telugu, etc.).\n"
            f"- Explain atmospheric safety, rain probability, outdoor comfort, and clothing recommendations."
        )

    messages = [{"role": "system", "content": system_prompt}]
    for item in history[-4:]:
        messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": "https://weathergpt.ai",
        "X-Title": "WeatherGPT FastAPI Backend"
    }
    if OPENROUTER_API_KEY:
        headers["Authorization"] = f"Bearer {OPENROUTER_API_KEY}"

    payload = {
        "model": "google/gemma-4-31b-it:free",
        "stream": True,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 120 if is_voice else 450
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
            yield f"data: Connection failed: {str(e)}\n\n"
