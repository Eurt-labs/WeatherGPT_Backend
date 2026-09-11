# WeatherGPT Ecosystem - Developer & Agent Guardrails (AGENTS.md)

> [!IMPORTANT]
> **MANDATORY READING FOR ALL AI AGENTS & TEAM DEVELOPERS**:
> This document defines the operational rules, architectural contracts, safety guardrails, and domain context for the entire **WeatherGPT** ecosystem.
> Follow these instructions strictly to prevent regressions, runtime crashes, quota depletion, or broken API contracts.

---

## 🌐 1. High-Level Ecosystem Architecture

WeatherGPT is India's premier multi-sector, AI-powered conversational weather and climate advisory platform (built for Smart India Hackathon - SIH 2026). It operates across **three synchronized repositories**:

```
                              ┌───────────────────────────────────┐
                              │     WeatherGPT_Android (Client)   │
                              │  - Kotlin / Jetpack Compose / M3  │
                              │  - Domain-Driven Design (DDD)     │
                              │  - Multi-Provider AI Routing      │
                              └─────────────────┬─────────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 │ (Online Mode)                                               │ (Offline Mode)
                 ▼                                                             ▼
┌───────────────────────────────────┐                         ┌───────────────────────────────────┐
│     WeatherGPT_Backend (Cloud)    │                         │      WeatherGPT_Local (PC Engine) │
│  - Hosted on Render (FastAPI)     │                         │  - FastAPI + llama-cpp-python     │
│  - Google Gemini 3.6 Flash        │                         │  - Qwen2.5 GGUF (7B / 3B / 1.5B)  │
│  - Rate Limiting (SlowAPI)        │                         │  - Zero-RAM Standalone or Server  │
│  - Supabase Auth & Sync           │                         │  - USB / Wi-Fi Android Bridge     │
└───────────────────────────────────┘                         └───────────────────────────────────┘
```

| Repository | Tech Stack | Primary Responsibilities | Deployment / Run Target |
| :--- | :--- | :--- | :--- |
| **`WeatherGPT_Android`** | Kotlin 2.0, Compose BOM, Material3, Coroutines | Native mobile interface, telemetry gathering, location provider, voice AI, SSE streaming chat, on-device SQLite | Android Devices (API 26+) |
| **`WeatherGPT_Backend`** | Python 3.14, FastAPI, Uvicorn, SlowAPI | Cloud AI inference via Gemini 3.6 Flash, Supabase auth/sync, fallback telemetry | Hosted on **Render** (`https://weathergpt-backend-m5kk.onrender.com`) |
| **`WeatherGPT_Local`** | Python 3.14, FastAPI, llama-cpp-python | Zero-internet offline LLM inference, quantized GGUF execution, live CLI testing | Local Windows/Linux PC (`localhost:8000`) |

---

## 🚫 2. Critical Guardrails ("DO NOT BREAK" Rules)

To protect the project from accidental regressions, agents and developers must obey these strict rules:

### A. The Streaming Protocol Contract (SSE)
- **Format**: All AI chat stream endpoints (`/api/ai/chat-stream`) MUST output Server-Sent Events in the exact format:
  ```
  data: <token_text>\n\n
  ...
  data: [DONE]\n\n
  ```
- **Rule**: NEVER change this payload to JSON arrays, chunks with different keys, or plain text. Doing so breaks `OpenRouterService.kt` on Android and `chat_cli.py` on PC.

### B. Conversational Proportionality & Brevity
- **The Bug We Fixed**: Earlier prompts generated 400-word essays when the user simply said "hello".
- **Rule**:
  - **Standard Chat**: Output EXACTLY **1 cohesive paragraph of 3 to 4 sentences (50–80 words)**. Never output bullet points, markdown tables, or giant lists unless explicitly in `detail_mode`.
  - **Voice AI Mode**: Output STRICTLY **1 to 2 warm, spoken sentences (maximum 35 words)** suitable for Text-to-Speech (TTS). ZERO markdown, zero asterisks, zero emojis.
  - **Detail Mode**: Output 2 to 3 structured paragraphs (150–250 words) only when the user explicitly requests deep details or analysis.

### C. Live Meteorological Grounding (No Pure Hallucinations)
- Every response must be grounded in the live **Open-Meteo telemetry** provided in `weather_context`:
  - Barometric pressure trends (falling pressure = approaching rain/storm).
  - Relative humidity & dew point proximity.
  - Topsoil moisture ($m^3/m^3$) & FAO Evapotranspiration ($ET_0$ mm/day) for agricultural queries.
  - River discharge and precipitation accumulation for flood risk.
- **Rule**: Never answer purely from static training data when dynamic weather telemetry is provided in the prompt.

