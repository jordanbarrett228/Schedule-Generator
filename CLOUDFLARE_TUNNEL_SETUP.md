# Cloudflare Tunnel Setup Guide

## What is Cloudflare Tunnel?

Cloudflare Tunnel creates a secure connection from your laptop to Cloudflare's network, allowing external users to access your application through a public URL **without opening any ports** on your router or firewall.

### Benefits for Your Use Case:
✅ **No port forwarding** - Works through firewalls and Fortinet
✅ **Free tier available** - No hosting costs
✅ **HTTPS by default** - Secure connections
✅ **Full control** - Data stays on your laptop
✅ **Easy on/off** - Start/stop whenever you want
✅ **Works like a normal website** - Standard HTTP/HTTPS requests
✅ **Bypass firewall restrictions** - Uses standard ports (443)

---

## Prerequisites

1. **Cloudflare Account** (free)
2. **A domain name** (optional - Cloudflare provides free *.trycloudflare.com URLs)
3. **Your laptop** (Windows/Mac/Linux)

---

## Step 1: Install Cloudflare Tunnel (cloudflared)

### Windows:
```powershell
# Download and install cloudflared
# Visit: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# Or use winget:
winget install --id Cloudflare.cloudflared
```

### After installation, verify:
```bash
cloudflared --version
```

---

## Step 2: Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This will:
1. Open your browser
2. Ask you to log in to Cloudflare
3. Save authentication credentials

---

## Step 3: Create a Tunnel

```bash
# Create a named tunnel
cloudflared tunnel create schedule-generator

# This creates a tunnel ID and saves credentials to:
# Windows: C:\Users\<username>\.cloudflared\<tunnel-id>.json
```

**Save the Tunnel ID** - you'll need it later!

---

## Step 4: Create Tunnel Configuration

Create a file: `C:\Users\illus\.cloudflared\config.yml`

```yaml
# Tunnel ID (replace with your actual tunnel ID from Step 3)
tunnel: <YOUR-TUNNEL-ID>

# Credentials file path
credentials-file: C:\Users\illus\.cloudflared\<YOUR-TUNNEL-ID>.json

ingress:
  # Route all traffic to your local backend
  - hostname: schedule.yourdomain.com
    service: http://localhost:8000
    originRequest:
      noTLSVerify: true

  # Catch-all rule (required)
  - service: http_status:404
```

### If you DON'T have a domain (use free Cloudflare URL):
```yaml
tunnel: <YOUR-TUNNEL-ID>
credentials-file: C:\Users\illus\.cloudflared\<YOUR-TUNNEL-ID>.json

ingress:
  # This will give you a random *.trycloudflare.com URL
  - service: http://localhost:8000
    originRequest:
      noTLSVerify: true
```

---

## Step 5: Route Your Domain (Optional - if you have a domain)

If you own a domain and have it on Cloudflare:

```bash
# Route your domain to the tunnel
cloudflared tunnel route dns schedule-generator schedule.yourdomain.com
```

This creates a DNS CNAME record pointing to your tunnel.

---

## Step 6: Update Backend CORS Settings

Your backend needs to accept requests from the Cloudflare URL.

**File**: `backend/app/main.py`

Find the CORS configuration and update it:

```python
# Allow both local development and Cloudflare tunnel
origins = [
    "http://localhost:5173",  # Local dev
    "http://localhost:3000",
    "https://schedule.yourdomain.com",  # Your tunnel domain
    "https://*.trycloudflare.com",  # Cloudflare free URLs
    # Add your manager's access URL here once you know it
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.trycloudflare\.com",  # Allow all Cloudflare URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Step 7: Start the Tunnel

### Option A: Quick Start (temporary URL)
```bash
# This gives you a temporary *.trycloudflare.com URL
cloudflared tunnel --url http://localhost:8000
```

**Output:**
```
Your quick Tunnel has been created! Visit it at:
https://random-name-123.trycloudflare.com
```

This URL changes every time you restart!

### Option B: Named Tunnel (permanent URL)
```bash
# Start your configured tunnel
cloudflared tunnel run schedule-generator
```

This uses your configured domain (schedule.yourdomain.com).

---

## Step 8: Start Your Application

### Terminal 1 - Start Backend:
```bash
cd backend
python run_app.py
```

### Terminal 2 - Start Cloudflare Tunnel:
```bash
cloudflared tunnel run schedule-generator
```

### Terminal 3 - Build and Serve Frontend (optional):
```bash
cd frontend
npm run build

# The backend will serve the built frontend from /dist
```

---

## Step 9: Access from External Network

Your manager can now access the app at:
- **With domain**: `https://schedule.yourdomain.com`
- **Without domain**: `https://random-name-123.trycloudflare.com`

The app will work exactly like a normal website - no special setup needed on their end!

---

## Production Setup (Recommended)

### Create an Auto-Start Script

**File**: `backend/start_tunnel.bat` (Windows)

```batch
@echo off
echo Starting Schedule Generator with Cloudflare Tunnel...
echo.

REM Start backend in background
echo Starting backend...
start /B python run_app.py

REM Wait for backend to start
timeout /t 3 /nobreak > nul

REM Start Cloudflare tunnel
echo Starting Cloudflare Tunnel...
cloudflared tunnel run schedule-generator

REM If tunnel stops, kill backend
taskkill /IM python.exe /F
```

