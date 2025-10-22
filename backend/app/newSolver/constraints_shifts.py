# backend/app/newSolver/constraints_shifts.py
from __future__ import annotations
from ortools.sat.python import cp_model
from typing import Dict, Tuple, List
from app.newSolver.grid import SLOTS_PER_HOUR


# ---------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------
def hours_to_slots(h: float) -> int:
    """Convert hour count to discrete slot count (e.g., 1h = 4 if 15-min slots)."""
    return int(round(h * SLOTS_PER_HOUR))


# ---------------------------------------------------------------------
# Core: daily segment enforcement
# ---------------------------------------------------------------------
def apply_daily_segments_and_lengths(
    model: cp_model.CpModel,
    X: Dict[Tuple[int, int, int], cp_model.IntVar],  # (eid, day, slot) -> var
    employees,
    week_grid,
) -> None:
    """
    Enforces daily shift shape rules:
      • ≤ 1 segment/day (or ≤ 2 if allow_split_shifts=True)
      • Each segment ≥ min_shift_hours
      • Each segment ≤ max_shift_hours

    These rules prevent unrealistic patterns like:
        08:00–09:00 + 12:15–13:15 (disjoint) unless explicitly allowed.
    """

    for e in employees:
        eid = int(e.id) if e.id is not None else -1
        min_len = hours_to_slots(getattr(e, "min_shift_hours", 0))
        max_len = hours_to_slots(getattr(e, "max_shift_hours", 8))
        seg_cap = 2 if getattr(e, "allow_split_shifts", False) else 1

        for d, day in enumerate(week_grid):
            n = len(day.slots)
            if n == 0:
                continue

            # -------------- Detect start of a working segment --------------
            y_start = [model.NewBoolVar(f"start_e{eid}_d{d}_i{i}") for i in range(n)]
            for i in range(n):
                prev = X.get((eid, d, i - 1), model.NewConstant(0))
                model.Add(y_start[i] >= X[(eid, d, i)] - prev)
                model.Add(y_start[i] <= X[(eid, d, i)])

            # Limit total segments per day
            model.Add(sum(y_start) <= seg_cap)

            # Prevent starting too late to fit minimum shift length
            for i in range(n):
                if i + min_len > n:
                    model.Add(y_start[i] == 0)

            # -------------- Enforce minimum length --------------
            # If a shift starts at i, at least min_len consecutive 1s must follow.
            for i in range(n - min_len + 1):
                model.Add(
                    sum(X[(eid, d, j)] for j in range(i, i + min_len))
                    >= min_len * y_start[i]
                )

            # -------------- Enforce maximum length --------------
            # No run of consecutive work slots longer than max_len.
            if max_len < n:
                for i in range(n - max_len):
                    model.Add(
                        sum(X[(eid, d, j)] for j in range(i, i + max_len + 1))
                        <= max_len
                    )
