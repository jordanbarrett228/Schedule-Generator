from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from sqlmodel import Session, select
from pathlib import Path

import os

from .db import init_db, get_session
from .models.employee import Employee, EmployeeCreate, EmployeeRead, EmployeeUpdate
from .models.unavailable import UnavailableBlock, UnavailableBlockCreate, UnavailableBlockRead
from .models.timeoff import TimeOff, TimeOffCreate, TimeOffRead
from .models.lockedshift import LockedShift, LockedShiftCreate, LockedShiftRead
from .models.settings import GlobalSettings, CoveragePeak, CoveragePeakCreate, CoveragePeakRead, BusinessHours, BusinessHoursRead, BusinessHoursCreate
from .solver import generate_week_schedule
from datetime import date
from .routers import staffing_windows

try:
    import debugpy
    debugpy.listen(("127.0.0.1", 5678))
    debugpy.wait_for_client()  # uncomment to pause on start
except Exception:
    pass

app = FastAPI(title="Schedule Generator API", version="0.1.0")
app.include_router(staffing_windows.router, prefix="/api/staffing-windows", tags=["staffing-windows"])

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


@app.post("/api/shutdown")
def shutdown():
    server = getattr(app.state, "server", None)
    if server:
        server.should_exit = True
    return {"ok": True}

@app.get("/api/health")
def health():
    return {"status": "ok"}

# ---- Employees ----
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


# ---- Unavailable blocks (weekly) ----
@app.get("/api/employees/{emp_id}/unavailable", response_model=list[UnavailableBlockRead])
def list_unavailable(emp_id: int, session: Session = Depends(get_session)):
    return session.exec(select(UnavailableBlock).where(UnavailableBlock.employee_id == emp_id)).all()

@app.post("/api/employees/{emp_id}/unavailable", response_model=UnavailableBlockRead)
def create_unavailable(emp_id: int, payload: UnavailableBlockCreate, session: Session = Depends(get_session)):
    if payload.employee_id != emp_id:
        payload.employee_id = emp_id
    rec = UnavailableBlock.model_validate(payload)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec

@app.delete("/api/unavailable/{rec_id}")
def delete_unavailable(rec_id: int, session: Session = Depends(get_session)):
    rec = session.get(UnavailableBlock, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Unavailable block not found")
    session.delete(rec)
    session.commit()
    return {"ok": True}

# ---- Time off ----
@app.get("/api/employees/{emp_id}/timeoff", response_model=list[TimeOffRead])
def list_timeoff(emp_id: int, session: Session = Depends(get_session)):
    return session.exec(select(TimeOff).where(TimeOff.employee_id == emp_id)).all()

@app.post("/api/employees/{emp_id}/timeoff", response_model=TimeOffRead)
def create_timeoff(emp_id: int, payload: TimeOffCreate, session: Session = Depends(get_session)):
    if payload.employee_id != emp_id:
        payload.employee_id = emp_id
    rec = TimeOff.model_validate(payload)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec

@app.delete("/api/timeoff/{rec_id}")
def delete_timeoff(rec_id: int, session: Session = Depends(get_session)):
    rec = session.get(TimeOff, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Time off not found")
    session.delete(rec)
    session.commit()
    return {"ok": True}


# ---- Locked shifts ----
@app.get("/api/employees/{emp_id}/locked_shifts", response_model=list[LockedShiftRead])
def list_locked(emp_id: int, session: Session = Depends(get_session)):
    return session.exec(select(LockedShift).where(LockedShift.employee_id == emp_id)).all()

@app.post("/api/employees/{emp_id}/locked_shifts", response_model=LockedShiftRead)
def create_locked(emp_id: int, payload: LockedShiftCreate, session: Session = Depends(get_session)):
    if payload.employee_id != emp_id:
        payload.employee_id = emp_id
    rec = LockedShift.model_validate(payload)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec

@app.delete("/api/locked_shifts/{rec_id}")
def delete_locked(rec_id: int, session: Session = Depends(get_session)):
    rec = session.get(LockedShift, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Locked shift not found")
    session.delete(rec)
    session.commit()
    return {"ok": True}


# ---- Global settings ----
@app.get("/api/settings/global", response_model=GlobalSettings)
def get_global_settings(session: Session = Depends(get_session)):
    gs = session.exec(select(GlobalSettings)).first()
    return gs

@app.put("/api/settings/global", response_model=GlobalSettings)
def update_global_settings(payload: GlobalSettings, session: Session = Depends(get_session)):
    gs = session.exec(select(GlobalSettings)).first()
    if not gs:
        gs = GlobalSettings()
        session.add(gs)
        session.commit()
        session.refresh(gs)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(gs, k, v)
    session.add(gs)
    session.commit()
    session.refresh(gs)
    return gs

# ---- Business Hours (per-day) ----
@app.get("/api/settings/business_hours", response_model=list[BusinessHoursRead])
def get_business_hours(session: Session = Depends(get_session)):
    return session.exec(select(BusinessHours).order_by(BusinessHours.weekday)).all()

@app.put("/api/settings/business_hours", response_model=list[BusinessHoursRead])
def put_business_hours(payload: list[BusinessHoursCreate] = Body(...), session: Session = Depends(get_session)):
    # Upsert by weekday (unique by design for simplicity)
    existing = {bh.weekday: bh for bh in session.exec(select(BusinessHours)).all()}
    for item in payload:
        if item.weekday in existing:
            rec = existing[item.weekday]
            rec.open_time = item.open_time
            rec.close_time = item.close_time
            session.add(rec)
        else:
            session.add(BusinessHours.model_validate(item))
    session.commit()
    return session.exec(select(BusinessHours).order_by(BusinessHours.weekday)).all()

# ---- Coverage peaks ----
@app.get("/api/coverage/peaks", response_model=list[CoveragePeakRead])
def list_peaks(session: Session = Depends(get_session)):
    return session.exec(select(CoveragePeak)).all()

@app.post("/api/coverage/peaks", response_model=CoveragePeakRead)
def create_peak(payload: CoveragePeakCreate, session: Session = Depends(get_session)):
    if payload.date is None and payload.weekday is None:
        raise HTTPException(status_code=400, detail="Provide either date or weekday")
    rec = CoveragePeak.model_validate(payload)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec

@app.delete("/api/coverage/peaks/{peak_id}")
def delete_peak(peak_id: int, session: Session = Depends(get_session)):
    rec = session.get(CoveragePeak, peak_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Peak not found")
    session.delete(rec)
    session.commit()
    return {"ok": True}

@app.post("/api/schedule/generate")
def api_generate_schedule(payload: dict | None = None, session: Session = Depends(get_session)):
    """
    JSON payload (optional): {"week_start": "YYYY-MM-DD"}
    If omitted, uses the upcoming Monday.
    """
    week_start_str = (payload or {}).get("week_start")
    week_start = date.fromisoformat(week_start_str) if week_start_str else None
    result = generate_week_schedule(session, week_start=week_start)
    return result

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