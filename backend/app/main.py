# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os

from .db import init_db
from .routers.new import rt_employees, rt_unavailable, rt_timeoff, rt_locked_shifts, rt_settings, rt_admin, rt_schedule, rt_staffing_windows, rt_auth

# try:
#     import debugpy
#     debugpy.listen(("127.0.0.1", 5678))
#     debugpy.wait_for_client()  # uncomment to pause on start
# except Exception:
#     pass


app = FastAPI(title="Schedule Generator API", version="0.1.0")

# include routers
app.include_router(rt_auth.router)
app.include_router(rt_employees.router)
app.include_router(rt_unavailable.router)
app.include_router(rt_timeoff.router)
app.include_router(rt_locked_shifts.router)
app.include_router(rt_settings.router)
app.include_router(rt_schedule.router)
app.include_router(rt_staffing_windows.router)
app.include_router(rt_admin.router)


# DEV CORS (if needed)
if os.environ.get("DEV", "0") == "1":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
def on_startup():
    init_db()

# Serve frontend build (static) AFTER APIs
FRONTEND_DIST = Path(__file__).resolve().parent / "static" / "dist"
if FRONTEND_DIST.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
