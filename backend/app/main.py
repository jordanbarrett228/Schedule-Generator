from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from .db import engine, create_db_and_tables
from .models.employee import Employee, EmployeeCreate

app = FastAPI(title="ChatGPT Schedule Generator - Backend")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/employees", response_model=Employee)
def create_employee(payload: EmployeeCreate):
    with Session(engine) as session:
        emp = Employee.from_orm(payload)
        session.add(emp)
        session.commit()
        session.refresh(emp)
        return emp


@app.get("/employees")
def list_employees():
    with Session(engine) as session:
        employees = session.exec(select(Employee)).all()
        return employees


@app.get("/employees/{employee_id}")
def get_employee(employee_id: int):
    with Session(engine) as session:
        emp = session.get(Employee, employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return emp
