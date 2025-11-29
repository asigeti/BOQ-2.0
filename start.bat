@echo off
echo ========================================
echo   ConstructionAI Pro - Startup Script
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/4] Starting Docker services (PostgreSQL + Redis)...
cd /d "%~dp0"
docker-compose up -d db redis
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start Docker services!
    pause
    exit /b 1
)
echo [OK] Docker services started
echo.

REM Wait for database to be ready
echo [2/4] Waiting for database to be ready...
timeout /t 5 /nobreak >nul
echo [OK] Database ready
echo.

echo [3/4] Starting Backend (Port 6000)...
start "BOQ Backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 6000"
echo [OK] Backend starting...
echo.

REM Wait for backend to initialize
timeout /t 3 /nobreak >nul

echo [4/4] Starting Frontend (Port 6001)...
start "BOQ Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- -p 6001"
echo [OK] Frontend starting...
echo.

echo ========================================
echo   All services started successfully!
echo ========================================
echo.
echo Backend:  http://localhost:6000
echo Frontend: http://localhost:6001
echo API Docs: http://localhost:6000/docs
echo.
echo Press any key to open the application in your browser...
pause >nul

start http://localhost:6001

echo.
echo To stop all services:
echo 1. Close the Backend and Frontend terminal windows
echo 2. Run: docker-compose down
echo.
pause
