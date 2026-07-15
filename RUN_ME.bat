@echo off
title RIOS - One Click Start
echo ================================================
echo RIOS - Recursive Intelligence Operating System
echo One-Click Start (Windows)
echo ================================================
echo.

if not exist backend\requirements.txt (
  echo ERROR: backend folder not found! 
  echo Clone with: git clone -b arena/019f67fb-arenatest-scaffolding https://github.com/Shresht-2009/arenaTest_Scaffolding.git
  pause
  exit /b
)

if "%GROQ_API_KEY%"=="" (
  echo Groq API Key not found in environment.
  echo Get free key at https://console.groq.com
  echo.
  set /p GROQ_API_KEY=Enter your GROQ_API_KEY (gsk_...): 
)

echo [1/4] Creating .env...
(
echo GROQ_API_KEY=%GROQ_API_KEY%
echo GROQ_MODEL=openai/gpt-oss-120b
echo GROQ_BASE_URL=https://api.groq.com/openai/v1
) > backend\.env

echo [2/4] Installing Python dependencies...
python -m pip install -q -r backend\requirements.txt

echo [3/4] Starting Backend on http://localhost:8000 ...
start "RIOS Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 5 /nobreak >nul

echo [4/4] Starting Frontend on http://localhost:3000 ...
cd frontend
if not exist node_modules (
  call npm install
)
start "RIOS Frontend" cmd /k "npm run dev"
cd ..
echo.
echo DONE! Backend http://localhost:8000/docs Frontend http://localhost:3000
echo Keep both windows open. Open http://localhost:3000
pause
