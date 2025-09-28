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

Try it (quick smoke tests)

1) Start backend

```powershell
cd backend
. .venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Then from another PowerShell window run:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/health
```

You should get {"status":"ok"}.

2) Start frontend

```powershell
cd frontend
npm install
npm run dev
```

