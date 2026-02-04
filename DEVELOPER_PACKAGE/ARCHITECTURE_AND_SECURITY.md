# Architecture and Security Model

## 🔑 API Key Structure

### One API Key Per Client Company

Each client company that uses your EFRIS backend gets **ONE unique API key**.

```
┌─────────────────────────────────────────┐
│ Company A (TIN: 1000123456)             │
│ API Key: efris_a1b2c3d4e5f6            │
│                                         │
│ Their ERP System (holds the key)       │
│   ├─ Frontend: User Interface          │
│   ├─ Backend: Business Logic          │
│   └─ API Key stored in: .env file     │
│                                         │
│ Developers working on Company A's ERP: │
│   ├─ Developer 1                       │
│   ├─ Developer 2                       │
│   └─ Developer 3                       │
│   → All use SAME API key in dev/staging│
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Company B (TIN: 1000789012)             │
│ API Key: efris_x9y8z7w6v5u4            │
│                                         │
│ Their ERP System (completely separate) │
│   └─ Different API key, isolated data  │
└─────────────────────────────────────────┘
```

**NOT per developer, NOT per user, NOT per device.**

One company = One API key = All their ERP systems use it.

---

## 🏗️ Authorization Architecture

### Who Controls What?

```
┌──────────────────────────────────────────────────────────┐
│                     YOUR RESPONSIBILITY                   │
│              (EFRIS Backend - Multi-tenant)              │
│                                                          │
│  ✅ Validate API key                                     │
│  ✅ Identify which company is calling                    │
│  ✅ Use correct EFRIS credentials per company           │
│  ✅ Submit to URA EFRIS                                  │
│  ✅ Store company's data separately                      │
│  ✅ Return FDN, QR code, results                         │
│                                                          │
│  ❌ NOT your job: User authentication                    │
│  ❌ NOT your job: User permissions                       │
│  ❌ NOT your job: ERP business logic                     │
└──────────────────────────────────────────────────────────┘

                            ↑
                    API Call with API Key
                            ↑

┌──────────────────────────────────────────────────────────┐
│                   CLIENT'S RESPONSIBILITY                 │
│                  (Their Custom ERP System)                │
│                                                          │
│  ✅ User login/authentication                            │
│  ✅ Role-based permissions                               │
│  ✅ Who can create invoices?                             │
│  ✅ Who can send to EFRIS?                               │
│  ✅ Approval workflows                                   │
│  ✅ Audit logs                                           │
│  ✅ Hold API key securely (environment variable)         │
│                                                          │
│  ❌ NOT their job: EFRIS technical integration           │
│  ❌ NOT their job: Certificate management                │
│  ❌ NOT their job: Multi-tenant data isolation           │
└──────────────────────────────────────────────────────────┘

                            ↑
                    User clicks button
                            ↑

┌──────────────────────────────────────────────────────────┐
│                        END USER                          │
│                                                          │
│  - Logs into their company's ERP                         │
│  - Creates invoice                                       │
│  - Clicks "Send to EFRIS"                                │
│  - ERP checks: Does this user have permission?           │
│  - If yes → ERP calls your API                           │
│  - User sees: FDN, QR code                               │
│                                                          │
│  ❌ Never sees the API key                               │
│  ❌ Never calls your API directly                        │
└──────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Model

### API Key Storage (Client's Responsibility)

**Development Environment:**
```python
# .env file (never commit to git!)
EFRIS_API_KEY=efris_a1b2c3d4e5f6
EFRIS_API_URL=http://efris-backend:8001/api/external/efris
```

**Production Environment:**
```bash
# Environment variable on server
export EFRIS_API_KEY="efris_a1b2c3d4e5f6"

# Or in config file with restricted permissions
chmod 600 /etc/myerp/config.ini
```

**NEVER:**
- ❌ Hardcode in source code
- ❌ Commit to Git/version control
- ❌ Send to frontend/JavaScript
- ❌ Include in error messages
- ❌ Log in plain text

### User Authentication (Client's Responsibility)

The ERP system authenticates users:

```python
# Their ERP backend
@app.route('/submit-invoice')
@login_required  # Their auth decorator
@require_permission('can_send_to_efris')  # Their permission check
def submit_invoice():
    # User is authenticated and authorized
    # Now call EFRIS API with company's API key
    
    response = requests.post(
        os.getenv('EFRIS_API_URL') + '/submit-invoice',
        json=invoice_data,
        headers={'X-API-Key': os.getenv('EFRIS_API_KEY')}
    )
    
    return response.json()
