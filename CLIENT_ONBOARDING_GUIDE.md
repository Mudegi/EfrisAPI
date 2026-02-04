# 🎯 CLIENT ONBOARDING GUIDE

## Complete Process for Adding New Clients to Your EFRIS Platform

---

## 📋 OVERVIEW

This guide explains how to onboard new clients to your multi-tenant EFRIS platform, including:
1. Creating client accounts
2. Configuring their ERP system
3. Setting up ERP webhooks
4. Testing the integration

---

## 🚀 METHOD 1: Platform Owner Portal (Recommended)

### Step 1: Access Owner Portal
```
http://localhost:8001/owner
```

Login with owner credentials:
- Email: `admin@efris.local`
- Password: `admin123`

### Step 2: Add Client via Form

Click **"Add New Client"** and fill in:

**Client Information:**
- Company Name: `ABC Trading Ltd`
- Email: `client@abctrading.com`
- Password: `SecurePass123`
- Phone: `+256700123456`

**EFRIS Configuration:**
- TIN: `1234567890`
- Device Number: `1234567890_01`
- Certificate File: Upload `.pfx` file
- Certificate Password: `cert_password`
- Test Mode: ✅ (check for testing)

**Subscription:**
- Plan: Annual (1 year)
- Auto-activate: ✅

### Step 3: System Creates
- ✅ User account with email/password
- ✅ Company record with TIN and device
- ✅ Certificate stored in `keys/clients/1234567890.pfx`
- ✅ Active subscription
- ✅ Welcome email sent (if SMTP configured)

---

## 🔧 METHOD 2: API Endpoint (For Automation)

### Endpoint: `POST /api/owner/add-client`

**Authentication:** JWT token in header
```
Authorization: Bearer <owner_jwt_token>
```

**Request (multipart/form-data):**
```bash
curl -X POST http://localhost:8001/api/owner/add-client \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "company_name=ABC Trading Ltd" \
  -F "email=client@abctrading.com" \
  -F "password=SecurePass123" \
  -F "phone=+256700123456" \
  -F "tin=1234567890" \
  -F "device_no=1234567890_01" \
  -F "cert_password=cert_password" \
  -F "test_mode=true" \
  -F "pfx_file=@/path/to/certificate.pfx"
```

**Response:**
```json
{
  "success": true,
  "user_id": 5,
  "company_id": 3,
  "message": "Client added successfully",
  "login_url": "http://localhost:8001/login"
}
```

---

## 🔌 ERP WEBHOOK CONFIGURATION

### Where Webhooks Go

All ERP webhooks are in `api_multitenant.py` in this section:

```python
# ========== ERP WEBHOOKS SECTION ==========
# Add all ERP-specific webhook handlers here
```

### Currently Available Webhooks

#### 1. **QuickBooks Webhooks** (Already Implemented)

**Location:** Lines 2542-2900 in `api_multitenant.py`

**Endpoints:**
```python
POST /api/quickbooks/refresh                           # Token refresh
POST /api/companies/{company_id}/quickbooks/disconnect # Disconnect QB
POST /api/companies/{company_id}/quickbooks/connect    # Connect QB
POST /api/quickbooks/sync-products                     # Sync items
POST /api/quickbooks/sync-invoice/{invoice_id}         # Sync invoice
POST /api/quickbooks/sync-purchase-orders              # Sync POs
```

