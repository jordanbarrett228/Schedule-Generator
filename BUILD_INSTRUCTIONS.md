# Build Standalone Portable Application

## Quick Start (Automated Build)

Simply run the batch file:
```bash
build-portable.bat
```

This automatically:
1. Builds the frontend
2. Bundles the Python backend with PyInstaller
3. Copies backend to resources folder
4. Creates the portable executable

**Output**: `dist-electron\Schedule Generator-Portable.exe` (109 MB single file)

## Distribution

Your portable app is ready at: **`dist-electron\Schedule Generator-Portable.exe`**

To distribute to your manager or users:
1. Copy the `Schedule Generator-Portable.exe` file
2. Transfer via USB drive, Google Drive, email, etc.
3. User runs the .exe - no installation needed!

## Important Features

✅ **Standalone**: Single 109MB .exe file - everything bundled
✅ **No Installation**: Double-click to run
✅ **No Admin Rights**: Runs from user directories only
✅ **100% Offline**: No network, no localhost, no ports
✅ **Portable**: Run from any folder, USB drive, or network share
✅ **Database**: Stored in `%APPDATA%\schedule-generator\data\`

## Windows SmartScreen Warning

⚠️ **First-time users may see a Windows Defender warning** because the app is not code-signed ($300-400/year for certificate).

Users can bypass by clicking:
1. "More info" → "Run anyway"

This is normal for unsigned apps and does NOT mean it's unsafe. The app is trustworthy.

## Prerequisites (for building)

- Python 3.13+ with dependencies installed
- Node.js and npm installed
- Git Bash or WSL (for running build script)

## Manual Build Process

If you need to build manually:

### Step 1: Build Python Backend

```bash
cd backend
python -m PyInstaller --clean --onedir --name schedule-backend \
  --hidden-import=ortools \
  --hidden-import=sqlmodel \
  --hidden-import=sqlalchemy \
  --hidden-import=pydantic \
  --hidden-import=app.models.employee \
  --hidden-import=app.models.timeoff \
  --hidden-import=app.models.unavailable \
  --hidden-import=app.models.lockedshift \
  --hidden-import=app.models.settings \
  --hidden-import=app.models.staffing_window \
  --hidden-import=app.newSolver.core \
  --collect-all=ortools \
  app\ipc_server.py
cd ..
```

### Step 2: Copy Python Bundle to Resources

```bash
mkdir -p resources
cp -r backend/dist/schedule-backend resources/
```

### Step 3: Build Electron Portable App

```bash
npm run build:portable
```

## Troubleshooting

### Build fails with "Cannot create symbolic link"
Solution: Code signing is now disabled in package.json. This error should not occur.

### "PyInstaller not found" error
Solution: The build script now uses `python -m PyInstaller` instead of `pyinstaller` command

### "schedule-backend.exe not found" error
Make sure `resources\schedule-backend\schedule-backend.exe` exists after Step 2.

### OR-Tools not working
Make sure PyInstaller includes ortools with `--collect-all=ortools`

### App won't start in production
Check that you ran `build-portable.bat` completely without errors.

## Development Mode

To run in dev mode with hot reload:
```bash
npm run dev
```

This uses local Python and rebuilds frontend on changes.