### D. Proactive Profile-Driven Follow-Ups
- At the end of every response, the AI must conclude with **ONE brief, caring question** tailored to the user's profile details (Name, Sector, Crops, Land Area, or Travel destination).
  - *Example*: *"Would you like to know the best pesticide spraying window for your 5 Acres of Wheat today?"*

### E. Python Multi-Line Prompt Formatting (Render Deployment Safety)
- **The Bug We Fixed**: Unescaped newlines between double quotes inside f-strings caused `SyntaxError: unterminated f-string literal`, crashing Render deployment.
- **Rule**: Always format multi-line prompts using explicit line continuation with closing quotes:
  ```python
  # CORRECT:
  system_prompt = (
      f"Line 1 text.\\n"\n
      f"Line 2 text with {variable}.\\n"\n
      f"Line 3 final instruction."
  )

  # NEVER DO THIS:
  system_prompt = (
      f"Line 1 text.
      Line 2 text."
  )
  ```
- Always validate Python files with `python -m py_compile <file>` before committing!

### F. Android SQLite Connection Safety
- In `ChatDatabaseHelper.kt`, NEVER wrap `readableDatabase` or `writableDatabase` in `.use { }` blocks when serving UI queries. Calling `.use` prematurely closes the underlying SQLite connection pool and crashes the app on subsequent clicks. Only close `Cursor` objects.

### G. Android Location & Geocoding Fallbacks
- In `LocationProvider.kt`, always check provider accuracy (`loc.accuracy < lastBestLocation.accuracy`).
- In `LocationData.kt`, NEVER set non-Indian defaults (like San Francisco). Use `New Delhi, India` (`28.6139°N, 77.2090°E`) as the baseline fallback if GPS permission is denied or pending.

### H. PC Server Memory & Port Management
- The offline LLM server on port 8000 holds 2–5 GB of GGUF weights in RAM.
- When shutting down, always free memory and unbind the socket:
  ```bash
  python main.py --stop
  ```
- Or type `/stop` directly in `chat_cli.py`.
- When starting `main.py`, it automatically detects and terminates any orphan zombie processes on port 8000 before binding.

### I. Testing Scripts & Batch Files
- **Rule**: Do NOT create stray `.bat` files for testing. The user can run and test everything with standard Python commands:
  ```bash
  python main.py           # Start server
  python main.py --stop    # Stop server
  python chat_cli.py       # Interactive CLI test
  ```

### J. Git Commit Discipline
- **Rule**: As instructed by the user: **DO NOT commit everything at once**.
  - Commit modularly and cleanly according to the specific domain or bug fixed.
  - Write descriptive, conventional commit messages (`feat(...)`, `fix(...)`, `refactor(...)`, `docs(...)`).

---

## 📁 3. Codebase Structure & Directory Guide

### A. Android Client (`WeatherGPT_Android`)
```
app/src/main/java/com/example/weathergpt_android/
├── MainActivity.kt                      # Root Activity, theme state, bottom navigation container
├── core/
│   ├── network/
│   │   ├── OpenRouterService.kt         # Streaming SSE client, HTTP 402 self-healing, Gemini AI Studio link
│   │   └── HmacSigner.kt                # HMAC-SHA256 signature generator for backend anti-tamper
│   ├── theme/
│   │   ├── Color.kt                     # OLED Pitch Black, Clean Minimal Light, Champagne Beige
│   │   ├── Theme.kt                     # Material3 Light/Dark theme provider & status bar controller
│   │   └── ThemePreferences.kt          # SharedPreferences persistence for theme selection
│   └── components/
│       ├── TopIslandHeader.kt           # Floating header island (Profile, Notifications, Live Widget)
│       └── FloatingBottomNavBar.kt      # Bottom navigation bar with raised Center Mic FAB
│
└── domain/
    ├── weather/
    │   ├── model/LiveWeatherData.kt     # Deep meteorological model (ET0, soil moisture, flood risk)
    │   ├── repository/OpenMeteoRepository.kt # Live Open-Meteo REST client & physical calculations
    │   └── ui/HomeScreen.kt             # Main weather dashboard, metric cards, scenario transitions
    ├── location/
    │   ├── provider/LocationProvider.kt # Fused GPS/Network location provider & Android Geocoder
    │   ├── cache/LocationCache.kt       # Persistent on-device location disk caching
    │   └── model/LocationData.kt        # City, Region, Country, Lat, Lon data model
    ├── assistant/
    │   ├── ui/GptChatScreen.kt          # Live streaming chat UI, sector chips, profile grounding
    │   └── database/ChatDatabaseHelper.kt # On-device SQLite message history and sessions
    ├── voice/
    │   ├── ui/VoiceAiScreen.kt          # Morphing fluid voice sphere & native Android TTS
    │   └── sherpa/SherpaOnnxEngine.kt   # Multilingual on-device ASR/TTS/VAD engine
    ├── news/ui/NewsScreen.kt            # Weather news, IMD advisories, radar updates
    ├── settings/ui/SettingsScreen.kt    # Units (°C/°F), PC Server IP pairing, theme selector
    ├── profile/ui/ProfileSheet.kt       # User profile modal (Crops, Land size, Sector focus)
    └── notifications/ui/NotificationSheet.kt # Emergency meteorological alerts modal
```

