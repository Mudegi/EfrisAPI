# 🚀 EFRIS API Deployment Guide

This guide explains what to deploy to production vs what stays in development.

---

## 📦 What to Deploy to Production Server

### ✅ Application Files
```
api_server.py
efris_client.py
auth.py
email_service.py
erp_adapters.py
api_multitenant.py
api_saas.py
main.py
```

### ✅ Static Assets
```
static/
├── dashboard_multitenant.html
├── owner_portal.html
├── mobile_client.html
├── manifest.json
├── service-worker.js
├── offline.html
└── icons/
```

### ✅ Configuration Files
```
requirements.txt          # Production dependencies only
.env                      # Create on server with production credentials
```

### ✅ Database
```
efris_api.db             # Or your production database
```

---

## ❌ What NOT to Deploy (Development Only)

### 🧪 Testing Infrastructure
```
tests/                    # All test files
  ├── test_unit_core.py
  ├── test_integration_efris.py
  ├── test_load.py
  └── conftest.py
run_tests.ps1            # Test runner script
run_tests.bat            # Test runner script
pytest.ini               # pytest configuration
requirements-dev.txt     # Development dependencies
```

### 📚 Documentation (Optional)
```
TESTING_GUIDE.md
TESTING_QUICKREF.md
TESTING_IMPLEMENTATION_COMPLETE.md
MOBILE_OPTIMIZATION_GUIDE.md
ARCHITECTURE.md
... (other .md files)
```

### 🔧 Development Tools
```
.github/workflows/       # CI/CD runs on GitHub, not server
generate_pwa_icons.py
debug_*.py
analyze_*.py
check_*.py
```

---

## 🔐 Environment Variables (.env)

Create a **NEW .env file** on production server with production values:

```env
# Production Environment Variables
# DO NOT copy from development!

# EFRIS Credentials
EFRIS_TIN=your_production_tin
EFRIS_DEVICE_NO=your_production_device
EFRIS_CERT_PATH=/path/to/production/certificate.p12
EFRIS_USE_TEST_MODE=false               # IMPORTANT: false for production!

# Database
DATABASE_URL=postgresql://user:pass@localhost/efris_prod

# Security
SECRET_KEY=generate_a_strong_secret_key_here
JWT_SECRET_KEY=another_strong_secret_key

# Email (if using email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@domain.com
SMTP_PASSWORD=your_app_password

# API Keys (if using)
API_KEY_SALT=random_salt_for_api_keys

# Server
HOST=0.0.0.0
PORT=8001
```

---

## 📋 Deployment Steps

### 1⃣ Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3 python3-pip python3-venv

# Install PostgreSQL (if using)
sudo apt install postgresql postgresql-contrib
```

### 2⃣ Upload Application Files

**Option A: Git Clone (Recommended)**
```bash
# On server
git clone https://github.com/yourusername/EfrisAPI.git
cd EfrisAPI
```

**Option B: Manual Upload**
```bash
# On your computer, create deployment package
# Exclude tests, docs, and dev tools
```

### 3⃣ Install Production Dependencies ONLY

```bash
# On server
cd EfrisAPI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install ONLY production dependencies
pip install -r requirements.txt

# DO NOT install requirements-dev.txt on production!
```

### 4⃣ Configure Environment

```bash
# Create production .env file
nano .env

# Add production credentials (see example above)
# Set EFRIS_USE_TEST_MODE=false
```

### 5⃣ Upload Certificate

```bash
# Create keys directory
mkdir -p keys

# Upload your production certificate
# Upload via SFTP/SCP, NOT git!
scp /local/path/certificate.p12 user@server:/path/to/EfrisAPI/keys/
```

### 6⃣ Run Application

```bash
# Test run
python api_server.py

# Or with uvicorn (for FastAPI)
uvicorn main:app --host 0.0.0.0 --port 8001

# Production with systemd service (recommended)
sudo nano /etc/systemd/system/efris-api.service
```

**systemd service file example:**
```ini
[Unit]
Description=EFRIS API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/EfrisAPI
Environment="PATH=/path/to/EfrisAPI/venv/bin"
ExecStart=/path/to/EfrisAPI/venv/bin/python api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable efris-api
sudo systemctl start efris-api
sudo systemctl status efris-api
```

---

## 🧪 When to Use Testing Infrastructure

### Local Development
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests before committing
.\run_tests.ps1 unit
.\run_tests.ps1 coverage
```

### CI/CD (GitHub Actions)
- Automatically runs when you push to GitHub
- Runs all tests including integration tests
- No manual intervention needed

### Pre-Deployment
```bash
# Run all tests before deploying
pytest tests/ -v

# Check code quality
black --check .
flake8 .
```

---

## 📊 File Size Comparison

**Production Deployment:**
- Application files: ~5 MB
- Dependencies: ~50 MB
- **Total: ~55 MB**

**With Dev/Test Files:**
- Test files: ~5 MB
- Dev dependencies: ~100 MB additional
- Documentation: ~5 MB
- **Total: ~165 MB**

**Deploy only production files = 3x smaller deployment!**

---

## 🔒 Security Checklist

Before deploying:

- [ ] `.env` file NOT committed to git
- [ ] Production `.env` has different credentials than dev
- [ ] `EFRIS_USE_TEST_MODE=false` in production
- [ ] Certificate files NOT in git repository
- [ ] Strong `SECRET_KEY` and `JWT_SECRET_KEY` generated
- [ ] Database credentials secured
- [ ] Firewall configured (only ports 80, 443 open)
- [ ] HTTPS/SSL certificate installed
- [ ] Regular backups configured

---

## 📁 Production Directory Structure

```
/var/www/EfrisAPI/          # Or your deployment path
├── api_server.py
├── efris_client.py
├── auth.py
├── main.py
├── static/
│   ├── dashboard_multitenant.html
│   ├── owner_portal.html
│   └── mobile_client.html
├── keys/
│   └── production_cert.p12
├── .env                     # Production credentials
├── requirements.txt
├── venv/                    # Virtual environment
└── efris_api.db            # Database

# NOT included on production:
# ❌ tests/
# ❌ run_tests.ps1
# ❌ requirements-dev.txt
# ❌ *.md documentation files
# ❌ .github/
```

---

## 🔄 Update Deployment

```bash
# On server
cd EfrisAPI
git pull origin main

# Check if requirements changed
pip install -r requirements.txt

# Restart service
sudo systemctl restart efris-api
```

---

## 🆘 Troubleshooting

### Import Errors on Server
```bash
# Make sure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Certificate Not Found
```bash
# Check certificate path in .env
cat .env | grep CERT_PATH

# Verify file exists
ls -l keys/
```

### Port Already in Use
```bash
# Check what's using the port
sudo lsof -i :8001

# Kill process or use different port
```

---

## ✅ Summary

| Item | Development | Production |
|------|-------------|-----------|
| Application code | ✅ | ✅ |
| Test files | ✅ | ❌ |
| requirements.txt | ✅ | ✅ |
| requirements-dev.txt | ✅ | ❌ |
| pytest, locust | ✅ | ❌ |
| .env (with secrets) | ✅ (test creds) | ✅ (prod creds) |
| Static files | ✅ | ✅ |
| Documentation .md | ✅ | ❌ (optional) |

**Key Point**: Testing infrastructure is for **development and CI/CD only**, not production servers!

---

**Questions?** Check the README or deployment documentation.
