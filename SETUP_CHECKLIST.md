# Setup Checklist - Follow in Order

Print this out or keep it open while you work!

---

## ☑️ Pre-Setup (DONE!)

- [x] Windows 10/11 installed
- [x] winget installed (v1.11.430)
- [x] cloudflared installed (v2025.8.1)
- [x] Cloudflare account created

---

## 📋 Main Setup (Do These Now)

### Step 1: Restart Terminal ⏸️
- [ ] Close ALL command prompt windows
- [ ] Open a NEW Command Prompt
- [ ] Test: Type `cloudflared --version`
- [ ] Should see: "cloudflared version 2025.8.1"

**If it says "command not found":** Restart your computer, then try again.

---

### Step 2: Login to Cloudflare 🔐
Open Command Prompt and type:
```
cloudflared tunnel login
```

- [ ] Browser opened automatically
- [ ] Logged in to Cloudflare
- [ ] Saw "Successfully authorized" message
- [ ] Command prompt shows "You have successfully logged in"

---

### Step 3: Create Tunnel 🌐
In Command Prompt, type:
```
cloudflared tunnel create schedule-generator
```

- [ ] Command completed successfully
- [ ] You saw output like: "Created tunnel schedule-generator with id abc123..."
- [ ] **Write down your tunnel ID here:**

```
MY TUNNEL ID: _________________________________
```

---

### Step 4: Get Your Permanent URL 🔗
In Command Prompt, type:
```
cloudflared tunnel info schedule-generator
```

- [ ] Command showed your tunnel info
- [ ] **Your permanent URL is:**

```
https://________________________________.cfargotunnel.com
```

**This is the URL your manager will use! Save it!**

---

### Step 5: Create Configuration File 📝

#### 5a: Create .cloudflared folder
- [ ] Opened File Explorer
- [ ] Went to: `C:\Users\illus\`
- [ ] Created folder named: `.cloudflared` (with the dot!)
  - Right-click → New → Folder → Name it `.cloudflared`

#### 5b: Create config.yml
- [ ] Went into `C:\Users\illus\.cloudflared\`
- [ ] Created new file: `config.yml`
  - Right-click → New → Text Document
  - Rename to `config.yml` (remove .txt!)

#### 5c: Edit config.yml
- [ ] Opened `config.yml` in Notepad
- [ ] Pasted this (replacing YOUR-TUNNEL-ID with actual ID):

```yaml
tunnel: YOUR-TUNNEL-ID
credentials-file: C:\Users\illus\.cloudflared\YOUR-TUNNEL-ID.json

ingress:
  - service: http://localhost:8000
```

- [ ] Replaced BOTH instances of `YOUR-TUNNEL-ID` with my real tunnel ID
- [ ] Saved the file
- [ ] Verified it's saved as `config.yml` (NOT `config.yml.txt`)

---

### Step 6: Test the Tunnel! 🧪

#### 6a: Start Backend
Open Command Prompt #1:
```
cd C:\Users\illus\OneDrive\Documents\GitHub\Schedule-Generator\backend
python run_app.py
```

- [ ] Backend started
- [ ] Saw "Application startup complete"
- [ ] **Keep this window OPEN**

#### 6b: Start Tunnel
Open Command Prompt #2:
```
cloudflared tunnel run schedule-generator
```

- [ ] Tunnel started
- [ ] Saw "Connection registered"
- [ ] Saw "Registered tunnel connection"
- [ ] **Keep this window OPEN**

---

### Step 7: Test from Phone 📱

- [ ] Opened phone browser (Safari/Chrome)
- [ ] **Made sure using CELLULAR DATA** (not WiFi!)
- [ ] Visited: `https://MY-TUNNEL-ID.cfargotunnel.com`
- [ ] Saw the Schedule Generator login page!

**If you saw the login page: SUCCESS! ✅**

---

### Step 8: Share with Manager 📧

- [ ] Copied my permanent URL
- [ ] Created login credentials for manager
- [ ] Sent them the URL and login info

---

## ✅ You're Done!

From now on, to make the app available:

**Easy way:**
```
cd backend
start_tunnel.bat
```
Choose option 2

**OR**

**Manual way:**
1. Window 1: `python run_app.py`
2. Window 2: `cloudflared tunnel run schedule-generator`

---

## 🆘 Troubleshooting

If something doesn't work:

### "cloudflared: command not found"
1. Close terminal
2. Open NEW terminal
3. If still doesn't work: Restart computer

### "tunnel not found"
Check you created it:
```
cloudflared tunnel list
```

### Can't access from phone
Check:
- [ ] Backend window shows "Application startup complete"
- [ ] Tunnel window shows "Registered tunnel connection"
- [ ] Using cellular data, not WiFi
- [ ] Laptop is online

### Port 8000 already in use
```
netstat -ano | findstr :8000
taskkill /PID [number] /F
```

---

## 📞 Need Help?

1. Check [STEP_BY_STEP_SETUP.md](STEP_BY_STEP_SETUP.md) for detailed instructions
2. Check troubleshooting section in that file
3. Visit: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

---

**Your Tunnel Info (fill this out):**

```
Tunnel Name: schedule-generator
Tunnel ID: _________________________________
Permanent URL: https://________________________________.cfargotunnel.com
Config File: C:\Users\illus\.cloudflared\config.yml
```

**Date Setup Completed:** __________________

---

Good luck! Follow each checkbox in order and you'll be done in 10 minutes! 🎉
