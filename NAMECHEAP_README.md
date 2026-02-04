# EFRIS API - NameCheap Deployment Guide

## 🎯 Overview

This guide helps you deploy the **EFRIS API** (Uganda Tax Management System) to **NameCheap Shared Hosting** - perfect for beginners.

**Time to Deploy:** 1-2 hours  
**Difficulty:** Beginner to Intermediate  
**Cost:** ~$2.99-5.99/month on NameCheap  

---

## 📚 Documentation Files

Choose your reading level:

### For Complete Beginners
1. **START HERE:** [QUICK_NAMECHEAP_SETUP.md](QUICK_NAMECHEAP_SETUP.md) - 5 simple steps (30 min read)
2. Then: This file (README) for overview

### For Intermediate Users
1. [NAMECHEAP_DEPLOYMENT_GUIDE.md](NAMECHEAP_DEPLOYMENT_GUIDE.md) - Complete step-by-step guide (60 min read)
2. [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md) - Full checklist before launch

### For Advanced Users
1. [.env.production](.env.production) - Environment configuration template
2. [deployment_setup.sh](deployment_setup.sh) - Automated setup script
3. [NAMECHEAP_DEPLOYMENT_GUIDE.md](NAMECHEAP_DEPLOYMENT_GUIDE.md) - Advanced sections

---

## 🚀 Quick Start (5 Steps)

### Step 1: Prepare Your Files
```bash
# Create production folder
mkdir efris_production
cd efris_production

# Copy these files:
# - api_multitenant.py
# - api_server.py
# - efris_client.py
# - auth.py
# - email_service.py
# - main.py
# - requirements.txt
# - static/
# - keys/
```

### Step 2: Create Configuration Files
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your database credentials
# See .env.production template for help
```

### Step 3: Compress & Upload
```bash
# Compress folder
zip -r efris_production.zip efris_production/

# Upload to NameCheap cPanel → File Manager → public_html/
# Extract the zip file
```

### Step 4: Create MySQL Database
- NameCheap cPanel → MySQL Databases
- Create database: `efris_prod`
- Create user: `efris_user`
- Add user to database with all permissions

### Step 5: Install & Test
```bash
# SSH into server
ssh username@yourdomain.com

# Navigate and setup
cd public_html/efris_production
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test
python3 main.py
```

---

## 💾 What You Need

### Accounts & Access
- ✅ NameCheap hosting account (~$2.99-5.99/month)
- ✅ Domain name (can register on NameCheap)
- ✅ cPanel access credentials
- ✅ FTP/SFTP access (if not using SSH)

### Files & Keys
- ✅ Your Python application files
- ✅ EFRIS API keys (from Uganda Revenue Authority)
- ✅ SSL certificate (usually included on NameCheap)
- ✅ API secrets and passwords

### Knowledge
- ✅ Basic file management
- ✅ Understanding of environment variables
- ✅ Can copy/paste commands in terminal

---

## 🔧 System Requirements

### NameCheap Hosting Must Have:
| Feature | Required | Why |
|---------|----------|-----|
| Python 3.8+ | ✅ | Run Flask application |
| MySQL/MariaDB | ✅ | Store user data |
| SSH access | ✅ | Install dependencies |
| Email accounts | ✅ | Send notifications |
| SSL certificate | ✅ | HTTPS security |

### Recommended:
- At least 2 GB storage
- 10 GB monthly bandwidth
- CPanel access
- Daily automatic backups

---

## 📁 Folder Structure

```
public_html/
├── efris_production/
│   ├── api_multitenant.py
│   ├── api_server.py
│   ├── efris_client.py
│   ├── auth.py
│   ├── email_service.py
│   ├── main.py
│   ├── app.py
│   ├── wsgi.py
│   ├── requirements.txt
│   ├── .env (NEVER UPLOAD EXAMPLE)
│   ├── .env.production (TEMPLATE ONLY)
│   ├── .htaccess
│   ├── errors.log
│   ├── venv/ (virtual environment - auto created)
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── keys/
│   │   ├── private_key.pem
│   │   └── public_key.pem
│   └── database/
│       └── schema.sql
└── .htaccess (main routing file)
```

---

## 🔑 Key Configuration Files

### 1. `.env` - Production Environment
```bash
FLASK_ENV=production
DATABASE_URL=mysql://user:pass@localhost/db
SECRET_KEY=your-random-key
EFRIS_TIN=your-tin
```

### 2. `wsgi.py` - Application Entry Point
```python
from main import app
if __name__ == "__main__":
    app.run()
