@echo off
echo ========================================
echo Building Portable Schedule Generator
echo ========================================
echo.

echo Step 1: Building Frontend...
cd frontend
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed!
    pause
    exit /b 1
)
cd ..
echo Frontend build complete!
echo.

echo Step 2: Creating Python Backend Bundle...
cd backend
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install pyinstaller!
    pause
    exit /b 1
)

pyinstaller --clean --onedir --name schedule-backend ^
  --hidden-import=ortools ^
  --hidden-import=sqlmodel ^
  --hidden-import=sqlalchemy ^
  --hidden-import=pydantic ^
  --hidden-import=pydantic_settings ^
  --hidden-import=app.models.dbbase ^
  --hidden-import=app.models.employee ^
  --hidden-import=app.models.timeoff ^
  --hidden-import=app.models.unavailable ^
  --hidden-import=app.models.lockedshift ^
  --hidden-import=app.models.settings ^
  --hidden-import=app.models.staffing_window ^
  --hidden-import=app.newSolver.core ^
  --collect-all=ortools ^
  app\ipc_server.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)
cd ..
echo Python backend bundle complete!
echo.

echo Step 3: Copying Python bundle to resources...
if not exist "resources" mkdir resources
xcopy /E /I /Y "backend\dist\schedule-backend" "resources\schedule-backend"
echo.

echo Step 4: Building Electron App...
call npm run build:portable
if errorlevel 1 (
    echo ERROR: Electron build failed!
    pause
    exit /b 1
)
echo.

echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo Your portable app is in: dist-electron\
echo.
pause
