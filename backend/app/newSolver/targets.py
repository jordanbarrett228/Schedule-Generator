# backend/app/newSolver/targets.py
from __future__ import annotations
from typing import Dict, List, Tuple
from sqlmodel import Session, select

from app.newSolver.grid import time_to_min, DayGrid
from app.models.settings import GlobalSettings
from app.models.staffing_window import StaffingWindow


def compute_targets(
    session: Session,
    user_id: int,
    employees_count: int,
    week_grid: List[DayGrid],
) -> Tuple[List[List[int]], List[List[int]], List[bool], int]:
    """
    Compute per-slot soft targets (desired staff) and hard caps (max staff).

    Returns
    -------
    (soft_target, hard_cap, prefer_full_day, min_staff_default)

    - soft_target[d][i]: desired staffing count (soft lower bound)
    - hard_cap[d][i]:   maximum staffing allowed (hard upper bound)
    - prefer_full_day[d]: whether to penalize fragmented shifts more heavily
    - min_staff_default: base soft lower bound if no StaffingWindow applies
    """

    # ---- Global settings ----
    gs = session.exec(
        select(GlobalSettings).where(GlobalSettings.user_id == user_id)
    ).first()
    min_staff_default: int = gs.min_staff_default if gs else 2

    # ---- Staffing windows ----
    windows = list(
        session.exec(
            select(StaffingWindow).where(StaffingWindow.user_id == user_id)
        ).all()
    )  # ensure list type for Pylance compatibility
    win_by_day: Dict[int, List[StaffingWindow]] = {d: [] for d in range(7)}
    for w in windows:
        win_by_day[w.weekday].append(w)

    # ---- Coordinator flags ----
    coord_flags: List[bool] = [
        getattr(gs, "coordinator_opening_mon", False) if gs else False,
        getattr(gs, "coordinator_opening_tue", False) if gs else False,
        getattr(gs, "coordinator_opening_wed", False) if gs else False,
        getattr(gs, "coordinator_opening_thu", False) if gs else False,
        getattr(gs, "coordinator_opening_fri", False) if gs else False,
        getattr(gs, "coordinator_opening_sat", False) if gs else False,
        getattr(gs, "coordinator_opening_sun", False) if gs else False,
    ]
    coord_open_mins: int = getattr(gs, "coordinator_open_window_minutes", 60) if gs else 60

    # ---- Output initialization ----
    soft_target: List[List[int]] = []
    hard_cap: List[List[int]] = []
    prefer_full_day: List[bool] = [False] * 7

    # ---- Per-day computation ----
    for d, day in enumerate(week_grid):
        n = len(day.slots)
        # Defaults: base staffing across all slots
        t = [min_staff_default] * n
        cap = [employees_count] * n

        # Staffing windows: override slot-specific min/max
        for w in win_by_day.get(d, []):
            w_start = time_to_min(w.start_time)
            w_end = time_to_min(w.end_time)
            if w.prefer_full_length:
                prefer_full_day[d] = True
            for i, m in enumerate(day.slots):
                if w_start <= m < w_end:
                    if w.min_staff is not None:
                        t[i] = max(t[i], int(w.min_staff))
                    if w.max_staff is not None:
                        cap[i] = min(cap[i], int(w.max_staff))

        # Coordinator-opening adjustment (early open window)
        if coord_flags[d] and n > 0:
            win_end = min(day.open_min + coord_open_mins, day.close_min)
            for i, m in enumerate(day.slots):
                if day.open_min <= m < win_end:
                    t[i] = max(1, min_staff_default - 1)

        soft_target.append(t)
        hard_cap.append(cap)

    return soft_target, hard_cap, prefer_full_day, min_staff_default
