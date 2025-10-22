# Step-by-Step Setup Guide - Cloudflare Tunnel
## Complete Beginner's Guide with Screenshots

---

## ✅ STEP 1: Install cloudflared (DONE!)

Good news - we just installed it! But you need to **restart your command prompt** for it to work.

**Do this now:**
1. Close ALL command prompt/PowerShell windows
2. Open a **NEW** Command Prompt or PowerShell window
3. Test that it works by typing:
   ```
   cloudflared --version
   ```

You should see: `cloudflared version 2025.8.1`

---

## STEP 2: Login to Cloudflare

This connects cloudflared to your Cloudflare account.

**In your NEW command prompt, type:**
```bash
cloudflared tunnel login
```

**What happens:**
1. A browser window will open automatically
2. You'll see the Cloudflare login page
3. Login with the account you just created
4. You'll see a page saying "You have successfully authorized cloudflared"
5. You can close the browser

**Back in the command prompt, you should see:**
```
You have successfully logged in.
```

---

## STEP 3: Create a Named Tunnel (Get Your Permanent URL!)

This creates a tunnel with a name and a permanent URL.

**Type this command:**
```bash
cloudflared tunnel create schedule-generator
```

**You'll see output like:**
```
Created tunnel schedule-generator with id abc123-def456-ghi789
```

**IMPORTANT: Copy that tunnel ID!** You'll need it in a moment.

The ID looks like: `abc123-def456-ghi789` (yours will be different)

---

## STEP 4: Find Your Permanent URL

**Type this command:**
```bash
cloudflared tunnel info schedule-generator
```

**You'll see output like:**
```
ID: abc123-def456-ghi789
Name: schedule-generator
Created: 2025-10-22
Connections: none
```

**Your permanent URL is:**
```
https://abc123-def456-ghi789.cfargotunnel.com
```

Replace `abc123-def456-ghi789` with YOUR actual tunnel ID.

**THIS IS THE URL YOUR MANAGER WILL USE!** Save it somewhere!

---

## STEP 5: Create Configuration File

Now we need to tell cloudflared how to route traffic.

**Step 5a: Find your .cloudflared folder**

Open File Explorer and go to:
```
C:\Users\illus\.cloudflared
```

If the folder doesn't exist, create it:
1. Go to `C:\Users\illus\`
2. Right-click → New → Folder
3. Name it `.cloudflared` (yes, with the dot!)

**Step 5b: Create config.yml file**

In that folder, create a new file called `config.yml`

Here's how:
1. Right-click in the folder → New → Text Document
2. Name it `config.yml` (delete the .txt extension!)
3. Open it in Notepad

**Step 5c: Paste this into config.yml:**

```yaml
tunnel: abc123-def456-ghi789
credentials-file: C:\Users\illus\.cloudflared\abc123-def456-ghi789.json

ingress:
  - service: http://localhost:8000
```

**IMPORTANT:** Replace `abc123-def456-ghi789` with YOUR actual tunnel ID (from Step 3)

**Step 5d: Save the file**

Make sure it's saved as `config.yml` (NOT `config.yml.txt`)

---

## STEP 6: Test the Tunnel!

Now let's test if everything works!

**Open TWO command prompt windows:**

**Window 1 - Start Backend:**
```bash
cd C:\Users\illus\OneDrive\Documents\GitHub\Schedule-Generator\backend
python run_app.py
```

Wait for it to say "Application startup complete"

**Window 2 - Start Tunnel:**
```bash
cloudflared tunnel run schedule-generator
```

**You should see:**
```
Connection registered
Registered tunnel connection
```

---

## STEP 7: Test Your URL!

**On your phone (using cellular data, NOT WiFi):**

1. Open browser
2. Go to: `https://YOUR-TUNNEL-ID.cfargotunnel.com`
3. You should see the Schedule Generator login page!

**If it works - YOU'RE DONE! 🎉**

---

## STEP 8: Share with Your Manager

Send your manager this message:

---

Hi! I've set up the Schedule Generator. Here's how to access it:

