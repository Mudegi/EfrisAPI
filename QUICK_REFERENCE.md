# 🚀 Quick Reference Card

## Server Commands

### Start Server
```powershell
cd d:\EfrisAPI
C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe api_multitenant.py
```

### Stop Server
```powershell
# Press Ctrl+C in terminal, or:
Get-Process -Name python | Stop-Process -Force
```

## Access Points

| Resource | URL |
|----------|-----|
| Dashboard | http://localhost:8001/ |
| API Docs | http://localhost:8001/docs |
| Health Check | http://localhost:8001/health |

## Login Credentials

**Admin Account**
- Email: `admin@wandera.com`
- Password: `Admin2026!`

## Company Information

**Wandera EFRIS**
- TIN: `1014409555`
- Device: `1014409555_02`
- ID: `1`
- Status: Active
- Test Mode: Enabled

## Database Connection

```
Host: localhost
Port: 5432
Database: efris_multitenant
User: postgres
Password: kian256
```

## API Authentication

### Get Token
```powershell
$body = @{username='admin@wandera.com'; password='Admin2026!'}
$response = Invoke-WebRequest -Uri 'http://localhost:8001/api/auth/login' -Method POST -Body $body -ContentType 'application/x-www-form-urlencoded'
$token = ($response.Content | ConvertFrom-Json).access_token
```

### Use Token
```powershell
$headers = @{Authorization = "Bearer $token"}
Invoke-WebRequest -Uri 'http://localhost:8001/api/companies' -Headers $headers
```

## Dashboard Navigation

| Tab | Description |
|-----|-------------|
| 📊 Overview | Company stats and info |
| 📦 Products | Product catalog |
| 📄 Invoices | Invoice history |
| ⚙️ Settings | Company settings |

## Common Tasks

### Switch Company
1. Click company dropdown in sidebar
2. Select company from list
3. Data reloads automatically

### Refresh Data
- Click 🔄 Refresh button in top bar

### Logout
- Click "Sign Out" button at bottom of sidebar

## File Locations

| Purpose | Path |
|---------|------|
| Multi-tenant API | `api_multitenant.py` |
| New Dashboard | `static/dashboard_multitenant.html` |
| Old Dashboard | `static/dashboard.html` |
| Database Models | `database/models.py` |
| Auth Logic | `auth/security.py` |
| API Schemas | `schemas/schemas.py` |

## Documentation Files

| File | Purpose |
|------|---------|
| `COMPLETE_SUMMARY.md` | Complete system overview |
| `MULTITENANT_STATUS.md` | System status and setup |
| `MULTITENANT_SETUP.md` | Architecture details |
| `DASHBOARD_GUIDE.md` | Dashboard user guide |
| `DASHBOARD_VISUAL_GUIDE.md` | Visual UI reference |
| `QUICK_REFERENCE.md` | This file |

## Troubleshooting

### Server Won't Start
```powershell
# Check if port is in use
Get-NetTCPConnection -LocalPort 8001

# Kill process on port
Get-Process -Name python | Stop-Process -Force
```

### Can't Login
1. Check server is running
2. Verify credentials are correct
3. Check browser console for errors

### Database Issues
```powershell
# Check PostgreSQL service
Get-Service postgresql-x64-18

# Test database connection
psql -h localhost -U postgres -d efris_multitenant
```

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Submit login | Enter |
| Refresh browser | Ctrl+R or F5 |
| Open dev tools | F12 |

## API Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

## Quick Health Check

```powershell
# Test server is running
Invoke-WebRequest -Uri 'http://localhost:8001/health'

# Should return:
# {"status":"healthy","version":"2.0.0","database":"connected"}
```

## System Requirements

- Python 3.13
- PostgreSQL 18
- Windows 10/11
- 4GB RAM minimum
- Modern web browser

## Support

For issues:
1. Check server logs in terminal
2. Check browser console (F12)
3. Review documentation files
4. Check database connectivity

---

**Keep this card handy for quick reference!**

System Status: 🟢 ONLINE  
Last Updated: January 18, 2026
