from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from sqlmodel import Session, select
from pathlib import Path
import os

from .db import init_db, get_session
from .models.employee import Employee, EmployeeCreate, EmployeeRead, EmployeeUpdate

app = FastAPI(title="Schedule Generator API", version="0.1.0")

# DEV CORS (only needed while vite dev server is used)
if os.environ.get("DEV", "0") == "1":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/api/health")
def health():
    return {"status": "ok"}



@app.get("/api/employees", response_model=list[EmployeeRead])
def list_employees(session: Session = Depends(get_session)):
    return session.exec(select(Employee).order_by(Employee.id)).all()


@app.post("/api/employees", response_model=EmployeeRead)
def create_employee(payload: EmployeeCreate, session: Session = Depends(get_session)):
    emp = Employee.model_validate(payload)
    session.add(emp)
    session.commit()
    session.refresh(emp)
    return emp


@app.put("/api/employees/{emp_id}", response_model=EmployeeRead)
def update_employee(emp_id: int, payload: EmployeeUpdate, session: Session = Depends(get_session)):
    emp = session.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(emp, k, v)
    session.add(emp)
    session.commit()
    session.refresh(emp)
    return emp


@app.delete("/api/employees/{emp_id}")
def delete_employee(emp_id: int, session: Session = Depends(get_session)):
    emp = session.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    session.delete(emp)
    session.commit()
    return {"ok": True}


@app.post("/api/shutdown")
def shutdown():
    server = getattr(app.state, "server", None)
    if server:
        server.should_exit = True
    return {"ok": True}

# ---- Serve React build in production ----
FRONTEND_DIST = (
    Path(__file__).resolve().parents[2] / "frontend" / "dist"
)  # repo-root/frontend/dist

if FRONTEND_DIST.exists():
    # Serve index.html for unknown routes (SPA fallback)
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"detail": "Frontend not built yet."}