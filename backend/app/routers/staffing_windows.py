from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..db import get_session
from ..models.staffing_window import StaffingWindow, StaffingWindowCreate, StaffingWindowRead

router = APIRouter()

@router.get("", response_model=list[StaffingWindowRead])
def list_windows(session: Session = Depends(get_session)):
    return session.exec(select(StaffingWindow)).all()

@router.post("", response_model=StaffingWindowRead)
def create_window(payload: StaffingWindowCreate, session: Session = Depends(get_session)):
    row = StaffingWindow.from_orm(payload)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row

@router.delete("/{wid}")
def delete_window(wid: int, session: Session = Depends(get_session)):
    row = session.get(StaffingWindow, wid)
    if not row:
        raise HTTPException(404, "Not found")
    session.delete(row)
    session.commit()
    return {"ok": True}
