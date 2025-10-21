# backend/app/routers/rt_admin.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, select
from sqlalchemy import text
from typing import Iterable, List, Any

from ...db import get_session
from ...models.employee import Employee
from ...models.unavailable import UnavailableBlock
from ...models.timeoff import TimeOff
from ...models.lockedshift import LockedShift
from ...models.settings import GlobalSettings
from ...models.staffing_window import StaffingWindow
from app.models.user import UserRead
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/backup")
def backup_all(
    session: Session = Depends(get_session),
    current_user: UserRead = Depends(get_current_user)
):
    # fetch current user's employees
    user_emps = session.exec(select(Employee).where(Employee.user_id == current_user.id)).all()
    emp_ids = [e.id for e in user_emps if e.id is not None]
    data = {
        "employees": user_emps,
        "unavailable": session.exec(
            select(UnavailableBlock).where(
                UnavailableBlock.employee_id.in_(emp_ids)  # type: ignore[attr-defined]
                if emp_ids else text("0=1")
            )
        ).all(),
        "timeoff": session.exec(
            select(TimeOff).where(
                TimeOff.employee_id.in_(emp_ids)  # type: ignore[attr-defined]
                if emp_ids else text("0=1")
            )
        ).all(),
        "locked_shifts": session.exec(
            select(LockedShift).where(
                LockedShift.employee_id.in_(emp_ids)  # type: ignore[attr-defined]
                if emp_ids else text("0=1")
            )
        ).all(),
        "settings": session.exec(
            select(GlobalSettings).where(GlobalSettings.user_id == current_user.id)
        ).all(),
        "staffing_windows": session.exec(
            select(StaffingWindow).where(StaffingWindow.user_id == current_user.id)
        ).all() if "StaffingWindow" in globals() else [],
        "version": "1",
    }

    return JSONResponse(content=jsonable_encoder(data))


@router.post("/restore")
def restore_all(
    payload: dict,
    session: Session = Depends(get_session),
    current_user: UserRead = Depends(get_current_user)
):
    # delete only current user's data
    user_emp_ids = [
        e.id for e in session.exec(select(Employee.id).where(Employee.user_id == current_user.id)).all() # type: ignore[attr-defined]
        if e is not None
    ]

    if user_emp_ids:
        # raw text deletes: perfectly valid, but type-ignored for Pylance
        session.exec(  text(f"DELETE FROM {LockedShift.__tablename__} WHERE employee_id IN ({','.join(map(str, user_emp_ids))})")) # type: ignore[arg-type]
        session.exec( text(f"DELETE FROM {TimeOff.__tablename__} WHERE employee_id IN ({','.join(map(str, user_emp_ids))})"))  # type: ignore[arg-type]
        session.exec(text(f"DELETE FROM {UnavailableBlock.__tablename__} WHERE employee_id IN ({','.join(map(str, user_emp_ids))})")) # type: ignore[arg-type]

    # delete user-owned top-level data
    session.exec(text(f"DELETE FROM {Employee.__tablename__} WHERE user_id = {current_user.id}"))  # type: ignore[arg-type]
    session.exec(text(f"DELETE FROM {GlobalSettings.__tablename__} WHERE user_id = {current_user.id}"))  # type: ignore[arg-type]
    session.exec(text(f"DELETE FROM {StaffingWindow.__tablename__} WHERE user_id = {current_user.id}"))  # type: ignore[arg-type]
    session.commit()

    def bulk_insert(model: Any, items: Iterable[dict]):
        for raw in items:
            obj = model.model_validate(raw)
            if hasattr(obj, "user_id"):
                setattr(obj, "user_id", current_user.id)
            session.add(obj)
        session.commit()

    if payload.get("employees"):
        bulk_insert(Employee, payload["employees"])
    if payload.get("unavailable"):
        bulk_insert(UnavailableBlock, payload["unavailable"])
    if payload.get("timeoff"):
        bulk_insert(TimeOff, payload["timeoff"])
    if payload.get("locked_shifts"):
        bulk_insert(LockedShift, payload["locked_shifts"])
    if payload.get("settings"):
        bulk_insert(GlobalSettings, payload["settings"])
    if payload.get("staffing_windows"):
        bulk_insert(StaffingWindow, payload["staffing_windows"])

    return {"ok": True}
