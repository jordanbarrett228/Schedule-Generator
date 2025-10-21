# backend/app/routers/rt_timeoff.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from ...db import get_session
from ...models.timeoff import TimeOff, TimeOffCreate, TimeOffRead
from ...models.employee import Employee
from app.models.user import UserRead
from app.auth import get_current_user

router = APIRouter(tags=["timeoff"])

@router.get("/api/employees/{emp_id}/timeoff", response_model=List[TimeOffRead])
def list_timeoff(emp_id: int, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    emp = session.get(Employee, emp_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Employee not found")
    return session.exec(select(TimeOff).where(TimeOff.employee_id == emp_id)).all()

@router.post("/api/employees/{emp_id}/timeoff", response_model=TimeOffRead)
def create_timeoff(emp_id: int, payload: TimeOffCreate, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    emp = session.get(Employee, emp_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Employee not found")
    if payload.employee_id != emp_id:
        payload.employee_id = emp_id
    rec = TimeOff.model_validate(payload)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec

@router.delete("/api/timeoff/{rec_id}")
def delete_timeoff(rec_id: int, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    rec = session.get(TimeOff, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Time off not found")
    emp = session.get(Employee, rec.employee_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Time off not found")
    session.delete(rec)
    session.commit()
    return {"ok": True}
