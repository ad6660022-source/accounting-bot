@echo off
title Accounting Bot - Start

docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Desktop is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Docker is running. Starting containers...
cd /d "%~dp0"
docker-compose up -d --build

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo  Bot started successfully!
    echo  API / Mini App: http://localhost:8000
    echo  Stop: run Ostanovit.bat
    echo ==========================================
) else (
    echo.
    echo ERROR: Failed to start containers.
    echo Check logs: docker-compose logs
)

pause