```

**Their users never directly interact with your API.**

---

## 🔄 Complete Flow Example

### Scenario: User submits invoice from ERP

```
1. USER ACTION
   └─ John (accountant) logs into Company A's ERP
   └─ ERP: Validates John's username/password ✓
   └─ ERP: Checks John has role "accountant" ✓

2. USER CREATES INVOICE
   └─ John fills invoice form in ERP
   └─ Invoice: INV-001, Customer: ABC Ltd, Amount: 100,000 UGX

3. USER CLICKS "SEND TO EFRIS"
   └─ ERP Frontend: Sends request to ERP Backend
   └─ ERP Backend: Checks if John can send to EFRIS
   └─ ERP Backend: ✓ Permission granted

4. ERP CALLS YOUR API
   └─ ERP Backend makes API call:
       POST http://your-server:8001/api/external/efris/submit-invoice
       Header: X-API-Key: efris_a1b2c3d4e5f6
       Body: {invoice details}

5. YOUR BACKEND PROCESSES
   └─ Validates API key "efris_a1b2c3d4e5f6"
   └─ Finds: Company A (TIN: 1000123456)
   └─ Uses Company A's EFRIS certificate
   └─ Submits to URA EFRIS
   └─ URA returns: FDN = 1234567890123456

6. YOUR BACKEND RESPONDS
   └─ Returns to ERP:
       {
         "success": true,
         "fdn": "1234567890123456",
         "qr_code": "...",
         "verification_code": "AB12CD34"
       }

7. ERP SHOWS RESULT
   └─ ERP saves FDN to their database
   └─ ERP displays QR code to John
   └─ ERP prints invoice with FDN

8. AUDIT TRAIL
   └─ ERP logs: "John submitted INV-001 to EFRIS at 10:30 AM"
   └─ Your backend logs: "Company A fiscalized invoice via API"
```

**John never knew the API key existed!**

---

## 👥 Multiple Developers Working on Same ERP

### Scenario: Company A has 3 developers building their ERP

```
┌─────────────────────────────────────────┐
│          COMPANY A                      │
├─────────────────────────────────────────┤
│ API Key: efris_a1b2c3d4e5f6            │
│                                         │
│ Development Team:                       │
│                                         │
│ Developer 1: Frontend (React)           │
│   └─ Builds UI forms                    │
│   └─ Calls Company A's backend API      │
│   └─ Never touches EFRIS API key        │
│                                         │
│ Developer 2: Backend (Python)           │
│   └─ Has API key in .env file          │
│   └─ Implements endpoint that calls     │
│       your EFRIS API                    │
│   └─ Handles user auth/permissions      │
│                                         │
│ Developer 3: Mobile App (Flutter)       │
│   └─ Calls Company A's backend          │
│   └─ Never touches EFRIS API key        │
│                                         │
└─────────────────────────────────────────┘
```

**All 3 developers use the SAME API key** (Company A's key).

**In their development environment:**

```bash
# Shared .env file (gitignored)
EFRIS_API_KEY=efris_a1b2c3d4e5f6
EFRIS_API_URL=http://efris-dev-server:8001/api/external/efris
```

**In production:**
- API key stored in environment variables
- Only backend server has access
- Frontend never sees it
- Mobile app never sees it

---

## 🔒 API Key Management

### When to Issue New API Keys

**One key per client company, period.**

```sql
-- Company A gets registered
INSERT INTO companies (company_name, tin, api_key, api_enabled)
VALUES ('Company A Ltd', '1000123456', 'efris_a1b2c3d4e5f6', true);

-- That's it! All of Company A's systems use this key.
```

### When to Rotate API Keys

**Rotate key if:**
1. ✓ Key was accidentally committed to public repo
2. ✓ Developer who had access left the company
3. ✓ Security breach suspected
4. ✓ Regular rotation policy (every 6-12 months)

**How to rotate:**

```sql
-- Generate new key for Company A
UPDATE companies 
SET api_key = 'efris_NEW_KEY_HERE',
    api_last_used = NULL
