@echo off
cd /d "%~dp0"
chcp 65001 >nul
title WorkerH - Paleidimas ir Demonstracija
echo ===========================================================================
echo WorkerH - Programos paleidimas be jokio kodo redaktoriaus (VS Code)
echo ===========================================================================

if not exist "backend\venv\Scripts\python.exe" (
    echo [1/4] Kuriama Python virtuali aplinka...
    python -m venv backend\venv
    backend\venv\Scripts\pip install -r backend\requirements.txt
)

echo [2/4] Uzpildoma SQLite duomenu baze ir patikrinami visi 15 API metodu...
set PYTHONIOENCODING=utf-8
backend\venv\Scripts\python.exe backend\demo_test.py

echo.
echo [3/4] Paleidziama kliento puse (Vue.js Front-End -> http://localhost:5173)...
start "WorkerH Front-End (http://localhost:5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [4/4] Paleidziamas Flask REST API serveris (http://localhost:5000)...
echo ---------------------------------------------------------------------------
echo  - Web aplikacija (Front-End):       http://localhost:5173
echo  - Swagger UI (OpenAPI testavimas):  http://localhost:5000/api/docs
echo  - OpenAPI JSON specifikacija:       http://localhost:5000/api/openapi.json
echo  - Prisijungimai:
echo      Admin:        admin / admin123
echo      Vadybininkas: vadybininkas / vadyba123
echo      Darbuotojas:  jonas / darbas123
echo ---------------------------------------------------------------------------
cd /d "%~dp0backend"
venv\Scripts\python.exe app.py
pause
