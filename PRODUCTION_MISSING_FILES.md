# Missing Files on Production Server

## Issue
The test endpoints fail with `'NoneType' object has no attribute 'decrypt'` because the certificate file is missing.

## Fix

### 1. Upload Certificate File
The API expects a test certificate at: `keys/wandera.pfx`

**On production server:**
```bash
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com
mkdir -p keys
```

**Then upload via FTP/File Manager:**
- Upload `keys/wandera.pfx` from your local machine
- Set permissions: `chmod 600 keys/wandera.pfx`

### 2. Verify Upload
```bash
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com
ls -la keys/
file keys/wandera.pfx
```

Should show: `keys/wandera.pfx: data` (binary file)

### 3. Restart App
```bash
touch tmp/restart.txt
sleep 3
curl -s https://efrisintegration.nafacademy.com/health
```

### 4. Test Endpoints
```bash
curl -s https://efrisintegration.nafacademy.com/api/public/efris/test/t103
```

Should return success instead of decrypt error.

---

## Files That MUST Be on Production

| File/Folder | Purpose | Required |
|-------------|---------|----------|
| `keys/wandera.pfx` | Test certificate for demo endpoints | Yes (for test endpoints) |
| `.env` | Environment variables | Yes |
| `passenger_wsgi.py` | WSGI entry point | Yes |
| `.htaccess` | Passenger config | Yes |
| `tmp/` directory | For restart trigger | Yes |
| All `.py` files | Application code | Yes |

---

## Alternative: Disable Test Endpoints

If you don't want to upload certificates, you can disable the test endpoints or make them return a message that certificates aren't configured:

Edit the test endpoints to return:
```python
return {
    "status": "unavailable",
    "message": "Test endpoints require certificate configuration. Contact admin."
}
```
