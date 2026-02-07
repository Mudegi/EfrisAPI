# How to Get API Credentials for Your ERP Integration

## For Your ERP Development Team

Since you're building an ERP and want to integrate with this EFRIS API platform, here's everything you need:

---

## 1. Getting API Credentials (Two Methods)

### Method A: Owner Creates Your Client Account Directly

**Process:**
1. **Owner logs in** at: https://efrisintegration.nafacademy.com/owner
   - Email: owner@efrisplatform.com
   - Password: OwnerSecure2026!

2. **Owner adds you as a client:**
   - Goes to "Clients" tab
   - Clicks "➕ Add Direct Client"
   - Fills in your company details:
     - Company Name: Your company name
     - Email: your-email@company.com
     - Password: YourSecurePassword (you'll use this to login)
     - Phone: +256 XXX XXX XXX
     - TIN: Your URA Tax Identification Number
     - Device Number: Your EFRIS device number
     - Uploads your .pfx certificate file
     - Certificate Password: Your .pfx password
     
   - **CRITICAL: Environment Selection**
     - ☑️ **Production Environment** (for real invoices) - Uses `efris.ura.go.ug`
     - ☐ **Test/Sandbox** (for demo only) - Uses `efristest.ura.go.ug`
     - **Default: Production** ✓ Most clients should use Production
   
   - **ERP Type Selection:**
     - Select "Custom API Integration" (since you're building your own ERP)
     - Optional: Add your ERP's API URL if you want webhooks

3. **What You Receive:**
   ```
   Client Login URL: https://efrisintegration.nafacademy.com/client/login
   Email: your-email@company.com
   Password: YourSecurePassword
   
   API Credentials (for Custom ERP):
   API Key: efris_abc123xyz... (64 characters)
   API Secret: xyz789abc... (64 characters)
   ```

4. **Access Your Dashboard:**
   - Login at: `/client/login` with your credentials
   - View all your fiscalized invoices
   - Monitor EFRIS submissions
   - See API usage statistics

---

### Method B: Register as Reseller (Full Platform Access)

If you want to manage multiple clients from your ERP:

1. **Register as Reseller:**
   - Visit: https://efrisintegration.nafacademy.com
   - Click "Get Started Free"
   - Select role: "Reseller"
   - Get 2-day free trial

2. **Add Your Clients:**
   - Each client you add gets their own API credentials
   - You can manage all clients from one dashboard
   - White-label option available

---

## 2. Understanding Production vs Testing Toggle

### ✅ How It Works:

**When Owner Creates Client (in owner portal):**

```javascript
// Frontend (owner_portal.html, line 2218)
const isTestMode = document.querySelector('input[name="efris_env"]:checked').value === 'test';

// Sent to API (line 2229)
formData.append('test_mode', isTestMode);
```

**Backend Receives (api_multitenant.py, line 2276):**
```python
test_mode: bool = Form(False),  # Default is Production (False)
```

**Stored in Database (line 2346):**
```python
company = Company(
    ...
    efris_test_mode=test_mode,  # TRUE = Test, FALSE = Production
    ...
)
```

### What This Controls:

| Environment | efris_test_mode Value | EFRIS URL | Use Case |
|-------------|----------------------|-----------|----------|
| **Production** (Default) | `False` | `https://efris.ura.go.ug` | Real business invoices |
| **Test/Sandbox** | `True` | `https://efristest.ura.go.ug` | Demo, training, testing |

### When EFRIS Calls Are Made:

**The system checks which environment to use:**

```python
# In efris_client.py (example)
if company.efris_test_mode:
    base_url = "https://efristest.ura.go.ug"  # Sandbox/Test
else:
    base_url = "https://efris.ura.go.ug"  # Production
```

**Important Notes:**
- ⚠️ **Most clients should use Production**
- Test mode is ONLY for:
  - Public demo endpoints
  - Training new users
  - Your development/testing (if URA gave you test credentials)
- Production certificates won't work on Test environment
- Test certificates won't work on Production

---

## 3. Your API Integration Steps

### Step 1: Get Your Credentials

Contact the platform owner to create your client account with **Custom API Integration** selected.

You'll receive:
```bash
API_KEY="efris_abc123xyz..."
API_SECRET="xyz789abc..."  # Optional, for request signing
BASE_URL="https://efrisintegration.nafacademy.com/api/external/efris"
ENVIRONMENT="production"  # or "test"
```

### Step 2: Store Credentials Securely

In your ERP configuration file:

```python
# config.py
EFRIS_API_KEY = os.getenv("EFRIS_API_KEY")  # Load from environment variable
EFRIS_BASE_URL = "https://efrisintegration.nafacademy.com/api/external/efris"
```

### Step 3: Make Your First API Call

**Example: Submit Invoice to EFRIS**

```python
import requests

API_KEY = "efris_abc123xyz..."
BASE_URL = "https://efrisintegration.nafacademy.com/api/external/efris"

# Prepare invoice data
invoice_data = {
    "invoice_number": "INV-2026-001",
    "invoice_date": "2026-02-07",
    "customer_name": "ACME Corporation",
    "customer_tin": "1000123456",
    "customer_phone": "+256700000000",
    "items": [
        {
            "item_name": "Laptop Computer",
            "quantity": 2,
            "unit_price": 2500000,
            "tax_rate": 18.0,
            "discount": 100000
        }
    ],
    "payment_mode": "CASH",
    "currency": "UGX"
}

# Submit to EFRIS
response = requests.post(
    f"{BASE_URL}/submit-invoice",
    json=invoice_data,
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Invoice fiscalized!")
    print(f"FDN: {result['fdn']}")
    print(f"QR Code: {result['qr_code']}")
else:
    print(f"❌ Error: {response.json()}")
```

### Step 4: Handle the Response

**Success Response:**
```json
{
    "success": true,
    "fdn": "1234567890123456",
    "invoice_number": "INV-2026-001",
    "qr_code": "data:image/png;base64,iVBORw0KG...",
    "verification_url": "https://efris.ura.go.ug/verify/1234567890123456",
    "fiscalization_date": "2026-02-07T10:30:00Z"
}
```

**What to do with FDN:**
- **Save it in your ERP database** (link to your invoice record)
- **Print it on the invoice** (required by URA)
- **Include QR code on invoice** (for customer verification)

---

## 4. Complete API Endpoints Available

### Invoice Operations
```bash
POST /api/external/efris/submit-invoice       # Submit new invoice
POST /api/external/efris/submit-credit-memo   # Submit credit note
GET  /api/external/efris/invoice-status/{fdn} # Check invoice status
```

### Product Operations
```bash
POST /api/external/efris/register-product     # Register product with EFRIS
GET  /api/external/efris/products             # List your registered products
```

### Purchase Orders
```bash
POST /api/external/efris/submit-purchase-order   # Submit PO to EFRIS
```

### Full Documentation
- **Interactive Docs**: https://efrisintegration.nafacademy.com/docs
- **External API Guide**: https://efrisintegration.nafacademy.com/external-api-docs
- **Code Samples**: Check `DEVELOPER_PACKAGE/QUICK_START_CUSTOM_ERP.md`

---

## 5. Testing Your Integration

### Test Checklist:

1. **✅ Can you authenticate?**
   ```bash
   curl -H "X-API-Key: your_api_key" \
        https://efrisintegration.nafacademy.com/api/external/efris/products
   ```
   Should return 200 OK (even if empty list)

2. **✅ Can you submit an invoice?**
   - Use the Python example above
   - Check response for `fdn` field
   - Verify invoice appears in your client dashboard

3. **✅ Is the environment correct?**
   - Login to your client dashboard
   - Check company settings - should show:
     - 🚀 Production Environment (most cases)
     - OR 🧪 Test/Sandbox (if testing)

4. **✅ Rate limit check:**
   - Default: 1000 requests per day
   - Check dashboard for API usage stats
   - Contact owner if you need higher limit

---

## 6. Common Issues & Solutions

### Issue 1: "API key not found"
**Solution:** 
- Check if owner enabled "Custom API Integration" when creating your account
- Verify you're using the correct API key
- Check with owner if API key was regenerated

### Issue 2: "Certificate authentication failed"
**Cause:** Wrong environment selected
- Production certificate won't work on Test environment
- Test certificate won't work on Production
**Solution:** Owner must update your account's environment setting

### Issue 3: "Rate limit exceeded"
**Solution:** 
- Check your dashboard for current usage
- API resets daily at midnight
- Contact owner to increase limit

### Issue 4: Can't see FDN in dashboard
**Cause:** Using wrong login URL
**Solution:**
- Client login: `/client/login` (for taxpayers)
- Reseller login: `/reseller` (for resellers)
- Don't use `/dashboard` (that's old URL)

---

## 7. Production Deployment Best Practices

### Security:
```python
# ✅ DO: Store in environment variables
API_KEY = os.getenv("EFRIS_API_KEY")

# ❌ DON'T: Hardcode in source code
API_KEY = "efris_abc123xyz..."
```

### Error Handling:
```python
try:
    response = requests.post(url, json=data, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()
except requests.exceptions.Timeout:
    # EFRIS servers slow - retry after 10 seconds
    time.sleep(10)
    return retry_submission()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        # Rate limit - wait and retry
        time.sleep(60)
        return retry_submission()
    else:
        # Log error and notify admin
        logger.error(f"EFRIS submission failed: {e}")
        raise
```

### Logging:
- Log all API requests (without sensitive data)
- Save FDN mappings to your invoice IDs
- Monitor API response times
- Set up alerts for failures

---

## 8. Quick Reference

### Your Credentials Location:
```
Client Dashboard: /client/login
API Key: Check dashboard → Settings → API Credentials
API Docs: /docs
Integration Guide: /external-api-docs
Support: support@efrisintegration.nafacademy.com / +256 706090021
```

### Environment Check:
```python
# Your company record in database:
# efris_test_mode = False  → Production (efris.ura.go.ug)
# efris_test_mode = True   → Test (efristest.ura.go.ug)
```

### Need Help?
1. Check `/external-api-docs` for complete guide
2. Review `DEVELOPER_PACKAGE/QUICK_START_CUSTOM_ERP.md`
3. Test in `/docs` (interactive API testing)
4. Contact platform owner
5. Email: support@efrisintegration.nafacademy.com
6. WhatsApp: +256 706090021

---

## Summary

**✅ To get credentials:**
- Owner creates your client account with "Custom API Integration"
- You receive API key + secret
- Login to `/client/login` to see dashboard

**✅ Environment toggle:**
- Works correctly ✓
- Owner sets it when creating your account
- Default: Production (recommended for real business)
- Test mode only for sandbox/demo

**✅ Integration:**
- Use API key in `X-API-Key` header
- POST invoices to `/api/external/efris/submit-invoice`
- Receive FDN in response
- Save FDN in your ERP database

**Your Next Steps:**
1. Ask owner to create your client account with Custom API
2. Receive API credentials via email
3. Login to dashboard to verify environment
4. Start integrating using `/external-api-docs` guide
5. Test first invoice submission
6. Deploy to production

---

**Last Updated:** February 7, 2026
