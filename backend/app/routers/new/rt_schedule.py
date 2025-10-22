# backend/app/routers/new/rt_schedule.py
from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import Optional
from datetime import date

from ...db import get_session
from app.newSolver.core import generate_week_schedule
from app.models.user import UserRead
from app.auth import get_current_user

router = APIRouter(prefix="/api/schedule", tags=["schedule"])

@router.post("/generate")
def api_generate_schedule(payload: dict | None = None, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    week_start_str = (payload or {}).get("week_start")
    week_start = date.fromisoformat(week_start_str) if week_start_str else None
    result = generate_week_schedule(session, week_start=week_start, user_id=current_user.id)
    return result
