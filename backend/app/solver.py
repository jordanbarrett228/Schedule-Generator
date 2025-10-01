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
from .models.staffing_window import StaffingWindow

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def _mins_to_hhmm(m: int) -> str:
    h = m // 60
    mm = m % 60
    return f"{h:02d}:{mm:02d}"

def _fmt_slot(day_idx: int, minute: int) -> str:
    return f"{WEEKDAYS[day_idx]} { _mins_to_hhmm(minute) }"


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
    
    # Staffing windows (all rows)
    windows: list[StaffingWindow] = session.exec(select(StaffingWindow)).all()
    win_by_day: Dict[int, list[StaffingWindow]] = {d: [] for d in range(7)}
    for w in windows:
        win_by_day[w.weekday].append(w)

    # Coordinator opening flags & window length from GlobalSettings
    coord_flags = [
        getattr(gs, "coordinator_opening_mon", False) if gs else False,
        getattr(gs, "coordinator_opening_tue", False) if gs else False,
        getattr(gs, "coordinator_opening_wed", False) if gs else False,
        getattr(gs, "coordinator_opening_thu", False) if gs else False,
        getattr(gs, "coordinator_opening_fri", False) if gs else False,
        getattr(gs, "coordinator_opening_sat", False) if gs else False,
        getattr(gs, "coordinator_opening_sun", False) if gs else False,
    ]
    coord_open_mins = getattr(gs, "coordinator_open_window_minutes", 60) if gs else 60

    # Per-slot soft targets and hard caps
    soft_target: list[list[int]] = []
    hard_cap: list[list[int]] = []
    prefer_full_day: list[bool] = [False]*7

    for d, day in enumerate(week_grid):
        n = len(day.slots)
        # defaults
        t = [min_staff_default]*n
        cap = [len(employees)]*n

        # apply staffing windows
        for w in win_by_day.get(d, []):
            w_start = time_to_min(w.start_time)
            w_end = time_to_min(w.end_time)
            if w.prefer_full_length:
                prefer_full_day[d] = True
            for i, m in enumerate(day.slots):
                if w_start <= m < w_end:
                    if w.min_staff is not None:
                        t[i] = max(t[i], int(w.min_staff))  # prefer the higher target
                    if w.max_staff is not None:
                        cap[i] = min(cap[i], int(w.max_staff))

        # coordinator opening lower soft target by 1 for opening window (keep hard ≥1)
        if coord_flags[d] and n > 0:
            win_end = min(day.open_min + coord_open_mins, day.close_min)
            for i, m in enumerate(day.slots):
                if day.open_min <= m < win_end:
                    t[i] = max(1, min_staff_default - 1)

        soft_target.append(t)
        hard_cap.append(cap)

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
    avail_map: dict[tuple[int,int], list[int]] = {}
    lock_map: dict[tuple[int,int], list[int]] = {}

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

            # Date-based time off (single-day, optional time window)
            for to in emp_timeoff[e.id]:
                if to.date != date_d:
                    continue
                if to.all_day or (to.start_time is None and to.end_time is None):
                    slots = [0] * len(day.slots)
                    break
                to_start = time_to_min(to.start_time) if to.start_time else day.open_min
                to_end = time_to_min(to.end_time) if to.end_time else day.close_min
                for i, m in enumerate(day.slots):
                    if to_start <= m < to_end:
                        slots[i] = 0

            # Weekly locked shifts (ignore if day closed or full time-off)
            if any(slots):
                for ls in emp_locked[e.id]:
                    if ls.weekday != d:
                        continue
                    ls_start = time_to_min(ls.start_time)
                    ls_end = time_to_min(ls.end_time)
                    for i, m in enumerate(day.slots):
                        if ls_start <= m < ls_end and slots[i] == 1:
                            locks[i] = 1

            # Opening capability (hard): if not capable_opening, forbid before open_not_before
            if not e.capable_opening:
                cutoff = time_to_min(e.open_not_before) if e.open_not_before else 7*60
                for i, m in enumerate(day.slots):
                    if m < cutoff:
                        slots[i] = 0
                        locks[i] = 0  # prevent illegal locks here

            mask_avail[e.id][d] = slots
            mask_lock[e.id][d] = locks

            avail_map[(e.id, d)] = list(slots)  # copy
            lock_map[(e.id, d)] = list(locks)

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

    # Hard coverage <= cap(d,i) where specified
    for d, day in enumerate(week_grid):
        for i, _ in enumerate(day.slots):
            model.Add(sum(X[(e.id, d, i)] for e in employees) <= hard_cap[d][i])

    # Softly aim toward per-slot soft_target[d][i]
    under_staff = {}
    for d, day in enumerate(week_grid):
        for i, _ in enumerate(day.slots):
            u = model.NewIntVar(0, len(employees), f"u_d{d}_i{i}")
            model.Add(sum(X[(e.id, d, i)] for e in employees) + u >= soft_target[d][i])
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

    # --- Target days off per week (setup) ---
    # We model the #off days as 7 - (#days worked). Then we penalize deviation from target.
    days_under = {}  # eid -> IntVar (shortfall vs target days off)
    days_over = {}   # eid -> IntVar (excess vs target days off)

    for e in employees:
        if e.target_days_off is None:
            continue

        # w_d is 1 if employee works any slot on day d; else 0
        worked_flags = []
        for d, day in enumerate(week_grid):
            if not day.slots:
                worked_flags.append(model.NewConstant(0))
            else:
                w_d = model.NewBoolVar(f"worked_e{e.id}_d{d}")
                model.AddMaxEquality(w_d, [X[(e.id, d, i)] for i in range(len(day.slots))])
                worked_flags.append(w_d)

        off_total = model.NewIntVar(0, 7, f"off_total_e{e.id}")
        model.Add(off_total == 7 - sum(worked_flags))

        u = model.NewIntVar(0, 7, f"days_under_e{e.id}")
        o = model.NewIntVar(0, 7, f"days_over_e{e.id}")
        # off_total + u - o == target
        model.Add(off_total + u - o == int(e.target_days_off))

        days_under[e.id] = u
        days_over[e.id] = o

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
   
    # --- No clopen (last-hour close) ---
    # If an employee worked in the last hour of business on day d, they cannot be
    # scheduled before clopen_next_day_not_before (default 09:00) on day d+1.
    for e in employees:
        if not e.no_clopen:
            continue

        not_before = time_to_min(e.clopen_next_day_not_before) if e.clopen_next_day_not_before else 9 * 60

        for d, day in enumerate(week_grid):
            # Skip the last day (no next day), and days when the business is closed
            if d == 6 or len(day.slots) == 0:
                continue

            # z_closed = 1 iff e worked any slot in the last hour on day d
            z_closed = model.NewBoolVar(f"closed_last_hour_e{e.id}_d{d}")
            last_window = min(len(day.slots), SLOTS_PER_HOUR)  # 60 minutes worth of 15-min slots
            start_i = len(day.slots) - last_window
            last_slots = [X[(e.id, d, j)] for j in range(start_i, len(day.slots))]
            model.AddMaxEquality(z_closed, last_slots)

            # For day d+1, forbid early slots if z_closed == 1
            day2 = week_grid[d + 1]
            for i, m in enumerate(day2.slots):
                if m < not_before:
                    # Can't work early next day if they closed last hour yesterday
                    model.Add(X[(e.id, d + 1, i)] + z_closed <= 1)

    # Objective: strongly minimize coverage shortage; then hours deviation; small penalty on starts
    W_COVER = 1000
    W_HOURS = 10
    W_FRAG = 1
    # Target days-off penalty (soft)
    W_DAYS_OFF = 8  # tweak weight to taste

    terms = []
    terms += [W_COVER * under_staff[k] for k in under_staff]

    for e in under_hours:
        terms.append(W_HOURS * under_hours[e])
    for e in over_hours:
        terms.append(W_HOURS * over_hours[e])
    for eid, u in days_under.items():
        terms.append(W_DAYS_OFF * u)
    for eid, o in days_over.items():
        terms.append(W_DAYS_OFF * o)

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
            terms.append((W_FRAG * (3 if prefer_full_day[d] else 1)) * sum(y))

    model.Minimize(sum(terms))

    # Solve (strict model first)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)
    relaxed_used = False

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # PRE-SOLVE DIAGNOSTICS (why strict failed)
        diagnostics = _collect_pre_solve_diagnostics(
            week_grid=week_grid,
            employees=employees,
            avail_map=avail_map,
            lock_map=lock_map,
            hard_cap=hard_cap,
            min_staff_hard=1,
        )
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

        # Hard coverage <= cap(d,i) in relaxed model too
        for d, day in enumerate(week_grid):
            for i, _ in enumerate(day.slots):
                model_r.Add(sum(Xr[(e.id, d, i)] for e in employees) <= hard_cap[d][i])

        # Soft toward per-slot target
        u = {}
        for d, day in enumerate(week_grid):
            for i, _ in enumerate(day.slots):
                uu = model_r.NewIntVar(0, len(employees), f"u_d{d}_i{i}")
                model_r.Add(sum(Xr[(e.id, d, i)] for e in employees) + uu >= soft_target[d][i])
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
        
        # --- No clopen (last-hour close) — relaxed model ---
        for e in employees:
            if not e.no_clopen:
                continue

            not_before = time_to_min(e.clopen_next_day_not_before) if e.clopen_next_day_not_before else 9 * 60

            for d, day in enumerate(week_grid):
                if d == 6 or len(day.slots) == 0:
                    continue

                z_closed_r = model_r.NewBoolVar(f"r_closed_last_hour_e{e.id}_d{d}")
                last_window = min(len(day.slots), SLOTS_PER_HOUR)  # 60 minutes worth of 15-min slots
                start_i = len(day.slots) - last_window
                last_slots_r = [Xr[(e.id, d, j)] for j in range(start_i, len(day.slots))]
                model_r.AddMaxEquality(z_closed_r, last_slots_r)

                day2 = week_grid[d + 1]
                for i, m in enumerate(day2.slots):
                    if m < not_before:
                        model_r.Add(Xr[(e.id, d + 1, i)] + z_closed_r <= 1)      

        # --- Target days off per week (relaxed) ---
        days_under_r = {}  # eid -> IntVar
        days_over_r = {}   # eid -> IntVar

        for e in employees:
            if e.target_days_off is None:
                continue

            worked_flags_r = []
            for d, day in enumerate(week_grid):
                if not day.slots:
                    worked_flags_r.append(model_r.NewConstant(0))
                else:
                    w_d_r = model_r.NewBoolVar(f"r_worked_e{e.id}_d{d}")
                    model_r.AddMaxEquality(w_d_r, [Xr[(e.id, d, i)] for i in range(len(day.slots))])
                    worked_flags_r.append(w_d_r)

            off_total_r = model_r.NewIntVar(0, 7, f"r_off_total_e{e.id}")
            model_r.Add(off_total_r == 7 - sum(worked_flags_r))

            u_r = model_r.NewIntVar(0, 7, f"r_days_under_e{e.id}")
            o_r = model_r.NewIntVar(0, 7, f"r_days_over_e{e.id}")
            model_r.Add(off_total_r + u_r - o_r == int(e.target_days_off))

            days_under_r[e.id] = u_r
            days_over_r[e.id] = o_r

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

        # Target days-off penalty (relaxed)
        W_DAYS_OFF = 8  # keep consistent with strict model (or tune separately)
        for eid, u in days_under_r.items():
            terms_r.append(W_DAYS_OFF * u)
        for eid, o in days_over_r.items():
            terms_r.append(W_DAYS_OFF * o)
        model_r.Minimize(sum(terms_r))

        solver_r = cp_model.CpSolver()
        solver_r.parameters.max_time_in_seconds = 5.0
        solver_r.parameters.num_search_workers = 8
        status_r = solver_r.Solve(model_r)

        if status_r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            diagnostics = _collect_pre_solve_diagnostics(
                week_grid=week_grid,
                employees=employees,
                avail_map=avail_map,
                lock_map=lock_map,
                hard_cap=hard_cap,
                min_staff_hard=1,
            )
            return {
                "status": "infeasible",
                "week_start": week_start.isoformat(),
                "slot_minutes": SLOT_MIN,
                "shifts": [],
                "notes": "No feasible schedule even with relaxation.",
                "diagnostics": diagnostics if 'diagnostics' in locals() else [],
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
        "diagnostics": diagnostics if 'diagnostics' in locals() else [],
    }

