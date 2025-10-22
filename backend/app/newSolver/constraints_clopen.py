# backend/app/newSolver/constraints_clopen.py
from __future__ import annotations
from ortools.sat.python import cp_model
from app.newSolver.grid import SLOTS_PER_HOUR, time_to_min

def apply_no_clopen(
    model: cp_model.CpModel,
    X,
    employees,
    week_grid,
):
    """
    If employee worked in the last hour on day d, they cannot work before
    clopen_next_day_not_before on day d+1. Matches your original code.
    """
    for e in employees:
        if not e.no_clopen:
            continue

        not_before = (
            time_to_min(e.clopen_next_day_not_before)
            if e.clopen_next_day_not_before
            else 9 * 60
        )

        for d, day in enumerate(week_grid):
            if d == 6 or len(day.slots) == 0:
                continue

            # worked in last hour of day d?
            z_closed = model.NewBoolVar(f"closed_last_hour_e{e.id}_d{d}")
            last_window = min(len(day.slots), SLOTS_PER_HOUR)
            start_i = len(day.slots) - last_window
            model.AddMaxEquality(z_closed, [X[(e.id, d, j)] for j in range(start_i, len(day.slots))])

            # forbid early slots on day d+1 if z_closed==1
            day2 = week_grid[d + 1]
            for i, m in enumerate(day2.slots):
                if m < not_before:
                    model.Add(X[(e.id, d + 1, i)] + z_closed <= 1)
