@echo off
title WeatherGPT FastAPI Cloud Engine
echo ========================================================
echo       Starting WeatherGPT FastAPI Backend Server
echo ========================================================
echo.
echo Installing / Verifying dependencies...
pip install -r requirements.txt
echo.
echo Starting Uvicorn on http://localhost:8000 ...
python main.py
pause
