# backend/app/newSolver/core.py
from __future__ import annotations
import datetime as dt
from ortools.sat.python import cp_model
from sqlmodel import Session

from app.newSolver.grid import build_week_grid, next_monday
from app.newSolver.data_loader import load_user_data
from app.newSolver.masks import build_masks
from app.newSolver.targets import compute_targets
from app.newSolver.model_builder import (
    build_cp_variables,
    apply_coverage_constraints,
    apply_weekly_hours,
)
from app.newSolver.constraints_shifts import apply_daily_segments_and_lengths
from app.newSolver.constraints_clopen import apply_no_clopen
from app.newSolver.objectives import add_objective
from app.newSolver.postprocess import extract_shifts, summarize_hours, summarize_coverage
from app.newSolver.diagnostics import _collect_pre_solve_diagnostics


def generate_week_schedule(
    session: Session, week_start: dt.date | None = None
) -> dict:
    """
    Main solver orchestrator for schedule generation.

    Steps:
      1. Load DB data (employees, unavailable blocks, timeoff, locked shifts, etc.)
      2. Build 15-min week grid based on BusinessHours.
      3. Compute staffing targets and caps.
      4. Build availability + lock masks.
      5. Build OR-Tools model (variables + constraints + objective).
      6. Solve and postprocess into JSON-ready result.
    """
    # 1) Establish week start
    week_start = week_start or next_monday()

    # 2) Load all data
    data = load_user_data(session)

    # 3) Build grid (open/close slots)
    week_grid = build_week_grid(session)

    # 4) Build availability & lock masks
    masks = build_masks(
        employees=data.employees,
        emp_unavail=data.unavailable,
        emp_timeoff=data.timeoff,
        emp_locked=data.locked,
        week_grid=week_grid,
        week_start=week_start,
    )

    # 5) Compute staffing targets and caps
    soft_target, hard_cap, prefer_full_day, min_staff_default = compute_targets(
        session=session,
        employees_count=len(data.employees),
        week_grid=week_grid,
    )

    # 5.5) Run pre-solve diagnostics to detect infeasibility early
    diagnostics = _collect_pre_solve_diagnostics(
        week_grid=week_grid,
        employees=data.employees,
        avail_map=masks.avail_map,
        lock_map=masks.lock_map,
        hard_cap=hard_cap,
        min_staff_hard=1,
    )

    # If we have errors, return early with diagnostic info
    errors = [d for d in diagnostics if d.get("severity") == "error"]
    if errors:
        return {
            "status": "infeasible",
            "week_start": week_start.isoformat(),
            "slot_minutes": 15,
            "shifts": [],
            "diagnostics": diagnostics,
            "notes": f"Pre-solve validation detected {len(errors)} error(s). See diagnostics for details.",
        }

    # 6) Build model + variables
    model = cp_model.CpModel()
    X = build_cp_variables(model, data.employees, week_grid, masks.avail, masks.lock)

    # 7) Coverage and hours constraints
    under_staff = apply_coverage_constraints(
        model, X, data.employees, week_grid, soft_target, hard_cap
    )
    emp_week_sum = apply_weekly_hours(model, X, data.employees, week_grid)

    # 8) Daily shift structure constraints
    apply_daily_segments_and_lengths(model, X, data.employees, week_grid)

    # 9) No-clopen rule
    apply_no_clopen(model, X, data.employees, week_grid)

    # 10) Objective function
    _aux = add_objective(model, X, data.employees, week_grid, under_staff, emp_week_sum)

    # 11) Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 120 
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # Try relaxation: remove minimum hours constraint
        import sys
        print("[Solver] Initial attempt failed. Trying with relaxed weekly minimum hours...", file=sys.stderr)

        model_relaxed = cp_model.CpModel()
        X_relaxed = build_cp_variables(model_relaxed, data.employees, week_grid, masks.avail, masks.lock)

        # Reapply coverage constraints
        under_staff_r = apply_coverage_constraints(
            model_relaxed, X_relaxed, data.employees, week_grid, soft_target, hard_cap
        )

        # Calculate week sum but DON'T enforce hard minimum (only max)
        from app.newSolver.model_builder import hours_to_slots
        emp_week_sum_r = {}
        for emp in data.employees:
            eid = int(emp.id) if emp.id is not None else -1
            slot_vars = [X_relaxed[(eid, d, i)] for d, day in enumerate(week_grid) for i in range(len(day.slots)) if (eid, d, i) in X_relaxed]
            total_expr = sum(slot_vars, model_relaxed.NewConstant(0))

            # Only enforce MAX hours (min becomes soft penalty)
            max_slots = hours_to_slots(getattr(emp, "max_hours_week", 40))
            model_relaxed.Add(total_expr <= max_slots)
            emp_week_sum_r[eid] = total_expr

        # Reapply shift structure and clopen
        apply_daily_segments_and_lengths(model_relaxed, X_relaxed, data.employees, week_grid)
        apply_no_clopen(model_relaxed, X_relaxed, data.employees, week_grid)

        # Objective (min hours is soft penalty now)
        _aux_r = add_objective(model_relaxed, X_relaxed, data.employees, week_grid, under_staff_r, emp_week_sum_r)

        # Solve relaxed model
        solver_relaxed = cp_model.CpSolver()
        solver_relaxed.parameters.max_time_in_seconds = 120
        solver_relaxed.parameters.num_search_workers = 8
        status_relaxed = solver_relaxed.Solve(model_relaxed)

        if status_relaxed not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return {
                "status": "infeasible",
                "week_start": week_start.isoformat(),
                "slot_minutes": 15,
                "shifts": [],
                "diagnostics": diagnostics,
                "notes": "Solver could not find a feasible schedule even with relaxed constraints. Check diagnostics for hard constraint conflicts.",
            }

        # Success with relaxed constraints
        X_get_r = lambda eid, d, i: int(solver_relaxed.Value(X_relaxed[(eid, d, i)]))
        shifts_relaxed = extract_shifts(solver_relaxed, X_get_r, data.employees, week_grid)

        return {
            "status": "feasible_relaxed",
            "week_start": week_start.isoformat(),
            "slot_minutes": 15,
            "min_staff_default": min_staff_default,
            "shifts": shifts_relaxed,
            "employee_hours": summarize_hours(shifts_relaxed, data.employees),
            "coverage": summarize_coverage(shifts_relaxed, week_grid),
            "diagnostics": diagnostics,
            "notes": "Schedule generated with RELAXED constraints: weekly minimum hours were reduced to fit availability. Some employees may have fewer hours than requested.",
        }

    # 12) Extract solution
    X_get = lambda eid, d, i: int(solver.Value(X[(eid, d, i)]))
    shifts = extract_shifts(solver, X_get, data.employees, week_grid)

    return {
        "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
        "week_start": week_start.isoformat(),
        "slot_minutes": 15,
        "min_staff_default": min_staff_default,
        "shifts": shifts,
        "employee_hours": summarize_hours(shifts, data.employees),
        "coverage": summarize_coverage(shifts, week_grid),
        "diagnostics": diagnostics,  # Include warnings even on success
    }
