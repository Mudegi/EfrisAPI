# 🔄 ERP SWITCHING GUIDE - Keep Same EFRIS Credentials

## Overview

Your platform now supports **changing ERP systems** while maintaining the same EFRIS registration (TIN, device number, private key).

**Real-World Scenario:**
- A business starts with **QuickBooks**
- After 6 months, they switch to **Xero**
- Their **EFRIS credentials stay the same** (issued by URA)
- Historical data from QuickBooks is **preserved**
- Dashboard **automatically adapts** to show Xero branding

---

## 🎯 What Happens When You Switch ERP?

### What CHANGES:
✅ **ERP Type** - From QUICKBOOKS → XERO (or any other)  
✅ **Dashboard UI** - Colors, icons, labels update automatically  
✅ **OAuth Connection** - New ERP authentication required  
✅ **Data Source** - New invoices/items come from new ERP  

### What STAYS THE SAME:
✅ **EFRIS Credentials** - TIN, device number, private key unchanged  
✅ **EFRIS Registration** - Same URA registration  
✅ **Historical Data** - Old ERP data preserved in database  
✅ **Fiscalized Invoices** - All past EFRIS submissions intact  
✅ **User Accounts** - Same login, same permissions  

---

## 📊 Database Behavior

### Your Companies Table:
```sql
CREATE TABLE companies (
    id INTEGER PRIMARY KEY,
    name TEXT,
    tin TEXT,                    -- ✅ NEVER CHANGES
    device_no TEXT,              -- ✅ NEVER CHANGES (unless URA updates)
    efris_cert_path TEXT,        -- ✅ NEVER CHANGES
    efris_cert_password TEXT,    -- ✅ NEVER CHANGES
    
    erp_type TEXT,               -- 🔄 CHANGES (QUICKBOOKS → XERO)
    erp_config JSON,             -- 🔄 CHANGES (realm_id → tenant_id)
    
    -- Historical data (NOT deleted when ERP changes)
    qb_items JSON,               -- 📦 Preserved
    qb_invoices JSON,            -- 📦 Preserved
    efris_products JSON,         -- 📦 Preserved
    efris_invoices JSON          -- 📦 Preserved
);
```

**When you switch from QB to Xero:**
1. `erp_type` changes: `"QUICKBOOKS"` → `"XERO"`
2. `erp_config` changes: `{"realm_id": "..."}` → `{"tenant_id": "..."}`
3. Old QuickBooks data (`qb_items`, `qb_invoices`) **remains in database**
4. EFRIS data (`efris_products`, `efris_invoices`) **remains untouched**
5. New Xero data will be fetched going forward

---

## 🔧 How to Switch ERP

### Method 1: API Request (Recommended)

**Endpoint:** `PUT /api/companies/{company_id}`

**Example: Switch from QuickBooks to Xero**

```bash
curl -X PUT "https://yourdomain.com/api/companies/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "erp_type": "XERO",
    "erp_config": {
      "tenant_id": "xxx-xxx-xxx-xxx"
    }
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "ABC Company Ltd",
  "tin": "1014409555",
  "device_no": "TZ00SD01",
  "erp_type": "XERO",
  "erp_config": {"tenant_id": "xxx-xxx-xxx-xxx"},
  "efris_test_mode": false,
  "is_active": true,
  "updated_at": "2026-01-23T10:30:00"
}
```

**Console Output:**
```
[ERP CHANGE] Company ABC Company Ltd (ID: 1)
  Old ERP: QUICKBOOKS
  New ERP: XERO
  EFRIS credentials remain unchanged (TIN: 1014409555)
  ✅ ERP successfully changed from QUICKBOOKS to XERO
  📊 Historical data from QUICKBOOKS preserved in database
  🔗 Dashboard will now show XERO branding
```

---

### Method 2: Dashboard UI (Future Enhancement)

**In the company settings page:**

