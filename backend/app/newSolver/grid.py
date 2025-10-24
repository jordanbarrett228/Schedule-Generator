# backend/app/newSolver/grid.py
from __future__ import annotations
import datetime as dt
from dataclasses import dataclass
from typing import List
from sqlmodel import Session, select
from app.models.settings import BusinessHours

# ---- Slot constants (shared by solver pipeline) ----
SLOT_MIN = 15  # minutes between adjacent decision slots
SLOTS_PER_HOUR = 60 // SLOT_MIN
WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


@dataclass(frozen=True)
class DayGrid:
    """
    All 15-minute slot boundaries for one weekday, derived from BusinessHours.

    Attributes
    ----------
    weekday : int
        0..6 (Sun..Sat)
    open_min : int
        Opening time in absolute minutes from 00:00 (e.g., 04:45 -> 285).
    close_min : int
        Closing time in absolute minutes from 00:00.
    slots : list[int]
        Sorted list of slot start minutes in [open_min, close_min), step=15.
        Empty if business is closed for that weekday.
    """
    weekday: int
    open_min: int
    close_min: int
    slots: List[int]


# ---- Time utilities (kept here so all solver modules can import consistently) ----
def time_to_min(t: dt.time) -> int:
    return t.hour * 60 + t.minute


def min_to_hhmm(m: int) -> str:
    h, mm = divmod(m, 60)
    return f"{h:02d}:{mm:02d}"


def hhmm_to_min(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def next_sunday(today: dt.date | None = None) -> dt.date:
    """
    Return the Sunday that starts the week containing 'today'.

    If today is Sunday, returns today.
    If today is Monday-Saturday, returns the previous Sunday.

    Examples:
        - Sunday 10/26 → Sunday 10/26
        - Monday 10/27 → Sunday 10/26
        - Saturday 11/1 → Sunday 10/26
    """
    today = today or dt.date.today()
    # Python weekday: 0=Mon, 1=Tue, ..., 6=Sun
    # We want to find the Sunday at the start of this week
    weekday = today.weekday()

    if weekday == 6:  # Already Sunday
        return today
    else:
        # Go back to the previous Sunday
        # Monday (0) -> go back 1 day
        # Tuesday (1) -> go back 2 days
        # ...
        # Saturday (5) -> go back 6 days
        days_since_sunday = weekday + 1
        return today - dt.timedelta(days=days_since_sunday)

# Kept for backwards compatibility, but now returns next Sunday
def next_monday(today: dt.date | None = None) -> dt.date:
    """DEPRECATED: Use next_sunday(). Returns next Sunday for compatibility."""
    return next_sunday(today)


# ---- Week grid builder ----
def build_week_grid(session: Session) -> List[DayGrid]:
    """
    Build 7 DayGrid objects (Sun..Sat) based on BusinessHours.

    NOTE: Database stores weekdays as 0=Sun..6=Sat
          Grid returns [Sun, Mon, Tue, Wed, Thu, Fri, Sat] matching database order

    Rules/Notes
    ----------
    - If a day's BusinessHours is missing or close_time <= open_time, that day is treated as closed (no slots).
    - Slots are half-open intervals with 15-minute step, i.e. [open, close) by SLOT_MIN.
      This matches post-processing that adds SLOT_MIN to the last '1' to compute an end time.
    """
    rows = session.exec(select(BusinessHours)).all()
    by_day = {r.weekday: r for r in rows}

    grid: List[DayGrid] = []

    for weekday in range(7):
        row = by_day.get(weekday)

        if not row:
            # No hours configured -> closed
            grid.append(DayGrid(weekday, 0, 0, []))
            continue

        open_m = time_to_min(row.open_time)
        close_m = time_to_min(row.close_time)

        # Guard against bad configs (e.g., close <= open) -> treat as closed
        if close_m <= open_m:
            grid.append(DayGrid(weekday, open_m, close_m, []))
            continue

        slots = list(range(open_m, close_m, SLOT_MIN))
        grid.append(DayGrid(weekday, open_m, close_m, slots))

    return grid
