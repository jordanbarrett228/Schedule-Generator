# backend/app/routers/rt_unavailable.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import time as dt_time
from sqlmodel import Session, select

from app.db import get_session
from app.models.unavailable import UnavailableBlock, UnavailableBlockCreate, UnavailableBlockRead
from app.models.employee import Employee
from app.models.user import UserRead
from app.auth import get_current_user

router = APIRouter(prefix="/api/unavailable", tags=["unavailable"])

WEEKDAYS = set(range(0, 7))


# ----- Update model (for PUT) -----
class UnavailableUpdate(BaseModel):
    weekday: int
    start_time: dt_time
    end_time: dt_time

    @field_validator("weekday")
    @classmethod
    def _weekday(cls, v: int) -> int:
        if v not in WEEKDAYS:
            raise ValueError("weekday must be 0..6 (Mon=0 .. Sun=6)")
        return v

    @field_validator("end_time")
    @classmethod
    def _end_after_start(cls, end: dt_time, info):
        start: Optional[dt_time] = info.data.get("start_time")
        if start is not None and end <= start:
            raise ValueError("end_time must be after start_time")
        return end


# ======================================================
#                   ENDPOINTS
# ======================================================

@router.get("/employees/{emp_id}", response_model=List[UnavailableBlockRead])
def list_unavailable(
    emp_id: int,
    session: Session = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    """List unavailable blocks for one of the current user's employees."""
    emp = session.get(Employee, emp_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Employee not found")

    return session.exec(
        select(UnavailableBlock).where(UnavailableBlock.employee_id == emp_id)
    ).all()


@router.post("/employees/{emp_id}", response_model=UnavailableBlockRead)
def create_unavailable(
    emp_id: int,
    payload: UnavailableBlockCreate,
    session: Session = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    """Create a new unavailable block for a user's employee."""
    emp = session.get(Employee, emp_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Employee not found")

    if payload.employee_id != emp_id:
        payload.employee_id = emp_id

    rec = UnavailableBlock.model_validate(payload)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec


@router.put("/{unavail_id}")
def update_unavailable(
    unavail_id: int,
    payload: UnavailableUpdate,
    session: Session = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    """Update an unavailable block (with field validation)."""
    u = session.get(UnavailableBlock, unavail_id)
    if not u:
        raise HTTPException(status_code=404, detail="Unavailable not found")

    emp = session.get(Employee, u.employee_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this record")

    u.weekday = payload.weekday
    u.start_time = payload.start_time
    u.end_time = payload.end_time

    session.add(u)
    session.commit()
    session.refresh(u)

    return {
        "id": u.id,
        "employee_id": u.employee_id,
        "weekday": u.weekday,
        "start_time": u.start_time.strftime("%H:%M"),
        "end_time": u.end_time.strftime("%H:%M"),
    }


@router.delete("/{rec_id}")
def delete_unavailable(
    rec_id: int,
    session: Session = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    """Delete an unavailable block belonging to the current user's employee."""
    rec = session.get(UnavailableBlock, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Unavailable block not found")

    emp = session.get(Employee, rec.employee_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this record")

    session.delete(rec)
    session.commit()
    return {"ok": True}
