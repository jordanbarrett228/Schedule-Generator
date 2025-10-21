from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ...db import get_session
from ...models.staffing_window import StaffingWindow, StaffingWindowCreate, StaffingWindowRead
from app.auth import get_current_user
from app.models.user import UserRead

router = APIRouter(prefix="/api/staffing-windows", tags=["staffing-windows"])

@router.get("", response_model=list[StaffingWindowRead])
def list_windows(session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    return session.exec(select(StaffingWindow).where(StaffingWindow.user_id == current_user.id)).all()

@router.post("", response_model=StaffingWindowRead)
def create_window(payload: StaffingWindowCreate, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    row = StaffingWindow.from_orm(payload)
    row.user_id = current_user.id
    session.add(row)
    session.commit()
    session.refresh(row)
    return row

@router.delete("/{wid}")
def delete_window(wid: int, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):  
    row = session.get(StaffingWindow, wid)
    if not row or row.user_id != current_user.id:
        raise HTTPException(404, "Not found")
    session.delete(row)
    session.commit()
    return {"ok": True}
