Portable build instructions

What this produces
- A folder (default: `portable_build`) containing:
  - `run_app.exe` — packaged backend executable (PyInstaller build)
  - `static/` — optional frontend build files copied into backend static directory
  - `schedule.db` — optional existing database copy
  - `run.bat` / `run.ps1` — convenience scripts to launch the exe

How to produce
1) Build frontend (on dev machine):

```powershell
cd frontend
npm install
npm run build

# copy build into backend static location the script expects
mkdir -Force backend\app\static\dist
copy-item -Path frontend\dist\* -Destination backend\app\static\dist -Recurse
```

2) Build backend exe with PyInstaller (on dev machine):

```powershell
cd backend
# activate venv
. .venv\Scripts\Activate.ps1
pip install pyinstaller
pyinstaller --onefile run_app.py
```

After PyInstaller runs the exe will be at `backend\dist\run_app.exe`.

3) Assemble the portable folder (this repo includes a helper script):

```powershell
cd repo-root
powershell -ExecutionPolicy Bypass -File tools\make_portable.ps1
```

Copy the produced `portable_build` folder to a flash drive and on the target machine run `run.bat`.

Notes and caveats
- The exe bundles the Python backend and serves static files from `app/static/dist` if present.
- The portable build is Windows-only (exe). For macOS/Linux you'd use other packaging.
- Target machine must allow running unsigned executables and have no strict antivirus policies blocking PyInstaller exes.
- If the user needs specific ports or reasons to run headlessly, modify `run_app.py` accordingly.

Important: OR-Tools native libraries
- OR-Tools includes native DLLs that must be bundled with the exe (they live in `venv\Lib\site-packages\ortools\.libs`).
- If you see an ImportError like: "DLL load failed while importing cp_model_helper", rebuild the exe with PyInstaller ensuring the ortools dynamic libs are included. The repo's `run_app.spec` has been updated to collect ortools dynamic libs using PyInstaller's `collect_dynamic_libs('ortools')`.

To rebuild the exe with ortools DLLs included:

```powershell
cd backend
. .venv\Scripts\Activate.ps1
pip install pyinstaller
pyinstaller --clean --onefile run_app.spec
```

After this the `backend\dist\run_app.exe` should start without the OR-Tools DLL error.
