@echo off
REM ============================================================================
REM Schedule Generator - Cloudflare Tunnel Startup Script (Windows)
REM ============================================================================
REM This script starts both the backend and Cloudflare Tunnel together.
REM When you stop the tunnel (Ctrl+C), it automatically stops the backend too.
REM ============================================================================

echo.
echo ========================================
echo  Schedule Generator - Cloudflare Tunnel
echo ========================================
echo.

REM Check if cloudflared is installed
where cloudflared >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] cloudflared is not installed!
    echo.
    echo Please install it first:
    echo   winget install --id Cloudflare.cloudflared
    echo.
    echo Or download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
    echo.
    pause
    exit /b 1
)

echo [1/3] Starting backend server...
echo.

REM Start backend in background and save PID
start /B python run_app.py
timeout /t 2 /nobreak >nul

REM Check if backend started successfully
curl -s http://localhost:8000/docs >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    timeout /t 3 /nobreak >nul
    curl -s http://localhost:8000/docs >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNING] Backend may not have started properly.
        echo           Check if port 8000 is already in use.
        echo.
    ) else (
        echo [OK] Backend is running on http://localhost:8000
        echo.
    )
) else (
    echo [OK] Backend is running on http://localhost:8000
    echo.
)

echo [2/3] Starting Cloudflare Tunnel...
echo.
echo Choose tunnel mode:
echo   1) Quick Tunnel (temporary URL, no config needed)
echo   2) Named Tunnel (permanent URL, requires setup)
echo.
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo Starting quick tunnel...
    echo NOTE: The URL will change each time you restart!
    echo.
    echo [3/3] Tunnel is starting...
    echo      Look for the URL below (https://xxx.trycloudflare.com)
    echo.
    echo ========================================
    echo.
    cloudflared tunnel --url http://localhost:8000
) else if "%choice%"=="2" (
    echo.
    echo Starting named tunnel...
    echo NOTE: Make sure you've run 'cloudflared tunnel create schedule-generator' first!
    echo.
    echo [3/3] Tunnel is starting...
    echo.
    echo ========================================
    echo.
    cloudflared tunnel run schedule-generator
) else (
    echo Invalid choice. Defaulting to quick tunnel...
    echo.
    cloudflared tunnel --url http://localhost:8000
)

REM If we get here, the tunnel has stopped
echo.
echo ========================================
echo  Tunnel stopped. Cleaning up...
echo ========================================
echo.

REM Kill all Python processes (this will stop the backend)
echo Stopping backend server...
taskkill /F /IM python.exe >nul 2>nul

echo.
echo Done! Both tunnel and backend have been stopped.
echo.
pause
