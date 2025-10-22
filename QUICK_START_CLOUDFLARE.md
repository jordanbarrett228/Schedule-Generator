# Quick Start - Cloudflare Tunnel

## TL;DR - Fastest Way to Get Running

### First Time Setup (5 minutes):

```bash
# 1. Install cloudflared
winget install --id Cloudflare.cloudflared

# 2. Login to Cloudflare (opens browser)
cloudflared tunnel login

# 3. Done! You can now use quick tunnels
```

### Every Time You Want to Share the App:

```bash
# Navigate to backend folder
cd backend

# Run the startup script
start_tunnel.bat

# Choose option 1 (Quick Tunnel)
# Copy the URL that appears (https://something.trycloudflare.com)
# Send that URL to your manager
```

**That's it!** Your manager can now access the app at that URL.

---

## What the Script Does

1. ✅ Starts your backend server (localhost:8000)
2. ✅ Creates a Cloudflare tunnel
3. ✅ Gives you a public HTTPS URL
4. ✅ Routes traffic from the URL to your laptop

When you press `Ctrl+C`, everything stops automatically.

---

## Two Tunnel Options

### Option 1: Quick Tunnel (Recommended for Testing)

**Pros:**
- ✅ No configuration needed
- ✅ Works immediately
- ✅ Perfect for occasional use

**Cons:**
- ⚠️ URL changes each time you restart
- ⚠️ You have to send new URL to manager each time

**How to use:**
```bash
start_tunnel.bat
# Choose option 1
```

---

### Option 2: Named Tunnel (Recommended for Regular Use)

**Pros:**
- ✅ URL stays the same
- ✅ Manager bookmarks it once
- ✅ More professional

**Cons:**
- ⚠️ Requires one-time setup

**How to set up:**

```bash
# 1. Create named tunnel (one time only)
cloudflared tunnel create schedule-generator

# 2. Note the tunnel ID that gets printed

# 3. Copy example config
copy backend\.cloudflared-config-example.yml C:\Users\%USERNAME%\.cloudflared\config.yml

# 4. Edit the config file:
notepad C:\Users\%USERNAME%\.cloudflared\config.yml
# - Replace YOUR-TUNNEL-ID-HERE with the actual ID
# - Update the credentials file path

# 5. Get your permanent URL
cloudflared tunnel info schedule-generator

# 6. Use it!
start_tunnel.bat
# Choose option 2
```

**Your URL will be**: `https://YOUR-TUNNEL-ID.cfargotunnel.com`

This URL **never changes**, so your manager can bookmark it!

---

## Troubleshooting

### "cloudflared: command not found"
**Fix:** Install cloudflared:
```bash
winget install --id Cloudflare.cloudflared
```

### "Backend is not responding"
**Fix:** Make sure no other app is using port 8000:
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill it if needed (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### "Tunnel not found" (Option 2 only)
**Fix:** Make sure you created the tunnel:
```bash
cloudflared tunnel list
```

### CORS errors in browser
**Fix:** The script handles this automatically, but if you still get errors:
1. Make sure your tunnel URL matches what's in the browser
2. Try clearing browser cache

---

## Daily Workflow

### You (on your laptop):
```bash
# Morning - when you want to make app available
cd C:\Users\illus\OneDrive\Documents\GitHub\Schedule-Generator\backend
start_tunnel.bat

# Keep this window open all day

# Evening - when you're done
# Press Ctrl+C to stop
```

### Your Manager:
```
# Visit the URL you gave them
https://something.trycloudflare.com

# Login and use the app like normal
# No special setup needed on their end!
```

---

## Security Notes

✅ **Secure by default:**
- HTTPS encryption (automatic)
- JWT authentication (already implemented)
- Data never leaves your laptop
- Only accessible when tunnel is running

✅ **Privacy:**
- Your laptop's IP address is hidden
- Cloudflare handles the routing
- Manager can't see your network details

✅ **Control:**
- Start tunnel = app online
- Stop tunnel = app offline
- You have complete control

---

## Cost

**$0/month** for everything:
- Unlimited bandwidth
- Unlimited users
- HTTPS certificates
- DDoS protection

Cloudflare's free tier is perfect for this use case.

---

## Next Steps

1. Run `start_tunnel.bat` to test it
2. Copy the URL
3. Test it on your phone (using cellular data, not WiFi)
4. If it works, send URL to your manager
5. They can now access the app!

---

## Need Help?

Full documentation: [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)

Cloudflare docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
