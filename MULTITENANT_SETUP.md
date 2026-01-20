# Multi-Tenant EFRIS API - Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_production.txt
```

### 2. Configure Environment
```bash
cp .env.production .env
# Edit .env with your settings:
# - DATABASE_URL (PostgreSQL connection)
# - SECRET_KEY (generate with: openssl rand -hex 32)
```

### 3. Create Database
```sql
-- In PostgreSQL:
CREATE DATABASE efris_multitenant;
```

### 4. Initialize Database
```bash
python -c "from database.connection import init_db; init_db()"
```

### 5. Start Server
```bash
python api_multitenant.py
```

Server runs on: **http://localhost:8001**

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────┐
│         FastAPI Application                 │
│  ┌──────────────────────────────────────┐  │
│  │    Authentication (JWT)              │  │
│  │    - OAuth2 Password Flow            │  │
│  │    - Bcrypt password hashing         │  │
│  └──────────────────────────────────────┘  │
│                    ↓                        │
│  ┌──────────────────────────────────────┐  │
│  │    Authorization Middleware          │  │
│  │    - Company access verification     │  │
│  │    - Role-based permissions          │  │
│  └──────────────────────────────────────┘  │
│                    ↓                        │
│  ┌──────────────────────────────────────┐  │
│  │    Business Logic Layer              │  │
│  │    - EFRIS integration (per company) │  │
│  │    - QuickBooks sync (per company)   │  │
│  │    - Data isolation                  │  │
│  └──────────────────────────────────────┘  │
│                    ↓                        │
│  ┌──────────────────────────────────────┐  │
│  │    PostgreSQL Database               │  │
│  │    - users                           │  │
│  │    - companies                       │  │
│  │    - company_users (many-to-many)    │  │
│  │    - products (company-scoped)       │  │
│  │    - invoices (company-scoped)       │  │
│  │    - audit_logs                      │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## 🔐 Database Schema

### users
- id, email (unique), hashed_password
- full_name, is_active, is_superuser
- Multi-company access via company_users

### companies
- id, name, tin (unique), device_no
- EFRIS config (test_mode, cert, AES key cache)
- QuickBooks tokens (encrypted)
- Each company = isolated tenant

### company_users (join table)
- user_id, company_id, role (admin/user/readonly)
- Users can belong to multiple companies

### products (company-scoped)
- QB data: item_id, name, sku, price
- EFRIS metadata: product_code, unit, status
- Excise duty info

### invoices (company-scoped)
- QB data: invoice_id, customer, amount
- EFRIS: FDN, verification_code, QR code

---

## 🔑 API Endpoints

### Authentication
```bash
# Register user
POST /api/auth/register
{
  "email": "user@company.com",
  "password": "secure_password",
  "full_name": "John Doe"
}

# Login (get JWT token)
POST /api/auth/login
Form: username=user@company.com&password=secure_password

# Get current user
GET /api/auth/me
Headers: Authorization: Bearer <token>
```

### Companies
```bash
# Get my companies
GET /api/companies
Headers: Authorization: Bearer <token>

# Create company
POST /api/companies
{
  "name": "ABC Ltd",
  "tin": "1014409555",
  "device_no": "1014409555_02",
  "efris_test_mode": true
}

# Get company details
GET /api/companies/{company_id}

# Add user to company
POST /api/companies/{company_id}/users
{
  "email": "colleague@company.com",
  "role": "user"
}
```

### Products
```bash
# Get company products
GET /api/companies/{company_id}/products

# Sync from QuickBooks
POST /api/companies/{company_id}/products/sync

# Register to EFRIS
POST /api/companies/{company_id}/products/{product_id}/register
```

### Invoices
```bash
# Get company invoices
GET /api/companies/{company_id}/invoices

# Sync from QuickBooks
POST /api/companies/{company_id}/invoices/sync

# Fiscalize invoice
POST /api/companies/{company_id}/invoices/{invoice_id}/fiscalize
```

---

## 🔒 Security Features

✅ **JWT Authentication** - Secure token-based auth
✅ **Password Hashing** - Bcrypt with salt
✅ **Company Isolation** - Data segregation by company_id
✅ **Role-Based Access** - Admin, User, Readonly roles
✅ **Encrypted Tokens** - QB/EFRIS tokens encrypted at rest
✅ **Audit Logging** - All operations tracked
✅ **Connection Pooling** - Efficient database connections
✅ **SQL Injection Protection** - SQLAlchemy ORM

---

## 🎯 Key Improvements vs Single-Tenant

| Feature | Old (Single) | New (Multi-Tenant) |
|---------|-------------|-------------------|
| Users | 1 | Unlimited |
| Companies | 1 | Unlimited |
| Data Isolation | ❌ None | ✅ Company-scoped |
| Authentication | ❌ test_token | ✅ JWT tokens |
| Database | ❌ JSON files | ✅ PostgreSQL |
| Scalability | ❌ Crashes | ✅ Production-ready |
| Security | ❌ None | ✅ Full security |
| Concurrent Access | ❌ No | ✅ Yes |

---

## 📝 Migration Steps from Old System

1. **Database Setup** - Create PostgreSQL database
2. **User Registration** - Register initial admin user
3. **Company Creation** - Create company with TIN
4. **QB Connection** - Connect QuickBooks per company
5. **EFRIS Config** - Upload certificate per company
6. **Data Migration** - Import existing products/invoices

---

## 🧪 Testing

```bash
# Register user
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"Test123456","full_name":"Admin"}'

# Login
curl -X POST http://localhost:8001/api/auth/login \
  -F "username=admin@test.com" \
  -F "password=Test123456"

# Get companies (use token from login)
curl -X GET http://localhost:8001/api/companies \
  -H "Authorization: Bearer <token>"
```

---

## 🚀 Production Deployment

1. **Environment** - Set production DATABASE_URL and SECRET_KEY
2. **HTTPS** - Use reverse proxy (nginx) with SSL
3. **Process Manager** - Use systemd or supervisor
4. **Monitoring** - Add logging and error tracking
5. **Backup** - Regular PostgreSQL backups
6. **Scaling** - Deploy multiple instances behind load balancer

---

## ⚠️ Important Notes

- Each company has isolated data (products, invoices)
- Users can belong to multiple companies with different roles
- QuickBooks tokens are per-company (not shared)
- EFRIS AES keys are cached per-company
- All sensitive data encrypted in database
- Audit trail for compliance

---

## 🎉 Ready for Production!

This architecture supports **hundreds of companies** with:
- ✅ Complete data isolation
- ✅ Secure authentication
- ✅ Scalable database
- ✅ Concurrent access
- ✅ Role-based permissions
