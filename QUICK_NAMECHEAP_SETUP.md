# Quick Setup for NameCheap - 5 Steps for Beginners

**Time:** 30 minutes overview  
**Level:** Complete beginner  
**Goal:** Understand the deployment process

---

## Step 1: What You Have (10 minutes)

### Your Application
This is a **Python Flask Web Application** that:
- Manages invoices (EFRIS integration)
- Handles user accounts
- Stores data in MySQL database
- Sends emails
- Processes payments

### What NameCheap Provides
- **Web hosting** - Where your app runs
- **Domain** - Your website address
- **MySQL database** - Where data is stored
- **Email** - Send customer notifications
- **SSL certificate** - Security (HTTPS)

### What You Need
1. **NameCheap account** - Get one for ~$2.99/month
2. **Domain name** - Like yourcompany.com
3. **Your files** - Your Python application
4. **API keys** - From EFRIS (for Uganda tax system)

---

## Step 2: Upload Your Code (10 minutes)

### Simple Method
1. **Prepare files:**
   ```
   Copy these files to a folder:
   - api_multitenant.py
   - api_server.py  
   - efris_client.py
   - auth.py
   - email_service.py
   - main.py
   - requirements.txt
   - static/ (folder with CSS, JS, images)
   - keys/ (folder with EFRIS keys)
   ```

2. **Create .env file:**
   ```
   Copy .env.example and fill with your values:
   DATABASE_URL=mysql://user:password@localhost/database
   FLASK_ENV=production
   SECRET_KEY=(run: python -c "import secrets; print(secrets.token_hex(32))")
   EFRIS_TIN=your_tin_number
   ```

3. **Create wsgi.py:**
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.dirname(__file__))
   from main import app
   if __name__ == "__main__":
       app.run()
   ```

4. **Create .htaccess:**
   ```apache
   <IfModule mod_rewrite.c>
       RewriteEngine On
       RewriteBase /
       RewriteCond %{REQUEST_FILENAME} !-f
       RewriteCond %{REQUEST_FILENAME} !-d
       RewriteRule ^(.*)$ /app.py/$1 [L]
   </IfModule>
   ```

5. **Zip everything into `efris_production.zip`**

6. **Upload to NameCheap:**
   - Log into cPanel
   - Go to File Manager
   - Click public_html folder
   - Upload zip file
   - Extract it

---

## Step 3: Setup Database (5 minutes)

### In cPanel:
1. Find "MySQL Databases"
2. Create new database: `efris_prod`
3. Create new user: `efris_user`
4. Set password (STRONG!)
5. Add user to database
6. Give all permissions

### Save these:
```
Host: localhost
Database: efris_prod
User: efris_user  
Password: YourStrongPassword123!
```

### Update .env with these values:
```
DATABASE_URL=mysql+pymysql://efris_user:YourStrongPassword123!@localhost/efris_prod
```

---

## Step 4: Install Python Packages (5 minutes)

### Using cPanel Terminal:
```bash
cd public_html/efris_production
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn pymysql
```

### If no terminal access:
- Email NameCheap support
- Ask them to install requirements.txt
- Should take 1 hour for them to do it

---

## Step 5: Test It Works (5 minutes)

### Simple test:
1. Visit: https://yourdomain.com
2. Should see your website
3. Should not see errors

### Check errors:
1. Go to cPanel
2. Click "Error Log"
3. Look for red errors
4. Fix any issues

### Test database:
1. Add this to main.py:
   ```python
   @app.route('/test-db')
   def test_db():
       return "Database works!"
   ```
2. Visit: https://yourdomain.com/test-db
3. Should show "Database works!"

---

## Common Issues & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| "500 Error" | Code error | Check cPanel Error Log |
| "Module not found" | Missing package | Run: pip install -r requirements.txt |
| "Database error" | Wrong credentials | Check .env file |
| "Static files missing" | Wrong path | Update .htaccess |
| "Won't load" | File permissions | Change to 755 for folders, 644 for files |

---

## After Launching

### First day:
- ✓ Check website loads
- ✓ Check for errors
- ✓ Test one user action
- ✓ Check emails send

### Every day:
- ✓ Glance at Error Log
- ✓ Check disk space
- ✓ Make sure website works

### Every month:
- ✓ Update Python packages
- ✓ Backup database
- ✓ Check server health

---

## Key Passwords to Save

```
Website Domain: ________________
NameCheap cPanel Username: ________________
cPanel Password: ________________
MySQL Username: efris_user
MySQL Password: ________________
Admin Email: ________________
API Key: ________________
```

**STORE IN SECURE LOCATION! Not in code!**

---

## Need Help?

### Quick Fixes
- Website not loading? → Check cPanel Error Log
- Database not working? → Test connection in .env
- Missing Python files? → Re-upload from zip
- File permissions wrong? → Set to 755/644

### Contact NameCheap
- Live chat (24/7): In cPanel panel bottom right
- Email: support@namecheap.com
- Ask about: Python version, mod_wsgi setup

### Documentation
- See: `NAMECHEAP_DEPLOYMENT_GUIDE.md` (complete guide)
- See: `PRODUCTION_DEPLOYMENT_CHECKLIST.md` (full checklist)

---

## Success Looks Like

✅ Website loads at https://yourdomain.com  
✅ No "500 Internal Server Error"  
✅ Login works  
✅ Database saves data  
✅ Emails send  
✅ Secure (has lock icon)  

---

## Summary

| Step | Time | What to do |
|------|------|-----------|
| 1 | Prep files | Gather your Python files + create .env |
| 2 | Upload | Zip and upload to cPanel public_html |
| 3 | Database | Create MySQL database in cPanel |
| 4 | Install | Run pip install on server |
| 5 | Test | Visit your domain and check it works |

**Total Time: 30-60 minutes**

**Then:** Website is LIVE! 🎉

---

## Next Level (Optional)

Once you're comfortable with basics:
- [ ] Setup automated backups
- [ ] Monitor performance
- [ ] Update packages regularly
- [ ] Scale to larger plan if needed

---

**Remember:** As a beginner, it's OK to ask NameCheap support for help!  
They handle thousands of deployments - they know the answers.

Good luck! 🚀
