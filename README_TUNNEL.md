# 🚀 Schedule Generator - Remote Access Setup

## How to Share Your App With Your Manager

### Quick Start (2 Steps):

**1. Install Cloudflare Tunnel (First Time Only):**
```bash
winget install --id Cloudflare.cloudflared
cloudflared tunnel login
```

**2. Start the App:**
```bash
cd backend
start_tunnel.bat
```

Choose option 1, copy the URL, send to your manager. **Done!** ✅

---

## What This Does

- ✅ Creates a public HTTPS URL for your local app
- ✅ Works through firewalls (no Fortinet blocking)
- ✅ No port forwarding needed
- ✅ Completely free
- ✅ Data stays on your laptop
- ✅ You control when it's online/offline

---

## Daily Usage

### Make App Available:
```bash
cd backend
start_tunnel.bat
```

### Stop App:
Press `Ctrl+C`

**That's all you need to know!** 🎉

---

## Full Documentation

- **Quick Start:** [QUICK_START_CLOUDFLARE.md](QUICK_START_CLOUDFLARE.md)
- **Complete Guide:** [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)
- **Summary:** [CLOUDFLARE_TUNNEL_COMPLETE.md](CLOUDFLARE_TUNNEL_COMPLETE.md)

---

## Your Manager's Experience

1. You send them: `https://something.trycloudflare.com`
2. They visit it (works like any website)
3. They login with their credentials
4. They use the app normally

**No setup required on their end!**

---

## Cost

**$0/month** for everything (Cloudflare's free tier)

---

## Support

Questions? Check the documentation files above or visit:
https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
