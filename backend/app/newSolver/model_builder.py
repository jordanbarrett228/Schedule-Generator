# backend/app/newSolver/model_builder.py
from __future__ import annotations
from typing import Dict, Tuple, List
from ortools.sat.python import cp_model

from app.newSolver.grid import SLOT_MIN, SLOTS_PER_HOUR, DayGrid
from app.models.employee import Employee


# ---------------------------------------------------------------------
# Variable creation
# ---------------------------------------------------------------------

def build_cp_variables(
    model: cp_model.CpModel,
    employees: List[Employee],
    week_grid: List[DayGrid],
    mask_avail: Dict[int, Dict[int, List[int]]],
    mask_lock: Dict[int, Dict[int, List[int]]],
) -> Dict[Tuple[int, int, int], cp_model.IntVar]:
    """
    Create Boolean vars X[(emp_id, day, slot)] for all available slots.
    Locked slots are fixed to 1; unavailable slots are constants 0.
    """
    import sys
    X: Dict[Tuple[int, int, int], cp_model.IntVar] = {}

    for emp in employees:
        eid = int(emp.id) if emp.id is not None else -1
        for d, day in enumerate(week_grid):
            # Debug for employee 1 on days 1 and 2
            if eid == 1 and d in [1, 2]:
                avail_day = mask_avail.get(eid, {}).get(d, [])
                blocked = sum(1 for x in avail_day if x == 0)
                print(f"[MODEL] Emp {eid} Day {d}: {blocked}/{len(avail_day)} slots blocked", file=sys.stderr)

            for i in range(len(day.slots)):
                avail = mask_avail.get(eid, {}).get(d, [])
                lock = mask_lock.get(eid, {}).get(d, [])

                if not avail or i >= len(avail) or avail[i] == 0:
                    X[(eid, d, i)] = model.NewConstant(0)
                    continue

                v = model.NewBoolVar(f"x_e{eid}_d{d}_i{i}")

                if lock and i < len(lock) and lock[i] == 1:
                    model.Add(v == 1)

                X[(eid, d, i)] = v

    return X


# ---------------------------------------------------------------------
# Coverage constraints
# ---------------------------------------------------------------------

def apply_coverage_constraints(
    model: cp_model.CpModel,
    X: Dict[Tuple[int, int, int], cp_model.IntVar],
    employees: List[Employee],
    week_grid: List[DayGrid],
    soft_target: List[List[int]],
    hard_cap: List[List[int]],
) -> Dict[Tuple[int, int], cp_model.IntVar]:
    """
    Adds coverage ≥1 and ≤hard_cap, plus soft_target penalties.
    Returns under_staff[(d,i)] = IntVar measuring shortage.
    """
    under_staff: Dict[Tuple[int, int], cp_model.IntVar] = {}

    for d, day in enumerate(week_grid):
        for i in range(len(day.slots)):
            total = sum(X[(int(e.id), d, i)] for e in employees if e.id is not None and (int(e.id), d, i) in X)

            model.Add(total >= 1)
            model.Add(total <= hard_cap[d][i])

            u = model.NewIntVar(0, len(employees), f"u_d{d}_i{i}")
            model.Add(total + u >= soft_target[d][i])
            under_staff[(d, i)] = u

    return under_staff


# ---------------------------------------------------------------------
# Weekly hours constraints
# ---------------------------------------------------------------------

def hours_to_slots(hours: float) -> int:
    """Convert hours to slot count given SLOT_MIN."""
    return int(round(hours * SLOTS_PER_HOUR))


def apply_weekly_hours(
    model: cp_model.CpModel,
    X: Dict[Tuple[int, int, int], cp_model.IntVar],
    employees: List[Employee],
    week_grid: List[DayGrid],
) -> Dict[int, cp_model.LinearExpr]:
    """
    Add min/max weekly hours per employee.
    Returns emp_week_sum[eid] = LinearExpr representing total slots worked.
    """
    emp_week_sum: Dict[int, cp_model.LinearExpr] = {}

    for emp in employees:
        eid = int(emp.id) if emp.id is not None else -1

        # Sum all slots where variable exists
        slot_vars = [X[(eid, d, i)] for d, day in enumerate(week_grid) for i in range(len(day.slots)) if (eid, d, i) in X]
        total_expr = sum(slot_vars, model.NewConstant(0))  # ✅ ensures LinearExpr type

        # Convert hour bounds to slot bounds
        min_slots = hours_to_slots(getattr(emp, "min_hours_week", 0))
        max_slots = hours_to_slots(getattr(emp, "max_hours_week", 40))

        model.Add(total_expr >= min_slots)
        model.Add(total_expr <= max_slots)

        emp_week_sum[eid] = total_expr  # ✅ always LinearExpr

    return emp_week_sum
