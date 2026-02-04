# 🚀 DEPLOYMENT CHECKLIST

## ✅ Pre-Deployment Steps

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run Database Migration
```powershell
py migrate_to_saas.py
```

Expected output:
```
[MIGRATE] Creating new SaaS tables...
[MIGRATE] ✓ Created admin user: admin@efris.local / admin123
[MIGRATE] ✓ Migration complete!
```

### 3. Set Environment Variables
Create `.env` file:
```
# JWT Secret (Production - CHANGE THIS!)
JWT_SECRET_KEY=your-super-secret-key-min-32-chars-change-in-production

# QuickBooks (if using)
QB_CLIENT_ID=your_qb_client_id
QB_CLIENT_SECRET=your_qb_secret
QB_REDIRECT_URI=https://yourdomain.com/api/quickbooks/callback
QB_ENVIRONMENT=production

# API Settings
API_TITLE=EFRIS Integration Platform
API_VERSION=1.0.0
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost/efris_db
```

### 4. Test Server Locally
```powershell
py api_multitenant.py
```

Visit: http://localhost:8001/

## 📋 Test Checklist

- [ ] Landing page loads at `/`
- [ ] API docs accessible at `/docs`
- [ ] Can register new user at `/api/auth/register`
- [ ] Can login at `/api/auth/login`
- [ ] Can create company (with valid token)
- [ ] QuickBooks OAuth flow works
- [ ] Invoice fiscalization works
- [ ] Admin dashboard accessible

## 🌐 Production Deployment

### Option 1: Linux VPS (DigitalOcean, Linode, etc.)

1. **Setup Server**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.10 python3.10-pip -y

# Install PostgreSQL (recommended for production)
sudo apt install postgresql postgresql-contrib -y
```

2. **Deploy Code**
```bash
# Clone/upload your code
cd /var/www/
git clone your-repo-url efris-api
cd efris-api

# Install dependencies
pip3 install -r requirements.txt

# Run migration
python3 migrate_to_saas.py
```

3. **Setup Systemd Service**
Create `/etc/systemd/system/efris-api.service`:
```ini
[Unit]
Description=EFRIS Integration API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/efris-api
Environment="PATH=/usr/bin"
EnvironmentFile=/var/www/efris-api/.env
ExecStart=/usr/bin/python3 /var/www/efris-api/api_multitenant.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl start efris-api
sudo systemctl enable efris-api
sudo systemctl status efris-api
```

4. **Setup Nginx Reverse Proxy**
Create `/etc/nginx/sites-available/efris-api`:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/efris-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

5. **SSL Certificate (Let's Encrypt)**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.yourdomain.com
```

### Option 2: Heroku

1. **Create Heroku App**
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
```

2. **Create `Procfile`**
```
web: uvicorn api_multitenant:app --host 0.0.0.0 --port $PORT
release: python migrate_to_saas.py
```

3. **Deploy**
```bash
git push heroku main
heroku open
```

### Option 3: Docker

1. **Create `Dockerfile`**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python migrate_to_saas.py

EXPOSE 8001

CMD ["uvicorn", "api_multitenant:app", "--host", "0.0.0.0", "--port", "8001"]
```

2. **Create `docker-compose.yml`**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=sqlite:///efris.db
      - JWT_SECRET_KEY=change-this-in-production
    volumes:
      - ./keys:/app/keys
      - ./efris.db:/app/efris.db
```

3. **Run**
```bash
docker-compose up -d
```

## 🔒 Security Checklist

- [ ] Change admin password from default
- [ ] Set strong JWT_SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Backup database regularly
- [ ] Secure certificate files (.pfx)
- [ ] Enable firewall (only ports 80, 443)
- [ ] Regular security updates

## 💰 Payment Integration

### Add Flutterwave/Paystack
1. Get API keys from payment provider
2. Create payment endpoint:
```python
@router.post("/api/payments/initiate")
async def initiate_payment(user=Depends(get_current_user)):
    # Create payment with Flutterwave
    # Return payment URL
    pass

@router.post("/api/payments/webhook")
async def payment_webhook(data: dict):
    # Verify payment
    # Activate subscription
    pass
```

## 📊 Monitoring

### Setup Logging
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("efris_api.log"),
        logging.StreamHandler()
    ]
)
```

### Monitor with Prometheus/Grafana
- Track API response times
- Monitor invoice processing
- Alert on errors
- Track user registrations

## 🎉 Post-Deployment

1. **Test all endpoints**
2. **Create marketing materials**
3. **Set pricing** (update landing page)
4. **Launch marketing campaign**
5. **Monitor for issues**
6. **Collect user feedback**

## 📞 Support Setup

1. Create support email: support@yourdomain.com
2. Setup helpdesk (Zendesk/Freshdesk)
3. Create FAQ page
4. Add live chat widget
5. Create documentation site

---

## 🚀 You're Ready to Launch!

Your SaaS platform is production-ready. Start accepting customers! 💰
