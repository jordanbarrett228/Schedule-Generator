# backend/app/routers/rt_settings.py
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlmodel import Session, select
from typing import List

from ...db import get_session
from ...models.settings import GlobalSettings, BusinessHours, BusinessHoursRead, BusinessHoursCreate
from app.models.user import UserRead
from app.auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/global", response_model=GlobalSettings)
def get_global_settings(session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    gs = session.exec(select(GlobalSettings).where(GlobalSettings.user_id == current_user.id)).first()
    if not gs:
        gs = GlobalSettings(user_id=current_user.id)
        session.add(gs)
        session.commit()
        session.refresh(gs)
    return gs

@router.put("/global", response_model=GlobalSettings)
def update_global_settings(payload: GlobalSettings, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    gs = session.exec(select(GlobalSettings).where(GlobalSettings.user_id == current_user.id)).first()
    if not gs:
        gs = GlobalSettings(user_id=current_user.id)
        session.add(gs)
        session.commit()
        session.refresh(gs)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(gs, k, v)
    session.add(gs)
    session.commit()
    session.refresh(gs)
    return gs

@router.get("/business_hours", response_model=List[BusinessHoursRead])
def get_business_hours(session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    return session.exec(select(BusinessHours).where(BusinessHours.user_id == current_user.id).order_by(BusinessHours.weekday)).all() # type: ignore

@router.put("/business_hours", response_model=List[BusinessHoursRead])
def put_business_hours(payload: List[BusinessHoursCreate] = Body(...), session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    existing = {bh.weekday: bh for bh in session.exec(select(BusinessHours).where(BusinessHours.user_id == current_user.id)).all()}
    for item in payload:
        if item.weekday in existing:
            rec = existing[item.weekday]
            rec.open_time = item.open_time
            rec.close_time = item.close_time
            session.add(rec)
        else:
            obj = BusinessHours.model_validate(item)
            obj.user_id = current_user.id
            session.add(obj)
    session.commit()
    return session.exec(select(BusinessHours).where(BusinessHours.user_id == current_user.id).order_by(BusinessHours.weekday)).all() # type: ignore
