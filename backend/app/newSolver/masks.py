# backend/app/newSolver/masks.py
from __future__ import annotations
import datetime as dt
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from app.newSolver.grid import time_to_min, SLOT_MIN, DayGrid
from app.models.unavailable import UnavailableBlock
from app.models.timeoff import TimeOff
from app.models.lockedshift import LockedShift
from app.models.employee import Employee


@dataclass
class MaskResult:
    """Availability and lock masks for each employee/day/slot."""
    avail: Dict[int, Dict[int, List[int]]]        # avail[eid][d][i] = 1 if available
    lock: Dict[int, Dict[int, List[int]]]         # lock[eid][d][i] = 1 if locked to work
    avail_map: Dict[Tuple[int, int], List[int]]   # (eid, d) -> slots
    lock_map: Dict[Tuple[int, int], List[int]]    # (eid, d) -> locks


def build_masks(
    employees: List[Employee],
    emp_unavail: Dict[int, List[UnavailableBlock]],
    emp_timeoff: Dict[int, List[TimeOff]],
    emp_locked: Dict[int, List[LockedShift]],
    week_grid: List[DayGrid],
    week_start: dt.date,
) -> MaskResult:
    """
    Build binary availability and lock masks per employee/day/slot.

    Returns
    -------
    MaskResult where:
        avail[eid][d][i] = 1 if employee available at slot i of day d
        lock[eid][d][i]  = 1 if employee must work (locked shift)
    """
    mask_avail: Dict[int, Dict[int, List[int]]] = {}
    mask_lock: Dict[int, Dict[int, List[int]]] = {}
    avail_map: Dict[Tuple[int, int], List[int]] = {}
    lock_map: Dict[Tuple[int, int], List[int]] = {}

    for d, day in enumerate(week_grid):
        date_d = week_start + dt.timedelta(days=d)

        for emp in employees:
            eid = int(emp.id) if emp.id is not None else -1
            n_slots = len(day.slots)
            slots = [1] * n_slots
            locks = [0] * n_slots
            ua_mask = [0] * n_slots
            to_mask = [0] * n_slots

            # --- Weekly Unavailability ---
            for ub in emp_unavail.get(eid, []):
                if ub.weekday != d:
                    continue
                s = time_to_min(ub.start_time)
                e_ = time_to_min(ub.end_time)
                for i, m in enumerate(day.slots):
                    if s <= m < e_:
                        ua_mask[i] = 1

            # --- Time Off (date-specific) ---
            for to in emp_timeoff.get(eid, []):
                if to.date != date_d:
                    continue
                if to.all_day or (to.start_time is None and to.end_time is None):
                    to_mask = [1] * n_slots
                else:
                    s = time_to_min(to.start_time) if to.start_time else day.open_min
                    e_ = time_to_min(to.end_time) if to.end_time else day.close_min
                    for i, m in enumerate(day.slots):
                        if s <= m < e_:
                            to_mask[i] = 1

            # --- Apply unavailability/timeoff ---
            for i in range(n_slots):
                if ua_mask[i] or to_mask[i]:
                    slots[i] = 0

            # --- Locked shifts (hard overrides for scheduling) ---
            for ls in emp_locked.get(eid, []):
                if ls.weekday != d:
                    continue
                s = time_to_min(ls.start_time)
                e_ = time_to_min(ls.end_time)
                for i, m in enumerate(day.slots):
                    if s <= m < e_:
                        locks[i] = 1
                        # lock overrides unavailability but not time-off
                        if to_mask[i] == 0:
                            slots[i] = 1

            # --- Store results ---
            mask_avail.setdefault(eid, {})[d] = slots
            mask_lock.setdefault(eid, {})[d] = locks
            avail_map[(eid, d)] = list(slots)
            lock_map[(eid, d)] = list(locks)

    return MaskResult(mask_avail, mask_lock, avail_map, lock_map)
