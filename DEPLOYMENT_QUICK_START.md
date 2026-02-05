# Quick Deployment Guide

## Option 1: WinSCP (Recommended - Free & Easy)

### First Time Setup:
1. Download WinSCP: https://winscp.net/eng/download.php
2. Install to default location: `C:\Program Files (x86)\WinSCP\`

### Deploy:
```powershell
.\deploy-winscp.ps1
```

Enter your cPanel password when prompted. Done!

---

## Option 2: Git for Windows (For Developers)

### First Time Setup:
1. Download Git for Windows: https://git-scm.com/download/win
2. Install with default options

### Deploy:
```powershell
.\deploy-to-production.ps1
```

---

## Option 3: Manual Upload via cPanel File Manager

1. Go to: https://nafacademy.com:2083
2. Login with cPanel credentials
3. Open File Manager
4. Navigate to: `/home/nafazplp/public_html/efrisintegration.nafacademy.com/`
5. Upload these files:
   - `api_multitenant.py`
   - `passenger_wsgi.py`
   - `.htaccess`
   - `efris_client.py`
   - `auth.py`
   - `quickbooks_client.py`
   - `static/login.html`
   - `static/landing.html`
   - `static/dashboard.html`
   - `static/reseller.html`
   - `static/owner.html`
6. Navigate to `tmp/` folder
7. Right-click `restart.txt` → Edit → Save (this restarts the app)

---

## What Gets Deployed

### Core Files:
- `api_multitenant.py` - Main FastAPI application
- `passenger_wsgi.py` - WSGI entry point for Passenger
- `.htaccess` - Web server configuration
- `efris_client.py` - EFRIS API client
- `auth.py` - Authentication logic
- `quickbooks_client.py` - QuickBooks integration

### Static UI Files:
- `static/login.html` - Login page
- `static/landing.html` - Public landing page
- `static/dashboard.html` - User dashboard
- `static/reseller.html` - Reseller admin panel
- `static/owner.html` - Platform owner panel

### NOT Deployed (Production-only):
- `.env` - Environment variables (already on server)
- Database files
- Virtual environment

---

## After Deployment

### Verify:
1. Check health endpoint: https://efrisintegration.nafacademy.com/health
2. Should return: `{"status":"healthy","database":"connected"}`

### If errors:
1. SSH to server: `ssh nafazplp@efrisintegration.nafacademy.com`
2. Check logs: `tail -50 ~/public_html/efrisintegration.nafacademy.com/stderr.log`
3. Restart manually: `touch ~/public_html/efrisintegration.nafacademy.com/tmp/restart.txt`

---

## FAQ

**Q: Which deployment method should I use?**  
A: WinSCP is easiest - just install and run the script.

**Q: Do I need to redeploy .env or database?**  
A: No, those stay on the server. Only deploy code files.

**Q: How do I know if deployment worked?**  
A: The script will test the health endpoint automatically.

**Q: Can I deploy single files?**  
A: Yes, with manual upload. Or edit the deploy script to only upload specific files.

**Q: How often should I deploy?**  
A: After any code changes in api_multitenant.py, efris_client.py, or HTML files.
