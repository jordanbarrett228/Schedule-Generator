# backend/app/newSolver/postprocess.py
from __future__ import annotations
import math
from typing import Dict
from ortools.sat.python import cp_model
from app.newSolver.grid import min_to_hhmm, hhmm_to_min, SLOT_MIN, WEEKDAYS

def extract_shifts(solver: cp_model.CpSolver, X_get, employees, week_grid):
    """Return list of contiguous scheduled shifts."""
    shifts = []
    for e in employees:
        for d, day in enumerate(week_grid):
            if not day.slots:
                continue
            n = len(day.slots)
            i = 0
            while i < n:
                if X_get(e.id, d, i) == 1:
                    start = i
                    i += 1
                    while i < n and X_get(e.id, d, i) == 1:
                        i += 1
                    end = i
                    start_min = day.slots[start]
                    end_min = day.slots[end-1] + SLOT_MIN
                    shifts.append({
                        "employee_id": e.id,
                        "employee_name": e.name,
                        "weekday": d,
                        "weekday_name": WEEKDAYS[d],
                        "start": min_to_hhmm(start_min),
                        "end": min_to_hhmm(end_min)
                    })
                else:
                    i += 1
    return shifts

def summarize_hours(shifts, employees):
    emp_minutes: Dict[int,int] = {e.id:0 for e in employees}
    for s in shifts:
        emp_minutes[s["employee_id"]] += max(0, hhmm_to_min(s["end"]) - hhmm_to_min(s["start"]))
    return [
        {"employee_id": e.id, "employee_name": e.name, "hours": round(emp_minutes[e.id]/60,2)}
        for e in employees
    ]

def summarize_coverage(shifts, week_grid):
    coverage = []
    for d, day in enumerate(week_grid):
        if not day.slots:
            coverage.append({"weekday":d,"weekday_name":WEEKDAYS[d],"segments":[]})
            continue
        counts = [0]*len(day.slots)
        for s in [s for s in shifts if s["weekday"]==d]:
            s_start = hhmm_to_min(s["start"])
            s_end = hhmm_to_min(s["end"])
            i0 = max(0,(s_start-day.open_min)//SLOT_MIN)
            i1 = min(len(day.slots), math.ceil((s_end-day.open_min)/SLOT_MIN))
            for i in range(i0,i1): counts[i]+=1
        segs=[]; i=0; n=len(counts)
        while i<n:
            c=counts[i]; j=i+1
            while j<n and counts[j]==c: j+=1
            segs.append({"start":min_to_hhmm(day.slots[i]),
                         "end":min_to_hhmm(day.slots[j-1]+SLOT_MIN),
                         "count":int(c)})
            i=j
        coverage.append({"weekday":d,"weekday_name":WEEKDAYS[d],"segments":segs})
    return coverage
