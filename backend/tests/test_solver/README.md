# Schedule Generator Solver Test Suite

This directory contains comprehensive tests for the scheduling solver logic.

## Purpose

These tests validate that all scheduling constraints work correctly and help prevent regressions when making changes to the solver code.

## Test Structure

### `test_constraints.py`
Main test file covering all constraint logic:

1. **Time-Off Constraints** (Priority: Bug Fix)
   - `test_all_day_timeoff_blocks_entire_day` - Validates all-day time-off
   - `test_partial_timeoff_blocks_specific_hours` - Validates partial time-off
   - `test_timeoff_cannot_be_overridden_by_locked_shifts` - Ensures time-off is a hard constraint

2. **Availability Constraints**
   - `test_weekly_unavailable_blocks_recurring_time` - Weekly recurring blocks
   - `test_locked_shift_overrides_unavailable_not_timeoff` - Lock override behavior

## Running the Tests

### Install Dependencies
```bash
cd backend
pip install pytest
```

### Run All Tests
```bash
# From backend directory
pytest tests/test_solver/ -v
```

### Run Specific Test Category
```bash
# Only time-off tests
pytest tests/test_solver/ -v -k "timeoff"

# Only availability tests
pytest tests/test_solver/ -v -k "availability"
```

### Run Single Test
```bash
pytest tests/test_solver/test_constraints.py::TestTimeOffConstraints::test_all_day_timeoff_blocks_entire_day -v
```

## Understanding Test Results

### Success ✅
```
tests/test_solver/test_constraints.py::TestTimeOffConstraints::test_all_day_timeoff_blocks_entire_day PASSED
```
The constraint is working as expected.

### Failure ❌
```
tests/test_solver/test_constraints.py::TestTimeOffConstraints::test_all_day_timeoff_blocks_entire_day FAILED

AssertionError: Expected all slots unavailable on Monday, but got: [1, 1, 0, 0, ...]
```
The constraint is NOT working correctly. The assertion message explains what went wrong.

## What Each Constraint Does

### Time-Off (Hard Constraint)
**Purpose**: Ensures employees are never scheduled during requested time-off.

**Behavior**:
- All-day time-off blocks the entire day (all slots = 0)
- Partial time-off blocks only specified hours
- Time-off CANNOT be overridden by locked shifts (unlike unavailable blocks)
- This is the HIGHEST priority constraint

**Example**: If Alice requests time-off on Monday, she will NOT appear in Monday's schedule, even if the manager creates a locked shift for her.

---

### Weekly Unavailable Blocks (Hard Constraint, but Overridable by Locks)
**Purpose**: Handles recurring weekly unavailability (e.g., "I have class every Wednesday 2-4pm").

**Behavior**:
- Blocks the same time window every week
- Can be OVERRIDDEN by manager-created locked shifts
- Less strict than time-off

**Example**: If Bob is unavailable Wednesdays 14:00-16:00, the solver won't schedule him then UNLESS the manager explicitly creates a locked shift (for emergencies).

**Note**: For early-morning restrictions (e.g., "cannot work before 9am"), use a weekly unavailable block for each day before 9am instead of the removed `capable_opening` field.

---

### Clopen Protection (Hard Constraint)
**Purpose**: Prevents employees from closing late and opening early next day (inhumane scheduling).

**Behavior**:
- If employee works in the last hour of the day (closing)
- AND they have `no_clopen = True`
- THEN they cannot work before `clopen_next_day_not_before` next day (default 09:00)

**Example**: If David closes at 21:00 on Monday, he cannot be scheduled before 09:00 on Tuesday.

---

### Min/Max Weekly Hours (Hard Constraint)
**Purpose**: Ensures employees get their minimum hours and don't exceed maximum.

**Behavior**:
- `min_hours_week`: Minimum hours per week (e.g., 20)
- `max_hours_week`: Maximum hours per week (e.g., 40)
- Solver will reject schedules that violate these

**Example**: If Emma needs 25 hours minimum, the solver guarantees she gets at least 25 hours.

---

### Min/Max Shift Length (Hard Constraint)
**Purpose**: Prevents unreasonably short or long shifts.

**Behavior**:
- `min_shift_hours`: Minimum shift length (e.g., 4 hours)
- `max_shift_hours`: Maximum shift length (e.g., 8 hours)
- Each contiguous shift must be within these bounds

**Example**: If min=4h, Frank cannot be scheduled for a 2-hour shift.

