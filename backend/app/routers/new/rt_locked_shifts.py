# backend/app/routers/rt_locked_shifts.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from ...db import get_session
from ...models.lockedshift import LockedShift, LockedShiftCreate, LockedShiftRead
from ...models.employee import Employee
from app.models.user import UserRead
from app.auth import get_current_user
from app.models.lockedshift import LockedShift as AppLockedShift, LockedShiftUpdate

router = APIRouter(tags=["locked_shifts"])

@router.get("/api/employees/{emp_id}/locked_shifts", response_model=List[LockedShiftRead])
def list_locked(emp_id: int, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    emp = session.get(Employee, emp_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Employee not found")
    return session.exec(select(LockedShift).where(LockedShift.employee_id == emp_id)).all()

@router.post("/api/employees/{emp_id}/locked_shifts", response_model=LockedShiftRead)
def create_locked(emp_id: int, payload: LockedShiftCreate, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    emp = session.get(Employee, emp_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Employee not found")
    if payload.employee_id != emp_id:
        payload.employee_id = emp_id
    rec = LockedShift.model_validate(payload)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec

@router.put("/api/employees/{emp_id}/locked_shifts/{lock_id}")
def update_locked_shift(emp_id: int, lock_id: int, payload: LockedShiftUpdate, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    ls = session.get(LockedShift, lock_id)
    if not ls:
        raise HTTPException(status_code=404, detail="Locked shift not found")
    emp = session.get(Employee, emp_id)
    if not emp or emp.user_id != current_user.id or ls.employee_id != emp_id:
        raise HTTPException(status_code=404, detail="Locked shift not found for this employee")
    ls.weekday = payload.weekday
    ls.start_time = payload.start_time
    ls.end_time = payload.end_time
    ls.note = payload.note
    session.add(ls)
    session.commit()
    session.refresh(ls)
    return {
        "id": ls.id,
        "employee_id": ls.employee_id,
        "weekday": ls.weekday,
        "start_time": ls.start_time.strftime("%H:%M"),
        "end_time": ls.end_time.strftime("%H:%M"),
        "note": ls.note or "",
    }

@router.delete("/api/locked_shifts/{rec_id}")
def delete_locked(rec_id: int, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    rec = session.get(LockedShift, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Locked shift not found")
    emp = session.get(Employee, rec.employee_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Locked shift not found")
    session.delete(rec)
    session.commit()
    return {"ok": True}
