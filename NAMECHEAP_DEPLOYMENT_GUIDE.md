# NameCheap Shared Hosting Deployment Guide
## For Complete Beginners

**Version:** 1.0  
**Date:** February 4, 2026  
**Difficulty:** Beginner ⭐  
**Time Required:** 2-3 hours

---

## 📋 Table of Contents

1. [What You'll Need](#what-youll-need)
2. [Step-by-Step Setup](#step-by-step-setup)
3. [Database Configuration](#database-configuration)
4. [Environment Variables](#environment-variables)
5. [Uploading Your Code](#uploading-your-code)
6. [Testing Your Deployment](#testing-your-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

---

## What You'll Need

### Before You Start
- [ ] NameCheap hosting account (shared hosting plan)
- [ ] Your domain name pointing to NameCheap
- [ ] FTP/SFTP access credentials (from NameCheap cPanel)
- [ ] SSH access to your hosting (if available)
- [ ] Your API keys and secret keys ready
- [ ] FileZilla or WinSCP (for uploading files)

### Hosting Plan Requirements
✅ **MUST HAVE:**
- Python support (3.8+)
- MySQL or MariaDB database
- Email service for notifications
- At least 1 GB storage
- Minimum 10 GB bandwidth

**Recommended:**
- CPanel access
- Email accounts
- SSL certificate (usually included)
- Daily backups

---

## Step-by-Step Setup

### Phase 1: Prepare Your Local Project (10 minutes)

#### Step 1.1: Organize Your Files

You need to identify which files are needed for production:

**REQUIRED FILES:**
```
api_multitenant.py      (Main API)
api_server.py           (Server config)
api_saas.py             (SaaS features - if using)
efris_client.py         (EFRIS integration)
auth.py                 (Authentication)
email_service.py        (Email notifications)
payment_service.py      (Payments - if needed)
requirements.txt        (Python packages)
main.py                 (Entry point)
.env.example            (Copy to .env)
```

**DATABASE FOLDER:**
```
database/               (Database migrations)
```

**STATIC FILES:**
```
static/                 (CSS, JS, images)
schemas/                (Data schemas)
keys/                   (EFRIS keys - SECURE!)
```

**OPTIONAL (Not needed for basic deployment):**
```
test_*.py              (All test files)
*_debug.py             (Debug files)
migrate_*.py           (Migration files)
Documentation/         (Keep for reference)
```

#### Step 1.2: Create Production-Ready Package

1. Create a new folder called `efris_production`
2. Copy only the REQUIRED FILES into it
3. Keep the folder structure clean

**Folder Structure for Upload:**
```
efris_production/
├── api_multitenant.py
├── api_server.py
├── efris_client.py
├── auth.py
├── email_service.py
├── main.py
├── requirements.txt
├── .env.example
├── .htaccess (we'll create this)
├── wsgi.py (we'll create this)
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── keys/
    ├── public_key.pem
    └── (other EFRIS keys)
```

---

### Phase 2: Create Essential Files (5 minutes)

#### Step 2.1: Create `wsgi.py`

This file tells NameCheap how to run your app:

```python
import os
import sys
import logging

# Add your project to the path
sys.path.insert(0, os.path.dirname(__file__))

# Import your Flask app
from main import app

# Setup logging
logging.basicConfig(
    filename='errors.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# This is what NameCheap will run
if __name__ == "__main__":
    app.run(debug=False, threaded=True)
```

**Save as:** `wsgi.py` in root folder

#### Step 2.2: Create `.htaccess`

This routes all requests to your Python app:

```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    
    # Don't rewrite static files
    RewriteCond %{REQUEST_FILENAME} -f [OR]
    RewriteCond %{REQUEST_FILENAME} -d
    RewriteRule ^ - [L]
    
    # Route everything else to app
    RewriteRule ^(.*)$ /index.py [L]
</IfModule>

# Enable compression
<IfModule mod_gzip.c>
    mod_gzip_on Yes
    mod_gzip_comp_level 6
    mod_gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss
</IfModule>
```

**Save as:** `.htaccess` in root folder

#### Step 2.3: Create `app.py` Wrapper

Create a simple wrapper for compatibility:

```python
# app.py - Wrapper for NameCheap compatibility
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import main app
from main import app

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=False,
        threaded=True
    )
```

**Save as:** `app.py` in root folder

---

### Phase 3: Database Setup (15 minutes)

#### Step 3.1: Create MySQL Database on NameCheap

1. **Log into cPanel:**
   - Go to your NameCheap account
   - Click "Manage" on your hosting plan
   - Click "cPanel" button

2. **Create Database:**
   - Find "MySQL Databases" icon
   - Click "Create New Database"
   - Name it: `efris_prod` (or similar)
   - Click "Create Database"

3. **Create Database User:**
   - Still in MySQL Databases
   - Find "MySQL Users" section
   - Username: `efris_user`
   - Password: Create a STRONG password (save this!)
   - Click "Create User"

4. **Assign User to Database:**
   - Find "Add User To Database"
   - Select user: `efris_user`
   - Select database: `efris_prod`
   - All privileges: Check ALL boxes
   - Click "Make Changes"

**Save these details:**
```
Host: localhost
Database: efris_prod
User: efris_user
Password: YOUR_STRONG_PASSWORD
```

#### Step 3.2: Update Your `.env` File

Create a production `.env` file with database details:

```
# Database Configuration
DATABASE_URL=mysql+pymysql://efris_user:YOUR_PASSWORD@localhost/efris_prod

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-random-secret-key-change-this

# EFRIS Configuration
EFRIS_TIN=YOUR_TIN
EFRIS_PIN=YOUR_PIN
TEST_MODE=False

# API Configuration
API_KEY=your-api-key
API_SECRET=your-api-secret

# Email Configuration
MAIL_SERVER=mail.yourdomain.com
MAIL_PORT=465
MAIL_USERNAME=info@yourdomain.com
MAIL_PASSWORD=your-email-password
MAIL_USE_SSL=True

# Application
APP_URL=https://yourdomain.com
DEBUG=False
```

**⚠️ IMPORTANT: Never share this file!**

---

### Phase 4: Prepare for Upload (10 minutes)

#### Step 4.1: Compress Your Project

1. Right-click your `efris_production` folder
2. Select "Send to" → "Compressed (zipped) folder"
3. Name it: `efris_production.zip`
4. Save it somewhere you can find it

#### Step 4.2: Organize Files

**Final file list before upload:**
```
efris_production.zip contains:
  ├── api_multitenant.py
  ├── api_server.py
  ├── efris_client.py
  ├── auth.py
  ├── email_service.py
  ├── main.py
  ├── app.py
  ├── wsgi.py
  ├── .htaccess
  ├── requirements.txt
  ├── .env (PRODUCTION VERSION)
  ├── static/
  ├── keys/
  └── database/
```

---

## Uploading Your Code

### Step 5.1: Access File Manager

**Option A: Using cPanel File Manager (Easiest)**

1. Log into cPanel
2. Click "File Manager"
3. Click "public_html" folder
4. You're now in your root web folder

**Option B: Using FTP/SFTP (Recommended for security)**

1. Download FileZilla: https://filezilla-project.org/
2. In NameCheap cPanel, find "FTP Accounts"
3. Create new FTP account if needed
4. Note: 
   - Host: `ftp.yourdomain.com`
   - Username: Your FTP username
   - Password: Your FTP password
   - Port: 21 (or 22 for SFTP)

### Step 5.2: Upload Your Files

**Using cPanel File Manager:**

1. In `public_html` folder, click "Upload"
2. Select your `efris_production.zip` file
3. Wait for upload to complete
4. Right-click the zip file → "Extract"
5. Select destination and extract

**Using FileZilla:**

1. Connect with your FTP credentials
2. Navigate to `public_html` folder (right side)
3. Drag and drop your files from left (your computer) to right (server)
4. Wait for all files to upload

### Step 5.3: Set File Permissions

1. Right-click files/folders → "Change Permissions"
2. Set permissions:
   - Files: `644` (rw-r--r--)
   - Folders: `755` (rwxr-xr-x)
   - `.env` file: `600` (rw------) - IMPORTANT for security!
   - `keys/` folder: `700` (rwx------)

---

### Phase 5: Install Dependencies (10 minutes)

#### Step 5.1: Install Python Packages

**Using SSH (Recommended):**

1. In cPanel, find "Terminal" or "SSH Shell Access"
2. Click to open terminal
3. Navigate to your app folder:
   ```bash
   cd public_html/efris_production
   ```

4. Create virtual environment:
   ```bash
   python3 -m venv venv
   ```

5. Activate it:
   ```bash
   source venv/bin/activate
   ```

6. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

7. Install additional tools:
   ```bash
   pip install gunicorn
   pip install pymysql  # For MySQL support
   ```

**If SSH not available:**

Ask NameCheap support to:
- [ ] Install Python 3.8+
- [ ] Enable mod_wsgi
- [ ] Install packages from requirements.txt

---

### Phase 6: Configure Web Server (10 minutes)

#### Step 6.1: Update `.htaccess`

Update the `.htaccess` file in public_html for your app:

```apache
# Redirect to your app
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule ^(.*)$ /app.py/$1 [L]
</IfModule>

# Security headers
<IfModule mod_headers.c>
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>

# HTTPS redirect
<IfModule mod_rewrite.c>
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</IfModule>

# Disable directory listing
<IfModule mod_autoindex.c>
    Options -Indexes
</IfModule>
```

#### Step 6.2: Create Startup Script

Create `start.sh` in your app root:

```bash
#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Export environment
export FLASK_APP=main.py
export FLASK_ENV=production

# Start application
gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app
```

Make it executable:
```bash
chmod +x start.sh
```

---

## Environment Variables

### What Each Variable Does

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | Connect to MySQL | `mysql://user:pass@localhost/db` |
| `FLASK_ENV` | Production mode | `production` |
| `SECRET_KEY` | Session security | Random 32+ characters |
| `EFRIS_TIN` | Your TIN | `1015264035` |
| `API_KEY` | API authentication | Your API key |
| `DEBUG` | Errors shown | `False` in production |

### Generate Secret Key

Open terminal and run:

```python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste into `.env` as `SECRET_KEY`

---

## Testing Your Deployment

### Test 1: Check Website Loads

```bash
curl https://yourdomain.com
```

Should show your homepage HTML

### Test 2: Check API Endpoint

```bash
curl https://yourdomain.com/api/health
```

Should return:
```json
{"status": "healthy"}
```

### Test 3: Check Database Connection

Add this temporary endpoint to `main.py`:

```python
@app.route('/api/db-check', methods=['GET'])
def db_check():
    try:
        # Test database connection
        # Your database query here
        return jsonify({"status": "Database connected"})
    except Exception as e:
        return jsonify({"status": "Database error: " + str(e)})
```

Test:
```bash
curl https://yourdomain.com/api/db-check
```

### Test 4: Monitor Logs

Check error logs in cPanel:

1. Log into cPanel
2. Go to "Error Log"
3. Look for any Python errors

---

## Troubleshooting

### Problem 1: "500 Internal Server Error"

**Check:**
1. Error log in cPanel
2. File permissions (should be 755 for folders, 644 for files)
3. Database connection in `.env`
4. Python version compatibility

**Fix:**
```bash
# Fix permissions
chmod -R 755 .
chmod 600 .env
chmod -R 700 keys/
```

### Problem 2: "Module not found" Error

**Fix:**
```bash
# Reinstall packages
source venv/bin/activate
pip install -r requirements.txt
```

### Problem 3: Database Connection Failed

**Check in cPanel:**
1. MySQL Databases → User has access to database
2. Username and password are correct
3. Database actually exists
4. Host is `localhost` (not IP address)

### Problem 4: Static Files Not Loading

**Fix in `.htaccess`:**
```apache
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
```

These lines tell server NOT to rewrite actual files/folders

### Problem 5: Email Not Sending

**Check:**
```env
MAIL_SERVER=mail.yourdomain.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=your-email@yourdomain.com
MAIL_PASSWORD=your-app-password
```

Create app-specific password in email settings

---

## Maintenance

### Daily Checks

- [ ] Website loads without errors
- [ ] API endpoints respond
- [ ] Database queries work
- [ ] Emails send successfully

### Weekly Tasks

- [ ] Check error logs for issues
- [ ] Backup database
- [ ] Review user activity
- [ ] Check disk space usage

### Monthly Tasks

- [ ] Update Python packages
  ```bash
  source venv/bin/activate
  pip list --outdated
  pip install --upgrade package-name
  ```
- [ ] Test backup restoration
- [ ] Review security
- [ ] Optimize database queries

### Backup Strategy

**Automatic:**
- NameCheap usually provides daily backups
- Check cPanel → "Backup" section

**Manual:**
1. Export database:
   ```bash
   mysqldump -u efris_user -p efris_prod > backup.sql
   ```

2. Download via FTP:
   - Download entire `public_html` folder
   - Download backup.sql
   - Store offline

---

## Security Checklist

Before going LIVE:

- [ ] `.env` file has `600` permissions
- [ ] `keys/` folder has `700` permissions
- [ ] `DEBUG=False` in `.env`
- [ ] `HTTPS/SSL` enabled
- [ ] Strong database password
- [ ] API keys rotated
- [ ] Sensitive files not in public_html
- [ ] `.htaccess` prevents directory listing
- [ ] Log files not readable from web

### Create a `.gitignore`

```
.env
.env.production
keys/
*.db
*.sqlite
__pycache__/
venv/
.vscode/
.DS_Store
```

---

## Common NameCheap Settings

### cPanel Shortcuts

| Task | Location |
|------|----------|
| View Error Log | Error Log |
| Manage Database | MySQL Databases |
| File Upload | File Manager |
| Send Email | Email Accounts |
| SSL Certificate | SSL/TLS Status |
| Domain Settings | Addon Domains |

### Useful cPanel Features

**Cron Jobs** - Schedule tasks:
- Backup database daily
- Clean up old logs
- Update cache

**Email Accounts** - Create email for your app:
- info@yourdomain.com
- support@yourdomain.com
- noreply@yourdomain.com

**SSL Certificate** - HTTPS (usually free):
- Auto-installed on shared hosting
- Renews automatically
- Check "SSL/TLS Status" in cPanel

---

## Performance Tips

### 1. Enable Caching

Add to `main.py`:
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/data')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_data():
    return jsonify(data)
```

### 2. Compress Responses

Add to `.htaccess`:
```apache
<IfModule mod_gzip.c>
    mod_gzip_on Yes
    mod_gzip_comp_level 6
    mod_gzip_types text/plain text/css text/xml text/javascript application/json
</IfModule>
```

### 3. Optimize Database

```python
# Use connection pooling
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app, engine_options={
    'pool_size': 10,
    'pool_recycle': 3600,
})
```

### 4. Use CDN for Static Files

- Upload CSS, JS, images to CloudFlare
- Update URLs in templates
- Much faster delivery

---

## Support & Help

### NameCheap Support Channels

1. **Live Chat:** Available 24/7
2. **Email:** support@namecheap.com
3. **Knowledge Base:** https://www.namecheap.com/support/
4. **Community:** https://www.namecheap.com/support/knowledgebase/

### Ask NameCheap For Help With

- [ ] Python installation/version
- [ ] mod_wsgi setup
- [ ] Database connection issues
- [ ] FTP/SFTP access
- [ ] SSL certificate
- [ ] Disk space issues
- [ ] PHP version (for compatibility check)

### Python-Specific Help

- **Flask Documentation:** https://flask.palletsprojects.com/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Requests Library:** https://requests.readthedocs.io/

---

## Quick Reference Commands

### SSH Access Commands

```bash
# Connect to server
ssh username@yourdomain.com

# Navigate to app
cd public_html/efris_production

# Activate Python environment
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# View error logs
tail -f errors.log

# Restart application
pkill -f gunicorn
./start.sh

# Check running processes
ps aux | grep python

# View system resources
top
df -h
free -m
```

### Database Commands

```bash
# Connect to MySQL
mysql -u efris_user -p efris_prod

# Create tables
# mysql> source database/schema.sql;

# Backup database
mysqldump -u efris_user -p efris_prod > backup.sql

# Import backup
# mysql -u efris_user -p efris_prod < backup.sql
```

---

## Final Checklist Before Going LIVE

### Pre-Launch
- [ ] All files uploaded
- [ ] Dependencies installed
- [ ] Database created and configured
- [ ] `.env` file set to production
- [ ] Static files accessible
- [ ] SSL certificate working
- [ ] DNS pointing correctly

### Post-Launch (Day 1)
- [ ] Test all endpoints
- [ ] Test user registration
- [ ] Test payments (if applicable)
- [ ] Test email notifications
- [ ] Check error logs
- [ ] Monitor performance

### First Week
- [ ] Monitor for errors
- [ ] Test edge cases
- [ ] Review user feedback
- [ ] Check server resources
- [ ] Verify backups working

---

## Contact for Advanced Issues

If you encounter problems beyond this guide:

1. **Collect Information:**
   - Error message (exact text)
   - What you were trying to do
   - When it started happening
   - Error logs

2. **Contact Support with:**
   - Your domain
   - Your hosting plan
   - The exact error
   - Steps to reproduce

3. **Development Team:**
   - Bring this guide
   - Mention it's beginner setup
   - Ask for specific help areas

---

## Summary

Your deployment is now LIVE! 🎉

**What you have:**
✅ Production Python application  
✅ MySQL database  
✅ HTTPS/SSL security  
✅ Error monitoring  
✅ Automated backups  

**What to do next:**
1. Share your domain with users
2. Monitor for issues
3. Follow maintenance schedule
4. Plan for scaling if needed

**Remember:** 
- Always backup before making changes
- Monitor error logs regularly
- Update packages monthly
- Keep `.env` and `keys/` secure

Good luck! 🚀