---

### Locked Shifts (Hard Constraint)
**Purpose**: Manager can force-assign specific shifts.

**Behavior**:
- Employee MUST work during locked shift times
- Overrides weekly unavailable blocks
- DOES NOT override time-off
- Still respects shift length and weekly hour limits

**Example**: Manager locks Grace to work Saturday 10:00-14:00. Grace will definitely be in the schedule for that time.

---

### Coverage Constraints (Hard Minimum, Soft Target)
**Purpose**: Ensure enough staff at all times.

**Behavior**:
- Hard minimum: At least 1 person scheduled per slot (configurable)
- Soft target: Prefer 2+ people per slot (from global settings)
- Solver penalizes under-staffing heavily (weight: 1000)

**Example**: Business needs at least 1 person always, prefers 2. Solver tries to achieve 2 but will accept 1 if necessary.

---

### Staffing Windows (Soft Min, Hard Max)
**Purpose**: Time-specific staffing rules (e.g., "need 4 people during lunch rush").

**Behavior**:
- Soft min: Prefer at least N people during window (soft penalty if under)
- Hard max: Never exceed M people during window (hard constraint)

**Example**: Lunch rush 12:00-14:00 needs min 4, max 5 people. Solver tries for 4+ but never exceeds 5.

---

### Preferred Hours (Soft Constraint)
**Purpose**: Try to give employees their desired weekly hours.

**Behavior**:
- Employee sets `preferred_hours` (e.g., 32)
- Solver penalizes deviation from this target (weight: 10)
- NOT a hard requirement (can be violated if necessary)

**Example**: If Helen wants 30 hours, solver will try to give her close to 30, but might give 28 or 32 if constraints conflict.

---

### Target Days Off (Soft Constraint)
**Purpose**: Balance work/life by giving employees desired days off per week.

**Behavior**:
- Employee sets `target_days_off` (e.g., 2)
- Solver penalizes deviation (weight: 8)

**Example**: If Ian wants 2 days off, solver tries to give him 5 working days (7 - 2 = 5).

---

## Constraint Priority (Highest to Lowest)

1. **Time-Off** (Hard) - Never violated
2. **Weekly Unavailability** (Hard, but overridable by locks) - Blocks recurring time slots
3. **Clopen Protection** (Hard) - Never violated
4. **Weekly Hours** (Hard) - Never violated
5. **Shift Length** (Hard) - Never violated
6. **Locked Shifts** (Hard) - Never violated
7. **Hard Coverage Minimum** (Hard) - At least 1 person per slot
8. **Hard Staffing Cap** (Hard) - Never exceed max per slot
9. **Coverage Target** (Soft, Weight: 1000) - Heavily penalized if under target
10. **Preferred Hours** (Soft, Weight: 10) - Lightly penalized
11. **Target Days Off** (Soft, Weight: 8) - Lightly penalized
12. **Fragmentation** (Soft, Weight: 1) - Minimize shift starts

## Adding New Tests

When adding new constraint logic to the solver:

1. Add a new test method to the appropriate test class
2. Use descriptive test names: `test_<what>_<expected_behavior>`
3. Include docstring explaining:
   - What is being tested
   - Expected behavior
   - What success looks like
4. Use assert messages that explain what went wrong

Example:
```python
def test_new_constraint_behaves_correctly(self):
    """
    TEST: <Brief description>

    Expected behavior:
    - <Condition 1>
    - <Expected result 1>
    - <Condition 2>
    - <Expected result 2>
    """
    # Setup
    employee = MockEmployee(id=1, name="Test")

    # Execute
    result = some_function(employee)

    # Validate
    assert result == expected, \
        f"Expected {expected} but got {result}"
```

## Troubleshooting

### Import Errors
If you get `ModuleNotFoundError`, make sure you're running from the `backend` directory:
```bash
cd backend
pytest tests/test_solver/ -v
```

### Assertion Failures
Read the assertion message carefully. It will tell you:
- What was expected
- What was actually received
- Which slot/day/employee failed

### Debugging a Failing Test
1. Run just that test with `-v` flag for verbose output
2. Add print statements to see intermediate values:
   ```python
   print(f"Availability mask: {masks.avail[1][0]}")
   ```
3. Check if the test assumption is correct (maybe the constraint changed?)

## Questions?

If you're unsure what a test is validating, read the docstring at the top of the test method. It explains the purpose and expected behavior in plain English.