**URL:** https://YOUR-TUNNEL-ID.cfargotunnel.com

**Your Login:**
- Username: [their username]
- Password: [their password]

**To use it:**
1. Visit the URL above
2. Login with your credentials
3. Use the app normally!

**Important:** The app is only available when I have it running on my laptop. If you can't connect, just send me a message and I'll start it up.

You can bookmark this URL - it won't change!

---

## Daily Usage (For You)

### To Make App Available:

**Option A: Use the easy script**
```bash
cd C:\Users\illus\OneDrive\Documents\GitHub\Schedule-Generator\backend
start_tunnel.bat
```
Choose option 2 (Named Tunnel)

**Option B: Manual**

Open two command prompts:

**Window 1:**
```bash
cd C:\Users\illus\OneDrive\Documents\GitHub\Schedule-Generator\backend
python run_app.py
```

**Window 2:**
```bash
cloudflared tunnel run schedule-generator
```

### To Stop:
Press `Ctrl+C` in both windows

---

## Troubleshooting

### Problem: "cloudflared: command not found"
**Fix:**
1. Close and reopen your command prompt
2. If still doesn't work, restart your computer

### Problem: "tunnel not found"
**Fix:** Make sure you created it:
```bash
cloudflared tunnel list
```

### Problem: Backend won't start (port 8000 in use)
**Fix:**
```bash
netstat -ano | findstr :8000
taskkill /PID [number] /F
```

### Problem: Can't access URL from phone
**Check:**
1. Is backend running? (Window 1 should show "Application startup complete")
2. Is tunnel running? (Window 2 should show "Registered tunnel connection")
3. Are you using cellular data, not WiFi?
4. Is your laptop online?

---

## Understanding the Cloudflare Dashboard (Optional)

You can also manage your tunnel from the Cloudflare website!

1. Go to: https://one.dash.cloudflare.com/
2. Login with your Cloudflare account
3. Click "Access" → "Tunnels"
4. You'll see your "schedule-generator" tunnel
5. You can start/stop it, see connection stats, etc.

**But the command line is easier for daily use!**

---

## What Each File Does

**Files Created:**

- `C:\Users\illus\.cloudflared\config.yml` - Tunnel configuration
- `C:\Users\illus\.cloudflared\abc123.json` - Credentials (auto-created)
- `C:\Users\illus\.cloudflared\cert.pem` - Auth certificate (auto-created)

**Don't delete these files!** They're needed for the tunnel to work.

---

## Summary

**What you did:**
1. ✅ Installed cloudflared
2. ✅ Logged in to Cloudflare
3. ✅ Created a named tunnel
4. ✅ Got a permanent URL
5. ✅ Configured routing
6. ✅ Tested it works

**What your manager gets:**
- A permanent URL they can bookmark
- Access from any browser, any device
- No special setup required

**What you control:**
- When the app is online (start tunnel = online)
- Who has login credentials
- All the data (stays on your laptop)

---

## Your Permanent URL Structure

```
https://[tunnel-id].cfargotunnel.com
         ^^^^^^^^^
         This is your unique identifier
```

**Example:**
```
https://abc123-def456-ghi789.cfargotunnel.com
```

This URL:
- ✅ Never changes
- ✅ Works through firewalls
- ✅ Has HTTPS security
- ✅ Is free forever
- ✅ Can be bookmarked

---

## Next Steps

1. **Right now:** Follow Steps 2-7 above to complete setup
2. **Test:** Verify you can access the URL from your phone
3. **Share:** Send URL to your manager
4. **Use:** Run `start_tunnel.bat` whenever you want it online

**Questions?** Check the troubleshooting section above!

---

## Quick Reference Card

**To start app:**
```bash
cd backend
start_tunnel.bat
# Choose option 2
```

**Your manager's URL:**
```
https://YOUR-TUNNEL-ID.cfargotunnel.com
```

**To stop:**
```
Ctrl+C in tunnel window
```

That's it! Simple once you know the steps! 🎉