**Usage**:
```bash
cd backend
start_tunnel.bat
```

### Linux/Mac: `start_tunnel.sh`

```bash
#!/bin/bash
echo "Starting Schedule Generator with Cloudflare Tunnel..."

# Start backend in background
echo "Starting backend..."
python run_app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Cloudflare tunnel
echo "Starting Cloudflare Tunnel..."
cloudflared tunnel run schedule-generator

# If tunnel stops, kill backend
kill $BACKEND_PID
```

Make it executable:
```bash
chmod +x start_tunnel.sh
./start_tunnel.sh
```

---

## Troubleshooting

### Issue: "Tunnel not found"
**Solution**: Make sure you created the tunnel:
```bash
cloudflared tunnel list
```

### Issue: "Connection refused"
**Solution**: Make sure your backend is running on port 8000:
```bash
# Check if backend is running
curl http://localhost:8000/api/me
```

### Issue: CORS errors in browser
**Solution**: Add your Cloudflare URL to CORS origins in `main.py`

### Issue: Can't access from manager's computer
**Solution**:
1. Verify tunnel is running: `cloudflared tunnel list`
2. Check tunnel URL is correct
3. Make sure your laptop is online and backend is running

---

## Security Considerations

### 1. Authentication (Already Implemented)
✅ Your app uses JWT tokens - good!

### 2. Rate Limiting (Recommended)
Add rate limiting to prevent abuse:

```bash
pip install slowapi
```

**File**: `backend/app/main.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/token")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(...):
    ...
```

### 3. IP Whitelisting (Optional)
If your manager's IP is static:

```yaml
# In config.yml
ingress:
  - hostname: schedule.yourdomain.com
    service: http://localhost:8000
    originRequest:
      noTLSVerify: true
      access:
        required: true
        teamName: your-team
```

---

## Cost Analysis

### Free Tier (What You'll Use):
- ✅ Unlimited bandwidth
- ✅ Unlimited requests
- ✅ HTTPS certificates
- ✅ DDoS protection
- ✅ 50 users (plenty for your manager)

### Paid Tiers (Not Needed):
- Advanced security features
- Analytics
- Load balancing
- Multiple origins

**Total Cost**: $0/month 🎉

---

## Monitoring & Logs

### Check Tunnel Status:
```bash
cloudflared tunnel info schedule-generator
```

### View Tunnel Logs:
```bash
# Windows
cloudflared tunnel run schedule-generator --loglevel debug

# Logs are also in:
# C:\Users\<username>\.cloudflared\logs\
```

### Check Backend Logs:
Your FastAPI backend logs will show all requests.

---

## Updating Your Setup

### To Change Domain:
```bash
# Remove old route
cloudflared tunnel route dns delete schedule-generator schedule.old.com

# Add new route
cloudflared tunnel route dns schedule-generator schedule.new.com
```

### To Update Configuration:
1. Edit `~/.cloudflared/config.yml`
2. Restart tunnel: `cloudflared tunnel run schedule-generator`

---

## Alternative: Using Free Cloudflare URL

If you don't want to buy a domain:

**Quick tunnel (changes URL every restart)**:
```bash
cloudflared tunnel --url http://localhost:8000
```

**Named tunnel with stable ID** (URL stays the same):
```bash
# Create tunnel
cloudflared tunnel create schedule-generator

# Note the tunnel ID, e.g., abc123-def456-ghi789

# Your URL will be:
# https://abc123-def456-ghi789.cfargotunnel.com
```

---

## Usage Instructions for Your Manager

Send this to your manager:

---

### How to Access the Schedule Generator

1. **Go to**: `https://schedule.yourdomain.com` (or the Cloudflare URL I give you)
2. **Login** with your username and password
3. **Use the app** - it works like any normal website!

**Note**: The app is only available when I have my laptop online and the tunnel running. If you can't connect, send me a message and I'll start it up.

---

## Daily Workflow (For You)

### Starting the App:
```bash
cd C:\Users\illus\OneDrive\Documents\GitHub\Schedule-Generator\backend
start_tunnel.bat
```

### Stopping the App:
- Press `Ctrl+C` in the tunnel terminal
- Both backend and tunnel will stop

### Checking Status:
```bash
cloudflared tunnel info schedule-generator
```

---

## Summary

**What You Get**:
- ✅ Public HTTPS URL for your app
- ✅ No port forwarding needed
- ✅ Works through firewalls (uses port 443)
- ✅ Free hosting
- ✅ Full control over data (stored on your laptop)
- ✅ Easy start/stop
- ✅ Secure (JWT + HTTPS)

**What You Need to Do**:
1. Install cloudflared
2. Create tunnel
3. Configure CORS
4. Run start_tunnel script

**What Your Manager Does**:
- Visit URL like any website
- Login and use the app

**No firewall issues, no port opening, no monthly fees!** 🎉

---

## Next Steps

1. Follow the installation steps above
2. Test the tunnel locally first
3. Share URL with your manager
4. Monitor usage and adjust as needed

If you have any issues, check the troubleshooting section or the Cloudflare Tunnel docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
