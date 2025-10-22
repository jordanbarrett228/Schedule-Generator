# backend/app/newSolver/objectives.py
from __future__ import annotations
from typing import Dict
from ortools.sat.python import cp_model
from app.newSolver.model_builder import hours_to_slots
from app.newSolver.grid import SLOTS_PER_HOUR

def add_objective(model: cp_model.CpModel,
                  X,
                  employees,
                  week_grid,
                  under_staff,
                  emp_week_sum):
    """
    Adds multi-weighted objective identical to original logic.
    Returns dict of all auxiliary vars for test visibility.
    """
    W_COVER = 1000
    W_HOURS = 10
    W_FRAG = 1
    W_DAYS_OFF = 8

    terms = [W_COVER * under_staff[k] for k in under_staff]

    # Preferred weekly hours (L1 deviation)
    under_hours, over_hours = {}, {}
    for e in employees:
        if e.preferred_hours is None:
            continue
        t = hours_to_slots(e.preferred_hours)
        u = model.NewIntVar(0, 7*24*SLOTS_PER_HOUR, f"under_e{e.id}")
        o = model.NewIntVar(0, 7*24*SLOTS_PER_HOUR, f"over_e{e.id}")
        model.Add(emp_week_sum[e.id] + u - o == t)
        under_hours[e.id] = u
        over_hours[e.id] = o
        terms.append(W_HOURS * u)
        terms.append(W_HOURS * o)

    # Days-off soft deviation
    days_under, days_over = {}, {}
    for e in employees:
        if e.target_days_off is None:
            continue
        worked_flags = []
        for d, day in enumerate(week_grid):
            if not day.slots:
                worked_flags.append(model.NewConstant(0))
                continue
            w = model.NewBoolVar(f"worked_e{e.id}_d{d}")
            model.AddMaxEquality(w, [X[(e.id, d, i)] for i in range(len(day.slots))])
            worked_flags.append(w)
        off_total = model.NewIntVar(0,7,f"off_e{e.id}")
        model.Add(off_total == 7 - sum(worked_flags))
        u = model.NewIntVar(0,7,f"days_under_e{e.id}")
        o = model.NewIntVar(0,7,f"days_over_e{e.id}")
        model.Add(off_total + u - o == int(e.target_days_off))
        days_under[e.id], days_over[e.id] = u,o
        terms.append(W_DAYS_OFF*u)
        terms.append(W_DAYS_OFF*o)

    # Fragment penalty (minimize starts)
    for e in employees:
        for d, day in enumerate(week_grid):
            n = len(day.slots)
            if n == 0:
                continue
            y = [model.NewBoolVar(f"frag_e{e.id}_d{d}_i{i}") for i in range(n)]
            for i in range(n):
                prev = X[(e.id, d, i-1)] if i>0 else model.NewConstant(0)
                model.Add(y[i] >= X[(e.id, d, i)] - prev)
                model.Add(y[i] <= X[(e.id, d, i)])
            terms.append(W_FRAG * sum(y))

    model.Minimize(sum(terms))
    return {"under_hours": under_hours, "over_hours": over_hours,
            "days_under": days_under, "days_over": days_over}
