# Developer Handoff Package - Custom ERP Integration

## 📦 What to Give Your Developers

### Files to Share (Documentation Only)

1. **YOUR_IMPLEMENTATION_CHECKLIST.md** - Quick start guide
2. **BACKEND_IMPLEMENTATION_GUIDE.md** - Complete implementation examples
3. **EXTERNAL_API_DOCUMENTATION.md** - Full API reference
4. **QUICK_START_CUSTOM_ERP.md** (optional) - Quick code samples
5. **IMPLEMENTATION_STATUS.md** (optional) - Status overview

---

## 🔑 Credentials to Provide

### For Each Client Company:

**Only 2 things needed:**

1. **API Base URL**: `http://your-server-ip:8001/api/external/efris`
2. **API Key**: `[unique key for this client]`

**Get API Key:**
```sql
SELECT company_name, api_key, api_enabled 
FROM companies 
WHERE id = [CLIENT_COMPANY_ID];
```

Or via Python:
```python
from database.models import Company
from database.connection import SessionLocal

db = SessionLocal()
company = db.query(Company).filter_by(id=CLIENT_ID).first()
print(f"Company: {company.company_name}")
print(f"API Key: {company.api_key}")
print(f"Enabled: {company.api_enabled}")
```

---

## 🏢 Multi-Tenant Architecture

**Important:** This is a multi-tenant system!

- **Each company gets their own unique API key**
- The backend automatically identifies the company from the API key
- **No need to pass company ID, TIN, or any company identifier**
- Developers just use: `X-API-Key: [their_api_key]`
- The system handles the rest

**Example:**
```javascript
// Company A uses their key
fetch('http://server:8001/api/external/efris/submit-invoice', {
  headers: { 'X-API-Key': 'company_a_key_xyz123' }
});

// Company B uses their key (same code, different key)
fetch('http://server:8001/api/external/efris/submit-invoice', {
  headers: { 'X-API-Key': 'company_b_key_abc789' }
});
```

The backend automatically:
- Validates the API key
- Retrieves the company record
- Uses that company's EFRIS credentials
- Submits to EFRIS with correct TIN/device number
- Saves to that company's records

**No hardcoding needed!**

---

## 📧 Developer Brief Template

```
Subject: EFRIS Integration - API Credentials

Hi [Developer/Team],

We need to integrate EFRIS fiscalization into our ERP system.

=== CREDENTIALS ===
API Endpoint: http://[your-server]:8001/api/external/efris
API Key: [paste their unique API key here]

=== DOCUMENTATION ===
See attached files:
1. YOUR_IMPLEMENTATION_CHECKLIST.md - Start here
2. BACKEND_IMPLEMENTATION_GUIDE.md - Implementation details
3. EXTERNAL_API_DOCUMENTATION.md - API reference

=== WHAT TO BUILD ===
Add "Send to EFRIS" buttons to these forms:
1. Invoice Form → Calls /submit-invoice
2. Product Form → Calls /register-product
3. Purchase Order Form → Calls /submit-purchase-order
4. Credit Note Form → Calls /submit-credit-note

All requests must include header:
X-API-Key: [their API key]

=== IMPORTANT NOTES ===
- This is multi-tenant: API key identifies your company automatically
- Don't hardcode company ID, TIN, or any company-specific values
- Just pass the API key - backend handles everything
- Display FDN, QR code, and verification code to users
- Handle errors and show user-friendly messages

=== EXAMPLES ===
Complete code examples (HTML/JS, Python, PHP) are in the docs.
Test endpoint with cURL first before building UI.

=== TIMELINE ===
[Your deadline]

=== QUESTIONS ===
Contact: [Your contact info]

Thanks!
```

---

## ❌ What NOT to Share

