from __future__ import annotations

import math
import datetime as dt
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from ortools.sat.python import cp_model
from sqlmodel import Session, select

from .models.employee import Employee
from .models.unavailable import UnavailableBlock
from .models.timeoff import TimeOff
from .models.lockedshift import LockedShift
from .models.settings import BusinessHours, GlobalSettings

SLOT_MIN = 15  # minutes
SLOTS_PER_HOUR = 60 // SLOT_MIN

weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

@dataclass
class DayGrid:
    weekday: int
    open_min: int
    close_min: int
    slots: List[int]  # absolute minutes from 00:00 within day for each slot start

def time_to_min(t: dt.time) -> int:
    return t.hour * 60 + t.minute

def min_to_hhmm(m: int) -> str:
    h = m // 60
    mm = m % 60
    return f"{h:02d}:{mm:02d}"

def hhmm_to_min(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)

def next_monday(today: Optional[dt.date] = None) -> dt.date:
    if not today:
        today = dt.date.today()
    return today + dt.timedelta(days=(7 - today.weekday()) % 7)

def build_week_grid(session: Session) -> List[DayGrid]:
    """Build per-day open-close grids in 15-min steps."""
    bh_rows = session.exec(select(BusinessHours)).all()
    by_day = {r.weekday: r for r in bh_rows}
    grid: List[DayGrid] = []
    for d in range(7):
        row = by_day.get(d)
        if not row:
            # closed: no slots
            grid.append(DayGrid(d, 0, 0, []))
            continue
        open_m = time_to_min(row.open_time)
        close_m = time_to_min(row.close_time)
        slots = list(range(open_m, close_m, SLOT_MIN))
        grid.append(DayGrid(d, open_m, close_m, slots))
    return grid