```
📊 Company Settings

ERP System:  [Xero ▼]     (was: QuickBooks)

⚠️ Warning: Changing ERP will:
   ✅ Preserve all historical data
   ✅ Keep EFRIS credentials unchanged
   ⚠️ Require new ERP authentication
   
[Save Changes]
```

---

## 🎨 Dashboard Adaptation

### Before (QuickBooks):
```
┌─────────────────────────────────────┐
│  Sidebar                            │
│  📘 QuickBooks Records              │ ← Green theme
│    📦 Items                          │
│    📄 Invoices                       │
│                                      │
│  Top Bar: 🔗 Connect QuickBooks     │
└─────────────────────────────────────┘
```

### After Switch to Xero (Instant):
```
┌─────────────────────────────────────┐
│  Sidebar                            │
│  📊 Xero Records                    │ ← Blue theme
│    📦 Items                          │
│    📄 Invoices                       │
│                                      │
│  Top Bar: 🔗 Connect Xero           │
└─────────────────────────────────────┘
```

**User refreshes page** → Dashboard reads `erp_type = "XERO"` → UI updates automatically!

---

## 📝 Step-by-Step Migration Example

### Scenario: Moving from QuickBooks to Xero

**Company:** ABC Company Ltd  
**TIN:** 1014409555  
**Current ERP:** QuickBooks  
**Target ERP:** Xero  

---

### Step 1: **Before Migration - Verify Current State**

```bash
GET /api/companies/1
```

**Response:**
```json
{
  "id": 1,
  "name": "ABC Company Ltd",
  "tin": "1014409555",
  "device_no": "TZ00SD01",
  "erp_type": "QUICKBOOKS",
  "erp_config": {
    "realm_id": "123456789"
  },
  "qb_company_name": "ABC Company QB",
  "efris_test_mode": false
}
```

**QuickBooks Historical Data:**
- 150 items synced
- 450 invoices synced
- 280 invoices fiscalized to EFRIS

---

### Step 2: **Switch ERP Type**

```bash
PUT /api/companies/1
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1...

{
  "erp_type": "XERO",
  "erp_config": {
    "tenant_id": "abc-def-ghi-jkl",
    "organization_name": "ABC Company Xero"
  }
}
```

**Server logs:**
```
[ERP CHANGE] Company ABC Company Ltd (ID: 1)
  Old ERP: QUICKBOOKS
  New ERP: XERO
  EFRIS credentials remain unchanged (TIN: 1014409555)
  ✅ ERP successfully changed from QUICKBOOKS to XERO
  📊 Historical data from QUICKBOOKS preserved in database
  🔗 Dashboard will now show XERO branding
```

---

### Step 3: **Verify New State**

```bash
GET /api/companies/1
```

**Response:**
```json
{
  "id": 1,
  "name": "ABC Company Ltd",
  "tin": "1014409555",          // ✅ Same
  "device_no": "TZ00SD01",      // ✅ Same
  "erp_type": "XERO",           // 🔄 Changed
  "erp_config": {
    "tenant_id": "abc-def-ghi-jkl"  // 🔄 Changed
  },
  "efris_test_mode": false,
  "updated_at": "2026-01-23T10:35:00"
}
```

---

### Step 4: **Reconnect New ERP**

**User action in dashboard:**
1. Dashboard detects `erp_type = "XERO"`
2. Shows "🔗 Connect Xero" button (blue theme)
3. User clicks → Xero OAuth popup opens
4. User authorizes → Xero tokens stored
5. Dashboard shows "✅ Xero Connected"

---

### Step 5: **Sync New ERP Data**

```bash
GET /api/companies/1/xero/items
```

**What happens:**
- Xero adapter fetches items from Xero API
- New items stored alongside old QuickBooks items
- Both datasets coexist in database

**Database state:**
```sql
-- Old data (preserved)
qb_items: [...150 QB items...]
qb_invoices: [...450 QB invoices...]

-- New data (from Xero)
xero_items: [...new items...]
xero_invoices: [...new invoices...]

-- EFRIS data (unchanged)
efris_products: [...same 150 products...]
efris_invoices: [...same 280 fiscalized invoices...]
```

