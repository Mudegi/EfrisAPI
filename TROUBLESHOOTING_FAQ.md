# 🛠️ EFRIS API - Troubleshooting FAQ

Complete guide to resolving common issues with EFRIS integration.

---

## 📋 Table of Contents

1. [Authentication Issues](#authentication-issues)
2. [Invoice Submission Errors](#invoice-submission-errors)
3. [Product Registration Problems](#product-registration-problems)
4. [Network & Connection Issues](#network--connection-issues)
5. [Certificate & Encryption Issues](#certificate--encryption-issues)
6. [Database Issues](#database-issues)
7. [Dashboard & UI Problems](#dashboard--ui-problems)
8. [Performance Issues](#performance-issues)
9. [Deployment Issues](#deployment-issues)
10. [EFRIS Error Codes Reference](#efris-error-codes-reference)

---

## 🔐 Authentication Issues

### Q: "Invalid API Key" error

**Problem**: Getting 401 Unauthorized when making API requests.

**Solutions**:
```bash
# 1. Check API key format
# Correct format: efris_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
X-API-Key: efris_abc123def456...

# 2. Verify API key hasn't expired
# Dashboard → Settings → API Keys → Check expiration

# 3. Check rate limits
# Default: 100 requests/minute
# Wait a minute or contact admin to increase limit
```

**Still not working?**
```python
# Test your API key
import requests

response = requests.get(
    "http://localhost:8001/api/dashboard/stats",
    headers={"X-API-Key": "efris_your_key_here"}
)
print(response.status_code)  # Should be 200
print(response.json())
```

---

### Q: "Token expired" error

**Problem**: JWT token expires after 30 minutes.

**Solution**:
```python
# Implement token refresh
def refresh_token_if_expired(token):
    # Decode without verification to check expiry
    payload = jwt.decode(token, options={"verify_signature": False})
    exp = payload.get('exp', 0)
    
    if time.time() > exp - 300:  # Refresh 5 min before expiry
        # Get new token
        response = requests.post(
            "http://localhost:8001/token",
            data={"username": "user@email.com", "password": "pass"}
        )
        return response.json()["access_token"]
    
    return token
```

---

### Q: Cannot login to dashboard

**Checklist**:
- [ ] Email and password correct?
- [ ] Account approved by owner? (Check email for approval)
- [ ] Browser cookies enabled?
- [ ] Try incognito mode
- [ ] Clear browser cache (Ctrl+Shift+Delete)

**Reset password**:
Contact platform owner or use password reset link (if configured).

---

## 📄 Invoice Submission Errors

### Q: Error Code 100 - "Taxpayer does not exist"

**Problem**: EFRIS doesn't recognize your TIN.

**Solutions**:
1. **Wrong TIN**: Verify TIN is correct (10 digits)
2. **Test Mode**: Using test TIN in production or vice versa
3. **Not registered**: Register business with URA first

**Check environment**:
```bash
# In .env file
EFRIS_USE_TEST_MODE=false  # Production
EFRIS_USE_TEST_MODE=true   # Testing
```

---

### Q: Error Code 01 - "Missing required fields"

**Problem**: Invoice missing required EFRIS fields.

**Required fields**:
```json
{
  "sellerDetails": {
    "tin": "required",
    "legalName": "required",
    "address": "required",
    "mobilePhone": "required",
    "emailAddress": "required"
  },
  "basicInformation": {
    "invoiceNo": "required - must be unique",
    "deviceNo": "required",
    "issuedDate": "required - format: YYYY-MM-DD HH:MM:SS",
    "currency": "required - usually UGX",
    "invoiceType": "required - 1 for normal invoice"
  },
  "buyerDetails": {
    "buyerTin": "required if B2B",
    "buyerLegalName": "required"
  },
  "goodsDetails": [
    {
      "item": "required",
      "qty": "required",
      "unitPrice": "required",
      "total": "required",
      "taxRate": "required",
      "goodsCategoryId": "required - 13 digits"
    }
  ],
  "summary": {
    "netAmount": "required",
    "taxAmount": "required",
    "grossAmount": "required"
  }
}
```

---

### Q: "Duplicate invoice number" error

**Problem**: Invoice number already used.

**Solution**:
```python
# Use unique invoice numbers with timestamp
import datetime

def generate_unique_invoice_no(prefix="INV"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}"

# Example: INV-20260206143502
```

---

### Q: "Invalid date format" error

**Problem**: Date not in EFRIS format.

**Solution**:
```python
# Correct format: YYYY-MM-DD HH:MM:SS
from datetime import datetime

# Correct
issued_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# Example: "2026-02-06 14:35:42"

# Wrong formats:
# ❌ "06/02/2026"
# ❌ "2026-02-06T14:35:42"
# ❌ "2026-02-06"
```

---

### Q: Tax calculation mismatch

**Problem**: EFRIS rejects invoice due to incorrect tax calculations.

**Solution**:
```python
def calculate_tax_correctly(items):
    """
    EFRIS requires exact calculations:
    netAmount = sum of all item totals (before tax)
    taxAmount = sum of all item taxes
    grossAmount = netAmount + taxAmount
    """
    net_amount = 0
    tax_amount = 0
    
    for item in items:
        unit_price = float(item['unitPrice'])
        qty = float(item['qty'])
        tax_rate = float(item['taxRate'])  # e.g., 0.18 for 18%
        
        # Calculate item total (before tax)
        item_total = unit_price * qty
        item['total'] = str(round(item_total, 2))
        
        # Calculate tax
        item_tax = item_total * tax_rate
        item['tax'] = str(round(item_tax, 2))
        
        net_amount += item_total
        tax_amount += item_tax
    
    gross_amount = net_amount + tax_amount
    
    return {
        "netAmount": str(round(net_amount, 2)),
        "taxAmount": str(round(tax_amount, 2)),
        "grossAmount": str(round(gross_amount, 2))
    }
```

---

## 📦 Product Registration Problems

### Q: "Product already exists" error

**Problem**: Trying to register duplicate product.

**Solution**:
```python
# Check if product exists first
def check_product_exists(item_code, efris_manager):
    try:
        result = efris_manager.t107_query_commodity_categories()
        existing = [p for p in result if p['itemCode'] == item_code]
        return len(existing) > 0
    except:
        return False

# Only register if not exists
if not check_product_exists("PROD001", efris_manager):
    efris_manager.t101_register_product(product_data)
```

---

### Q: "Invalid goodsCategoryId" error

**Problem**: Category ID not in EFRIS system.

**Common goodsCategoryIds**:
```
1010101010101 - General Goods
1010101010102 - Electronics
1010101010103 - Food & Beverages
1010101010104 - Textiles
1010101010105 - Construction Materials
```

**Get full list**:
```python
# T108 - Query commodity categories
categories = efris_manager.t108_query_commodity_categories()
for cat in categories:
    print(f"{cat['goodsCategoryId']} - {cat['name']}")
```

---

## 🌐 Network & Connection Issues

### Q: "Connection timeout" to EFRIS

**Problem**: Cannot reach EFRIS servers.

**Check network**:
```bash
# 1. Test connectivity
ping efristest.ura.go.ug

# 2. Check if EFRIS is up
curl https://efristest.ura.go.ug/efrisws/ws/taapp/getInformation

# 3. Check firewall
# Ensure ports 80 and 443 are open
```

**Increase timeout**:
```python
# In .env file
EFRIS_REQUEST_TIMEOUT=60  # Increase from 30 to 60 seconds
```

---

### Q: "SSL Certificate verification failed"

**Problem**: Certificate issues with EFRIS connection.

**Temporary solution** (not recommended for production):
```python
# In efris_client.py, add verify=False (for testing only!)
response = requests.post(url, json=payload, verify=False)
```

**Proper solution**:
```bash
# Update system certificates
pip install --upgrade certifi
pip install --upgrade requests
```

---

## 🔒 Certificate & Encryption Issues

### Q: "Failed to load certificate"

**Problem**: Cannot load .p12 certificate file.

**Check**:
```python
import os

cert_path = "keys/certificate.p12"

# 1. File exists?
if not os.path.exists(cert_path):
    print(f"❌ Certificate not found at {cert_path}")
else:
    print(f"✅ Certificate found")

# 2. Correct permissions?
# On Linux/Mac:
# chmod 600 keys/certificate.p12

# 3. Valid password?
# Try loading manually
from cryptography.hazmat.primitives.serialization import pkcs12
with open(cert_path, 'rb') as f:
    pkcs12.load_key_and_certificates(
        f.read(),
        password=b"your_password"
    )
```

---

### Q: "Invalid signature" error

**Problem**: RSA signature verification fails.

**Common causes**:
1. **Wrong hash algorithm**: EFRIS uses SHA1, not SHA256
2. **Wrong padding**: Must use PKCS1v15
3. **Incorrect key**: Using wrong certificate

**Correct implementation**:
```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Correct (EFRIS requires SHA1 + PKCS1v15)
signature = private_key.sign(
    content.encode('utf-8'),
    padding.PKCS1v15(),
    hashes.SHA1()  # SHA1, not SHA256!
)
```

---

### Q: AES encryption fails

**Problem**: Cannot encrypt/decrypt data.

**Check**:
```python
# 1. Key length (must be 32 bytes for AES-256)
if len(aes_key) != 32:
    print(f"❌ Invalid key length: {len(aes_key)}, expected 32")

# 2. Key exchange successful?
if efris_manager.aes_key is None:
    print("❌ No AES key - run T104 key exchange first")
    efris_manager.t104_get_aes_key()

# 3. Key not expired? (24-hour validity)
# Force refresh
efris_manager.aes_key = None
efris_manager.t104_get_aes_key()
```

---

## 💾 Database Issues

### Q: "Database is locked"

**Problem**: SQLite database locked by another process.

**Solutions**:
```bash
# 1. Check if another instance is running
ps aux | grep api_server.py
# Kill if needed: kill <PID>

# 2. Check for .db-journal file
ls -la efris_api.db*
# Remove if exists: rm efris_api.db-journal

# 3. Increase timeout
# In database connection
conn = sqlite3.connect('efris_api.db', timeout=30.0)
```

---

### Q: "No such table" error

**Problem**: Database table doesn't exist.

**Solution**:
```bash
# Run migrations
python run_migrations.py

# Or manually create tables
python -c "
import sqlite3
conn = sqlite3.connect('efris_api.db')
# Run your CREATE TABLE statements
conn.close()
"
```

---

### Q: Migration failed

**Check migration errors**:
```bash
# View migration log
python run_migrations.py

# Check database structure
sqlite3 efris_api.db ".schema"

# Rollback if needed
# (No automatic rollback - backup database first!)
cp efris_api.db efris_api.db.backup
```

---

## 🖥️ Dashboard & UI Problems

### Q: Dashboard shows "Loading..." forever

**Check browser console** (F12):
```javascript
// Common issues:
// 1. API endpoint wrong
// 2. CORS error
// 3. Authentication failed

// Test API directly
fetch('http://localhost:8001/api/dashboard/stats', {
    headers: {
        'X-API-Key': 'your_api_key_here'
    }
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

**Check CORS**:
```python
# In api_multitenant.py, ensure CORS configured
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Q: Mobile dashboard not working

**Check PWA installation**:
1. Open dashboard in Chrome/Edge
2. Press F12 → Application → Manifest
3. Check for manifest errors
4. Verify service worker registered

**Common issues**:
```bash
# 1. Manifest not found
# Check: /static/manifest.json exists

# 2. HTTPS required (for PWA)
# Use HTTPS in production

# 3. Icons missing
python generate_pwa_icons.py
```

---

## ⚡ Performance Issues

### Q: API responses are slow

**Optimize**:
```python
# 1. Add database indexes
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_invoices_tin 
    ON invoices(company_tin)
""")
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_invoices_date 
    ON invoices(created_at)
""")

# 2. Use pagination
# Limit results
GET /api/invoices?page=1&limit=20

# 3. Cache frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=100)
def get_product_categories():
    # Cached for 5 minutes
    return efris_manager.t108_query_commodity_categories()
```

---

### Q: EFRIS responses taking too long

**Timeout settings**:
```env
# In .env - increase timeout
EFRIS_REQUEST_TIMEOUT=60  # 60 seconds

# If still slow, check:
# 1. EFRIS server status (their side)
# 2. Your internet connection
# 3. Try during off-peak hours
```

---

## 🚀 Deployment Issues

### Q: Deployment failed on Namecheap

**Check GitHub Actions**:
1. Go to GitHub → Actions → Latest run
2. Look for failed step
3. Common issues:
   - SSH port blocked
   - Wrong directory path
   - Missing secrets

**Test SSH manually**:
```bash
ssh nafazplp@184.94.213.244 -p 21098
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com
git pull origin main
```

---

### Q: Dependencies not installing

**Check pip version**:
```bash
# On server
pip3 --version

# Update pip
python3 -m pip install --upgrade pip

# Install dependencies
pip3 install -r requirements.txt --user
```

---

### Q: Application not starting after deployment

**Check**:
```bash
# 1. Python version
python3 --version  # Should be 3.9+

# 2. Check for errors
python3 api_server.py
# Read error messages

# 3. Check .env exists
ls -la .env

# 4. Check permissions
chmod +x api_server.py
```

---

## 📚 EFRIS Error Codes Reference

### Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| **00** | Success | No action needed |
| **01** | Missing required field | Check invoice structure |
| **02** | Invalid format | Check date/number formats |
| **100** | Taxpayer not found | Verify TIN is correct |
| **101** | Device not registered | Register device with URA |
| **102** | Certificate invalid | Check certificate file |
| **103** | Signature verification failed | Check RSA signature (SHA1) |
| **104** | Duplicate invoice | Use unique invoice numbers |
| **105** | Invalid date | Use YYYY-MM-DD HH:MM:SS |
| **106** | Tax calculation error | Verify calculations |
| **107** | Invalid product code | Register product first |
| **108** | Network timeout | Retry or increase timeout |
| **109** | Database error | Check database connection |
| **110** | Rate limit exceeded | Wait and retry |

### Excise Duty Errors

| Code | Meaning | Solution |
|------|---------|----------|
| **201** | Invalid excise code | Check `exciseDutyCode` |
| **202** | Missing excise tax | Add to `taxDetails` |
| **203** | exciseFlag mismatch | Set `exciseFlag = "1"` for excisable goods |

---

## 🆘 Still Need Help?

### 1. Check Logs

```bash
# Application logs
tail -f logs/app.log

# EFRIS API logs
grep "EFRIS" logs/app.log

# Error logs
grep "ERROR" logs/app.log
```

### 2. Enable Debug Mode

```python
# In .env
DEBUG=True
LOG_LEVEL=DEBUG

# Restart application
```

### 3. Test Minimal Example

```python
# minimal_test.py
from efris_client import EfrisManager

# Test connection
efris = EfrisManager(
    tin="1000000000",
    device_no="1000000000_02",
    cert_path="keys/cert.p12",
    test_mode=True
)

# Test key exchange
try:
    result = efris.t104_get_aes_key()
    print("✅ Connection OK")
except Exception as e:
    print(f"❌ Error: {e}")
```

### 4. Contact Support

- 📧 Email: support@yourdomain.com
- 📱 WhatsApp: +256 XXX XXX XXX
- 💬 Discord: [Link to Discord]
- 📚 Documentation: https://docs.yourdomain.com

### 5. Report a Bug

Include:
- Error message
- Steps to reproduce
- Environment (.env settings without secrets)
- Log excerpts
- EFRIS response (if applicable)

---

## 🔍 Quick Diagnostic Checklist

Run this before asking for help:

```bash
# 1. Check environment
cat .env | grep EFRIS

# 2. Check certificate
ls -la keys/

# 3. Check database
sqlite3 efris_api.db "SELECT COUNT(*) FROM invoices;"

# 4. Check network
ping efristest.ura.go.ug

# 5. Check dependencies
pip3 list | grep -E "(fastapi|requests|cryptography)"

# 6. Check application
curl http://localhost:8001/health

# 7. Run tests
python -m pytest tests/test_unit_core.py -v
```

---

**Last Updated**: February 2026  
**Version**: 2.0  
**Feedback**: Submit issues on GitHub or contact support
