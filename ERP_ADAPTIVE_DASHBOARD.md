# 🎨 ERP-Adaptive Dashboard Guide

## Overview

The dashboard **automatically adapts** based on which ERP system each client is using. The UI dynamically changes colors, text, buttons, and connection flows for QuickBooks, Xero, Zoho, or Custom ERPs.

---

## 🔄 How It Works

### 1. **ERP Configuration Object**

Located in `dashboard_multitenant.html`:

```javascript
const ERP_CONFIGS = {
    QUICKBOOKS: {
        name: "QuickBooks",
        icon: "📘",
        color: "#2ca01c",  // QuickBooks green
        navTitle: "QuickBooks Records",
        connectText: "Connect QuickBooks",
        syncButtonText: "Import from QuickBooks",
        authUrl: "/api/quickbooks/auth",
        supportsOAuth: true
    },
    XERO: {
        name: "Xero",
        icon: "📊",
        color: "#13B5EA",  // Xero blue
        navTitle: "Xero Records",
        connectText: "Connect Xero",
        syncButtonText: "Import from Xero",
        authUrl: "/api/xero/auth",
        supportsOAuth: true
    },
    ZOHO: {
        name: "Zoho Books",
        icon: "📗",
        color: "#e42527",  // Zoho red
        navTitle: "Zoho Records",
        connectText: "Connect Zoho Books",
        syncButtonText: "Import from Zoho",
        authUrl: "/api/zoho/auth",
        supportsOAuth: true
    },
    CUSTOM: {
        name: "Your ERP",
        icon: "🔌",
        color: "#7f8c8d",  // Neutral gray
        navTitle: "ERP Records",
        connectText: "Configure ERP Connection",
        syncButtonText: "Import from ERP",
        authUrl: null,
        supportsOAuth: false  // Uses API keys instead
    }
};
```

### 2. **Dynamic Updates**

When a user switches companies, `updateERPConfig()` function:

1. **Detects ERP Type** from `company.erp_type` field
2. **Loads Correct Config** from `ERP_CONFIGS` object
3. **Updates UI Elements**:
   - Sidebar navigation title
   - Connection button text
   - Banner colors (matches ERP brand)
   - Icon throughout the UI
   - OAuth vs Manual config flow

---

## 📊 What Changes For Each ERP?

### QuickBooks Client Sees:

**Sidebar:**
```
📘 QuickBooks Records
  📦 Items
  📄 Invoices
  📋 Purchase Orders
  📝 Credit Memos
```

**Top Bar:**
```
🔗 📘 Connect QuickBooks
```

**Connection Banner:**
```
⚠️ Connect QuickBooks
Sync your QuickBooks invoices and products automatically to EFRIS
[Connect Now →]  ← Green button (#2ca01c)
```

**Connected Banner:**
```
✅ 📘 QuickBooks Connected
Last synced: Just now
[🔄 Sync Now]  [Disconnect]
```

---

### Xero Client Sees:

**Sidebar:**
```
📊 Xero Records
  📦 Items
  📄 Invoices
  📋 Purchase Orders
  📝 Credit Memos
```

**Top Bar:**
```
🔗 📊 Connect Xero
```

**Connection Banner:**
```
⚠️ Connect Xero
Sync your Xero invoices and products automatically to EFRIS
[Connect Now →]  ← Blue button (#13B5EA)
```

**Connected Banner:**
```
✅ 📊 Xero Connected
Last synced: Just now
[🔄 Sync Now]  [Disconnect]
```

---

### Zoho Books Client Sees:

**Sidebar:**
```
📗 Zoho Records
  📦 Items
  📄 Invoices
  📋 Purchase Orders
  📝 Credit Memos
```

**Top Bar:**
```
🔗 📗 Connect Zoho Books
```

**Connection Banner:**
```
⚠️ Connect Zoho Books
Sync your Zoho Books invoices and products automatically to EFRIS
[Connect Now →]  ← Red button (#e42527)
```

**Connected Banner:**
```
✅ 📗 Zoho Books Connected
Last synced: Just now
[🔄 Sync Now]  [Disconnect]
```

---

### Custom ERP Client Sees:

**Sidebar:**
```
🔌 ERP Records
  📦 Items
  📄 Invoices
  📋 Purchase Orders
  📝 Credit Memos
```

**Top Bar:**
```
🔗 🔌 Configure ERP Connection
```

**Connection Banner:**
```
⚠️ Connect Your ERP
Configure API credentials to sync with your accounting system
[Configure Now →]  ← Gray button (#7f8c8d)
```

**Connected Banner:**
```
✅ 🔌 Your ERP Connected
Last synced: Just now
[🔄 Sync Now]  [Disconnect]
```

---

## 🎨 Visual Examples

### Example 1: Multi-Company User

**Scenario:** A reseller manages 3 clients:
- Client A → QuickBooks
- Client B → Xero
- Client C → Zoho

