@echo off
echo ========================================
echo   AI Video Generator - Dev Startup
echo ========================================
echo.

echo [1/4] Starting PostgreSQL and Redis via Docker...
docker-compose up -d postgres redis
echo.

echo [2/4] Waiting for services...
timeout /t 5 /nobreak >nul
echo.

echo [3/4] Starting backend...
cd backend
start "Backend" cmd /k "python -m uvicorn app.main:app --reload --port 8000"
cd ..
echo.

echo [4/4] Starting frontend...
cd frontend
start "Frontend" cmd /k "npm run dev"
cd ..
echo.

echo ========================================
echo   Services starting...
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo ========================================
pause
