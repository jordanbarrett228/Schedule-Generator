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


# CORS Configuration
# Allow local development and Cloudflare Tunnel access
allowed_origins = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add Cloudflare Tunnel URL if specified in environment
cloudflare_url = os.environ.get("CLOUDFLARE_TUNNEL_URL", "")
if cloudflare_url:
    allowed_origins.append(cloudflare_url)

# In development mode, allow all origins for easier testing
if os.environ.get("DEV", "0") == "1":
    allowed_origins.append("http://localhost:5173")
    allowed_origins.append("http://127.0.0.1:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.trycloudflare\.com",  # Allow Cloudflare quick tunnels
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# Serve frontend build (static) AFTER APIs
FRONTEND_DIST = Path(__file__).resolve().parent / "static" / "dist"
if FRONTEND_DIST.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

#if __name__ == "__main__":
 #   import uvicorn
  #  uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