**What Happens:**

1. **Login** → Dashboard loads
2. **Select "Client A"** → UI turns green, shows QuickBooks branding
3. **Switch to "Client B"** → UI turns blue, shows Xero branding
4. **Switch to "Client C"** → UI turns red, shows Zoho branding

All **without page reload** - instant visual feedback!

---

### Example 2: New Client Onboarding

**Reseller creates new client:**

1. **Set ERP Type** in reseller portal:
   ```
   Company Name: ABC Ltd
   ERP Type: [Xero ▼]
   ```

2. **Client logs in** to their dashboard:
   - Sees Xero branding everywhere
   - Clicks "Connect Xero" button
   - OAuth popup opens for Xero authentication
   - Returns to dashboard → "✅ Xero Connected"

3. **If they had chosen "Custom ERP":**
   - Would see generic branding
   - Would see "Configure API" instead of OAuth
   - Would enter API key manually

---

## 🔧 Technical Implementation

### How Company Data Includes ERP Type

In `database/models.py`:

```python
class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    tin = Column(String, nullable=False, unique=True)
    erp_type = Column(String, default="QUICKBOOKS")  # ← This field!
    erp_config = Column(JSON, default={})
    # ... other fields
```

### When User Fetches Companies

API returns:

```json
[
  {
    "id": 1,
    "name": "ABC Ltd",
    "tin": "1234567890",
    "erp_type": "XERO",  // ← Dashboard reads this
    "erp_config": {
      "tenant_id": "xxx-xxx-xxx"
    }
  },
  {
    "id": 2,
    "name": "XYZ Corp",
    "tin": "9876543210",
    "erp_type": "QUICKBOOKS",  // ← Dashboard reads this
    "erp_config": {
      "realm_id": "123456789"
    }
  }
]
```

### JavaScript Function Flow

```javascript
// 1. User switches company
async function switchCompany() {
    currentCompany = companies.find(c => c.id == companyId);
    updateERPConfig();  // ← Triggers ERP detection
    await loadCompanyData();
}

// 2. Update ERP config
function updateERPConfig() {
    const erpType = currentCompany.erp_type.toUpperCase();
    currentERPConfig = ERP_CONFIGS[erpType];
    
    // Update all UI elements
    document.getElementById('erpNavTitle').textContent = 
        `${currentERPConfig.icon} ${currentERPConfig.navTitle}`;
    
    // Update banner colors
    document.getElementById('erpConnectionBanner').style.background = 
        `linear-gradient(135deg, ${currentERPConfig.color} 0%, ...)`;
    
    // Update all buttons
    // ... etc
}
```

---

## 🚀 Connection Flow Differences

### OAuth ERPs (QuickBooks, Xero, Zoho)

1. **User clicks "Connect QuickBooks"**
2. **Popup opens** → `https://api.example.com/api/quickbooks/auth?company_id=123`
3. **Backend redirects** to QuickBooks OAuth page
4. **User authorizes** → QuickBooks redirects back with tokens
5. **Backend stores tokens** in `company.erp_config`
6. **Popup closes** → Dashboard shows "✅ QuickBooks Connected"

### Manual ERPs (Custom)

1. **User clicks "Configure ERP Connection"**
2. **Modal opens** with form:
   ```
   API Endpoint: [_____________________]
   API Key:      [_____________________]
   Secret:       [_____________________]
   [Save Configuration]
   ```
3. **Backend validates** connection
4. **Stores credentials** in `company.erp_config` (encrypted)
5. **Modal closes** → Dashboard shows "✅ Your ERP Connected"

---

## 📝 Adding a New ERP

### Example: Adding Sage 50

1. **Add to ERP_CONFIGS:**

```javascript
SAGE50: {
    name: "Sage 50",
    icon: "📙",
    color: "#00A14B",  // Sage green
    navTitle: "Sage 50 Records",
    connectText: "Connect Sage 50",
    syncButtonText: "Import from Sage 50",
    authUrl: "/api/sage50/auth",
    supportsOAuth: false  // Uses API key
}
```

2. **Add backend route** in `api_multitenant.py`:

```python
@app.get("/api/sage50/auth")
async def sage50_auth(company_id: int):
    # Show API key configuration page
    return templates.TemplateResponse("sage50_config.html", ...)
```

3. **Create adapter** in `erp_adapters.py`:

```python
class Sage50Adapter(ERPAdapter):
    async def authenticate(self) -> bool:
        # Validate API key
        pass
    
    async def get_invoices(self, ...):
        # Fetch from Sage 50 API
        pass
```

4. **Update database** (migration):

```sql
-- Allow 'SAGE50' as valid erp_type
ALTER TABLE companies 
  ADD CONSTRAINT check_erp_type 
  CHECK (erp_type IN ('QUICKBOOKS', 'XERO', 'ZOHO', 'SAGE50', 'CUSTOM'));
```

