"""
IPC Implementation Functions for Standalone Mode
All functions run without authentication (single-user mode)
"""
from datetime import date
from sqlmodel import Session, select
from typing import Any, Iterable

from .db import get_session
from .models.employee import Employee, EmployeeCreate, EmployeeRead, EmployeeUpdate
from .models.timeoff import TimeOff, TimeOffCreate, TimeOffRead
from .models.unavailable import UnavailableBlock, UnavailableBlockCreate, UnavailableBlockRead
from .models.lockedshift import LockedShift, LockedShiftCreate, LockedShiftRead
from .models.settings import GlobalSettings, BusinessHours, BusinessHoursRead, BusinessHoursCreate
from .models.staffing_window import StaffingWindow, StaffingWindowCreate, StaffingWindowRead
from .newSolver.core import generate_week_schedule


# ===== EMPLOYEES =====

def get_employees_impl():
    """Get all employees (single-user mode)"""
    with next(get_session()) as session:
        employees = session.exec(select(Employee)).all()
        # Sort by ID in Python (more compatible than order_by)
        sorted_employees = sorted(employees, key=lambda e: e.id if e.id is not None else 0)
        return [EmployeeRead.model_validate(emp).model_dump(mode='json') for emp in sorted_employees]


def get_employee_impl(emp_id: int):
    """Get single employee"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        return EmployeeRead.model_validate(emp).model_dump(mode='json')


def create_employee_impl(data: dict):
    """Create new employee (single-user mode)"""
    with next(get_session()) as session:
        emp = Employee.model_validate(EmployeeCreate(**data))
        session.add(emp)
        session.commit()
        session.refresh(emp)
        return EmployeeRead.model_validate(emp).model_dump(mode='json')


def update_employee_impl(emp_id: int, data: dict):
    """Update employee"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")

        # Use Pydantic to validate and convert types (e.g., string time -> time object)
        update_model = EmployeeUpdate(**data)
        update_data = update_model.model_dump(exclude_unset=True)

        for k, v in update_data.items():
            if hasattr(emp, k):
                setattr(emp, k, v)
        session.add(emp)
        session.commit()
        session.refresh(emp)
        return EmployeeRead.model_validate(emp).model_dump(mode='json')


def delete_employee_impl(emp_id: int):
    """Delete employee"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        session.delete(emp)
        session.commit()
        return {"ok": True}


# ===== TIME-OFF =====

def get_timeoff_impl(emp_id: int):
    """Get all time-off records for employee"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        records = session.exec(select(TimeOff).where(TimeOff.employee_id == emp_id)).all()
        return [TimeOffRead.model_validate(rec).model_dump(mode='json') for rec in records]


def create_timeoff_impl(emp_id: int, data: dict):
    """Create new time-off record"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        data['employee_id'] = emp_id
        rec = TimeOff.model_validate(TimeOffCreate(**data))
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return TimeOffRead.model_validate(rec).model_dump(mode='json')


def delete_timeoff_impl(rec_id: int):
    """Delete time-off record"""
    with next(get_session()) as session:
        rec = session.get(TimeOff, rec_id)
        if not rec:
            raise ValueError("Time off not found")
        session.delete(rec)
        session.commit()
        return {"ok": True}


# ===== UNAVAILABLE =====

def get_unavailable_impl(emp_id: int):
    """Get all unavailable blocks for employee"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        records = session.exec(select(UnavailableBlock).where(UnavailableBlock.employee_id == emp_id)).all()
        return [UnavailableBlockRead.model_validate(rec).model_dump(mode='json') for rec in records]


def create_unavailable_impl(emp_id: int, data: dict):
    """Create new unavailable block"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        data['employee_id'] = emp_id
        rec = UnavailableBlock.model_validate(UnavailableBlockCreate(**data))
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return UnavailableBlockRead.model_validate(rec).model_dump(mode='json')


def delete_unavailable_impl(rec_id: int):
    """Delete unavailable block"""
    with next(get_session()) as session:
        rec = session.get(UnavailableBlock, rec_id)
        if not rec:
            raise ValueError("Unavailable block not found")
        session.delete(rec)
        session.commit()
        return {"ok": True}


# ===== LOCKED SHIFTS =====

def get_locked_shifts_impl(emp_id: int):
    """Get all locked shifts for employee"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        records = session.exec(select(LockedShift).where(LockedShift.employee_id == emp_id)).all()
        return [LockedShiftRead.model_validate(rec).model_dump(mode='json') for rec in records]