def generate_week_schedule(session: Session, week_start: Optional[dt.date] = None) -> dict:
    # Inputs
    week_start = week_start or next_monday()
    gs = session.exec(select(GlobalSettings)).first()
    min_staff_default = gs.min_staff_default if gs else 2

    employees: List[Employee] = session.exec(
        select(Employee).where(Employee.active == True)  # noqa: E712
    ).all()

    # Quick out if no employees or closed all week
    week_grid = build_week_grid(session)
    if not employees or all(len(day.slots) == 0 for day in week_grid):
        return {
            "status": "empty",
            "week_start": week_start.isoformat(),
            "slot_minutes": SLOT_MIN,
            "shifts": [],
            "notes": "No active employees or business closed."
        }

    # Pull constraints
    emp_unavail: Dict[int, List[UnavailableBlock]] = {}
    for e in employees:
        emp_unavail[e.id] = session.exec(
            select(UnavailableBlock).where(UnavailableBlock.employee_id == e.id)
        ).all()

    emp_timeoff: Dict[int, List[TimeOff]] = {}
    for e in employees:
        emp_timeoff[e.id] = session.exec(
            select(TimeOff).where(TimeOff.employee_id == e.id)
        ).all()

    emp_locked: Dict[int, List[LockedShift]] = {}
    for e in employees:
        emp_locked[e.id] = session.exec(
            select(LockedShift).where(LockedShift.employee_id == e.id)
        ).all()

    # Build per-employee/day availability masks & locked masks
    # mask_avail[e][d][slot_index] = 1/0
    mask_avail: Dict[int, Dict[int, List[int]]] = {e.id: {} for e in employees}
    mask_lock: Dict[int, Dict[int, List[int]]] = {e.id: {} for e in employees}

    for d, day in enumerate(week_grid):
        date_d = week_start + dt.timedelta(days=d)
        for e in employees:
            slots = [1] * len(day.slots)
            locks = [0] * len(day.slots)

            # Weekly unavailability
            for ub in emp_unavail[e.id]:
                if ub.weekday != d:
                    continue
                ub_start = time_to_min(ub.start_time)
                ub_end = time_to_min(ub.end_time)
                for i, m in enumerate(day.slots):
                    if ub_start <= m < ub_end:
                        slots[i] = 0

            # Date-based time off
            for to in emp_timeoff[e.id]:
                if to.start_date <= date_d <= to.end_date:
                    # Entire day off
                    slots = [0] * len(day.slots)
                    break

            # Weekly locked shifts (ignore if day closed or full time-off)
            if any(slots):
                for ls in emp_locked[e.id]:
                    if ls.weekday != d:
                        continue
                    ls_start = time_to_min(ls.start_time)
                    ls_end = time_to_min(ls.end_time)
                    for i, m in enumerate(day.slots):
                        if ls_start <= m < ls_end:
                            # Lock only where business is open; if user locks outside, it will be trimmed
                            locks[i] = 1
                            slots[i] = 1  # ensure availability at locked times

            mask_avail[e.id][d] = slots
            mask_lock[e.id][d] = locks

    # Build model
    model = cp_model.CpModel()

    # Variables x[e][d][i]
    X: Dict[Tuple[int,int,int], cp_model.IntVar] = {}
    for e in employees:
        for d, day in enumerate(week_grid):
            for i, _ in enumerate(day.slots):
                if mask_avail[e.id][d][i] == 0:
                    # create a fixed-zero var for simpler indexing
                    X[(e.id, d, i)] = model.NewConstant(0)
                else:
                    v = model.NewBoolVar(f"x_e{e.id}_d{d}_i{i}")
                    # lock to 1 if required
                    if mask_lock[e.id][d][i] == 1:
                        model.Add(v == 1)
                    X[(e.id, d, i)] = v

    # Hard coverage >= 1 when open
    for d, day in enumerate(week_grid):
        for i, _ in enumerate(day.slots):
            model.Add(sum(X[(e.id, d, i)] for e in employees) >= 1)

    # Softly aim toward min_staff_default with shortage vars
    under_staff = {}
    for d, day in enumerate(week_grid):
        for i, _ in enumerate(day.slots):
            u = model.NewIntVar(0, len(employees), f"u_d{d}_i{i}")
            model.Add(sum(X[(e.id, d, i)] for e in employees) + u >= min_staff_default)
            under_staff[(d, i)] = u

    # Per-employee weekly min/max hours (convert to slots)
    def hours_to_slots(h: float) -> int:
        return int(round(h * SLOTS_PER_HOUR))

    emp_week_sum: Dict[int, cp_model.LinearExpr] = {}
    for e in employees:
        s = []
        for d, day in enumerate(week_grid):
            for i, _ in enumerate(day.slots):
                s.append(X[(e.id, d, i)])
        total_slots = sum(s) if s else model.NewConstant(0)
        emp_week_sum[e.id] = total_slots
        model.Add(total_slots >= hours_to_slots(e.min_hours_week))
        model.Add(total_slots <= hours_to_slots(e.max_hours_week))

    # Target hours soft objective (L1 via over/under)
    under_hours = {}
    over_hours = {}
    for e in employees:
        if e.preferred_hours is None:
            continue
        t_slots = hours_to_slots(e.preferred_hours)
        u = model.NewIntVar(0, 7*24*SLOTS_PER_HOUR, f"under_e{e.id}")
        o = model.NewIntVar(0, 7*24*SLOTS_PER_HOUR, f"over_e{e.id}")
        model.Add(emp_week_sum[e.id] + u - o == t_slots)
        under_hours[e.id] = u
        over_hours[e.id] = o

    # Daily segment constraints: ≤1 shift/day (or ≤2 if split allowed), min/max lengths
    for e in employees:
        min_len = hours_to_slots(e.min_shift_hours)
        max_len = hours_to_slots(e.max_shift_hours)

        seg_cap = 2 if e.allow_split_shifts else 1

        for d, day in enumerate(week_grid):
            n = len(day.slots)
            if n == 0:
                continue

            # y_start[i] indicates a 0->1 transition at i
            y_start = [model.NewBoolVar(f"start_e{e.id}_d{d}_i{i}") for i in range(n)]
            # link: y_start[i] >= x[i] - x[i-1]; with x[-1]=0
            for i in range(n):
                prev = X[(e.id, d, i-1)] if i > 0 else model.NewConstant(0)
                model.Add(y_start[i] >= X[(e.id, d, i)] - prev)
                model.Add(y_start[i] <= X[(e.id, d, i)])  # cannot start if x=0

            # limit number of segments
            model.Add(sum(y_start) <= seg_cap)

            # forbid starting so late that min_len cannot be satisfied
            for i in range(n):
                if i + min_len > n:
                    model.Add(y_start[i] == 0)

            # enforce minimum length when a segment starts
            for i in range(n - min_len + 1):
                model.Add(sum(X[(e.id, d, j)] for j in range(i, i + min_len)) >= min_len * y_start[i])

            # enforce maximum length by sliding window: no run longer than max_len
            if max_len < n:
                for i in range(n - (max_len)):
                    model.Add(sum(X[(e.id, d, j)] for j in range(i, i + max_len + 1)) <= max_len)

    # Objective: strongly minimize coverage shortage; then hours deviation; small penalty on starts
    W_COVER = 1000
    W_HOURS = 10
    W_FRAG = 1

    terms = []
    terms += [W_COVER * under_staff[k] for k in under_staff]

    for e in under_hours:
        terms.append(W_HOURS * under_hours[e])
    for e in over_hours:
        terms.append(W_HOURS * over_hours[e])

    # Small penalty for number of segments (fewer fragments)
    for e in employees:
        for d, day in enumerate(week_grid):
            n = len(day.slots)
            if n == 0:
                continue
            # approximate starts: x0 + sum max(0, x[i]-x[i-1]) via y_start linkage above (recreate briefly)
            # reuse same logic cheaply: additional vars are fine at this scale
            y = [model.NewBoolVar(f"frag_e{e.id}_d{d}_i{i}") for i in range(n)]
            for i in range(n):
                prev = X[(e.id, d, i-1)] if i > 0 else model.NewConstant(0)
                model.Add(y[i] >= X[(e.id, d, i)] - prev)
                model.Add(y[i] <= X[(e.id, d, i)])
            terms.append(W_FRAG * sum(y))

    model.Minimize(sum(terms))

    # Solve (strict model first)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)
    relaxed_used = False

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # Relax weekly min hours and hard coverage=1 to "as much as possible"
        relaxed_used = True
        model_r = cp_model.CpModel()
        # Rebuild variables by reference (reuse same X via map builder)
        # For simplicity, rebuild the model with relaxed constraints:
        Xr = {(e.id, d, i): model_r.NewBoolVar(f"x_e{e.id}_d{d}_i{i}") if mask_avail[e.id][d][i] == 1 else model_r.NewConstant(0)
              for e in employees for d, day in enumerate(week_grid) for i, _ in enumerate(day.slots)}
        # lock
        for e in employees:
            for d, day in enumerate(week_grid):
                for i, _ in enumerate(day.slots):
                    if mask_lock[e.id][d][i] == 1:
                        model_r.Add(Xr[(e.id, d, i)] == 1)

        # Soft coverage to 1
        miss1 = {}
        for d, day in enumerate(week_grid):
            for i, _ in enumerate(day.slots):
                m1 = model_r.NewIntVar(0, len(employees), f"m1_d{d}_i{i}")
                model_r.Add(sum(Xr[(e.id, d, i)] for e in employees) + m1 >= 1)
                miss1[(d, i)] = m1

        # Soft toward min_staff_default
        u = {}
        for d, day in enumerate(week_grid):
            for i, _ in enumerate(day.slots):
                uu = model_r.NewIntVar(0, len(employees), f"u_d{d}_i{i}")
                model_r.Add(sum(Xr[(e.id, d, i)] for e in employees) + uu >= min_staff_default)
                u[(d, i)] = uu

        # Weekly hours: allow shortfall with penalty; enforce max hard
        shortfall = {}
        week_sum = {}
        for e in employees:
            tot = sum(Xr[(e.id, d, i)] for d, day in enumerate(week_grid) for i, _ in enumerate(day.slots)) \
                  if any(len(day.slots) for day in week_grid) else model_r.NewConstant(0)
            week_sum[e.id] = tot
            model_r.Add(tot <= hours_to_slots(e.max_hours_week))
            sf = model_r.NewIntVar(0, 7*24*SLOTS_PER_HOUR, f"sf_e{e.id}")
            model_r.Add(tot + sf >= hours_to_slots(e.min_hours_week))
            shortfall[e.id] = sf

        # Daily segments/min/max same as before (copy logic)
        for e in employees:
            min_len = hours_to_slots(e.min_shift_hours)
            max_len = hours_to_slots(e.max_shift_hours)
            seg_cap = 2 if e.allow_split_shifts else 1
            for d, day in enumerate(week_grid):
                n = len(day.slots)
                if n == 0: continue
                y_start = [model_r.NewBoolVar(f"start_e{e.id}_d{d}_i{i}") for i in range(n)]
                for i in range(n):
                    prev = Xr[(e.id, d, i-1)] if i > 0 else model_r.NewConstant(0)
                    model_r.Add(y_start[i] >= Xr[(e.id, d, i)] - prev)
                    model_r.Add(y_start[i] <= Xr[(e.id, d, i)])
                model_r.Add(sum(y_start) <= seg_cap)
                for i in range(n):
                    if i + min_len > n:
                        model_r.Add(y_start[i] == 0)
                for i in range(n - min_len + 1):
                    model_r.Add(sum(Xr[(e.id, d, j)] for j in range(i, i + min_len)) >= min_len * y_start[i])
                if max_len < n:
                    for i in range(n - (max_len)):
                        model_r.Add(sum(Xr[(e.id, d, j)] for j in range(i, i + max_len + 1)) <= max_len)

        # Preferred hours soft
        uh, oh = {}, {}
        for e in employees:
            if e.preferred_hours is None:
                continue
            t_slots = hours_to_slots(e.preferred_hours)
            u_e = model_r.NewIntVar(0, 7*24*SLOTS_PER_HOUR, f"under_e{e.id}")
            o_e = model_r.NewIntVar(0, 7*24*SLOTS_PER_HOUR, f"over_e{e.id}")
            model_r.Add(week_sum[e.id] + u_e - o_e == t_slots)
            uh[e.id] = u_e
            oh[e.id] = o_e

        # Objective
        terms_r = []
        terms_r += [2000 * miss1[k] for k in miss1]        # very strong push to cover >=1
        terms_r += [1000 * u[k] for k in u]               # push toward min_staff_default
        terms_r += [50 * shortfall[eid] for eid in shortfall]  # penalize min-hours shortfall
        for eid in uh: terms_r.append(10 * uh[eid])
        for eid in oh: terms_r.append(10 * oh[eid])
        model_r.Minimize(sum(terms_r))

        solver_r = cp_model.CpSolver()
        solver_r.parameters.max_time_in_seconds = 5.0
        solver_r.parameters.num_search_workers = 8
        status_r = solver_r.Solve(model_r)

        if status_r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return {
                "status": "infeasible",
                "week_start": week_start.isoformat(),
                "slot_minutes": SLOT_MIN,
                "shifts": [],
                "notes": "No feasible schedule even with relaxation."
            }

        X_get = lambda eid, d, i: int(solver_r.Value(Xr[(eid, d, i)]))
        status_txt = "relaxed"
    else:
        X_get = lambda eid, d, i: int(solver.Value(X[(eid, d, i)]))
        status_txt = "optimal" if status == cp_model.OPTIMAL else "feasible"

    # Build contiguous shifts for output
    shifts_out = []
    for e in employees:
        for d, day in enumerate(week_grid):
            if not day.slots:
                continue
            n = len(day.slots)
            i = 0
            while i < n:
                if X_get(e.id, d, i) == 1:
                    # start of a run
                    start_i = i
                    i += 1
                    while i < n and X_get(e.id, d, i) == 1:
                        i += 1
                    end_i = i  # exclusive
                    start_min = day.slots[start_i]
                    end_min = day.slots[end_i - 1] + SLOT_MIN
                    shifts_out.append({
                        "employee_id": e.id,
                        "employee_name": e.name,
                        "weekday": d,
                        "weekday_name": weekdays[d],
                        "start": min_to_hhmm(start_min),
                        "end": min_to_hhmm(end_min),
                    })
                else:
                    i += 1
    # ---- Aggregate: per-employee hours/week ----
    emp_minutes: Dict[int, int] = {e.id: 0 for e in employees}
    for s in shifts_out:
        start_m = hhmm_to_min(s["start"])
        end_m = hhmm_to_min(s["end"])
        emp_minutes[s["employee_id"]] += max(0, end_m - start_m)
    emp_hours_list = [
        {"employee_id": e.id, "employee_name": e.name, "hours": round(emp_minutes[e.id] / 60.0, 2)}
        for e in employees
    ]

    # ---- Aggregate: per-day coverage segments ----
    coverage_out = []
    for d, day in enumerate(week_grid):
        if not day.slots:
            coverage_out.append({
                "weekday": d,
                "weekday_name": weekdays[d],
                "open": None,
                "close": None,
                "segments": []
            })
            continue
        counts = [0] * len(day.slots)
        # rebuild counts from shifts_out
        for s in [s for s in shifts_out if s["weekday"] == d]:
            s_start = max(day.open_min, hhmm_to_min(s["start"]))
            s_end = min(day.close_min, hhmm_to_min(s["end"]))
            if s_end <= s_start:
                continue
            i0 = max(0, (s_start - day.open_min) // SLOT_MIN)
            i1 = min(len(day.slots), math.ceil((s_end - day.open_min) / SLOT_MIN))
            for i in range(i0, i1):
                counts[i] += 1
        # compress to segments
        segs = []
        i = 0
        n = len(counts)
        while i < n:
            c = counts[i]
            j = i + 1
            while j < n and counts[j] == c:
                j += 1
            start_min = day.slots[i]
            end_min = day.slots[j - 1] + SLOT_MIN
            segs.append({"start": min_to_hhmm(start_min), "end": min_to_hhmm(end_min), "count": int(c)})
            i = j
        coverage_out.append({
            "weekday": d,
            "weekday_name": weekdays[d],
            "open": min_to_hhmm(day.open_min),
            "close": min_to_hhmm(day.close_min),
            "segments": segs
        })

    return {
        "status": status_txt if not relaxed_used else "relaxed",
        "week_start": week_start.isoformat(),
        "slot_minutes": SLOT_MIN,
        "min_staff_default": min_staff_default,
        "shifts": shifts_out,
        "employee_hours": emp_hours_list,
        "coverage": coverage_out,
    }
