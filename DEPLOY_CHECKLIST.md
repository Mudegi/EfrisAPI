# Files to Upload to Production

## Current Session Changes (Upload These):

- [ ] `static/login.html` - Fixed JSON error handling
- [ ] `static/landing.html` - Removed invoice endpoint button
- [ ] `api_multitenant.py` - Removed invoice test endpoint

## Upload Instructions:

### Via FTP/File Manager:
1. Connect to server
2. Navigate to: `/home/nafazplp/public_html/efrisintegration.nafacademy.com/`
3. Upload the 3 files above (overwrite existing)
4. Via SSH, run: `touch tmp/restart.txt`
5. Wait 3 seconds, test: `curl -s https://efrisintegration.nafacademy.com/health`

### Via SSH (Faster):
```bash
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com

# Backup current files
cp api_multitenant.py api_multitenant.py.backup.$(date +%Y%m%d)
cp static/login.html static/login.html.backup.$(date +%Y%m%d)
cp static/landing.html static/landing.html.backup.$(date +%Y%m%d)

# Upload new files (use FTP or nano to edit)
# Then restart:
touch tmp/restart.txt
```

## Files That Should MATCH Between Local and Production:

✅ **api_multitenant.py** - Has `from sqlalchemy import text` fix
✅ **passenger_wsgi.py** - Lazy loading version
✅ **.env** - Production database config
✅ **.htaccess** - Passenger configuration

## Going Forward:

**Rule:** Make ALL changes locally first, then upload to production.

**Never edit directly on production** - Always update local, test locally, then deploy.
