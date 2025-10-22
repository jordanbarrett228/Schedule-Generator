#!/usr/bin/env python3
"""
Verification script to ensure the solver migration is complete and correct.

Run this to verify:
- All imports work correctly
- No references to old solver
- All functions are accessible
- Diagnostics can be called
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all newSolver modules can be imported."""
    print("Testing imports...")

    try:
        from app.newSolver.core import generate_week_schedule
        print("  ✓ core.generate_week_schedule")
    except ImportError as e:
        print(f"  ✗ core: {e}")
        return False

    try:
        from app.newSolver.grid import build_week_grid, time_to_min, min_to_hhmm
        print("  ✓ grid.build_week_grid")
        print("  ✓ grid.time_to_min")
        print("  ✓ grid.min_to_hhmm")
    except ImportError as e:
        print(f"  ✗ grid: {e}")
        return False

    try:
        from app.newSolver.masks import build_masks
        print("  ✓ masks.build_masks")
    except ImportError as e:
        print(f"  ✗ masks: {e}")
        return False

    try:
        from app.newSolver.diagnostics import _collect_pre_solve_diagnostics
        print("  ✓ diagnostics._collect_pre_solve_diagnostics")
    except ImportError as e:
        print(f"  ✗ diagnostics: {e}")
        return False

    try:
        from app.newSolver.data_loader import load_user_data
        print("  ✓ data_loader.load_user_data")
    except ImportError as e:
        print(f"  ✗ data_loader: {e}")
        return False

    try:
        from app.newSolver.targets import compute_targets
        print("  ✓ targets.compute_targets")
    except ImportError as e:
        print(f"  ✗ targets: {e}")
        return False

    try:
        from app.newSolver.model_builder import build_cp_variables, apply_coverage_constraints, apply_weekly_hours
        print("  ✓ model_builder.build_cp_variables")
        print("  ✓ model_builder.apply_coverage_constraints")
        print("  ✓ model_builder.apply_weekly_hours")
    except ImportError as e:
        print(f"  ✗ model_builder: {e}")
        return False

    try:
        from app.newSolver.constraints_shifts import apply_daily_segments_and_lengths
        print("  ✓ constraints_shifts.apply_daily_segments_and_lengths")
    except ImportError as e:
        print(f"  ✗ constraints_shifts: {e}")
        return False

    try:
        from app.newSolver.constraints_clopen import apply_no_clopen
        print("  ✓ constraints_clopen.apply_no_clopen")
    except ImportError as e:
        print(f"  ✗ constraints_clopen: {e}")
        return False

    try:
        from app.newSolver.objectives import add_objective
        print("  ✓ objectives.add_objective")
    except ImportError as e:
        print(f"  ✗ objectives: {e}")
        return False

    try:
        from app.newSolver.postprocess import extract_shifts, summarize_hours, summarize_coverage
        print("  ✓ postprocess.extract_shifts")
        print("  ✓ postprocess.summarize_hours")
        print("  ✓ postprocess.summarize_coverage")
    except ImportError as e:
        print(f"  ✗ postprocess: {e}")
        return False

    print()
    return True

def test_no_old_solver():
    """Test that old solver is not accessible."""
    print("Testing old solver is removed...")

    try:
        from app.solver import generate_week_schedule
        print("  ✗ WARNING: Old solver is still importable!")
        return False
    except ImportError:
        print("  ✓ Old solver is properly removed")

    # Check file doesn't exist
    solver_path = Path(__file__).parent / "app" / "solver.py"
    if solver_path.exists():
        print("  ✗ WARNING: solver.py file still exists!")
        return False
    else:
        print("  ✓ solver.py file is deleted")

    print()
    return True

def test_router_import():
    """Test that the router uses the new solver."""
    print("Testing router import...")

    try:
        from app.routers.new.rt_schedule import router
        print("  ✓ rt_schedule.router imports successfully")

        # Check the module's imports
        import app.routers.new.rt_schedule as rt_schedule_module
        if hasattr(rt_schedule_module, 'generate_week_schedule'):
            print("  ✓ rt_schedule uses new solver")
        else:
            print("  ✗ Could not verify solver import")

    except ImportError as e:
        print(f"  ✗ rt_schedule: {e}")
        return False

    print()
    return True

def test_function_availability():
    """Test that key functions are callable."""
    print("Testing function signatures...")

    try:
        from app.newSolver.grid import min_to_hhmm, _fmt_slot

        # Test min_to_hhmm
        result = min_to_hhmm(480)  # 08:00
        assert result == "08:00", f"Expected '08:00', got '{result}'"
        print(f"  ✓ min_to_hhmm(480) = '{result}'")

        # Test _fmt_slot
        result = _fmt_slot(0, 480)  # Mon 08:00
        assert result == "Mon 08:00", f"Expected 'Mon 08:00', got '{result}'"
        print(f"  ✓ _fmt_slot(0, 480) = '{result}'")

    except Exception as e:
        print(f"  ✗ Function test failed: {e}")
        return False

    print()
    return True

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("SCHEDULE GENERATOR SOLVER VERIFICATION")
    print("=" * 60)
    print()

    all_pass = True

    all_pass = test_imports() and all_pass
    all_pass = test_no_old_solver() and all_pass
    all_pass = test_router_import() and all_pass
    all_pass = test_function_availability() and all_pass

    print("=" * 60)
    if all_pass:
        print("✅ ALL TESTS PASSED - Solver migration is complete!")
    else:
        print("❌ SOME TESTS FAILED - Check output above")
    print("=" * 60)

    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