def _collect_pre_solve_diagnostics(
    week_grid,
    employees,
    avail_map: dict[tuple[int,int], list[int]],
    lock_map: dict[tuple[int,int], list[int]],
    hard_cap: list[list[int]],
    min_staff_hard: int = 1,
):
    """
    Returns a list of dicts with human-readable 'message' plus structured fields.
    Looks only at hard-constraint feasibility before solving:
      - zero availability slots
      - weekly min-hours impossible
      - fixed shift conflicts
      - hard cap below hard min
      - opening capability vs lock
      - clopen locks (close then early next-day open)
    """
    diags: list[dict] = []

    # 1) Slots where NO ONE is available (given unavailability, time-off, opening cutoffs, etc.)
    for d, day in enumerate(week_grid):
        for i, m in enumerate(day.slots):
            avail_count = sum(avail_map.get((e.id, d), [])[i] for e in employees)
            if avail_count < min_staff_hard:
                diags.append({
                    "severity": "error",
                    "code": "NO_AVAILABLE_STAFF_SLOT",
                    "day": d,
                    "time": _mins_to_hhmm(m),
                    "message": f"No available employees at {_fmt_slot(d, m)} while hard minimum is {min_staff_hard}.",
                })

    # 2) Hard cap below hard minimum (e.g., max=0 while we require >=1)
    for d, day in enumerate(week_grid):
        for i, _ in enumerate(day.slots):
            if hard_cap[d][i] < min_staff_hard:
                diags.append({
                    "severity": "error",
                    "code": "HARD_CAP_LT_MIN",
                    "day": d,
                    "time": _mins_to_hhmm(day.slots[i]),
                    "message": f"Hard maximum {hard_cap[d][i]} < required minimum {min_staff_hard} at {_fmt_slot(d, day.slots[i])}.",
                })

    # 3) Employee weekly minimum hours impossible (sum of feasible minutes < min_hours_week*60)
    for e in employees:
        feasible_minutes = 0
        for d, day in enumerate(week_grid):
            feasible_minutes += sum(avail_map.get((e.id, d), [])) * 15  # each slot=15 min if available (1)
        need = int(round(e.min_hours_week * 60))
        if feasible_minutes < need:
            diags.append({
                "severity": "error",
                "code": "EMP_WEEK_MIN_EXCEEDS_AVAILABLE",
                "employee_id": e.id,
                "employee_name": e.name,
                "message": (
                    f"{e.name}'s weekly minimum ({e.min_hours_week:.1f}h) exceeds their feasible availability "
                    f"({feasible_minutes/60.0:.1f}h). Reduce min hours or expand availability."
                ),
            })

    # 4) Locked shift conflicts (lock is set where availability was zeroed)
    for e in employees:
        for d, day in enumerate(week_grid):
            a = avail_map.get((e.id, d), [])
            l = lock_map.get((e.id, d), [])
            for i, _ in enumerate(day.slots):
                if i < len(a) and i < len(l) and l[i] == 1 and a[i] == 0:
                    diags.append({
                        "severity": "error",
                        "code": "LOCKED_SHIFT_CONFLICT",
                        "employee_id": e.id,
                        "employee_name": e.name,
                        "day": d,
                        "time": _mins_to_hhmm(day.slots[i]),
                        "message": f"Fixed shift for {e.name} at {_fmt_slot(d, day.slots[i])} conflicts with time-off/unavailability/opening cutoff.",
                    })

    # 5) Opening capability conflicts in locks (incapable_opening & lock before open_not_before)
    for e in employees:
        if getattr(e, "capable_opening", True):
            continue
        cutoff = (e.open_not_before.hour * 60 + e.open_not_before.minute) if getattr(e, "open_not_before", None) else 7*60
        for d, day in enumerate(week_grid):
            for i, m in enumerate(day.slots):
                if m < cutoff and lock_map.get((e.id, d), [0]*len(day.slots))[i] == 1:
                    diags.append({
                        "severity": "error",
                        "code": "LOCK_BEFORE_OPENING_CUTOFF",
                        "employee_id": e.id,
                        "employee_name": e.name,
                        "day": d,
                        "time": _mins_to_hhmm(m),
                        "message": f"{e.name} has a fixed shift before their allowed opening time at {_fmt_slot(d, m)}.",
                    })

    # 6) Clopen lock conflicts: last-hour lock day d AND early lock day d+1 before clopen cutoff
    SLOTS_PER_HOUR = 60 // 15  # your SLOT_MIN is 15; keep consistent
    for e in employees:
        if not getattr(e, "no_clopen", False):
            continue
        nb = (e.clopen_next_day_not_before.hour * 60 + e.clopen_next_day_not_before.minute) if getattr(e, "clopen_next_day_not_before", None) else 9*60
        for d, day in enumerate(week_grid):
            if d == 6 or len(day.slots) == 0:
                continue
            last_window = min(len(day.slots), SLOTS_PER_HOUR)
            start_i = len(day.slots) - last_window
            closed_last_hour = any(lock_map.get((e.id, d), [0]*len(day.slots))[j] == 1 for j in range(start_i, len(day.slots)))
            if not closed_last_hour:
                continue
            day2 = week_grid[d+1]
            early_lock_next = any(
                lock_map.get((e.id, d+1), [0]*len(day2.slots))[i] == 1 and day2.slots[i] < nb
                for i in range(len(day2.slots))
            )
            if early_lock_next:
                diags.append({
                    "severity": "error",
                    "code": "CLOPEN_LOCK_CONFLICT",
                    "employee_id": e.id,
                    "employee_name": e.name,
                    "day": d,
                    "message": f"{e.name} is locked to close on {WEEKDAYS[d]} and also locked to open early on {WEEKDAYS[d+1]} before {_mins_to_hhmm(nb)}.",
                })

    # 7) Locked employees exceed hard cap in some slot
    for d, day in enumerate(week_grid):
        for i, _ in enumerate(day.slots):
            locked_here = sum(lock_map.get((e.id, d), [0]*len(day.slots))[i] for e in employees)
            if locked_here > hard_cap[d][i]:
                diags.append({
                    "severity": "error",
                    "code": "LOCKS_EXCEED_HARD_CAP",
                    "day": d,
                    "time": _mins_to_hhmm(day.slots[i]),
                    "message": f"{locked_here} fixed shifts at {WEEKDAYS[d]} {_mins_to_hhmm(day.slots[i])} exceed hard cap of {hard_cap[d][i]}.",
                })

    # 8) Locked shift length outside employee min/max shift bounds
    for e in employees:
        min_len = int(round(e.min_shift_hours * 60))
        max_len = int(round(e.max_shift_hours * 60))
        for d, day in enumerate(week_grid):
            # derive contiguous lock blocks for that day
            l = lock_map.get((e.id, d), [])
            if not l:
                continue
            j = 0
            while j < len(l):
                if l[j] == 0:
                    j += 1
                    continue
                start = j
                while j + 1 < len(l) and l[j+1] == 1:
                    j += 1
                end = j
                length_min = (end - start + 1) * SLOT_MIN
                if length_min < min_len or length_min > max_len:
                    diags.append({
                        "severity": "error",
                        "code": "LOCK_LENGTH_OUT_OF_BOUNDS",
                        "employee_id": e.id,
                        "employee_name": e.name,
                        "day": d,
                        "message": (f"Locked shift for {e.name} on {WEEKDAYS[d]} is "
                                    f"{length_min/60:.2f}h, outside min/max [{e.min_shift_hours:.2f}, {e.max_shift_hours:.2f}]h."),
                    })
                j += 1

    # 9) Locked segments per day exceed allowed (split-shift policy)
    for e in employees:
        max_segments = 2 if getattr(e, "allow_split_shifts", False) else 1
        for d, day in enumerate(week_grid):
            l = lock_map.get((e.id, d), [])
            if not l:
                continue
            segs = 0
            j = 0
            while j < len(l):
                if l[j] == 1:
                    segs += 1
                    while j + 1 < len(l) and l[j+1] == 1:
                        j += 1
                j += 1
            if segs > max_segments:
                diags.append({
                    "severity": "error",
                    "code": "LOCK_SEGMENTS_EXCEED_PER_DAY_LIMIT",
                    "employee_id": e.id,
                    "employee_name": e.name,
                    "day": d,
                    "message": (f"{e.name} has {segs} locked shift segment(s) on {WEEKDAYS[d]}, "
                                f"exceeding allowed {max_segments} for that day."),
                })

    # 10) Sum of weekly locked minutes exceeds weekly max hours
    for e in employees:
        locked_minutes = 0
        for d, day in enumerate(week_grid):
            l = lock_map.get((e.id, d), [])
            locked_minutes += sum(l) * SLOT_MIN
        max_week_min = int(round(e.max_hours_week * 60))
        if locked_minutes > max_week_min:
            diags.append({
                "severity": "error",
                "code": "LOCKED_TIME_EXCEEDS_WEEKLY_MAX",
                "employee_id": e.id,
                "employee_name": e.name,
                "message": (f"Locked shifts for {e.name} total {locked_minutes/60:.1f}h, "
                            f"which exceeds weekly max {e.max_hours_week:.1f}h."),
            })
            
    return diags