**QuickBooks Webhook Handler:**
```python
@app.post("/api/webhooks/quickbooks/{company_id}")
async def quickbooks_webhook(
    company_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives real-time notifications from QuickBooks
    When invoice is created/updated in QB, sync to EFRIS
    """
    payload = await request.json()
    
    # Verify QuickBooks signature
    signature = request.headers.get("intuit-signature")
    if not verify_quickbooks_webhook(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Get company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Handle different event types
    event_type = payload.get("eventNotifications", [{}])[0].get("realmId")
    entities = payload.get("eventNotifications", [{}])[0].get("dataChangeEvent", {}).get("entities", [])
    
    for entity in entities:
        if entity.get("name") == "Invoice":
            invoice_id = entity.get("id")
            operation = entity.get("operation")  # CREATE, UPDATE, DELETE
            
            if operation in ["CREATE", "UPDATE"]:
                # Fetch full invoice from QuickBooks
                from quickbooks_client import QuickBooksClient
                qb = QuickBooksClient()
                invoice = qb.get_invoice(invoice_id)
                
                # Transform and fiscalize to EFRIS
                from quickbooks_efris_mapper import QuickBooksEfrisMapper
                efris_invoice = QuickBooksEfrisMapper.map_invoice_to_efris(
                    invoice, {}, 
                    {"tin": company.tin, "device_no": company.device_no}
                )
                
                # Send to EFRIS
                from efris_client import EfrisManager
                efris = EfrisManager(
                    tin=company.tin,
                    device_no=company.device_no,
                    cert_path=company.cert_path,
                    test_mode=company.test_mode
                )
                
                result = efris.upload_invoice(efris_invoice)
                
                # Log result
                print(f"[QB Webhook] Invoice {invoice_id} fiscalized: {result}")
    
    return {"success": True, "message": "Webhook processed"}
```

**Configure in QuickBooks:**
1. Go to QuickBooks Developer Portal
2. Navigate to your app settings
3. Set webhook URL: `https://yourdomain.com/api/webhooks/quickbooks/{company_id}`
4. Select events: Invoice Created, Invoice Updated
5. Save webhook endpoint

---

#### 2. **Xero Webhooks** (Template - To Implement)

**Add this to `api_multitenant.py`:**

```python
@app.post("/api/webhooks/xero/{company_id}")
async def xero_webhook(
    company_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives real-time notifications from Xero
    """
    payload = await request.json()
    
    # Verify Xero signature
    signature = request.headers.get("x-xero-signature")
    webhook_key = os.getenv("XERO_WEBHOOK_KEY")
    
    import hmac
    import hashlib
    body = await request.body()
    expected = hmac.new(webhook_key.encode(), body, hashlib.sha256).hexdigest()
    
    if signature != expected:
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Get company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)
    
    # Handle events
    for event in payload.get("events", []):
        if event.get("eventType") == "UPDATE" and event.get("eventCategory") == "INVOICE":
            resource_id = event.get("resourceId")
            
            # Fetch invoice from Xero API
            from erp_adapters import XeroAdapter
            xero = XeroAdapter(json.loads(company.erp_config))
            invoice = await xero.get_invoice(resource_id)
            
            # Transform to EFRIS
            efris_invoice = xero.transform_to_efris(invoice, {
                "tin": company.tin,
                "device_no": company.device_no
            })
            
            # Fiscalize
            from efris_client import EfrisManager
            efris = EfrisManager(
                tin=company.tin,
                device_no=company.device_no,
                cert_path=company.cert_path,
                test_mode=company.test_mode
            )
            efris.upload_invoice(efris_invoice)
    
    return {"success": True}
```

**Configure in Xero:**
1. Xero Developer Portal → Your App → Webhooks
2. Webhook URL: `https://yourdomain.com/api/webhooks/xero/{company_id}`
3. Webhook Key: Generate and save to `.env` as `XERO_WEBHOOK_KEY`
4. Events: Invoice Created, Invoice Updated

---

#### 3. **Zoho Books Webhooks** (Template - To Implement)

**Add this to `api_multitenant.py`:**

```python
@app.post("/api/webhooks/zoho/{company_id}")
async def zoho_webhook(
    company_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives real-time notifications from Zoho Books
    """
    payload = await request.json()
    
    # Zoho sends JSON payload with event details
    event_type = payload.get("event_type")
    resource_type = payload.get("resource_type")
    resource_id = payload.get("resource_id")
    
    if resource_type == "invoice" and event_type in ["invoice.created", "invoice.updated"]:
        # Get company
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404)
        
        # Fetch invoice from Zoho
        from erp_adapters import ZohoAdapter
        zoho = ZohoAdapter(json.loads(company.erp_config))
        invoice = await zoho.get_invoice(resource_id)
        
        # Transform to EFRIS
        efris_invoice = zoho.transform_to_efris(invoice, {
            "tin": company.tin,
            "device_no": company.device_no
        })
        
        # Fiscalize
        from efris_client import EfrisManager
        efris = EfrisManager(
            tin=company.tin,
            device_no=company.device_no,
            cert_path=company.cert_path,
            test_mode=company.test_mode
        )
        efris.upload_invoice(efris_invoice)
    
    return {"success": True}
```

