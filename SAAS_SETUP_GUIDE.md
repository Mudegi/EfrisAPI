# 🚀 EFRIS SaaS Platform - Setup Guide

## What Changed?

Your EFRIS API is now a **multi-tenant SaaS platform**! Users can:
- ✅ Register and create accounts
- ✅ Manage multiple companies (clients)
- ✅ Use different ERP systems (QuickBooks, Xero, Zoho, Custom API)
- ✅ Annual subscription model
- ✅ Track usage and billing

## Quick Setup (5 Steps)

### 1. Install New Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run Migration (IMPORTANT - Do this once!)
```powershell
py migrate_to_saas.py
```

This will:
- Create user accounts table
- Create subscriptions table
- Create admin user: `admin@efris.local` / `admin123`
- Link existing companies to admin

### 3. Update Main API Server

Replace your `api_multitenant.py` import at the top:

```python
# Add this import
from api_saas import router as saas_router

# Add this route
app.include_router(saas_router)
```

### 4. Set Environment Variable (Production Security)
```powershell
$env:JWT_SECRET_KEY="your-super-secret-key-min-32-chars-long-change-this"
```

### 5. Start Server
```powershell
py api_multitenant.py
```

## 📋 New API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (returns JWT token)
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/subscription` - Check subscription status

### Company Management
- `POST /api/companies` - Create company (requires auth)
- `GET /api/companies` - List user's companies
- `GET /api/companies/{id}` - Get company details
- `DELETE /api/companies/{id}` - Delete company

### Public Demo Endpoints
- `GET /api/public/efris/test` - Test EFRIS connectivity
- `GET /api/public/efris/query/{fdn}` - Query invoice by FDN

## 🔐 How Authentication Works

1. **User registers** → Gets 30-day trial (2 companies max)
2. **User logs in** → Receives JWT token
3. **All requests** → Include token in header:
   ```
   Authorization: Bearer {token}
   ```

## 💰 Subscription Model

### Trial Plan (Free - 30 days)
- 2 companies max
- All features enabled
- Auto-expires after 30 days

### Annual Plan (After Payment)
- 5+ companies (configurable)
- Unlimited invoices
- 1 year validity

## 🎯 How to Test

### 1. Register a User
```bash
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "full_name": "Test User",
    "phone": "+256700000000"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {...}
}
```

### 3. Create Company (with token)
```bash
curl -X POST http://localhost:8001/api/companies \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "My Business Ltd",
    "tin": "1014409555",
    "device_no": "1014409555_01",
    "erp_type": "quickbooks",
    "qb_region": "UK"
  }'
```

## 🔧 ERP Configuration

### QuickBooks
```json
{
  "company_name": "Business Name",
  "tin": "1014409555",
  "device_no": "1014409555_01",
  "erp_type": "quickbooks",
  "erp_config": "{\"oauth_tokens\": \"from_qb_auth\"}",
  "qb_region": "UK"
}
```

### Custom API
```json
{
  "company_name": "Business Name",
  "tin": "1014409555",
  "device_no": "1014409555_01",
  "erp_type": "custom",
  "erp_config": "{\"api_key\": \"your_key\", \"webhook_url\": \"...\"}"
}
```

### Xero / Zoho (Coming Soon)
```json
{
  "company_name": "Business Name",
  "tin": "1014409555",
  "device_no": "1014409555_01",
  "erp_type": "xero",
  "erp_config": "{\"client_id\": \"...\", \"client_secret\": \"...\"}"
}
```

## 📊 Database Schema

```
Users
├── Subscription (1:1)
└── Companies (1:many)
    ├── Products
    ├── EFRISInvoices
    └── ERP Config

AuditLog (tracks all actions)
```

## 🛠 Next Steps (Future Enhancements)

1. **Payment Integration**
   - Integrate Flutterwave/Paystack
   - Auto-activate subscriptions after payment

2. **User Dashboard**
   - Usage analytics
   - Invoice history
   - Billing reports

3. **Complete ERP Adapters**
   - Finish Xero implementation
   - Finish Zoho implementation
   - Add Sage, Wave, etc.

4. **Webhook System**
   - Auto-fiscalize on invoice creation
   - Real-time sync

5. **Admin Panel**
   - Manage all users
   - View revenue
   - System monitoring

## 📝 Important Notes

- **Admin Credentials:** `admin@efris.local` / `admin123` (CHANGE THIS!)
- **JWT Secret:** Set `JWT_SECRET_KEY` environment variable in production
- **Certificates:** Each company needs its own `.pfx` certificate file
- **Billing:** Track `invoice_count` in subscriptions for usage-based billing

## 🎉 You Now Have a SaaS Platform!

Your API can now:
- Accept paying customers
- Manage multiple tenants
- Support different ERP systems
- Track usage and billing
- Scale to hundreds of companies

**Start monetizing your EFRIS integration!** 💰