### B. Cloud Backend (`WeatherGPT_Backend`)
```
WeatherGPT_Backend/
├── main.py                              # FastAPI entry point, SlowAPI rate limiting, CORS
├── services/
│   ├── ai_service.py                    # Gemini 3.6 Flash streaming prompt engine & SSE generator
│   ├── weather_service.py               # Open-Meteo live proxy & telemetry synthesis
│   └── supabase_service.py              # Supabase user authentication & database syncing
├── models/schemas.py                    # Pydantic request/response schemas
├── requirements.txt                     # FastAPI, Uvicorn, SlowAPI, httpx, sse-starlette
└── Procfile / render.yaml               # Render deploy command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### C. Local PC Engine (`WeatherGPT_Local/PC`)
```
WeatherGPT_local/PC/
├── main.py                              # FastAPI GGUF server, interactive model selector, --stop handler
├── model_engine.py                      # llama-cpp-python wrapper, thread allocation, context management
├── config.py                            # Models catalog (Qwen2.5 7B/3B/1.5B), system prompts, host/port
├── chat_cli.py                          # Interactive terminal chat client, token streaming, /fetch Open-Meteo
├── download_model.py                    # Automated HuggingFace GGUF downloader with resume support
├── requirements.txt                     # fastapi, uvicorn, llama-cpp-python, requests, psutil
└── models/                              # Local storage directory for .gguf quantized model files
```

---

## 🔑 4. Secrets, Configuration & Environment Variables

| Variable | Location | Description |
| :--- | :--- | :--- |
| `OPENROUTER_API_KEY` | Android `local.properties` & Render Env | OpenRouter / Google AI Studio API key for cloud LLM inference. |
| `GEMINI_API_KEY` | Android `local.properties` & Render Env | Direct Google AI Studio key (`AIzaSy...`) for 15 RPM free tier. |
| `SUPABASE_URL` | Render Environment Variables | Supabase project URL for cloud authentication. |
| `SUPABASE_KEY` | Render Environment Variables | Supabase service/anon key. |
| `WEATHERGPT_URL` | PC Environment (Optional) | Override server URL for `chat_cli.py` (defaults to `http://localhost:8000`). |

> [!CAUTION]
> Never commit `.env` files, `local.properties`, or raw API keys into Git repositories!

---

## 🛠️ 5. Standard Developer Runbooks

### 1. Running & Verifying the Android App
```bash
# In WeatherGPT_Android directory:
./gradlew assembleDebug
# Or run directly from Android Studio onto a connected device or emulator.
```

### 2. Connecting Android to Local PC Offline Engine
- **Method A: USB Cable (Zero Latency - Recommended)**
  ```bash
  adb reverse tcp:8000 tcp:8000
  ```
  In Android Settings ⚙️ -> Select **PC (USB)** -> Connect to `http://localhost:8000`.
- **Method B: Same Wi-Fi / Hotspot**
  Find PC IP address (e.g. `192.168.1.15`).
  In Android Settings ⚙️ -> Select **PC (Wi-Fi)** -> Connect to `http://192.168.1.15:8000`.

### 3. Running & Testing the Local PC Server
```bash
# In WeatherGPT_local/PC directory:

# Start server:
python main.py

# Test interactively via terminal CLI:
python chat_cli.py

# Cleanly stop server and release port 8000 and RAM:
python main.py --stop
```

### 4. Running the Cloud Backend Locally
```bash
# In WeatherGPT_Backend directory:
uvicorn main:app --reload --port 8000
```

---

## 👥 6. Team Collaboration Checklist

Before submitting a Pull Request or pushing changes:
1. [ ] **Syntax Check**: All Python files pass `python -m py_compile <file>`.
2. [ ] **Streaming Check**: SSE response matches `data: <token>\n\n` -> `data: [DONE]\n\n`.
3. [ ] **Prompt Check**: No unescaped newlines in f-strings; answers remain concise (3-4 sentences in chat, 1-2 in voice).
4. [ ] **Database Check**: No `.use { }` calls on SQLite instances in Android.
5. [ ] **Secrets Check**: No API keys or credentials exposed in committed code.
6. [ ] **Clean Git History**: Commits are focused, atomic, and properly described.
