# backend/app/routers/rt_employees.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from ...db import get_session
from ...models.employee import Employee, EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.models.user import UserRead
from app.auth import get_current_user

router = APIRouter(prefix="/api/employees", tags=["employees"])

# ===== HTTP ENDPOINTS (for legacy/web mode) =====

@router.get("", response_model=List[EmployeeRead])
def list_employees(session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    return session.exec(
        select(Employee).where(Employee.user_id == current_user.id).order_by(Employee.id)  # type: ignore
    ).all()

@router.post("", response_model=EmployeeRead)
def create_employee(payload: EmployeeCreate, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    emp = Employee.model_validate(payload)
    emp.user_id = current_user.id
    session.add(emp)
    session.commit()
    session.refresh(emp)
    return emp

@router.put("/{emp_id}", response_model=EmployeeRead)
def update_employee(emp_id: int, payload: EmployeeUpdate, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    emp = session.get(Employee, emp_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Employee not found")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(emp, k, v)
    session.add(emp)
    session.commit()
    session.refresh(emp)
    return emp

@router.delete("/{emp_id}")
def delete_employee(emp_id: int, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    emp = session.get(Employee, emp_id)
    if not emp or emp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Employee not found")
    session.delete(emp)
    session.commit()
    return {"ok": True}


# ===== IPC IMPLEMENTATIONS (for standalone/Electron mode - no auth) =====

def get_employees_impl():
    """Get all employees (single-user mode)"""
    with next(get_session()) as session:
        employees = session.exec(select(Employee).order_by(Employee.id)).all()
        return [EmployeeRead.model_validate(emp).model_dump() for emp in employees]


def get_employee_impl(emp_id: int):
    """Get single employee"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        return EmployeeRead.model_validate(emp).model_dump()


def create_employee_impl(data: dict):
    """Create new employee (single-user mode)"""
    with next(get_session()) as session:
        emp = Employee.model_validate(EmployeeCreate(**data))
        # No user_id needed in single-user mode
        session.add(emp)
        session.commit()
        session.refresh(emp)
        return EmployeeRead.model_validate(emp).model_dump()


def update_employee_impl(emp_id: int, data: dict):
    """Update employee"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        for k, v in data.items():
            if hasattr(emp, k):
                setattr(emp, k, v)
        session.add(emp)
        session.commit()
        session.refresh(emp)
        return EmployeeRead.model_validate(emp).model_dump()


def delete_employee_impl(emp_id: int):
    """Delete employee"""
    with next(get_session()) as session:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise ValueError("Employee not found")
        session.delete(emp)
        session.commit()
        return {"ok": True}