def create_locked_shift_impl(emp_id: int, data: dict):
    """Create new locked shift"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        data['employee_id'] = emp_id
        rec = LockedShift.model_validate(LockedShiftCreate(**data))
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return LockedShiftRead.model_validate(rec).model_dump(mode='json')


def delete_locked_shift_impl(rec_id: int):
    """Delete locked shift"""
    with next(get_session()) as session:
        rec = session.get(LockedShift, rec_id)
        if not rec:
            raise ValueError("Locked shift not found")
        session.delete(rec)
        session.commit()
        return {"ok": True}


# ===== SETTINGS =====

def get_global_settings_impl():
    """Get global settings (single-user mode)"""
    with next(get_session()) as session:
        gs = session.exec(select(GlobalSettings)).first()
        if not gs:
            gs = GlobalSettings()
            session.add(gs)
            session.commit()
            session.refresh(gs)
        return gs.model_dump(mode='json')


def update_global_settings_impl(data: dict):
    """Update global settings"""
    with next(get_session()) as session:
        gs = session.exec(select(GlobalSettings)).first()
        if not gs:
            gs = GlobalSettings()
            session.add(gs)
            session.commit()
            session.refresh(gs)
        for k, v in data.items():
            if hasattr(gs, k) and k != 'id':
                setattr(gs, k, v)
        session.add(gs)
        session.commit()
        session.refresh(gs)
        return gs.model_dump(mode='json')


def get_business_hours_impl():
    """Get business hours for all days"""
    with next(get_session()) as session:
        hrs = session.exec(select(BusinessHours)).all()
        # Sort by weekday in Python
        sorted_hrs = sorted(hrs, key=lambda h: h.weekday)
        return [BusinessHoursRead.model_validate(h).model_dump(mode='json') for h in sorted_hrs]


def update_business_hours_impl(data: list):
    """Update business hours"""
    with next(get_session()) as session:
        existing = {bh.weekday: bh for bh in session.exec(select(BusinessHours)).all()}
        for item in data:
            weekday = item['weekday']
            if weekday in existing:
                rec = existing[weekday]
                rec.open_time = item['open_time']
                rec.close_time = item['close_time']
                session.add(rec)
            else:
                obj = BusinessHours.model_validate(BusinessHoursCreate(**item))
                session.add(obj)
        session.commit()
        hrs = session.exec(select(BusinessHours)).all()
        # Sort by weekday in Python
        sorted_hrs = sorted(hrs, key=lambda h: h.weekday)
        return [BusinessHoursRead.model_validate(h).model_dump(mode='json') for h in sorted_hrs]


# ===== STAFFING WINDOWS =====

def get_staffing_windows_impl():
    """Get all staffing windows"""
    with next(get_session()) as session:
        windows = session.exec(select(StaffingWindow)).all()
        return [StaffingWindowRead.model_validate(w).model_dump(mode='json') for w in windows]


def create_staffing_window_impl(data: dict):
    """Create a new staffing window"""
    with next(get_session()) as session:
        window = StaffingWindow.model_validate(StaffingWindowCreate(**data))
        session.add(window)
        session.commit()
        session.refresh(window)
        return StaffingWindowRead.model_validate(window).model_dump(mode='json')


def delete_staffing_window_impl(window_id: int):
    """Delete a staffing window"""
    with next(get_session()) as session:
        window = session.get(StaffingWindow, window_id)
        if not window:
            raise ValueError("Staffing window not found")
        session.delete(window)
        session.commit()
        return {"ok": True}


def update_staffing_windows_impl(data: list):
    """Update all staffing windows"""
    from sqlalchemy import delete as sql_delete

    with next(get_session()) as session:
        # Delete all existing
        session.exec(sql_delete(StaffingWindow))
        session.commit()

        # Add new ones
        for item in data:
            obj = StaffingWindow.model_validate(StaffingWindowCreate(**item))
            session.add(obj)
        session.commit()

        windows = session.exec(select(StaffingWindow)).all()
        return [StaffingWindowRead.model_validate(w).model_dump(mode='json') for w in windows]


# ===== SCHEDULE =====

def generate_schedule_impl(data: dict | None):
    """Generate schedule for a week"""
    import sys
    import json

    def progress_callback(progress_data):
        """Send progress updates to stdout for Electron to forward to renderer"""
        event = {
            'type': 'progress',
            'event': progress_data
        }
        print(json.dumps(event), flush=True)

    with next(get_session()) as session:
        week_start_str = (data or {}).get("week_start")
        week_start = date.fromisoformat(week_start_str) if week_start_str else None

        print(f"[SCHEDULE DEBUG] Received week_start_str='{week_start_str}', parsed={week_start}", file=sys.stderr)

        result = generate_week_schedule(session, week_start=week_start, progress_callback=progress_callback)
        return result


# ===== ADMIN =====

def backup_data_impl():
    """Export all data to JSON for backup"""
    with next(get_session()) as session:
        # Export all data
        backup = {
            "version": 1,
            "employees": [EmployeeRead.model_validate(e).model_dump(mode='json') for e in session.exec(select(Employee)).all()],
            "timeoff": [TimeOffRead.model_validate(t).model_dump(mode='json') for t in session.exec(select(TimeOff)).all()],
            "unavailable": [UnavailableBlockRead.model_validate(u).model_dump(mode='json') for u in session.exec(select(UnavailableBlock)).all()],
            "locked_shifts": [LockedShiftRead.model_validate(l).model_dump(mode='json') for l in session.exec(select(LockedShift)).all()],
            "global_settings": session.exec(select(GlobalSettings)).first().model_dump(mode='json') if session.exec(select(GlobalSettings)).first() else None,
            "business_hours": [BusinessHoursRead.model_validate(h).model_dump(mode='json') for h in session.exec(select(BusinessHours)).all()],
            "staffing_windows": [StaffingWindowRead.model_validate(w).model_dump(mode='json') for w in session.exec(select(StaffingWindow)).all()],
        }
        return backup


def restore_data_impl(data: dict):
    """Restore data from JSON backup"""
    from sqlalchemy import delete as sql_delete

    with next(get_session()) as session:
        # Clear existing data
        session.exec(sql_delete(LockedShift))
        session.exec(sql_delete(TimeOff))
        session.exec(sql_delete(UnavailableBlock))
        session.exec(sql_delete(Employee))
        session.exec(sql_delete(GlobalSettings))
        session.exec(sql_delete(StaffingWindow))
        session.exec(sql_delete(BusinessHours))
        session.commit()

        # Restore employees
        for emp_data in data.get("employees", []):
            # Remove id to let DB auto-generate
            emp_dict = {k: v for k, v in emp_data.items() if k != 'id'}
            emp = Employee.model_validate(EmployeeCreate(**emp_dict))
            session.add(emp)
        session.commit()

        # Build ID mapping (old_id -> new_id)
        old_to_new_emp_id = {}
        for idx, old_emp in enumerate(data.get("employees", [])):
            new_emp = session.exec(select(Employee)).all()[idx]
            old_to_new_emp_id[old_emp['id']] = new_emp.id

        # Restore time-off (with updated employee_id)
        for timeoff_data in data.get("timeoff", []):
            timeoff_dict = {k: v for k, v in timeoff_data.items() if k != 'id'}
            if timeoff_dict['employee_id'] in old_to_new_emp_id:
                timeoff_dict['employee_id'] = old_to_new_emp_id[timeoff_dict['employee_id']]
                timeoff = TimeOff.model_validate(TimeOffCreate(**timeoff_dict))
                session.add(timeoff)
        session.commit()

        # Restore unavailable blocks (with updated employee_id)
        for unavail_data in data.get("unavailable", []):
            unavail_dict = {k: v for k, v in unavail_data.items() if k != 'id'}
            if unavail_dict['employee_id'] in old_to_new_emp_id:
                unavail_dict['employee_id'] = old_to_new_emp_id[unavail_dict['employee_id']]
                unavail = UnavailableBlock.model_validate(UnavailableBlockCreate(**unavail_dict))
                session.add(unavail)
        session.commit()

        # Restore locked shifts (with updated employee_id)
        for locked_data in data.get("locked_shifts", []):
            locked_dict = {k: v for k, v in locked_data.items() if k != 'id'}
            if locked_dict['employee_id'] in old_to_new_emp_id:
                locked_dict['employee_id'] = old_to_new_emp_id[locked_dict['employee_id']]
                locked = LockedShift.model_validate(LockedShiftCreate(**locked_dict))
                session.add(locked)
        session.commit()

        # Restore global settings
        if data.get("global_settings"):
            gs = GlobalSettings.model_validate(data["global_settings"])
            session.add(gs)
            session.commit()

        # Restore business hours
        for bh_data in data.get("business_hours", []):
            bh_dict = {k: v for k, v in bh_data.items() if k != 'id'}
            bh = BusinessHours.model_validate(BusinessHoursCreate(**bh_dict))
            session.add(bh)
        session.commit()

        # Restore staffing windows
        for sw_data in data.get("staffing_windows", []):
            sw_dict = {k: v for k, v in sw_data.items() if k != 'id'}
            sw = StaffingWindow.model_validate(StaffingWindowCreate(**sw_dict))
            session.add(sw)
        session.commit()

        return {"ok": True, "message": "Data restored successfully"}


def reset_data_impl():
    """Reset all data (single-user mode)"""
    from sqlalchemy import delete as sql_delete

    with next(get_session()) as session:
        # Delete all data using SQLAlchemy delete() instead of raw SQL
        session.exec(sql_delete(LockedShift))
        session.exec(sql_delete(TimeOff))
        session.exec(sql_delete(UnavailableBlock))
        session.exec(sql_delete(Employee))
        session.exec(sql_delete(GlobalSettings))
        session.exec(sql_delete(StaffingWindow))
        session.exec(sql_delete(BusinessHours))
        session.commit()
        return {"ok": True}
