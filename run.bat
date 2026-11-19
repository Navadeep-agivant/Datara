@echo off
echo ========================================================
echo Starting AI Data Quality & Anomaly Detection Agent
echo ========================================================

echo.
echo [1/2] Starting Backend Server (FastAPI on http://localhost:8000)...
start "Backend - FastAPI" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --port 8000"

echo.
echo [2/2] Starting Frontend UI (React + Vite on http://localhost:5173)...
start "Frontend - Vite" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================
echo Both servers are launching in separate windows!
echo - API Docs: http://localhost:8000/docs
echo - Web App:  http://localhost:5173
echo ========================================================
echo Sample dataset available at: datasets/online_store_orders_sample.csv
pause
