# backend/app/newSolver/data_loader.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from sqlmodel import Session, select

from app.models.employee import Employee
from app.models.unavailable import UnavailableBlock
from app.models.timeoff import TimeOff
from app.models.lockedshift import LockedShift
from app.models.settings import GlobalSettings, BusinessHours
from app.models.staffing_window import StaffingWindow


@dataclass
class ScheduleInputs:
    """All DB inputs required for schedule generation."""
    employees: List[Employee]
    unavailable: Dict[int, List[UnavailableBlock]]
    timeoff: Dict[int, List[TimeOff]]
    locked: Dict[int, List[LockedShift]]
    settings: Optional[GlobalSettings]
    business_hours: List[BusinessHours]
    staffing_windows: List[StaffingWindow]


def load_user_data(session: Session) -> ScheduleInputs:
    """
    Load all schedule-related data from schedule.db (single-user mode).

    Returns a structured object containing:
      - active employees
      - unavailable/timeoff/locked entries grouped per employee
      - global settings
      - business hours
      - staffing windows
    """
    # --- Employees (active only)
    employees: List[Employee] = list(
        session.exec(select(Employee).where(Employee.active == True)).all()
    )

    # --- Related data dictionaries keyed by employee.id
    unavailable: Dict[int, List[UnavailableBlock]] = {}
    timeoff: Dict[int, List[TimeOff]] = {}
    locked: Dict[int, List[LockedShift]] = {}

    for e in employees:
        eid = int(e.id) if e.id is not None else -1  # defensive guard
        unavailable[eid] = list(
            session.exec(
                select(UnavailableBlock).where(UnavailableBlock.employee_id == e.id)
            ).all()
        )
        timeoff[eid] = list(
            session.exec(select(TimeOff).where(TimeOff.employee_id == e.id)).all()
        )
        locked[eid] = list(
            session.exec(select(LockedShift).where(LockedShift.employee_id == e.id)).all()
        )

    # --- Global settings and schedule context
    settings: Optional[GlobalSettings] = session.exec(select(GlobalSettings)).first()
    business_hours: List[BusinessHours] = list(session.exec(select(BusinessHours)).all())
    staffing_windows: List[StaffingWindow] = list(session.exec(select(StaffingWindow)).all())

    return ScheduleInputs(
        employees=employees,
        unavailable=unavailable,
        timeoff=timeoff,
        locked=locked,
        settings=settings,
        business_hours=business_hours,
        staffing_windows=staffing_windows,
    )
