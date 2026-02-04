# Production Deployment Checklist
## Pre-Launch Security & Configuration

**Project:** EFRIS API  
**Host:** NameCheap Shared Hosting  
**Status:** [ ] Ready for Deployment  

---

## Phase 1: Local Preparation (Before Upload)

### Code Organization
- [ ] Created separate `efris_production` folder
- [ ] Removed all test files (`test_*.py`)
- [ ] Removed all debug files (`*_debug.py`)
- [ ] Removed development documentation
- [ ] Kept only necessary Python files

### Required Files
- [ ] `api_multitenant.py` - Main API
- [ ] `api_server.py` - Server config
- [ ] `efris_client.py` - EFRIS integration
- [ ] `auth.py` - Authentication
- [ ] `email_service.py` - Email service
- [ ] `main.py` - Application entry
- [ ] `requirements.txt` - Dependencies
- [ ] `wsgi.py` - Web server gateway
- [ ] `app.py` - Flask app wrapper
- [ ] `.htaccess` - Web server routing
- [ ] `start.sh` - Startup script

### Essential Folders
- [ ] `static/` - CSS, JS, images
- [ ] `keys/` - EFRIS encryption keys
- [ ] `database/` - Database schema
- [ ] (Optional) `templates/` - HTML templates

### Environment Files
- [ ] `.env.example` created with safe defaults
- [ ] `.env.production` created with real values
- [ ] `.env.development` for local testing
- [ ] NO passwords in example files

### Compressed Package
- [ ] All files compressed into `efris_production.zip`
- [ ] File size < 100 MB
- [ ] Can extract without errors
- [ ] Path length < 260 characters

---

## Phase 2: NameCheap Account Setup

### Hosting & Domain
- [ ] Shared hosting plan active
- [ ] Domain registered
- [ ] Domain pointing to NameCheap nameservers
- [ ] NameCheap cPanel accessible
- [ ] FTP/SFTP credentials obtained
- [ ] SSH access enabled (if available)

### cPanel Access
- [ ] Login to cPanel works
- [ ] Can access "File Manager"
- [ ] Can access "MySQL Databases"
- [ ] Can access "Error Log"
- [ ] Can access "Email Accounts"

### SSL Certificate
- [ ] SSL certificate installed (usually auto)
- [ ] HTTPS works on domain
- [ ] Certificate not expired
- [ ] Auto-renewal enabled

---

## Phase 3: Database Configuration

### MySQL Setup
- [ ] Database created: `efris_prod`
- [ ] Database user created: `efris_user`
- [ ] Strong password set for user
- [ ] User assigned to database
- [ ] ALL privileges granted to user
- [ ] Connection tested successfully

### Database Credentials
- [ ] Host: `localhost` (verified)
- [ ] Database name: `efris_prod` (or custom)
- [ ] Username: `efris_user` (or custom)
- [ ] Password: Strong (16+ characters, mixed)
- [ ] Saved securely (password manager)

### Tables & Schema
- [ ] Database schema files prepared
- [ ] Migration scripts identified
- [ ] Initial data ready to import
- [ ] Backup plan documented

---

## Phase 4: File Upload & Extraction

### Upload Process
- [ ] `efris_production.zip` uploaded to `public_html/`
- [ ] File extracted successfully
- [ ] Folder structure looks correct
- [ ] All files present and readable
- [ ] No upload corruption

### Folder Verification
- [ ] `public_html/efris_production/` exists
- [ ] All Python files are there
- [ ] `static/` folder has assets
- [ ] `keys/` folder present
- [ ] `requirements.txt` readable

### File Permissions
- [ ] Python files: `644` (rw-r--r--)
- [ ] Folders: `755` (rwxr-xr-x)
- [ ] `.env` file: `600` (rw------) **CRITICAL**
- [ ] `keys/` folder: `700` (rwx------)
- [ ] `start.sh`: `755` (rwxr-xr-x)
- [ ] `errors.log`: `644` (rw-r--r--)

---

## Phase 5: Configuration & Installation