WHERE id = [company_a_id];
```

Notify Company A: "Your API key has changed. Update your .env file."

### When to Revoke Access

```sql
-- Disable Company A's API access
UPDATE companies 
SET api_enabled = false
WHERE id = [company_a_id];
```

Their API calls will now return: `401 Unauthorized`

---

## 📊 Monitoring & Audit

### What You Track (EFRIS Backend)

```sql
-- API usage by company
SELECT 
    company_name,
    COUNT(*) as api_calls_today,
    MAX(api_last_used) as last_call
FROM companies c
LEFT JOIN efris_invoices i ON i.company_id = c.id
WHERE i.created_at > CURRENT_DATE
GROUP BY company_name;
```

**You track:**
- Which company made the call (via API key)
- What operation (invoice, product, PO, credit note)
- When it happened
- Success/failure
- EFRIS response

**You DON'T track:**
- Which end user in their ERP made the request
- What permissions that user had
- Their approval workflows

### What They Track (Client's ERP)

```python
# Their audit log
{
    "timestamp": "2026-01-24 10:30:00",
    "user": "john@companya.com",
    "action": "submit_invoice_to_efris",
    "invoice_number": "INV-001",
    "result": "success",
    "fdn": "1234567890123456"
}
```

**They track:**
- Which user performed the action
- When they did it
- What data was submitted
- What permissions they had
- Approval chain

---

## 🎯 Summary

### Your Role (EFRIS Backend Provider)

✅ **What you provide:**
- Multi-tenant EFRIS API
- One API key per client company
- Secure EFRIS integration
- Data isolation between companies
- FDN, QR code generation

❌ **What you DON'T handle:**
- User authentication in their ERP
- User permissions in their ERP
- Business logic in their ERP
- Which users can do what
- Their internal workflows

### Client's Role (ERP System Owner)

✅ **What they handle:**
- User authentication (login)
- User permissions (roles)
- Business logic
- Approval workflows
- Audit logs
- Hold API key securely

❌ **What they DON'T handle:**
- EFRIS technical integration
- Certificate management
- URA API communication
- Multi-tenant infrastructure

### Clean Separation of Concerns

```
┌────────────────────────────────────────────────┐
│  You: Technical EFRIS integration layer       │
│  Input: API key + invoice data                │
│  Output: FDN + QR code                         │
└────────────────────────────────────────────────┘
                    ↑
                    │
┌────────────────────────────────────────────────┐
│  Client: Business application layer            │
│  Input: User credentials + invoice data        │
│  Output: UI showing FDN + QR code              │
└────────────────────────────────────────────────┘
```

**Perfect separation. No overlap. Clean architecture.** ✅

---

## 🔄 Alternative: OAuth 2.0 (Future Enhancement)

If you want more granular control in the future, you could implement OAuth 2.0:

```
1. Client's ERP redirects user to your auth server
2. User authorizes: "Allow Company A ERP to access EFRIS?"
3. You issue access token (expires in 1 hour)
4. ERP uses access token for API calls
5. Token expires, ERP requests new one

Benefits:
- Token expiration
- Revoke specific sessions
- Audit which ERP instance called
- Rate limiting per session

Complexity:
- More complex to implement
- Client needs to handle OAuth flow
- Token refresh logic required
```

**Current simple API key approach is fine for most use cases.**

Only implement OAuth if:
- Client has multiple ERP instances
- Need per-session auditing
- Need fine-grained revocation
- Have security compliance requirements

---

## 📞 Support Scenarios

### Scenario 1: "Our developer left, is the API key compromised?"

**Your response:**
```
I'll generate a new API key for your company.

Old key: efris_a1b2c3d4e5f6 (will be disabled)
New key: efris_NEW_KEY_HERE (active now)

Update your .env file and redeploy.
Old key will stop working immediately.
```

### Scenario 2: "We have 5 developers, do we need 5 API keys?"

**Your response:**
```
No, one API key per company.

Your company has ONE API key.
All your developers use the same key in development.
Your production server uses the same key.

Your ERP system controls which users can trigger EFRIS operations.
We just validate that it's your company calling us.
```

### Scenario 3: "Can we give different permissions to different users?"

**Your response:**
```
Yes, but that's handled in YOUR ERP system, not ours.

In your ERP:
- User A: Can create invoices, can send to EFRIS
- User B: Can create invoices, CANNOT send to EFRIS
- User C: Can only view invoices

When User B tries to send to EFRIS, your ERP should block it
BEFORE calling our API.

We only check: Is this API key valid for a company?
You check: Does this user have permission?
```

---

**This architecture gives you maximum control while keeping clients' ERPs independent!** 🎯