---

### Step 6: **Continue EFRIS Operations**

**Create new invoice in Xero → Fiscalize to EFRIS:**

```bash
POST /api/companies/1/efris/fiscalize/XERO-INV-001
```

**What happens:**
1. System detects `erp_type = "XERO"`
2. Xero adapter extracts invoice data
3. Formats to EFRIS spec
4. Submits to URA using **same TIN, device_no, private key**
5. Invoice fiscalized successfully! ✅

**EFRIS doesn't care** that you switched from QuickBooks to Xero - same credentials work!

---

## 🔍 Common Scenarios

### Scenario 1: QuickBooks → Xero

**Reason:** Xero has better reporting features  
**Action:** `PUT /api/companies/1` with `{"erp_type": "XERO"}`  
**Result:** Dashboard shows Xero branding, Xero OAuth, Xero data import  

---

### Scenario 2: Xero → Zoho Books

**Reason:** Moving to Zoho ecosystem  
**Action:** `PUT /api/companies/1` with `{"erp_type": "ZOHO"}`  
**Result:** Dashboard shows Zoho branding (red theme), Zoho OAuth  

---

### Scenario 3: QuickBooks → Custom ERP

**Reason:** Switched to proprietary system  
**Action:** `PUT /api/companies/1` with `{"erp_type": "CUSTOM", "erp_config": {"api_url": "...", "api_key": "..."}}`  
**Result:** Dashboard shows generic "🔌 ERP" branding, manual config instead of OAuth  

---

### Scenario 4: Xero → None (Manual Entry)

**Reason:** Temporarily disconnecting ERP, entering data manually  
**Action:** `PUT /api/companies/1` with `{"erp_type": "NONE"}`  
**Result:** Dashboard shows "⚙️ Manual Entry" mode, no ERP sync  

---

## 🛡️ What About Historical Data?

### QuickBooks Items (Before Switch)

**Database:**
```sql
SELECT * FROM qb_items WHERE company_id = 1;

id | company_id | qb_item_id | name           | efris_sync
---|------------|------------|----------------|------------
1  | 1          | QB-001     | Product A      | true
2  | 1          | QB-002     | Product B      | true
```

**After switching to Xero:**
- ✅ These records **remain in database**
- ✅ Still visible in dashboard under "Historical Data"
- ✅ Can still be referenced
- ⚠️ No longer syncing from QuickBooks (ERP disconnected)

---

### EFRIS Products (Before Switch)

**Database:**
```sql
SELECT * FROM efris_products WHERE company_id = 1;

id | company_id | product_code | name       | source_erp
---|------------|--------------|------------|------------
1  | 1          | PRD-001      | Product A  | QUICKBOOKS
2  | 1          | PRD-002      | Product B  | QUICKBOOKS
```

**After switching to Xero:**
- ✅ Records **remain intact**
- ✅ Still registered with EFRIS
- ✅ Can still be used in new invoices from Xero
- 📝 New products from Xero will have `source_erp = "XERO"`

---

### EFRIS Fiscalized Invoices (Before Switch)

**Database:**
```sql
SELECT * FROM efris_invoices WHERE company_id = 1;

id | company_id | invoice_no    | fdn        | source_erp
---|------------|---------------|------------|------------
1  | 1          | QB-INV-001    | FDN123     | QUICKBOOKS
2  | 1          | QB-INV-002    | FDN124     | QUICKBOOKS
```

**After switching to Xero:**
- ✅ All fiscalized invoices **remain valid**
- ✅ URA records are permanent
- ✅ Historical reports still work
- 📝 New fiscalized invoices will have `source_erp = "XERO"`

---

## ⚠️ Important Considerations

### 1. **OAuth Tokens Reset**

When you switch ERP:
- Old ERP tokens become invalid (disconnected)
- New ERP requires fresh OAuth authentication
- User must click "Connect [New ERP]" in dashboard

**Action Required:** Reconnect new ERP after switching

---