**Configure in Zoho Books:**
1. Settings → Automation → Webhooks
2. Create new webhook
3. URL: `https://yourdomain.com/api/webhooks/zoho/{company_id}`
4. Module: Invoices
5. Events: Invoice Created, Invoice Updated

---

#### 4. **Payment Gateway Webhook** (Already Implemented)

**Location:** Line 1256 in `api_multitenant.py`

```python
POST /api/webhooks/flutterwave  # Payment confirmations
```

This webhook activates subscriptions when clients pay.

---

## 📂 FILE STRUCTURE FOR WEBHOOKS

```
api_multitenant.py
├── Line 1256:  POST /api/webhooks/flutterwave      (Payment)
├── Line 2542:  POST /api/quickbooks/refresh         (QB token)
├── Line 2623:  POST /api/quickbooks/disconnect      (QB disconnect)
├── Line 2685:  POST /api/quickbooks/connect         (QB connect)
├── Line 2834:  POST /api/quickbooks/sync-products   (QB sync)
├── Line 3050:  POST /api/quickbooks/sync-invoice    (QB sync)
├── TO ADD:     POST /api/webhooks/quickbooks/{id}   (QB real-time)
├── TO ADD:     POST /api/webhooks/xero/{id}         (Xero real-time)
└── TO ADD:     POST /api/webhooks/zoho/{id}         (Zoho real-time)
```

**Recommended Location:** Add all new webhooks after line 1300 in the **"ERP WEBHOOKS"** section.

---

## ⚙️ CLIENT CONFIGURATION STEPS

### 1. Client Logs In
```
http://localhost:8001/login
Email: client@abctrading.com
Password: SecurePass123
```

### 2. Client Connects Their ERP

**For QuickBooks:**
```
Dashboard → Settings → Connect QuickBooks
→ OAuth flow → Authorize
→ Realm ID saved automatically
```

**For Xero:**
```
Dashboard → Settings → Connect Xero
→ OAuth flow → Authorize
→ Tenant ID saved
```

**For Zoho:**
```
Dashboard → Settings → Connect Zoho Books
→ OAuth flow → Authorize
→ Organization ID saved
```

### 3. System Stores ERP Config

In `companies` table, `erp_config` column:
```json
{
  "realm_id": "4620816365324345807",
  "access_token": "encrypted_token",
  "refresh_token": "encrypted_token",
  "webhook_url": "https://yourdomain.com/api/webhooks/quickbooks/3"
}
```

### 4. Configure ERP Webhook

**Manual Setup:**
- QuickBooks: Developer Portal → Webhooks
- Xero: Developer Portal → Webhooks
- Zoho: Settings → Automation → Webhooks

**URL Format:**
```
https://yourdomain.com/api/webhooks/{erp_name}/{company_id}
```

**Example:**
```
https://api.efris.ug/api/webhooks/quickbooks/3
https://api.efris.ug/api/webhooks/xero/3
https://api.efris.ug/api/webhooks/zoho/3
```

---

## 🧪 TESTING NEW CLIENT SETUP

### Test 1: Login Works
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "client@abctrading.com",
    "password": "SecurePass123"
  }'
```

**Expected:** JWT token returned

### Test 2: Can Access Company Data
```bash
curl http://localhost:8001/api/companies \
  -H "Authorization: Bearer <client_token>"
```

**Expected:** Returns client's company

### Test 3: ERP Connection Works
```bash
# For QuickBooks
curl http://localhost:8001/api/companies/3/qb-items \
  -H "Authorization: Bearer <client_token>"
```

**Expected:** Returns items from client's QuickBooks

### Test 4: EFRIS Integration Works
```bash
curl -X POST http://localhost:8001/api/companies/3/efris-goods/import \
  -H "Authorization: Bearer <client_token>"