**Keep on your server (don't give to developers):**

- ❌ `api_multitenant.py` (backend code)
- ❌ `efris_client.py` (EFRIS integration)
- ❌ `database/models.py` (database schema)
- ❌ `requirements.txt` (backend dependencies)
- ❌ Certificate files (.pfx, .pem)
- ❌ Database connection strings
- ❌ Environment variables (.env)
- ❌ Any backend implementation code

**Why?**
- Security: Keep EFRIS certificates and credentials private
- Separation: Developers only need to call the API
- Simplicity: Less confusion, clearer boundaries

---

## 🔐 Security Checklist

Before giving API key to developers:

- [ ] Verify company is set up correctly in database
- [ ] Check `api_enabled = True` for this company
- [ ] Verify EFRIS credentials are configured
- [ ] Test the API key works (use cURL)
- [ ] Consider IP whitelisting if needed
- [ ] Set up monitoring/logging for API usage
- [ ] Prepare to rotate key if compromised

---

## 🧪 Testing Instructions for Developers

**Quick Test - Submit Invoice:**

```bash
curl -X POST http://your-server:8001/api/external/efris/submit-invoice \
  -H "Content-Type: application/json" \
  -H "X-API-Key: [THEIR_API_KEY]" \
  -d '{
    "invoice_number": "TEST-001",
    "invoice_date": "2026-01-24",
    "customer_name": "Test Customer",
    "items": [{
      "item_name": "Test Product",
      "quantity": 1,
      "unit_price": 10000,
      "total": 10000,
      "tax_rate": 0.18,
      "tax_amount": 1800
    }],
    "total_amount": 10000,
    "total_tax": 1800,
    "currency": "UGX"
  }'
```

**Expected Success Response:**
```json
{
  "success": true,
  "fdn": "1234567890123456",
  "verification_code": "AB12CD34",
  "qr_code": "data:image/png;base64,...",
  "invoice_number": "TEST-001",
  "fiscalized_at": "2026-01-24T10:30:00"
}
```

If this works, they're ready to build!

---

## 📊 Monitoring API Usage

**Track usage per company:**

```sql
-- Check API activity
SELECT 
    company_name,
    api_key,
    api_last_used,
    api_enabled
FROM companies
ORDER BY api_last_used DESC;

-- Check invoice submissions
SELECT 
    c.company_name,
    COUNT(e.id) as invoices_submitted,
    MAX(e.created_at) as last_submission
FROM companies c
LEFT JOIN efris_invoices e ON e.company_id = c.id
WHERE c.api_enabled = TRUE
GROUP BY c.id;
```

---

## 🔄 API Key Rotation

**If a key is compromised:**

1. Generate new key:
```sql
UPDATE companies 
SET api_key = 'new_key_' || md5(random()::text)
WHERE id = [COMPANY_ID];
```

2. Notify developer of new key
3. Update their configuration
4. Old key stops working immediately

---

## 📞 Support Protocol

**When developers have issues:**

1. **Authentication errors (401)**
   - Verify API key is correct
   - Check `api_enabled = TRUE`
   - Test with cURL

2. **Validation errors (400)**
   - Check request format in documentation
   - Verify all required fields present
   - Check data types

3. **EFRIS errors**
   - Check backend logs
   - Verify company EFRIS credentials
   - Test in EFRIS test mode first

4. **Connection errors**
   - Verify server is running
   - Check firewall/network
   - Verify port 8001 accessible

---

## ✅ Pre-Handoff Checklist

Before giving docs and credentials to developers:

- [ ] Backend server is running and tested
- [ ] Company record exists in database
- [ ] API key generated and verified
- [ ] `api_enabled = TRUE` for this company
- [ ] EFRIS credentials configured correctly
- [ ] Test API with cURL and got success
- [ ] Documentation files are up to date
- [ ] Developer brief email prepared
- [ ] Support contact info included
- [ ] Timeline communicated
- [ ] Billing/licensing arranged (if applicable)

---

## 🎯 Summary

**Give Developers:**
- ✅ 3-5 documentation files
- ✅ API base URL
- ✅ Their unique API key

**Developers Build:**
- Buttons in their ERP UI
- API calls with X-API-Key header
- Display for FDN/QR code/results
- Error handling

**Backend Handles:**
- Multi-tenant company identification
- EFRIS credential management
- Certificate handling
- Data persistence
- Security

**No hardcoding, no shared secrets, clean separation!**

---

## 🚀 Go Live Process

1. **Development Phase**
   - Use test mode: `is_test_mode = TRUE`
   - Test all 4 operations
   - Verify error handling

2. **UAT Phase**
   - Still in test mode
   - Full end-to-end testing
   - Verify QR codes display correctly

3. **Production**
   - Switch to production: `is_test_mode = FALSE`
   - Monitor first submissions closely
   - Have rollback plan ready

4. **Post-Launch**
   - Monitor API usage
   - Track error rates
   - Collect developer feedback
   - Plan improvements

---

**That's everything your developers need!**

Simple, secure, scalable multi-tenant integration. 🎉