### 2. **Data Sync Stops from Old ERP**

After switch:
- No more automatic sync from old ERP
- Historical data remains accessible (read-only)
- New data comes from new ERP only

**Example:** After switching to Xero, new QuickBooks invoices won't appear

---

### 3. **ERP Configuration Changes**

Each ERP has different config:

**QuickBooks:**
```json
{
  "realm_id": "123456789",
  "refresh_token": "..."
}
```

**Xero:**
```json
{
  "tenant_id": "abc-def-ghi-jkl",
  "organization_id": "..."
}
```

**Zoho:**
```json
{
  "organization_id": "12345",
  "books_org_id": "..."
}
```

**Custom:**
```json
{
  "api_url": "https://myerp.com/api",
  "api_key": "...",
  "api_secret": "..."
}
```

**Action Required:** Provide correct config for new ERP

---

### 4. **EFRIS Credentials NEVER Change**

**Critical:** Your EFRIS credentials are issued by URA and tied to your business:
- TIN (Tax Identification Number)
- Device Number
- Private Key (.pfx certificate)
- Certificate Password

**These NEVER change** when you switch ERP systems!

---

## 🧪 Testing ERP Switch

### Test 1: Switch from QuickBooks to Xero

```powershell
# Start server
py api_multitenant.py

# Get current state
curl -X GET "http://localhost:8001/api/companies/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Switch to Xero
curl -X PUT "http://localhost:8001/api/companies/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"erp_type": "XERO", "erp_config": {"tenant_id": "test-tenant"}}'

# Verify change
curl -X GET "http://localhost:8001/api/companies/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Open dashboard in browser
# Navigate to http://localhost:8001/dashboard
# Login and select company
# Verify: Dashboard shows Xero branding (blue theme, "📊 Xero Records")
```

---

### Test 2: Switch Back to QuickBooks

```bash
curl -X PUT "http://localhost:8001/api/companies/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"erp_type": "QUICKBOOKS", "erp_config": {"realm_id": "123456789"}}'

# Dashboard will revert to QuickBooks branding (green theme)
```

---

## 📊 API Reference

### Update Company Endpoint

**Endpoint:** `PUT /api/companies/{company_id}`

**Authentication:** JWT Bearer Token (Admin/Owner only)

**Request Body:**
```json
{
  "name": "New Company Name (optional)",
  "device_no": "New device number (optional)",
  "erp_type": "XERO | QUICKBOOKS | ZOHO | CUSTOM | NONE (optional)",
  "erp_config": {
    "tenant_id": "for Xero",
    "realm_id": "for QuickBooks",
    "organization_id": "for Zoho",
    "api_url": "for Custom ERP"
  },
  "efris_test_mode": true | false (optional)
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Company Name",
  "tin": "1014409555",
  "device_no": "TZ00SD01",
  "erp_type": "XERO",
  "erp_config": {...},
  "efris_test_mode": false,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2026-01-23T10:30:00"
}
```

**Errors:**
- `400 Bad Request` - Invalid ERP type
- `403 Forbidden` - Not company admin
- `404 Not Found` - Company doesn't exist
- `500 Internal Server Error` - Database error

---

## ✅ Summary

**Your platform now supports:**

✅ **Seamless ERP switching** - Change from QuickBooks → Xero → Zoho anytime  
✅ **Preserved historical data** - Old ERP data remains in database  
✅ **Unchanged EFRIS credentials** - TIN, device number, keys stay the same  
✅ **Automatic dashboard adaptation** - UI updates to match new ERP branding  
✅ **Continuous EFRIS operations** - Fiscalization works with any ERP  

**Use cases:**
- Business migrates to better ERP system
- Temporary ERP disconnection (switch to NONE)
- Multi-ERP support for different departments
- Testing different ERP systems

**Next steps:**
1. Test ERP switching with your companies
2. Document for end users
3. Add UI button in dashboard settings
4. Consider migration wizard for smooth transitions

---

**Your platform is now production-ready for real-world ERP changes! 🎉**
