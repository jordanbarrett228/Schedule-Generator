# backend/app/newSolver/diagnostics.py
from __future__ import annotations
from typing import List, Dict
from app.newSolver.grid import min_to_hhmm, WEEKDAYS, SLOT_MIN


def _fmt_slot(day_idx: int, minute: int) -> str:
    """Format a day index and minute into a readable string like 'Mon 08:30'."""
    return f"{WEEKDAYS[day_idx]} {min_to_hhmm(minute)}"


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
                    "time": min_to_hhmm(m),
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
                    "time": min_to_hhmm(day.slots[i]),
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
                        "time": min_to_hhmm(day.slots[i]),
                        "message": f"Fixed shift for {e.name} at {_fmt_slot(d, day.slots[i])} conflicts with time-off or unavailability.",
                    })

    # 5) Clopen lock conflicts: last-hour lock day d AND early lock day d+1 before clopen cutoff
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
                    "message": f"{e.name} is locked to close on {WEEKDAYS[d]} and also locked to open early on {WEEKDAYS[d+1]} before {min_to_hhmm(nb)}.",
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
                    "time": min_to_hhmm(day.slots[i]),
                    "message": f"{locked_here} fixed shifts at {WEEKDAYS[d]} {min_to_hhmm(day.slots[i])} exceed hard cap of {hard_cap[d][i]}.",
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
