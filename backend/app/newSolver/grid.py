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
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass(frozen=True)
class DayGrid:
    """
    All 15-minute slot boundaries for one weekday, derived from BusinessHours.

    Attributes
    ----------
    weekday : int
        0..6 (Mon..Sun)
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


def next_monday(today: dt.date | None = None) -> dt.date:
    """Return the date of the next Monday (or today if already Monday)."""
    today = today or dt.date.today()
    return today + dt.timedelta(days=(7 - today.weekday()) % 7)


# ---- Week grid builder ----
def build_week_grid(session: Session) -> List[DayGrid]:
    """
    Build 7 DayGrid objects (Mon..Sun) based on BusinessHours.

    Rules/Notes
    ----------
    - If a day's BusinessHours is missing or close_time <= open_time, that day is treated as closed (no slots).
    - Slots are half-open intervals with 15-minute step, i.e. [open, close) by SLOT_MIN.
      This matches post-processing that adds SLOT_MIN to the last '1' to compute an end time.
    """
    rows = session.exec(select(BusinessHours)).all()

    by_day = {r.weekday: r for r in rows}
    grid: List[DayGrid] = []

    for d in range(7):
        row = by_day.get(d)
        if not row:
            # No hours configured -> closed
            grid.append(DayGrid(d, 0, 0, []))
            continue

        open_m = time_to_min(row.open_time)
        close_m = time_to_min(row.close_time)

        # Guard against bad configs (e.g., close <= open) -> treat as closed
        if close_m <= open_m:
            grid.append(DayGrid(d, open_m, close_m, []))
            continue

        slots = list(range(open_m, close_m, SLOT_MIN))
        grid.append(DayGrid(d, open_m, close_m, slots))

    return grid