```

**Expected:** Imports goods from EFRIS using client's TIN

### Test 5: Webhook Receives Events

**Trigger invoice in QuickBooks:**
1. Create invoice in QB
2. Check logs: Should see "QB Webhook received"
3. Invoice should auto-fiscalize to EFRIS

---

## 🔐 SECURITY CHECKLIST

### Client Isolation
- ✅ Each client has separate user account
- ✅ JWT tokens scoped to user
- ✅ Company data isolated by user_id
- ✅ ERP credentials encrypted in database
- ✅ Certificates stored separately per TIN

### Webhook Security
- ✅ Verify signatures from ERP providers
- ✅ Use HTTPS in production
- ✅ Validate company_id in webhook URL
- ✅ Check user has access to company
- ✅ Rate limit webhook endpoints

### ERP Token Management
- ✅ Refresh tokens before expiry
- ✅ Store tokens encrypted
- ✅ Revoke on disconnect
- ✅ Auto-refresh on API calls

---

## 📊 CLIENT DASHBOARD FEATURES

Once onboarded, clients can:

1. **View Invoices** - See all invoices from ERP
2. **Fiscalize Invoices** - Send to EFRIS manually or auto
3. **Sync Products** - Import items from ERP and EFRIS
4. **View Sync Status** - See what's fiscalized vs pending
5. **Configure Settings** - Update TIN, device, certificate
6. **Disconnect ERP** - Revoke access to QuickBooks/Xero/Zoho
7. **View Audit Log** - See all EFRIS submissions

---

## 🚨 TROUBLESHOOTING

### Client Can't Login
- Check email is correct in database
- Verify password was set correctly
- Check user status is 'active'

### ERP Connection Fails
- Verify OAuth redirect URL matches
- Check ERP credentials are valid
- Ensure tokens haven't expired
- Check ERP adapter is configured for that company

### Webhook Not Receiving Events
- Verify URL is publicly accessible (use ngrok for local testing)
- Check ERP provider has webhook configured
- Verify signature validation is correct
- Check webhook secret is in .env

### EFRIS Fiscalization Fails
- Verify TIN and device number are correct
- Check certificate is valid and not expired
- Ensure EFRIS server is up (not returning HTML)
- Check invoice data format matches EFRIS spec

---

## 🎯 QUICK ONBOARDING CHECKLIST

For each new client:

- [ ] Add client via owner portal or API
- [ ] Verify client can login
- [ ] Client connects their ERP (OAuth flow)
- [ ] Configure ERP webhook in provider portal
- [ ] Test: Create invoice in ERP
- [ ] Verify: Invoice auto-fiscalizes to EFRIS
- [ ] Send client their login credentials
- [ ] Schedule training session
- [ ] Monitor first week of usage

---

## 📞 SUPPORT FOR CLIENTS

Provide clients with:

1. **Login URL:** `https://yourdomain.com/login`
2. **Documentation:** Link to user guide
3. **Support Email:** support@yourdomain.com
4. **Training Video:** How to connect ERP and fiscalize invoices
5. **FAQ:** Common issues and solutions

---

## 💡 TIPS FOR SCALING

### Managing Multiple Clients
- Use reseller accounts for partners
- Automate client creation via API
- Set up email templates for onboarding
- Create video tutorials for self-service setup

### Performance Optimization
- Cache ERP tokens to reduce API calls
- Batch fiscalize invoices during off-peak hours
- Use background tasks for heavy operations
- Monitor webhook response times

### Monitoring
- Track fiscalization success rate per client
- Alert on failed webhook deliveries
- Monitor EFRIS API uptime
- Log all ERP sync operations

---

## 📚 NEXT STEPS

1. **Add Webhook Handlers:** Copy templates above for Xero/Zoho
2. **Test with Real Client:** Onboard one client completely
3. **Document Issues:** Track edge cases and solutions
4. **Automate More:** Build self-service client portal
5. **Scale:** Add more ERP integrations as needed

---

**You now have everything needed to onboard clients! 🚀**
