"""
Test script to debug why scheduling fails with 10+ employees.
Creates 10 employees with default settings and attempts to generate a schedule.
"""
import sys
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel, select
from app.models.employee import Employee
from app.models.settings import BusinessHours, GlobalSettings
from app.newSolver.core import generate_week_schedule
import datetime as dt

# Setup test database
TEST_DB = "sqlite:///test_schedule.db"
engine = create_engine(TEST_DB, echo=False)

def setup_test_database():
    """Create tables and initialize business hours + settings"""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create business hours (Mon-Sun, 4:45 AM to 9:15 PM)
        defaults = {
            0: (dt.time(4, 45), dt.time(21, 15)),  # Mon
            1: (dt.time(4, 45), dt.time(21, 15)),  # Tue
            2: (dt.time(4, 45), dt.time(21, 15)),  # Wed
            3: (dt.time(4, 45), dt.time(21, 15)),  # Thu
            4: (dt.time(4, 45), dt.time(21, 15)),  # Fri
            5: (dt.time(4, 45), dt.time(21, 15)),  # Sat
            6: (dt.time(4, 45), dt.time(21, 15)),  # Sun
        }

        for weekday, (open_time, close_time) in defaults.items():
            bh = BusinessHours(
                weekday=weekday,
                open_time=open_time,
                close_time=close_time
            )
            session.add(bh)

        # Create global settings
        settings = GlobalSettings(
            min_staff_default=2,
            max_staff_default=10
        )
        session.add(settings)

        session.commit()
        print("✓ Business hours and settings initialized")

def create_test_employees(count: int):
    """Create N employees with default settings (all 100% available)"""
    with Session(engine) as session:
        for i in range(1, count + 1):
            emp = Employee(
                name=f"Employee {i}",
                active=True,
                min_hours_week=20,  # HR requirement
                max_hours_week=40,
                min_shift_hours=4,
                max_shift_hours=7,
                preferred_hours=25,
                target_days_off=2,
                prefer_opening=True,
                prefer_mid=True,
                prefer_closing=True,
                allow_split_shifts=False,
                no_clopen=False
            )
            session.add(emp)

        session.commit()
        print(f"✓ Created {count} employees with default settings")

def analyze_availability():
    """Calculate total available hours and required minimum hours"""
    with Session(engine) as session:
        # Get business hours
        bh_list = list(session.exec(select(BusinessHours)).all())

        total_minutes = 0
        for bh in bh_list:
            open_min = bh.open_time.hour * 60 + bh.open_time.minute
            close_min = bh.close_time.hour * 60 + bh.close_time.minute
            total_minutes += (close_min - open_min)

        total_hours = total_minutes / 60

        # Get employees
        employees = list(session.exec(select(Employee).where(Employee.active == True)).all())
        emp_count = len(employees)

        # Calculate requirements
        total_min_hours_required = sum(e.min_hours_week for e in employees)
        total_preferred_hours = sum(e.preferred_hours or 0 for e in employees)

        print("\n" + "="*60)
        print("AVAILABILITY ANALYSIS")
        print("="*60)
        print(f"Business hours per week: {total_hours:.1f} hours")
        print(f"Number of employees: {emp_count}")
        print(f"Min hours per employee: 20 hours")
        print(f"Total minimum hours required: {total_min_hours_required:.1f} hours")
        print(f"Total preferred hours: {total_preferred_hours:.1f} hours")

        # Get min staff requirement
        settings = session.exec(select(GlobalSettings)).first()
        min_staff = settings.min_staff_default if settings else 1

        # Calculate maximum assignable hours (considering min staff constraint)
        max_assignable = total_hours * emp_count / min_staff

        print(f"\nMinimum staff required: {min_staff}")
        print(f"Maximum assignable hours: {max_assignable:.1f} hours")
        print(f"  (total_hours × emp_count / min_staff)")

        # Analysis
        print("\n" + "-"*60)
        if total_min_hours_required <= max_assignable:
            print("✓ FEASIBLE: Minimum hours can be satisfied")
            slack = max_assignable - total_min_hours_required
            print(f"  Slack: {slack:.1f} hours available above minimum")
        else:
            deficit = total_min_hours_required - max_assignable
            print(f"✗ INFEASIBLE: Minimum hours CANNOT be satisfied")
            print(f"  Deficit: {deficit:.1f} hours SHORT")
            print(f"\n  Reason: With min_staff={min_staff}, you can only assign")
            print(f"  {max_assignable:.1f} hours total, but need {total_min_hours_required:.1f} hours minimum.")

        if total_preferred_hours <= max_assignable:
            print(f"✓ Preferred hours can be satisfied")
        else:
            deficit = total_preferred_hours - max_assignable
            print(f"⚠ Preferred hours might not be fully satisfied")
            print(f"  Would need {deficit:.1f} more hours")
        print("="*60 + "\n")

def test_schedule_generation():
    """Attempt to generate a schedule and report results"""
    with Session(engine) as session:
        print("Attempting to generate schedule...")
        result = generate_week_schedule(session)

        print("\n" + "="*60)
        print("SCHEDULE GENERATION RESULT")
        print("="*60)
        print(f"Status: {result['status']}")

        if result['status'] == 'infeasible':
            print("\n✗ SCHEDULE GENERATION FAILED (INFEASIBLE)")

            if 'diagnostics' in result and result['diagnostics']:
                print(f"\nDiagnostics ({len(result['diagnostics'])} issues found):")
                print("-"*60)
                for diag in result['diagnostics']:
                    severity = diag.get('severity', 'unknown').upper()
                    code = diag.get('code', 'UNKNOWN')
                    message = diag.get('message', 'No message')
                    print(f"[{severity}] {code}")
                    print(f"  {message}")
                    print()

            if 'notes' in result:
                print(f"Notes: {result['notes']}")
        else:
            print(f"\n✓ SCHEDULE GENERATION SUCCEEDED")
            print(f"Generated {len(result.get('shifts', []))} shifts")

            if 'employee_hours' in result:
                print("\nEmployee hours:")
                for emp_hours in result['employee_hours']:
                    print(f"  {emp_hours['name']}: {emp_hours['total_hours']:.1f} hours")

        print("="*60)
        return result

def main():
    print("="*60)
    print("TESTING SCHEDULE GENERATION WITH 10+ EMPLOYEES")
    print("="*60 + "\n")

    # Setup
    setup_test_database()

    # Test with different employee counts
    for count in [7, 9, 10, 12]:
        print(f"\n{'='*60}")
        print(f"TESTING WITH {count} EMPLOYEES")
        print(f"{'='*60}\n")

        # Clear and recreate employees
        with Session(engine) as session:
            employees = session.exec(select(Employee)).all()
            for emp in employees:
                session.delete(emp)
            session.commit()

        create_test_employees(count)
        analyze_availability()
        result = test_schedule_generation()

        if result['status'] == 'infeasible':
            print(f"\n⚠ FAILED at {count} employees - stopping here to analyze")
            break
        else:
            print(f"\n✓ SUCCESS with {count} employees - continuing...")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
