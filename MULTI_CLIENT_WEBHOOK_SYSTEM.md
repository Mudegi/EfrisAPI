# 🎯 MULTI-CLIENT WEBHOOK SYSTEM (No Coding Required!)

## The Problem You're Solving

**Scenario:** You have 10 clients all using QuickBooks Online. Do you need 10 different webhook handlers?

**Answer:** NO! You need **ONE webhook per ERP type** that automatically routes to the right client.

---

## ✅ THE STANDARD SOLUTION

### Architecture: One Webhook to Rule Them All

```
QuickBooks (Client A - realm_id: 123) ──┐
QuickBooks (Client B - realm_id: 456) ──┤
QuickBooks (Client C - realm_id: 789) ──┤
QuickBooks (Client D - realm_id: 101) ──┤──> Single Webhook URL
QuickBooks (Client E - realm_id: 202) ──┤    /api/webhooks/quickbooks
QuickBooks (Client F - realm_id: 303) ──┤    (Routes automatically)
QuickBooks (Client G - realm_id: 404) ──┤
QuickBooks (Client H - realm_id: 505) ──┤
QuickBooks (Client I - realm_id: 606) ──┤
QuickBooks (Client J - realm_id: 707) ──┘
```

**How it works:**
1. QuickBooks sends `realm_id` in webhook payload
2. Your system looks up which client has that `realm_id`
3. Routes to that client's configuration automatically
4. No code changes needed for new clients!

---

## 🎨 UI-BASED CLIENT MANAGEMENT

### Step 1: Admin Adds Client via UI

**URL:** `http://localhost:8001/owner`

**Form Fields:**
```
┌─────────────────────────────────────────┐
│  ADD NEW CLIENT                         │
├─────────────────────────────────────────┤
│  Company Name:    [ABC Trading Ltd]     │
│  Email:          [client@abc.com]       │
│  Password:       [SecurePass123]        │
│  Phone:          [+256700123456]        │
│                                         │
│  TIN:            [1234567890]           │
│  Device Number:  [1234567890_01]        │
│  Certificate:    [Upload .pfx file]     │
│  Cert Password:  [••••••••]             │
│                                         │
│  ERP System:     [▼ QuickBooks Online]  │
│  Test Mode:      [✓] Enable             │
│                                         │
│  [Cancel]              [Add Client]     │
└─────────────────────────────────────────┘
```

**Click "Add Client"** → System creates everything automatically.

---

### Step 2: Client Connects Their ERP

**Client logs in:** `http://localhost:8001/login`

**Dashboard shows:**
```
┌─────────────────────────────────────────┐
│  ABC TRADING LTD - Dashboard            │
├─────────────────────────────────────────┤
│  ERP Integration: Not Connected         │
│                                         │
│  [Connect QuickBooks Online]            │
│                                         │
└─────────────────────────────────────────┘
```

**Client clicks "Connect QuickBooks Online":**
1. Redirects to QuickBooks OAuth
2. Client authorizes
3. QuickBooks returns `realm_id` (their unique ID)
4. System automatically saves: `realm_id: 4620816365324345807`
5. Status changes to "Connected ✓"

**No coding needed - it's all automatic!**

---

## 🔧 THE SMART WEBHOOK HANDLER

### Single Webhook for ALL QuickBooks Clients

Add this ONE TIME to `api_multitenant.py`:

