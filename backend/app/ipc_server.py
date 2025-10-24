"""
IPC Server for Electron Desktop App
Handles stdin/stdout communication instead of HTTP
No authentication - single-user mode
"""
import sys
import json
import argparse
import threading
from pathlib import Path

from .db import init_db, set_data_directory
from . import ipc_implementations as impl

# Track active background tasks
active_tasks = {}
task_results = {}
task_lock = threading.Lock()


def run_solver_background(data):
    """Run the solver in a background thread"""
    try:
        with task_lock:
            active_tasks['solver'] = True

        result = impl.generate_schedule_impl(data)

        with task_lock:
            task_results['solver'] = result
            if 'solver' in active_tasks:
                del active_tasks['solver']

        # Send completion event
        completion_event = {
            'type': 'solver_complete',
            'event': {'status': 'complete'}
        }
        print(json.dumps(completion_event), flush=True)
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        with task_lock:
            task_results['solver'] = {'status': 'error', 'error': str(e)}
            if 'solver' in active_tasks:
                del active_tasks['solver']


def handle_request(method: str, endpoint: str, data: dict | None = None):
    """
    Route requests to appropriate handlers
    Since we're in single-user mode, we don't need authentication
    """
    try:
        # Split endpoint into parts
        parts = endpoint.strip('/').split('/')

        # Route to appropriate handler based on endpoint
        # EMPLOYEES
        if endpoint.startswith('/api/employees'):
            if len(parts) == 2:  # /api/employees
                if method == 'GET':
                    return impl.get_employees_impl()
                elif method == 'POST':
                    return impl.create_employee_impl(data or {})
            elif len(parts) == 3:  # /api/employees/{id}
                emp_id = int(parts[2])
                if method == 'GET':
                    return impl.get_employee_impl(emp_id)
                elif method == 'PUT':
                    return impl.update_employee_impl(emp_id, data or {})
                elif method == 'DELETE':
                    return impl.delete_employee_impl(emp_id)
            elif len(parts) == 4 and parts[3] == 'timeoff':  # /api/employees/{id}/timeoff
                emp_id = int(parts[2])
                if method == 'GET':
                    return impl.get_timeoff_impl(emp_id)
                elif method == 'POST':
                    return impl.create_timeoff_impl(emp_id, data or {})
            elif len(parts) == 4 and parts[3] == 'unavailable':  # /api/employees/{id}/unavailable
                emp_id = int(parts[2])
                if method == 'GET':
                    return impl.get_unavailable_impl(emp_id)
                elif method == 'POST':
                    return impl.create_unavailable_impl(emp_id, data or {})
            elif len(parts) == 4 and parts[3] == 'locked-shifts':  # /api/employees/{id}/locked_shifts
                emp_id = int(parts[2])
                if method == 'GET':
                    return impl.get_locked_shifts_impl(emp_id)
                elif method == 'POST':
                    return impl.create_locked_shift_impl(emp_id, data or {})

        # TIME-OFF
        elif endpoint.startswith('/api/timeoff/'):
            rec_id = int(parts[2])
            if method == 'DELETE':
                return impl.delete_timeoff_impl(rec_id)

        # UNAVAILABLE
        elif endpoint.startswith('/api/unavailable/'):
            rec_id = int(parts[2])
            if method == 'DELETE':
                return impl.delete_unavailable_impl(rec_id)

        # LOCKED SHIFTS
        elif endpoint.startswith('/api/locked-shift/'):
            rec_id = int(parts[2])
            if method == 'DELETE':
                return impl.delete_locked_shift_impl(rec_id)

        # SETTINGS
        elif endpoint == '/api/settings/global':
            if method == 'GET':
                return impl.get_global_settings_impl()
            elif method == 'PUT':
                return impl.update_global_settings_impl(data or {})
        elif endpoint == '/api/settings/business_hours':
            if method == 'GET':
                return impl.get_business_hours_impl()
            elif method == 'PUT':
                return impl.update_business_hours_impl(data if isinstance(data, list) else [])

        # STAFFING WINDOWS
        elif endpoint == '/api/staffing-windows':
            if method == 'GET':
                return impl.get_staffing_windows_impl()
            elif method == 'POST':
                return impl.create_staffing_window_impl(data or {})
            elif method == 'PUT':
                return impl.update_staffing_windows_impl(data if isinstance(data, list) else [])
        elif endpoint.startswith('/api/staffing-windows/'):
            window_id = int(parts[2])
            if method == 'DELETE':
                return impl.delete_staffing_window_impl(window_id)

        # SCHEDULE
        elif endpoint == '/api/schedule/generate':
            if method == 'POST':
                # Launch solver in background thread
                with task_lock:
                    if 'solver' in active_tasks:
                        return {"status": "error", "message": "Solver already running"}
                    # Clear previous result
                    if 'solver' in task_results:
                        del task_results['solver']

                thread = threading.Thread(target=run_solver_background, args=(data,), daemon=True)
                thread.start()
                return {"status": "started", "message": "Schedule generation started"}

        elif endpoint == '/api/schedule/result':
            if method == 'GET':
                # Get the result if available
                with task_lock:
                    if 'solver' in active_tasks:
                        return {"status": "generating"}
                    elif 'solver' in task_results:
                        result = task_results['solver']
                        del task_results['solver']  # Clear after retrieval
                        return result
                    else:
                        return {"status": "no_result"}

        # ADMIN
        elif endpoint == '/api/admin/reset':
            if method == 'POST':
                return impl.reset_data_impl()

        raise ValueError(f"Unknown endpoint: {method} {endpoint}")

    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(description='IPC Server for Schedule Generator')
    parser.add_argument('--data-dir', type=str, help='Data directory path')
    args = parser.parse_args()

    # Set data directory if provided
    if args.data_dir:
        set_data_directory(args.data_dir)
        print(f"Using data directory: {args.data_dir}", file=sys.stderr)

    # Initialize database
    init_db()
    print("Database initialized", file=sys.stderr)
    print("IPC server ready", file=sys.stderr)

    # Main loop: read requests from stdin, send responses to stdout
    for line in sys.stdin:
        request = None
        request_id = -1
        try:
            request = json.loads(line)
            request_id = request.get('id', -1)
            method = request.get('method')
            endpoint = request.get('endpoint')
            data = request.get('data')

            # Handle the request
            result = handle_request(method, endpoint, data)

            # Send response
            response = {
                'id': request_id,
                'data': result
            }
            print(json.dumps(response), flush=True)

        except Exception as e:
            # Send error response (use request_id from above if available)
            response = {
                'id': request_id,
                'error': str(e)
            }
            print(json.dumps(response), flush=True)


if __name__ == '__main__':
    main()
