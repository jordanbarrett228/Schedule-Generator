# ChatGPT Schedule Generator

Fullstack scaffold: FastAPI backend and Vite + React + TypeScript frontend.

Requirements
- Node.js >= 18
- Python >= 3.11
- git

Quick setup (Windows PowerShell)

1) Backend: create venv & install

```powershell
cd backend
python -m venv .venv
. .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run backend (from backend/)

```powershell
. .venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

2) Frontend: install and run

```powershell
cd frontend
npm install
npm run dev
```

Notes
- Backend dependencies are listed in `backend/requirements.txt`.
- Frontend scaffold uses Vite + React + TypeScript.