**Done!** Dashboard will automatically show Sage 50 branding for any company with `erp_type = "SAGE50"`.

---

## 🎯 Benefits

### For End Users (Clients):

✅ **Familiar Branding** - See their ERP's logo/colors  
✅ **No Confusion** - Clear which system they're connecting  
✅ **Seamless UX** - OAuth flows work natively for their ERP  
✅ **Professional** - Looks like it was built specifically for them

### For You (Platform Owner):

✅ **Single Codebase** - One dashboard supports all ERPs  
✅ **Easy Expansion** - Add new ERPs by editing one config object  
✅ **Multi-Tenant** - Each client sees their own ERP branding  
✅ **White Label Ready** - Can customize per ERP without forking code

### For Resellers:

✅ **Flexible Offering** - Support clients on different ERPs  
✅ **Easy Onboarding** - Just select ERP type when creating client  
✅ **No Technical Work** - Dashboard adapts automatically  
✅ **Professional Image** - Show clients you support their ERP natively

---

## 🔍 Testing the Adaptive Dashboard

### Test 1: QuickBooks Company

```powershell
# Login to dashboard
# Select a company with erp_type = "QUICKBOOKS"
# Verify:
- Sidebar says "📘 QuickBooks Records"
- Top bar says "Connect QuickBooks"
- Banner is green (#2ca01c)
- Connect button opens QuickBooks OAuth
```

### Test 2: Switch Between ERPs

```powershell
# Create 3 test companies with different erp_types
py -c "
from database.connection import SessionLocal
from database.models import Company

db = SessionLocal()

# Company 1: QuickBooks
c1 = Company(name='QB Test', tin='1111111111', erp_type='QUICKBOOKS')
db.add(c1)

# Company 2: Xero
c2 = Company(name='Xero Test', tin='2222222222', erp_type='XERO')
db.add(c2)

# Company 3: Zoho
c3 = Company(name='Zoho Test', tin='3333333333', erp_type='ZOHO')
db.add(c3)

db.commit()
print('✓ Created 3 test companies')
"

# Login and switch between companies
# Verify UI changes instantly:
# QB Test → Green + QuickBooks branding
# Xero Test → Blue + Xero branding
# Zoho Test → Red + Zoho branding
```

### Test 3: Custom ERP

```powershell
# Create company with CUSTOM erp_type
# Verify:
- Sidebar says "🔌 ERP Records"
- Top bar says "Configure ERP Connection"
- Banner is gray (#7f8c8d)
- Connect button shows manual config (not OAuth)
```

---

## 🚨 Important Notes

### 1. **Database Field Required**

Every company **must have** `erp_type` set:

```sql
SELECT id, name, erp_type FROM companies;

id | name        | erp_type
---|-------------|------------
1  | ABC Ltd     | QUICKBOOKS
2  | XYZ Corp    | XERO
3  | 123 Inc     | NULL  ← ⚠️ Will default to NONE
```

**Fix missing erp_types:**

```python
from database.connection import SessionLocal
from database.models import Company

db = SessionLocal()
companies = db.query(Company).filter(Company.erp_type == None).all()

for c in companies:
    c.erp_type = "QUICKBOOKS"  # or ask user
    
db.commit()
print(f'Updated {len(companies)} companies')
```

### 2. **Case Sensitivity**

ERP type comparison is **case-insensitive**:

```javascript
const erpType = (company.erp_type || 'NONE').toUpperCase();
// Accepts: 'quickbooks', 'QuickBooks', 'QUICKBOOKS'
```

But database should store **UPPERCASE**:

```python
company.erp_type = "QUICKBOOKS"  # ✅ Recommended
company.erp_type = "quickbooks"  # ⚠️ Works but not standard
```

### 3. **Fallback to NONE**

If `erp_type` is unrecognized:

```javascript
currentERPConfig = ERP_CONFIGS[erpType] || ERP_CONFIGS.NONE;
// Unknown ERP → Shows generic "Connect Accounting Software"
```

---

## 📖 Summary

The dashboard is now **fully adaptive** to each client's ERP system:

| ERP Type | Icon | Color | OAuth | UI Branding |
|----------|------|-------|-------|-------------|
| **QuickBooks** | 📘 | Green (#2ca01c) | ✅ Yes | QuickBooks |
| **Xero** | 📊 | Blue (#13B5EA) | ✅ Yes | Xero |
| **Zoho Books** | 📗 | Red (#e42527) | ✅ Yes | Zoho |
| **Custom** | 🔌 | Gray (#7f8c8d) | ❌ Manual | Generic |
| **None** | ⚙️ | Gray (#95a5a6) | ❌ N/A | Generic |

**No separate dashboards needed** - one codebase serves all clients with personalized branding! 🎉
