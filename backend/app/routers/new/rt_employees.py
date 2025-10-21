# backend/app/routers/rt_employees.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from ...db import get_session
from ...models.employee import Employee, EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.models.user import UserRead
from app.auth import get_current_user

router = APIRouter(prefix="/api/employees", tags=["employees"])

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