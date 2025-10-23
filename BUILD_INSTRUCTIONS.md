# Build Standalone Portable Application

## Prerequisites
- Python installed with all dependencies (`ortools`, `sqlmodel`, etc.)
- Node.js and npm installed
- All frontend dependencies installed

## Step-by-Step Build Process

### Step 1: Build Python Backend (One-time setup)

```bash
cd backend
pip install pyinstaller

pyinstaller --clean --onedir --name schedule-backend --hidden-import=ortools --hidden-import=sqlmodel --hidden-import=sqlalchemy --hidden-import=pydantic --hidden-import=pydantic_settings --hidden-import=app.models.dbbase --hidden-import=app.models.employee --hidden-import=app.models.timeoff --hidden-import=app.models.unavailable --hidden-import=app.models.lockedshift --hidden-import=app.models.settings --hidden-import=app.models.staffing_window --hidden-import=app.newSolver.core --collect-all=ortools app\ipc_server.py

cd ..
```

This creates: `backend\dist\schedule-backend\` with the bundled Python executable.

### Step 2: Copy Python Bundle to Resources

```bash
mkdir resources
xcopy /E /I /Y backend\dist\schedule-backend resources\schedule-backend
```

### Step 3: Build Frontend (if not already done)

```bash
cd frontend
npm run build
cd ..
```

### Step 4: Build Electron Portable App

```bash
npm run build:portable
```

### Step 5: Find Your Portable App

Your standalone app is in: **`dist-electron\win-unpacked\`**

The main executable is: **`Schedule Generator.exe`**

## Distribution

To distribute:
1. Copy the entire `dist-electron\win-unpacked\` folder
2. Zip it or copy it to a USB drive
3. Run `Schedule Generator.exe` on any Windows computer
4. No installation needed!

## Important Notes

- **Database Location**: The app stores its database in `%APPDATA%\schedule-generator\data\`
- **No Internet Required**: Works completely offline
- **No Firewall Issues**: Uses NO network ports or HTTP calls
- **No Admin Rights**: Runs from user directories
- **Portable**: Can run from any folder or USB drive

## Troubleshooting

### "schedule-backend.exe not found" error
Make sure you completed Step 1 and Step 2 correctly.
Check that `resources\schedule-backend\schedule-backend.exe` exists.

### "VCRUNTIME140.dll missing" error
Install Microsoft Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

### OR-Tools not working
Make sure pyinstaller includes ortools with `--collect-all=ortools`

### App won't start
Check the console output for errors when running in dev mode:
```bash
npm run dev
```

## Automated Build (Recommended)

Simply run the batch file:
```bash
build-portable.bat
```

This does all steps automatically!
