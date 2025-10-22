# Opening Capability Feature Removal

## Summary
Removed the `capable_opening` and `open_not_before` fields from the Employee model and all related logic throughout the application. This functionality can be replaced by using weekly unavailable blocks.

## Reason for Removal
The `capable_opening` feature was redundant - the same behavior can be achieved by creating weekly unavailable blocks for each day before the desired start time. This simplifies the codebase and reduces the number of constraints managers need to understand.

## Files Modified

### Backend - Employee Model
**File**: `backend/app/models/employee.py`

**Removed from EmployeeBase**:
```python
# Opening capability
capable_opening: bool = True
open_not_before: Optional[dt.time] = Field(default=dt.time(7, 0), sa_column=Column(SATime, nullable=True))
```

**Removed from EmployeeUpdate**:
```python
capable_opening: Optional[bool] = None
open_not_before: Optional[dt.time] = Field(default=None, sa_column=Column(SATime, nullable=True))
```

---

### Backend - Solver Logic
**File**: `backend/app/newSolver/masks.py`

**Removed** (lines 84-90):
```python
# --- Opening capability (optional early-block logic) ---
if hasattr(emp, "capable_opening") and not emp.capable_opening:
    open_not_before: Optional[dt.time] = getattr(emp, "open_not_before", None)
    cutoff = time_to_min(open_not_before) if open_not_before else 7 * 60  # default 7:00
    for i, m in enumerate(day.slots):
        if m < cutoff:
            slots[i] = 0
```

**Impact**: Opening capability is no longer checked when building availability masks. Use weekly unavailable blocks instead.

---

### Backend - Diagnostics
**File**: `backend/app/newSolver/diagnostics.py`

**Removed** (lines 92-108):
```python
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
                    "time": min_to_hhmm(m),
                    "message": f"{e.name} has a fixed shift before their allowed opening time at {_fmt_slot(d, m)}.",
                })
```

**Updated error message** (line 89):
```python
# BEFORE
"message": f"Fixed shift for {e.name} at {_fmt_slot(d, day.slots[i])} conflicts with time-off/unavailability/opening cutoff.",

# AFTER
"message": f"Fixed shift for {e.name} at {_fmt_slot(d, day.slots[i])} conflicts with time-off or unavailability.",
```

---

### Frontend - Employee Editor
**File**: `frontend/src/components/EmployeeEditor.tsx`

**Removed from Employee type** (lines 20-21):
```typescript
capable_opening: boolean
open_not_before: string | null
```

**Removed UI elements** (lines 224-241):
```tsx
<label className="row" style={{gap:8}}>
  <input
    type="checkbox"
    checked={emp.capable_opening}
    onChange={e=>setEmp({...emp, capable_opening: e.target.checked})}
  />
  Capable of opening
</label>

<div className="row" style={{gap:8}}>
  <div className="label">If NOT opening, earliest start</div>
  <input
    className="input"
    type="time"
    value={emp.open_not_before ?? '07:00'}
    onChange={e=>setEmp({...emp, open_not_before: e.target.value })}
  />
</div>
```

**Visual Impact**: The employee edit modal no longer shows the "Capable of opening" checkbox or "If NOT opening, earliest start" time picker.

---

### Tests
**File**: `backend/tests/test_solver/test_constraints.py`

**Removed from MockEmployee**:
```python
capable_opening: bool = True
open_not_before: dt.time = dt.time(7, 0)
```

**Removed entire test class**:
```python
class TestOpeningCapability:
    def test_incapable_opening_blocks_early_hours(self):
        # ... test implementation
```

---

### Documentation
**File**: `backend/tests/test_solver/README.md`

**Removed sections**:
- Test category: "Opening Capability"
- Constraint documentation: "Opening Capability (Hard Constraint)"
- Test running example: `pytest -v -k "opening"`

**Updated**:
- Constraint priority list (removed "Opening Capability" entry)
- Added note about using weekly unavailable blocks as replacement

**Added clarification**:
```markdown
**Note**: For early-morning restrictions (e.g., "cannot work before 9am"),
use a weekly unavailable block for each day before 9am instead of the
removed `capable_opening` field.
```

---

## Migration Guide for Existing Users

If you have employees with `capable_opening = False` and `open_not_before = 09:00`:

### Old Way (No Longer Works):
```
Employee: Alice
  ☐ Capable of opening
  If NOT opening, earliest start: 09:00
```

### New Way (Recommended):
```
Employee: Alice
  Unavailable Blocks:
    - Monday 00:00 - 09:00
    - Tuesday 00:00 - 09:00
    - Wednesday 00:00 - 09:00
    - Thursday 00:00 - 09:00
    - Friday 00:00 - 09:00
    - Saturday 00:00 - 09:00
    - Sunday 00:00 - 09:00
```

**Why this is better**:
1. More flexible - can set different times for different days
2. Uses existing constraints (no special case logic)
3. Easier to understand (explicitly blocks time)
4. Visible in the UI alongside other unavailability

---

## Database Migration (If Needed)

If you have existing data with `capable_opening` or `open_not_before` values, you can run this SQL to clean up:

```sql
-- Remove columns from employee table (SQLite doesn't support DROP COLUMN directly)
-- You would need to:
-- 1. Create new table without those columns
-- 2. Copy data
-- 3. Drop old table
-- 4. Rename new table

-- OR just leave the columns (they'll be ignored by the code)
-- New installs won't have these columns at all
```

**Recommendation**: Since the fields are ignored by the code, you can leave them in the database if you have existing data. New installations won't create these columns.

---

## Testing

### Verify Removal:
```bash
# Backend compilation
cd backend
python -m py_compile app/models/employee.py app/newSolver/masks.py app/newSolver/diagnostics.py

# Frontend compilation
cd ../frontend
npx tsc --noEmit

# Run tests (should now be 5 tests instead of 6)
cd ../backend
pytest tests/test_solver/ -v
```

### Expected Test Results:
```
tests/test_solver/test_constraints.py::TestTimeOffConstraints::test_all_day_timeoff_blocks_entire_day PASSED
tests/test_solver/test_constraints.py::TestTimeOffConstraints::test_partial_timeoff_blocks_specific_hours PASSED
tests/test_solver/test_constraints.py::TestTimeOffConstraints::test_timeoff_cannot_be_overridden_by_locked_shifts PASSED
tests/test_solver/test_constraints.py::TestAvailabilityConstraints::test_weekly_unavailable_blocks_recurring_time PASSED
tests/test_solver/test_constraints.py::TestAvailabilityConstraints::test_locked_shift_overrides_unavailable_not_timeoff PASSED

========================= 5 passed in X.XXs =========================
```

---

## Summary

### Removed:
- ✅ `capable_opening` field (backend model)
- ✅ `open_not_before` field (backend model)
- ✅ Opening capability logic in masks.py
- ✅ Opening capability diagnostics
- ✅ Opening capability UI (2 form elements)
- ✅ Opening capability tests
- ✅ Opening capability documentation

### Simplified:
- Constraint count reduced by 1
- Fewer fields in employee edit UI
- Clearer constraint model (use unavailability for everything)

### No Breaking Changes:
- Existing schedules continue to work
- Weekly unavailable blocks provide the same functionality
- Database columns can remain (ignored by code)

---

**Feature removal complete! ✅**

Use weekly unavailable blocks to achieve the same behavior with more flexibility.