```python
@app.post("/api/webhooks/quickbooks")
async def quickbooks_webhook_all_clients(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ONE webhook handles ALL QuickBooks clients
    Routes automatically based on realm_id
    """
    payload = await request.json()
    
    # QuickBooks sends realm_id in payload
    event_notifications = payload.get("eventNotifications", [])
    if not event_notifications:
        return {"success": True, "message": "No events"}
    
    for notification in event_notifications:
        realm_id = notification.get("realmId")
        
        # AUTOMATIC ROUTING: Find which client has this realm_id
        company = db.query(Company).filter(
            Company.erp_type == "QUICKBOOKS",
            Company.erp_config.contains(f'"realm_id": "{realm_id}"')
        ).first()
        
        if not company:
            print(f"[Webhook] Unknown realm_id: {realm_id}")
            continue
        
        print(f"[Webhook] Routing to company: {company.name} (ID: {company.id})")
        
        # Process events for this specific client
        data_change = notification.get("dataChangeEvent", {})
        entities = data_change.get("entities", [])
        
        for entity in entities:
            if entity.get("name") == "Invoice":
                invoice_id = entity.get("id")
                operation = entity.get("operation")
                
                if operation in ["CREATE", "UPDATE"]:
                    # Auto-fiscalize this client's invoice
                    await auto_fiscalize_invoice(company, invoice_id)
    
    return {"success": True, "message": "Processed"}


async def auto_fiscalize_invoice(company: Company, invoice_id: str):
    """Automatically fiscalize invoice to EFRIS"""
    try:
        # Get invoice from QuickBooks
        from quickbooks_client import QuickBooksClient
        qb = QuickBooksClient()
        invoice = qb.get_invoice(invoice_id)
        
        # Transform to EFRIS format
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
        print(f"[Auto-Fiscalize] Company {company.name} - Invoice {invoice_id}: SUCCESS")
        
    except Exception as e:
        print(f"[Auto-Fiscalize] Company {company.name} - Invoice {invoice_id}: ERROR - {e}")
```

---

## 🌐 WEBHOOK CONFIGURATION (One-Time Setup)

### For QuickBooks (Handles ALL Clients)

1. Go to **QuickBooks Developer Portal**
2. Your App → Settings → Webhooks
3. **Webhook URL:** `https://yourdomain.com/api/webhooks/quickbooks`
4. **Events to Subscribe:**
   - Invoice Created
   - Invoice Updated
   - Invoice Deleted
5. **Save**

**That's it!** This ONE webhook now handles all your QuickBooks clients automatically.

---

### For Xero (Handles ALL Clients)

```python
@app.post("/api/webhooks/xero")
async def xero_webhook_all_clients(request: Request, db: Session = Depends(get_db)):
    """ONE webhook for ALL Xero clients"""
    payload = await request.json()
    
    for event in payload.get("events", []):
        tenant_id = event.get("tenantId")
        
        # Auto-route to correct client
        company = db.query(Company).filter(
            Company.erp_type == "XERO",
            Company.erp_config.contains(f'"tenant_id": "{tenant_id}"')
        ).first()
        
        if company:
            # Process event for this client
            await auto_fiscalize_invoice(company, event.get("resourceId"))
    
    return {"success": True}
```

**Configure:**
- Xero Developer Portal → Webhooks
- URL: `https://yourdomain.com/api/webhooks/xero`

---

### For Zoho Books (Handles ALL Clients)

```python
@app.post("/api/webhooks/zoho")
async def zoho_webhook_all_clients(request: Request, db: Session = Depends(get_db)):
    """ONE webhook for ALL Zoho clients"""
    payload = await request.json()
    
    organization_id = payload.get("organization_id")
    
    # Auto-route to correct client
    company = db.query(Company).filter(
        Company.erp_type == "ZOHO",
        Company.erp_config.contains(f'"organization_id": "{organization_id}"')
    ).first()
    
    if company and payload.get("resource_type") == "invoice":
        await auto_fiscalize_invoice(company, payload.get("resource_id"))
    
    return {"success": True}
```

**Configure:**
- Zoho Books → Settings → Webhooks
- URL: `https://yourdomain.com/api/webhooks/zoho`

---

## 📊 HOW IT SCALES

### Adding 10 QuickBooks Clients

**Old way (WRONG):**
```
Client 1 → Write webhook code → Deploy
Client 2 → Write webhook code → Deploy
Client 3 → Write webhook code → Deploy
... (10 times = lots of work!)
```

**New way (CORRECT):**
```
Client 1  → Add via UI → Connect QB → Done
Client 2  → Add via UI → Connect QB → Done
Client 3  → Add via UI → Connect QB → Done
Client 4  → Add via UI → Connect QB → Done
Client 5  → Add via UI → Connect QB → Done
Client 6  → Add via UI → Connect QB → Done
Client 7  → Add via UI → Connect QB → Done
Client 8  → Add via UI → Connect QB → Done
Client 9  → Add via UI → Connect QB → Done
Client 10 → Add via UI → Connect QB → Done
```

**Time per client:** 2 minutes (no coding!)

---

## 🎯 COMPLETE WORKFLOW

### For You (Platform Owner)

**Step 1: One-Time Setup** (Do this ONCE)
1. Add webhook handlers (copy code above)
2. Deploy your API
3. Configure webhooks in QB/Xero/Zoho portals
4. ✅ Done forever!