```

### 3. `.htaccess` - Web Server Routing
```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteRule ^(.*)$ /app.py/$1 [L]
</IfModule>
```

### 4. `requirements.txt` - Python Dependencies
```
flask==2.0.0
sqlalchemy==1.4.0
mysql-connector-python==8.0.0
...
```

---

## 🚨 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| 500 Internal Server Error | Check cPanel Error Log |
| Module not found | Run: `pip install -r requirements.txt` |
| Database connection failed | Verify DATABASE_URL in .env |
| Static files not loading | Check .htaccess rewrite rules |
| Emails not sending | Verify MAIL_* settings in .env |
| Permission denied | Use: `chmod 755 folder; chmod 644 file` |

---

## 🔒 Security Checklist

Before launching:
- [ ] All passwords are STRONG (16+ chars, mixed case, numbers, symbols)
- [ ] `.env` file permissions: `600` (only you can read)
- [ ] `keys/` folder permissions: `700`
- [ ] DEBUG mode is OFF (`FLASK_DEBUG=False`)
- [ ] No hardcoded secrets in code
- [ ] HTTPS/SSL enabled and working
- [ ] No test data in production database
- [ ] Backups enabled
- [ ] Error logs monitored

---

## 📊 Deployment Timeline

| Step | Time | Status |
|------|------|--------|
| Prepare files | 10 min | ⏳ |
| Create database | 5 min | ⏳ |
| Upload files | 10 min | ⏳ |
| Install dependencies | 10 min | ⏳ |
| Configuration | 10 min | ⏳ |
| Testing | 15 min | ⏳ |
| **TOTAL** | **60 min** | ⏳ |

---

## 📞 Support

### NameCheap Help
- **Live Chat:** 24/7 in cPanel
- **Email:** support@namecheap.com
- **Phone:** (669) 228-3650

### Ask Them For:
- [ ] Python version confirmation
- [ ] mod_wsgi/WSGI support
- [ ] Package installation help
- [ ] SSL certificate setup
- [ ] Database creation
- [ ] FTP/SSH access

### Your Team Help
- Refer to full [NAMECHEAP_DEPLOYMENT_GUIDE.md](NAMECHEAP_DEPLOYMENT_GUIDE.md)
- Check [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md)
- Review error logs in cPanel

---

## ✅ Success Indicators

Your deployment is successful when:

✅ Website loads: https://yourdomain.com  
✅ No "500 Internal Server Error"  
✅ Logo/CSS loads correctly (static files work)  
✅ Login page displays  
✅ Database connects (no connection errors)  
✅ Can create test user  
✅ Confirmation emails send  
✅ Browser shows lock icon (HTTPS works)  

---

## 📖 Full Documentation Index

### Getting Started
- [QUICK_NAMECHEAP_SETUP.md](QUICK_NAMECHEAP_SETUP.md) - 5 simple steps
- [NAMECHEAP_DEPLOYMENT_GUIDE.md](NAMECHEAP_DEPLOYMENT_GUIDE.md) - Complete guide (read this!)

### Before Launch
- [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md) - Full verification
- [.env.production](.env.production) - Config template

### Automation
- [deployment_setup.sh](deployment_setup.sh) - Auto-setup script
- [QUICK_START.md](QUICK_START.md) - Quick reference commands

### Architecture
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [API_ENDPOINTS_GUIDE.md](API_ENDPOINTS_GUIDE.md) - All endpoints
- [BACKEND_IMPLEMENTATION_GUIDE.md](BACKEND_IMPLEMENTATION_GUIDE.md) - Technical details

---

## 🎯 Recommended Reading Order

**For Beginners:**
1. ✅ This README (you're reading it!)
2. → [QUICK_NAMECHEAP_SETUP.md](QUICK_NAMECHEAP_SETUP.md) (5 steps overview)
3. → [NAMECHEAP_DEPLOYMENT_GUIDE.md](NAMECHEAP_DEPLOYMENT_GUIDE.md) (detailed walkthrough)
4. → [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md) (before launch)

**For Experienced Users:**
1. ✅ This README (overview)
2. → [NAMECHEAP_DEPLOYMENT_GUIDE.md](NAMECHEAP_DEPLOYMENT_GUIDE.md) (jump to relevant sections)
3. → [.env.production](.env.production) (configuration)
4. → [deployment_setup.sh](deployment_setup.sh) (automation)

---

## 🚀 Next Steps

### Now (Preparation)
1. Read [QUICK_NAMECHEAP_SETUP.md](QUICK_NAMECHEAP_SETUP.md)
2. Gather all required files
3. Create NameCheap account (if needed)
4. Register/point domain

### Today (Deployment)
1. Follow [NAMECHEAP_DEPLOYMENT_GUIDE.md](NAMECHEAP_DEPLOYMENT_GUIDE.md)
2. Upload files to cPanel
3. Configure database
4. Install Python packages
5. Test website

### Week 1 (Verification)
1. Monitor error logs daily
2. Test all main features
3. Verify emails work
4. Check performance
5. Document any issues

### Ongoing (Maintenance)
1. Daily: Check if site loads
2. Weekly: Review error logs
3. Monthly: Update packages, backup database
4. Quarterly: Security review

---

## 📝 Important Notes

### Security
- ⚠️ **NEVER** commit `.env` file to git
- ⚠️ **NEVER** share API keys or passwords
- ⚠️ **ALWAYS** use HTTPS (SSL enabled)
- ⚠️ **ALWAYS** backup before major changes

### Backup Strategy
- Automatic: NameCheap daily backups (verify in cPanel)
- Manual: Download files via FTP weekly
- Database: Export via MySQL regularly
- Keep offline copy for disaster recovery

### Performance
- Monitor disk space (keep >500MB free)
- Monitor database size
- Update packages monthly
- Clear old logs quarterly

---

## 💡 Pro Tips

1. **Test locally first:** Don't upload broken code
2. **Use virtual environment:** `python3 -m venv venv`
3. **Check error logs often:** First indicator of problems
4. **Strong passwords:** Use password manager
5. **Document changes:** Keep log of what you update
6. **Monitor resources:** Watch CPU, disk, memory
7. **Plan backups:** Schedule weekly exports
8. **Update packages:** Don't wait for emergencies

---

## 🎓 Learning Resources

| Topic | Resource |
|-------|----------|
| Flask Framework | https://flask.palletsprojects.com/ |
| SQLAlchemy ORM | https://docs.sqlalchemy.org/ |
| MySQL Basics | https://dev.mysql.com/doc/ |
| Python Best Practices | https://pep8.org/ |
| Web Security | https://owasp.org/ |

---

## 📄 File Manifest

This deployment includes:

**Configuration Files:**
- `.env.production` - Environment template
- `.env.example` - Safe example values
- `.htaccess` - Web server routing
- `requirements.txt` - Python packages

**Deployment Guides:**
- `NAMECHEAP_DEPLOYMENT_GUIDE.md` - Full guide (THIS IS MAIN ONE)
- `QUICK_NAMECHEAP_SETUP.md` - Quick 5-step version
- `PRODUCTION_DEPLOYMENT_CHECKLIST.md` - Pre-launch checklist
- `deployment_setup.sh` - Automated setup

**Application Files:**
- `main.py` - Main Flask app
- `api_multitenant.py` - Multi-tenant API
- `api_server.py` - Server configuration
- `efris_client.py` - EFRIS integration
- `auth.py` - Authentication
- `email_service.py` - Email handling

---

## 🎉 Final Notes

**You've got this!** Deploying a Python application to shared hosting is straightforward when you follow the steps. The guide is detailed so you won't get stuck.

**Common beginner worries:**
- ❌ "I'll break something" → You can always restore from backup
- ❌ "It's too technical" → No! All steps are clearly explained
- ❌ "Will it cost too much?" → NameCheap is very affordable
- ❌ "How do I support it?" → Daily monitoring takes 5 minutes

**Your journey:**
1. **Day 1:** Follow this guide step-by-step (takes 2 hours)
2. **Week 1:** Make sure everything keeps running
3. **Month 1:** Learn from running it, make improvements
4. **Ongoing:** Maintain and scale as needed

---

## 📞 Need Help?

1. **First:** Check [NAMECHEAP_DEPLOYMENT_GUIDE.md](NAMECHEAP_DEPLOYMENT_GUIDE.md) troubleshooting section
2. **Then:** Look at [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md)
3. **Finally:** Contact NameCheap support (they're helpful!)

---

## Version Info

- **Created:** February 4, 2026
- **Guide Version:** 1.0
- **Python:** 3.8+
- **Framework:** Flask 2.0+
- **Database:** MySQL 5.7+ or PostgreSQL 10+

---

**Ready to deploy? Start with [QUICK_NAMECHEAP_SETUP.md](QUICK_NAMECHEAP_SETUP.md)!** 🚀

---

**Last Updated:** February 4, 2026  
**Status:** ✅ Production Ready
