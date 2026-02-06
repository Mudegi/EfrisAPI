# 🚀 Auto-Deployment Configuration

Your EFRIS API automatically deploys to Namecheap when you push to the `main` branch.

## ✅ Current Setup

**GitHub Actions Workflow**: `.github/workflows/deploy.yml`

```
Push to main → GitHub Actions → SSH to Namecheap → git pull → Remove tests → Install deps → Done!
```

## 🔒 What Gets Deployed

### ✅ Deployed to Production:
- All `.py` application files
- `static/` folder (dashboards, PWA)
- `requirements.txt` (production dependencies)
- `.env` (created manually on server - NOT from git!)

### ❌ Automatically Removed:
- `tests/` folder (removed after pull)
- `run_tests.ps1`, `run_tests.bat` (removed after pull)
- `pytest.ini` (removed after pull)
- `requirements-dev.txt` (removed after pull)
- `TESTING_*.md` files (removed after pull)

## 📋 Deployment Process

1. **You push code:**
   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin main
   ```

2. **GitHub Actions runs:**
   - Connects to your Namecheap server via SSH
   - Runs `git pull origin main`
   - Automatically removes test files: `rm -rf tests/`
   - Installs production dependencies: `pip3 install -r requirements.txt`

3. **Production is updated!** ✅

## 🔐 Security Notes

### ✅ Safe - Never Committed:
- `.env` file (in `.gitignore`)
- Certificate files `.p12`, `.pfx` (in `.gitignore`)
- Database files `.db` (in `.gitignore`)

### ⚠️ Create Manually on Server:
```bash
# SSH into your server
ssh nafazplp@184.94.213.244 -p 21098

# Navigate to deployment directory
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com

# Create production .env file
nano .env

# Add:
EFRIS_TIN=your_production_tin
EFRIS_DEVICE_NO=your_production_device
EFRIS_CERT_PATH=/home/nafazplp/public_html/efrisintegration.nafacademy.com/keys/production_cert.p12
EFRIS_USE_TEST_MODE=false
SECRET_KEY=your_production_secret
```

## 📦 Repository Contents

| File/Folder | In Git? | On Server? | Purpose |
|-------------|---------|------------|---------|
| `api_server.py` | ✅ | ✅ | Application |
| `static/` | ✅ | ✅ | Dashboards |
| `tests/` | ✅ | ❌ (removed) | Testing |
| `.env` | ❌ | ✅ (manual) | Secrets |
| `requirements.txt` | ✅ | ✅ | Prod deps |
| `requirements-dev.txt` | ✅ | ❌ (removed) | Dev deps |

## 🔄 Update Deployment

To change what gets deployed, edit:
`.github/workflows/deploy.yml`

Current cleanup commands:
```bash
rm -rf tests/
rm -f run_tests.ps1 run_tests.bat pytest.ini
rm -f requirements-dev.txt
rm -f TESTING_*.md
```

## 🧪 Testing Before Deploy

Always test locally before pushing:

```powershell
# Run tests
.\run_tests.ps1 unit

# Check code quality
black --check .
flake8 .

# If all tests pass, deploy:
git push origin main
```

## 📊 Deployment History

View deployment logs:
- GitHub → Your Repository → Actions → Deploy EfrisAPI

## 🆘 Rollback

If deployment breaks something:

```bash
# On server
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com
git log  # Find last working commit
git reset --hard <commit-hash>
```

Or push a fix:
```bash
# On local machine
git revert HEAD
git push origin main
```

## ✅ Deployment Checklist

Before pushing to main:

- [ ] Tests pass: `.\run_tests.ps1 unit`
- [ ] No `.env` changes committed
- [ ] No certificate files committed
- [ ] Code formatted: `black .`
- [ ] Commit message is clear
- [ ] Production `.env` is up to date on server

---

**Your current setup is secure!** 🔒

- Test files are in git for development
- They get removed automatically after deployment
- Secrets never get committed
- Production stays clean!