### Environment Configuration
- [ ] `.env` file created in app root
- [ ] `DATABASE_URL` set correctly
- [ ] `FLASK_ENV=production`
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` generated and set
- [ ] All API keys entered
- [ ] All email settings configured
- [ ] `.env` file permissions: `600`

### Python Environment
- [ ] Python 3.8+ installed on server
- [ ] Virtual environment created: `venv/`
- [ ] Activated: `source venv/bin/activate`
- [ ] pip upgraded
- [ ] `requirements.txt` installed completely
- [ ] No package installation errors
- [ ] `gunicorn` installed for production

### Verification
- [ ] `python3 --version` shows 3.8+
- [ ] `pip list` shows all packages
- [ ] No missing dependencies
- [ ] No conflicting package versions

---

## Phase 6: Web Server Configuration

### .htaccess Setup
- [ ] `.htaccess` file created in `public_html/`
- [ ] Rewrite rules correct
- [ ] Static file exclusions present
- [ ] HTTPS redirect enabled
- [ ] Directory listing disabled
- [ ] Compression enabled (optional)

### Application Entry Point
- [ ] `wsgi.py` configured correctly
- [ ] `app.py` wrapper created
- [ ] Entry point references correct
- [ ] Application imports work
- [ ] No import errors on startup

### Server Configuration
- [ ] mod_wsgi enabled (request from NameCheap if needed)
- [ ] mod_rewrite enabled
- [ ] mod_gzip enabled (optional)
- [ ] Custom Python version (if available)

---

## Phase 7: Application Testing

### Startup Test
- [ ] Application starts without errors
- [ ] No Python syntax errors
- [ ] No module import errors
- [ ] No database connection errors
- [ ] Listens on correct port

### Endpoint Testing
- [ ] GET `/` returns homepage
- [ ] GET `/api/health` returns status
- [ ] API endpoints respond
- [ ] Static files load correctly
- [ ] 404 errors handled properly

### Database Testing
- [ ] Database connection successful
- [ ] Tables created/migrated
- [ ] Can read from database
- [ ] Can write to database
- [ ] Queries execute without errors

### Security Testing
- [ ] HTTPS enforced
- [ ] HTTP redirects to HTTPS
- [ ] `.env` not accessible via web
- [ ] `keys/` folder not accessible
- [ ] Directory listing disabled

---

## Phase 8: Error & Log Management

### Error Logging
- [ ] Error log file created
- [ ] Error logging configured
- [ ] Check cPanel "Error Log" regularly
- [ ] Python errors logged properly
- [ ] Database errors captured

### Log Monitoring
- [ ] View cPanel Error Log frequently
- [ ] Check `errors.log` file daily
- [ ] Subscribe to error notifications (if available)
- [ ] Set up log rotation (prevents disk space issues)

### Performance Monitoring
- [ ] Application response time acceptable
- [ ] No timeout errors
- [ ] CPU usage normal
- [ ] Memory usage normal
- [ ] Disk space adequate (>500MB free)

---

## Phase 9: Email & Notifications

### Email Configuration
- [ ] Email account created in cPanel
- [ ] MAIL_SERVER configured (usually mail.yourdomain.com)
- [ ] MAIL_USERNAME correct
- [ ] MAIL_PASSWORD set
- [ ] MAIL_PORT correct (usually 465 or 587)
- [ ] SSL/TLS enabled
- [ ] Test email sends successfully

### Email Testing
- [ ] Test email sent from application
- [ ] Email received in inbox
- [ ] Email formatting correct
- [ ] No email sending errors
- [ ] Sender address correct

---

## Phase 10: Backup & Recovery

### Backup Configuration
- [ ] NameCheap automatic backups enabled
- [ ] Backup frequency verified (daily recommended)
- [ ] Can restore from backup
- [ ] Manual backup created before launch

### Backup Strategy
- [ ] Database backup created
- [ ] Files backup created
- [ ] Configuration backup created
- [ ] Backups stored securely
- [ ] Test restoration procedure

---

## Phase 11: Security Hardening

### File Security
- [ ] Sensitive files not in public_html
- [ ] `.env` file protected (600 permissions)
- [ ] `keys/` folder protected (700 permissions)
- [ ] No debug files in production
- [ ] `.git` folder removed or protected

### Application Security
- [ ] DEBUG mode OFF
- [ ] All input validated
- [ ] SQL injection prevention enabled
- [ ] CSRF protection enabled
- [ ] XSS prevention enabled
- [ ] Security headers added

### Access Control
- [ ] Strong database password
- [ ] Strong admin password
- [ ] API keys protected
- [ ] SSH keys (if using) secured
- [ ] FTP account secured or disabled

### SSL/HTTPS
- [ ] SSL certificate installed
- [ ] HTTPS working
- [ ] HTTP redirects to HTTPS
- [ ] Certificate valid and not expired
- [ ] Auto-renewal enabled

---

## Phase 12: Monitoring & Maintenance

### Daily Checks
- [ ] Check if website loads
- [ ] Check error log for issues
- [ ] Verify database responds
- [ ] Check email functionality
- [ ] Monitor disk space

### Weekly Tasks
- [ ] Review error logs
- [ ] Check server resources
- [ ] Verify backups completed
- [ ] Test critical features
- [ ] Monitor user activity

### Monthly Tasks
- [ ] Update Python packages
- [ ] Optimize database
- [ ] Review security logs
- [ ] Test recovery procedure
- [ ] Update documentation

---

## Phase 13: Launch Readiness

### Final Security Audit
- [ ] No test data in production
- [ ] No debug information visible
- [ ] No hardcoded passwords
- [ ] All secrets in `.env`
- [ ] `.env` not committed to git
- [ ] `.gitignore` properly configured

### Final Functionality Check
- [ ] All core features working
- [ ] All API endpoints tested
- [ ] All forms submit correctly
- [ ] All payments process (if applicable)
- [ ] All notifications send

### Final Performance Check
- [ ] Page load time acceptable (<3 seconds)
- [ ] API response time acceptable (<1 second)
- [ ] No memory leaks
- [ ] No database slowness
- [ ] CPU usage reasonable

---

## Launch Decision Matrix

| Check | Status | Issue? | Resolved? |
|-------|--------|--------|-----------|
| All code uploaded | ✓ | [ ] | [ ] |
| Database configured | ✓ | [ ] | [ ] |
| Environment set | ✓ | [ ] | [ ] |
| Website loads | ✓ | [ ] | [ ] |
| API endpoints work | ✓ | [ ] | [ ] |
| Database connects | ✓ | [ ] | [ ] |
| Security hardened | ✓ | [ ] | [ ] |
| Backups working | ✓ | [ ] | [ ] |
| SSL/HTTPS enabled | ✓ | [ ] | [ ] |
| Monitoring ready | ✓ | [ ] | [ ] |

**DECISION:**
- [ ] **GO** - All checks passed, ready to launch
- [ ] **NO-GO** - Issues remain, not ready

---

## Post-Launch Checklist (Day 1)

- [ ] Announce website to users
- [ ] Monitor error log (every 30 minutes)
- [ ] Monitor server resources (every hour)
- [ ] Test with real users
- [ ] Gather user feedback
- [ ] Document any issues found
- [ ] Stand by for emergency fixes

---

## Contact Information

### NameCheap Support
- **Email:** support@namecheap.com
- **Phone:** (669) 228-3650
- **Live Chat:** https://www.namecheap.com/support/
- **Status Page:** https://www.namecheapstatus.com/

### Admin Credentials
- **Domain:** _______________
- **cPanel Username:** _______________
- **FTP Username:** _______________
- **Database Name:** _______________
- **Database User:** _______________

**STORE THESE SECURELY - NOT IN CODE!**

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | _________ | ___/___/___ | _________ |
| Tester | _________ | ___/___/___ | _________ |
| Manager | _________ | ___/___/___ | _________ |

---

## Notes & Issues Log

### Issue #1
- **Date:** __________
- **Issue:** ______________________________________
- **Status:** [ ] Open [ ] Resolved
- **Resolution:** _________________________________

### Issue #2
- **Date:** __________
- **Issue:** ______________________________________
- **Status:** [ ] Open [ ] Resolved
- **Resolution:** _________________________________

---

**FINAL STATUS:** [ ] Production Ready ✅

**Date Deployed:** _____________________  
**Version:** _____________________  
**Team:** _____________________

---

Remember: A thorough checklist prevents emergencies! ✓
