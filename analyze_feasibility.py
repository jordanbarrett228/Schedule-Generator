"""
Simple feasibility analysis without running the solver.
Calculates if the constraints are mathematically feasible.
"""
import datetime as dt

# Business hours (same as defaults)
business_hours = {
    0: (dt.time(4, 45), dt.time(21, 15)),  # Mon
    1: (dt.time(4, 45), dt.time(21, 15)),  # Tue
    2: (dt.time(4, 45), dt.time(21, 15)),  # Wed
    3: (dt.time(4, 45), dt.time(21, 15)),  # Thu
    4: (dt.time(4, 45), dt.time(21, 15)),  # Fri
    5: (dt.time(4, 45), dt.time(21, 15)),  # Sat
    6: (dt.time(4, 45), dt.time(21, 15)),  # Sun
}

def time_to_minutes(t):
    return t.hour * 60 + t.minute

def analyze_feasibility(num_employees, min_staff=2):
    """Analyze if scheduling is mathematically feasible"""

    # Calculate total business hours
    total_minutes = sum(
        time_to_minutes(close) - time_to_minutes(open)
        for open, close in business_hours.values()
    )
    total_hours = total_minutes / 60

    # Staff-hours needed (every minute needs min_staff people)
    staff_hours_needed = total_hours * min_staff

    # Employee constraints
    min_hours_per_emp = 20
    max_hours_per_emp = 40

    # Total hours employees can provide
    total_min_hours = num_employees * min_hours_per_emp
    total_max_hours = num_employees * max_hours_per_emp

    print("="*70)
    print(f"FEASIBILITY ANALYSIS: {num_employees} EMPLOYEES")
    print("="*70)
    print(f"\nBUSINESS SCHEDULE:")
    print(f"  Total business hours per week: {total_hours:.1f} hours")
    print(f"  Minimum staff required: {min_staff} people at all times")
    print(f"  Total staff-hours needed: {staff_hours_needed:.1f} hours")
    print(f"    (business_hours × min_staff)")

    print(f"\nEMPLOYEE CONSTRAINTS:")
    print(f"  Number of employees: {num_employees}")
    print(f"  Min hours per employee: {min_hours_per_emp} hrs")
    print(f"  Max hours per employee: {max_hours_per_emp} hrs")
    print(f"  Total minimum hours available: {total_min_hours} hrs")
    print(f"  Total maximum hours available: {total_max_hours} hrs")

    print(f"\nFEASIBILITY CHECK:")
    print(f"  Staff-hours needed: {staff_hours_needed:.1f} hrs")
    print(f"  Employee hours available: {total_min_hours} - {total_max_hours} hrs")

    if staff_hours_needed > total_max_hours:
        print(f"\n  ✗ INFEASIBLE: Need {staff_hours_needed:.1f} hrs but max available is {total_max_hours} hrs")
        deficit = staff_hours_needed - total_max_hours
        print(f"    SHORT BY: {deficit:.1f} hours")
        print(f"    NEED {deficit / max_hours_per_emp:.1f} MORE EMPLOYEES (at max hours)")
    elif staff_hours_needed < total_min_hours:
        print(f"\n  ⚠ OVER-STAFFED: Need {staff_hours_needed:.1f} hrs but minimum is {total_min_hours} hrs")
        excess = total_min_hours - staff_hours_needed
        print(f"    EXCESS: {excess:.1f} hours")
        print(f"    This will force employees to work more than needed for coverage")
        print(f"    OR reduce min_hours_week OR remove {excess / min_hours_per_emp:.1f} employees")
    else:
        print(f"\n  ✓ FEASIBLE: Staff-hours needed ({staff_hours_needed:.1f}) is between")
        print(f"    employee min ({total_min_hours}) and max ({total_max_hours})")

    # Additional constraint checks
    print(f"\nADDITIONAL CONSTRAINTS:")

    # Check shift length constraints
    min_shift = 4  # hours
    max_shift = 7  # hours
    print(f"  Shift length: {min_shift}-{max_shift} hours")

    # Check if employee can physically be scheduled
    # Each employee works min 20hrs with shifts of 4-7hrs
    min_shifts_needed = min_hours_per_emp / max_shift  # minimum number of shifts
    max_shifts_possible = max_hours_per_emp / min_shift  # maximum number of shifts

    print(f"  Min shifts per employee: {min_shifts_needed:.1f} (at {max_shift}hrs each)")
    print(f"  Max shifts per employee: {max_shifts_possible:.1f} (at {min_shift}hrs each)")

    # With 7 days, check if realistic
    if min_shifts_needed > 7:
        print(f"  ⚠ WARNING: Employee needs {min_shifts_needed:.1f} shifts but only 7 days available!")
        print(f"    This requires split shifts (multiple shifts per day)")

    print("="*70)
    print()

# Test different employee counts
print("\n" + "="*70)
print("SCHEDULE GENERATOR FEASIBILITY ANALYSIS")
print("="*70 + "\n")

for count in [7, 8, 9, 10, 11, 12]:
    analyze_feasibility(count, min_staff=2)
    input("Press Enter to continue...")

print("\nANALYSIS COMPLETE")