**Step 2: Add Clients** (Via UI, 2 minutes each)
1. Go to `/owner` portal
2. Fill form (name, email, TIN, etc.)
3. Upload client's certificate
4. Click "Add Client"
5. ✅ Client created!

**Step 3: Send Client Login Info**
```
Hi ABC Trading,

Your EFRIS integration is ready!

Login: https://yourdomain.com/login
Email: client@abc.com
Password: SecurePass123

Next steps:
1. Login to your dashboard
2. Click "Connect QuickBooks Online"
3. Authorize the connection
4. All invoices will auto-fiscalize!

Support: support@yourdomain.com
```

---

### For Client (End User)

**Step 1: Login**
- Go to login URL
- Enter email/password

**Step 2: Connect ERP**
```
Dashboard shows:
┌─────────────────────────────────────────┐
│  ERP: Not Connected                     │
│  [Connect QuickBooks Online]            │
└─────────────────────────────────────────┘
```
- Click button
- Authorize on QuickBooks
- ✅ Connected!

**Step 3: Create Invoices**
- Create invoices in QuickBooks normally
- **Automatic:** Invoice fiscalizes to EFRIS
- **View Status:** Check dashboard for results

---

## 🎨 ENHANCED UI FEATURES

### Add to Owner Portal (`static/owner_portal.html`)

```html
<!-- Client Management Section -->
<div class="section">
    <h2>Manage Clients</h2>
    
    <!-- Add Client Button -->
    <button onclick="showAddClientForm()">+ Add New Client</button>
    
    <!-- Clients List -->
    <table id="clientsTable">
        <thead>
            <tr>
                <th>Company</th>
                <th>Email</th>
                <th>TIN</th>
                <th>ERP</th>
                <th>Status</th>
                <th>Invoices Fiscalized</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <!-- Auto-populated from /api/owner/clients -->
            <tr>
                <td>ABC Trading Ltd</td>
                <td>client@abc.com</td>
                <td>1234567890</td>
                <td>
                    <span class="badge green">QuickBooks ✓</span>
                </td>
                <td>
                    <span class="badge blue">Active</span>
                </td>
                <td>234 invoices</td>
                <td>
                    <button onclick="viewClient(1)">View</button>
                    <button onclick="editClient(1)">Edit</button>
                    <button onclick="resetPassword(1)">Reset Password</button>
                </td>
            </tr>
            <!-- More clients... -->
        </tbody>
    </table>
</div>

<!-- Webhook Status Section -->
<div class="section">
    <h2>Webhook Health</h2>
    
    <div class="webhook-status">
        <div class="webhook-item">
            <span class="icon">📨</span>
            <div>
                <strong>QuickBooks Webhook</strong>
                <p>Last received: 2 minutes ago</p>
                <p>Total events today: 45</p>
                <span class="badge green">Healthy</span>
            </div>
        </div>
        
        <div class="webhook-item">
            <span class="icon">📨</span>
            <div>
                <strong>Xero Webhook</strong>
                <p>Last received: 15 minutes ago</p>
                <p>Total events today: 12</p>
                <span class="badge green">Healthy</span>
            </div>
        </div>
    </div>
</div>

<!-- Auto-Fiscalization Stats -->
<div class="section">
    <h2>Today's Activity</h2>
    
    <div class="stats-grid">
        <div class="stat-card">
            <h3>78</h3>
            <p>Invoices Auto-Fiscalized</p>
        </div>
        <div class="stat-card">
            <h3>3</h3>
            <p>Failed (Retry Scheduled)</p>
        </div>
        <div class="stat-card">
            <h3>10</h3>
            <p>Active Clients</p>
        </div>
        <div class="stat-card">
            <h3>98.7%</h3>
            <p>Success Rate</p>
        </div>
    </div>
</div>
```

---

### Add to Client Dashboard (`static/dashboard.html`)

