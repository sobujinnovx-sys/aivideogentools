@echo off
echo ========================================
echo   AI Video Generator - Dev Startup
echo ========================================
echo.

echo [1/3] Starting Redis...
start "Redis" /MIN "E:\laragon\bin\redis\redis-x64-5.0.14.1\redis-server.exe"
timeout /t 2 /nobreak >nul
echo.

echo [2/3] Starting backend on port 8001...
cd backend
start "Backend" cmd /k "python -m uvicorn app.main:app --reload --port 8001"
cd ..
echo.

echo [3/3] Starting frontend...
cd frontend
start "Frontend" cmd /k "npm run dev"
cd ..
echo.

echo ========================================
echo   Services starting...
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8001
echo   API Docs: http://localhost:8001/docs
echo ========================================
pause
