# URGENT: Deploy Address Bug Fix to Production

## Issue Fixed
- ✅ **Commit:** fdd87a0
- ✅ **Bug:** 'Company' object has no attribute 'address'
- ✅ **Fix:** Changed to use empty strings for optional seller fields
- ✅ **Status:** Code pushed to GitHub main branch

## Deploy to Production (efrisintegration.nafacademy.com)

### Step 1: SSH to Production Server
```bash
ssh nafazplp@your-server-ip
# Or use your hosting control panel SSH terminal
```

### Step 2: Navigate to Project Directory
```bash
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com
```

### Step 3: Pull Latest Code from GitHub
```bash
git pull origin main
```

Expected output:
```
remote: Enumerating objects: 17, done.
remote: Counting objects: 100% (17/17), done.
Updating 0777869..fdd87a0
Fast-forward
 api_multitenant.py | 6 +++---
 CUSTOM_ERP_COMPLETE_API_GUIDE.md | 28 ++++++++++++++++++++++++++++
 2 files changed, 31 insertions(+), 3 deletions(-)
```

### Step 4: Reload Passenger Application
```bash
# Method 1: Touch the passenger_wsgi.py file
touch passenger_wsgi.py

# Method 2: Create/touch restart.txt (if using Passenger)
mkdir -p tmp
touch tmp/restart.txt

# Method 3: Use Passenger restart command (if available)
passenger-config restart-app /home/nafazplp/public_html/efrisintegration.nafacademy.com
```

### Step 5: Verify Fix is Live

Test with curl or Postman:
```bash
curl -X POST https://efrisintegration.nafacademy.com/api/external/efris/submit-invoice \
  -H "X-API-Key: your_api_key" \
  -H "X-API-Secret: your_api_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "TEST-001",
    "invoice_date": "2026-02-13",
    "customer_name": "Test Customer",
    "items": [{
      "item_name": "Test Product",
      "item_code": "TEST-001",
      "quantity": 1,
      "unit_price": 1000,
      "tax_rate": 18
    }]
  }'
```

**Expected:** HTTP 200 with FDN number
**Not:** HTTP 500 with "no attribute 'address'" error

## Alternative: cPanel File Manager Method

If you can't access SSH:

1. Log in to cPanel
2. Go to **File Manager**
3. Navigate to `public_html/efrisintegration.nafacademy.com`
4. Click **Git Version Control** or **Terminal**
5. Run: `git pull origin main`
6. Find `passenger_wsgi.py` file
7. Right-click → **Touch** (updates timestamp to reload app)
8. Wait 30 seconds for reload

## Verification Checklist

After deployment:

- [ ] SSH to production server
- [ ] Pull latest code (`git pull origin main`)
- [ ] Reload app (`touch passenger_wsgi.py`)
- [ ] Test invoice submission endpoint
- [ ] Confirm HTTP 200 response (not 500)
- [ ] Verify FDN returned in response
- [ ] Notify team fix is deployed

## Rollback (if needed)

If something goes wrong:
```bash
git checkout 0777869  # Previous working commit
touch passenger_wsgi.py
```

## Contact

If deployment issues occur, check:
- Git pull successful?
- Passenger reloaded?
- Python virtual environment active?
- Environment variables loaded?
- Database accessible?

---

**Fix deployed:** Once you run these commands, the bug is resolved.
**Estimated time:** 2-3 minutes
**Downtime:** None (Passenger hot reload)