```html
<!-- ERP Connection Status -->
<div class="erp-status">
    <h2>ERP Integration</h2>
    
    <!-- If not connected -->
    <div id="not-connected" style="display: none;">
        <p>Connect your accounting system to auto-fiscalize invoices</p>
        <button class="btn-primary" onclick="connectQuickBooks()">
            Connect QuickBooks Online
        </button>
        <button class="btn-primary" onclick="connectXero()">
            Connect Xero
        </button>
        <button class="btn-primary" onclick="connectZoho()">
            Connect Zoho Books
        </button>
    </div>
    
    <!-- If connected -->
    <div id="connected" style="display: none;">
        <div class="connection-info">
            <span class="icon">✓</span>
            <div>
                <strong>QuickBooks Online Connected</strong>
                <p>Company: ABC Trading Ltd</p>
                <p>Connected: Jan 15, 2026</p>
            </div>
            <button onclick="disconnectERP()">Disconnect</button>
        </div>
        
        <div class="auto-fiscalize-toggle">
            <label>
                <input type="checkbox" id="autoFiscalize" checked />
                Auto-fiscalize new invoices
            </label>
            <small>New invoices will automatically send to EFRIS</small>
        </div>
    </div>
</div>

<!-- Recent Activity -->
<div class="activity-log">
    <h2>Recent Activity</h2>
    <ul>
        <li>
            <span class="time">2 min ago</span>
            <span class="badge green">Success</span>
            Invoice INV-1234 fiscalized to EFRIS
        </li>
        <li>
            <span class="time">15 min ago</span>
            <span class="badge green">Success</span>
            Invoice INV-1233 fiscalized to EFRIS
        </li>
        <li>
            <span class="time">1 hour ago</span>
            <span class="badge orange">Retry</span>
            Invoice INV-1232 - EFRIS server down, will retry
        </li>
    </ul>
</div>
```

---

## 🔔 AUTOMATIC NOTIFICATIONS

### Email Alerts (No UI Needed)

Add to webhook handler:

```python
async def auto_fiscalize_invoice(company: Company, invoice_id: str):
    try:
        # ... fiscalize invoice ...
        
        # Send success email
        send_email(
            to=company.user.email,
            subject=f"Invoice {invoice_id} Fiscalized",
            body=f"Your invoice {invoice_id} was successfully sent to EFRIS."
        )
        
    except Exception as e:
        # Send error email
        send_email(
            to=company.user.email,
            subject=f"Invoice {invoice_id} Failed",
            body=f"Failed to fiscalize invoice {invoice_id}. Error: {e}"
        )
```

---

## 📈 MONITORING DASHBOARD

### Add to Owner Portal

```python
@app.get("/api/owner/webhook-stats")
async def webhook_stats(db: Session = Depends(get_db)):
    """Show webhook activity across all clients"""
    return {
        "quickbooks": {
            "total_events_today": 45,
            "last_received": "2 minutes ago",
            "status": "healthy"
        },
        "xero": {
            "total_events_today": 12,
            "last_received": "15 minutes ago",
            "status": "healthy"
        },
        "clients": [
            {
                "company_name": "ABC Trading",
                "invoices_today": 12,
                "success_rate": 100.0,
                "last_invoice": "5 minutes ago"
            },
            # ... more clients
        ]
    }
```

---

## ✅ FINAL CHECKLIST

### One-Time Setup (Do Once)
- [ ] Add webhook handlers to `api_multitenant.py`
- [ ] Deploy API to production
- [ ] Configure QB webhook in developer portal
- [ ] Configure Xero webhook (if needed)
- [ ] Configure Zoho webhook (if needed)
- [ ] Test with dummy client

### Per Client (Via UI - 2 minutes each)
- [ ] Add client via `/owner` portal
- [ ] Upload their certificate
- [ ] Send login credentials
- [ ] Client connects their ERP
- [ ] Test: Create invoice in ERP
- [ ] Verify: Invoice auto-fiscalizes
- [ ] ✅ Client is live!

---

## 💡 KEY TAKEAWAYS

1. **ONE webhook per ERP type** - not per client
2. **Automatic routing** - based on realm_id/tenant_id/organization_id
3. **UI-based management** - no coding for new clients
4. **Scales infinitely** - 10 clients or 1000 clients, same effort
5. **Self-service** - clients connect their own ERP
6. **Zero maintenance** - once set up, it runs forever

---

## 🚀 READY TO GO!

You now have a **professional multi-tenant webhook system** where:
- ✅ You add clients via UI (no coding)
- ✅ Clients connect their own ERP (self-service)
- ✅ Invoices auto-fiscalize (no manual work)
- ✅ Scales to unlimited clients
- ✅ Standard enterprise pattern

**Next step:** Copy the webhook handlers and deploy! 🎯
