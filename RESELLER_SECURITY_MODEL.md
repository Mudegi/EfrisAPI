# CRITICAL SECURITY MODEL: Reseller Permissions

## 🚨 **SECURITY INCIDENT THAT LED TO THIS CHANGE**

**Real-world case from Uganda EFRIS service operator:**

> "2 resellers removed clients from the platform and they reported to URA and they nearly canceled his license"

### What Happened:
- Platform gave resellers ability to add/delete clients
- 2 malicious resellers deleted clients from system
- Resellers reported issues to Uganda Revenue Authority (URA)
- Platform owner nearly lost their EFRIS integration license
- **Business-ending risk from bad actors**

---

## ✅ **NEW SECURITY MODEL (Implemented)**

### Friend's Advice:
> "don't let resellers add clients, they should only bring you clients, then I do configuration by myself"

### Core Principles:
1. **Resellers REFER clients** (cannot add directly)
2. **Owner CONFIGURES all EFRIS credentials** (certificates, devices)
3. **Resellers VIEW ONLY** their referred clients
4. **Owner-only deletion** (prevents sabotage)
5. **Audit logs** for URA compliance

---

## 📋 **WORKFLOW: How It Works Now**

### Step 1: Reseller Submits Referral
**Endpoint:** `POST /api/reseller/submit-referral`

Reseller provides:
- Company name
- Client name & email
- TIN (Tax Identification Number)
- Device number (optional)
- Phone number
- Notes

**What reseller CANNOT provide:**
- ❌ EFRIS certificate (.pfx file)
- ❌ Certificate password
- ❌ Direct client access

**Result:** Referral goes to "pending" status, awaiting owner approval

---

### Step 2: Owner Reviews Referral
**Endpoint:** `GET /api/owner/pending-referrals`

Owner sees:
- Reseller who submitted referral
- Company details (name, TIN, contact info)
- Reseller's notes about the client
- Submission date

---

### Step 3: Owner Approves & Configures
**Endpoint:** `POST /api/owner/approve-referral/{referral_id}`

Owner provides:
- ✅ Client login password
- ✅ EFRIS certificate (.pfx file upload)
- ✅ Certificate password
- ✅ EFRIS environment (test/production)

**System automatically:**
- Creates client user account
- Creates company with EFRIS credentials
- Links client to reseller (parent_id)
- Updates referral status to "approved"
- Logs action for audit trail
- Returns client login URL

---

### Step 4: Owner Sends Credentials to Client
Owner receives:
```
Client Login URL: http://127.0.0.1:8001/client/login
Client Email: client@company.com
Password: [generated]

Send these credentials to your client directly.
```

---

### Step 5: Reseller Views Client Status
**Endpoint:** `GET /api/reseller/clients`

Reseller sees **READ-ONLY** list of their clients:
- Client name & company
- TIN
- Status (active, issues, pending)
- Last activity

**What reseller CANNOT do:**
- ❌ Edit client settings
- ❌ Delete/deactivate clients
- ❌ Access EFRIS credentials
- ❌ View client dashboard

---

## 🔒 **SECURITY CHANGES IMPLEMENTED**

### ❌ **REMOVED (Dangerous Endpoints):**

1. **`POST /api/reseller/clients`** - Let resellers add clients directly
   - Allowed certificate upload by reseller
   - Created security vulnerability
   
2. **`DELETE /api/reseller/clients/{id}`** - Let resellers delete clients
   - Used by malicious resellers to sabotage platform
   - Caused URA compliance issues

### ✅ **ADDED (Safe Endpoints):**

1. **`POST /api/reseller/submit-referral`**
   - Reseller submits client info only
   - No certificates, no direct access
   
2. **`GET /api/reseller/referrals`**
   - View own referrals and status
   
3. **`GET /api/owner/pending-referrals`**
   - Owner sees all pending referrals
   
4. **`POST /api/owner/approve-referral/{id}`**
   - Owner configures and approves
   
5. **`POST /api/owner/reject-referral/{id}`**
   - Owner can reject with reason

---

## 📊 **DATABASE CHANGES**

### New Table: `client_referrals`

```sql
CREATE TABLE client_referrals (
    id INTEGER PRIMARY KEY,
    reseller_id INTEGER REFERENCES users(id),
    company_name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    client_email VARCHAR(255) NOT NULL,
    client_phone VARCHAR(50),
    tin VARCHAR(50) NOT NULL,
    device_no VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected
    notes TEXT,
    rejection_reason TEXT,
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    created_client_id INTEGER REFERENCES users(id),
    created_company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### Enhanced Table: `audit_logs`
Already exists, now used for:
- REFERRAL_SUBMITTED
- REFERRAL_APPROVED
- REFERRAL_REJECTED
- CLIENT_DEACTIVATED (owner-only)

---

## 🛡️ **COMPLIANCE & AUDIT TRAIL**

Every critical action is logged:

```json
{
  "action": "REFERRAL_APPROVED",
  "user_id": 1,  // Owner who approved
  "resource_type": "ClientReferral",
  "resource_id": "123",
  "details": {
    "referral_id": 123,
    "reseller_id": 45,
    "client_id": 678,
    "tin": "1234567890"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Purpose:** If URA asks "Who added this client?", you have proof:
- Owner approved after review
- Reseller only referred
- All actions timestamped
- Certificate upload by owner only

---

## 🚫 **WHAT RESELLERS CAN'T DO ANYMORE**

1. ❌ Add clients directly
2. ❌ Delete/deactivate clients
3. ❌ Upload EFRIS certificates
4. ❌ Configure device numbers
5. ❌ Set test/production environment
6. ❌ Access client credentials
7. ❌ Modify client settings
8. ❌ View other resellers' clients

---

## ✅ **WHAT RESELLERS CAN DO**

1. ✓ Submit client referrals
2. ✓ View their own referrals' status
3. ✓ See which clients they referred (read-only)
4. ✓ View client activity/issues (read-only)
5. ✓ Add notes when submitting referrals

---

## 🎯 **OWNER RESPONSIBILITIES**

As platform owner, you must:

1. **Review all referrals** - Don't auto-approve
2. **Verify TIN validity** - Check with URA if needed
3. **Upload certificates securely** - Only you handle .pfx files
4. **Set correct environment** - Test vs Production per client
5. **Send credentials directly to client** - Don't let reseller do it
6. **Monitor audit logs** - Track all actions
7. **Deactivate bad actors** - Suspend malicious resellers

---

## 🔧 **UI CHANGES NEEDED**

### Reseller Portal (`static/reseller_portal.html`)

**REMOVE:**
- ❌ "Add Client" button
- ❌ "Delete Client" button
- ❌ Certificate upload form
- ❌ Edit client settings

**REPLACE WITH:**
- ✅ "Refer New Client" button
- ✅ Shows: Company name, TIN, contact info, notes
- ✅ Status indicator: Pending, Approved, Rejected
- ✅ Read-only client list

### Owner Portal (`static/owner_portal.html`)

**ADD:**
- ✅ "Pending Referrals" tab (badge with count)
- ✅ Referral review interface:
  - Reseller info
  - Client details
  - Approve button (opens cert upload form)
  - Reject button (with reason field)

---

## 📖 **EXAMPLE: Complete Workflow**

### Scenario: Reseller John wants to bring client "ABC Ltd"

1. **John (Reseller) submits referral:**
   ```
   Company: ABC Ltd
   Client Name: David Manager
   Email: david@abc.co.ug
   TIN: 1234567890
   Phone: +256700123456
   Notes: "Met at trade show, needs invoice management"
   ```

2. **Platform Owner receives notification:**
   - Opens "Pending Referrals" tab
   - Sees John referred ABC Ltd
   - Checks TIN with URA (valid)
   - Contacts David to confirm

3. **Owner approves referral:**
   - Uploads ABC Ltd's EFRIS certificate (.pfx)
   - Enters certificate password
   - Selects Production environment
   - Generates login password: "Abc@2024"
   - Clicks "Approve"

4. **System creates:**
   - Client user: david@abc.co.ug
   - Company: ABC Ltd (TIN 1234567890)
   - Links to John (parent_id)
   - Updates referral status: approved

5. **Owner sends to David:**
   ```
   Login URL: http://platform.com/client/login
   Email: david@abc.co.ug
   Password: Abc@2024
   ```

6. **John sees in his portal:**
   - ABC Ltd - ACTIVE ✅
   - Referred on: 2024-01-15
   - Status: Working (read-only)

7. **David logs in:**
   - Uses /client/login
   - Sees his dashboard
   - Starts using EFRIS integration

---

## ⚠️ **MIGRATION FOR EXISTING CLIENTS**

If you already have clients added by resellers:

1. **Don't delete them** - They're already configured
2. **Audit review** - Check who added each client
3. **Document** - Note which reseller referred which client
4. **Going forward** - All new clients use referral system

---

## 🚀 **TESTING THE NEW SYSTEM**

### Test as Reseller:
1. Login as reseller
2. Try to submit referral (should work)
3. Try to access old add-client endpoint (should fail 403)
4. Try to delete client (endpoint removed)

### Test as Owner:
1. Login as owner/admin
2. See pending referrals tab
3. Approve a referral with cert upload
4. Check client created successfully
5. Verify reseller can see client (read-only)

---

## 📞 **SUPPORT & QUESTIONS**

If resellers complain about "can't add clients":
- ✅ **Correct response:** "For security and URA compliance, all EFRIS credentials must be configured by platform owner. Please submit referral and we'll set up within 24 hours."
- ❌ **Don't say:** "We don't trust you" or "You did something wrong"

**Key message:** This protects EVERYONE (resellers, clients, platform owner) from URA compliance issues.

---

## 🎓 **LESSONS LEARNED**

1. **Never give resellers full control** - They might become competitors or bad actors
2. **Owner handles all compliance-critical items** - Certificates, credentials, URA registration
3. **Audit everything** - If URA asks questions, you have answers
4. **Referral > Direct Add** - Creates accountability layer
5. **Read-only is enough** - Resellers don't need edit/delete to do their job

---

## ✅ **COMPLIANCE CHECKLIST**

Before going live in Uganda:

- [ ] ClientReferral table created
- [ ] Old add/delete endpoints removed
- [ ] New referral endpoints tested
- [ ] Owner approval workflow working
- [ ] Audit logs capturing all actions
- [ ] Reseller portal UI updated (remove add/delete buttons)
- [ ] Owner portal has pending referrals tab
- [ ] Certificate upload only by owner
- [ ] All existing clients documented (who referred them)
- [ ] Test referral workflow end-to-end

---

## 🆘 **IN CASE OF URA INQUIRY**

If URA contacts you about a client:

1. **Pull audit logs** - Show who approved, when, what was configured
2. **Show referral trail** - Reseller referred, owner approved
3. **Prove owner control** - Only owner uploads certificates
4. **Demonstrate compliance** - Audit trail of all actions

**You can say:** "We maintain strict controls. All EFRIS credentials are configured by our licensed platform owner only. Resellers cannot add or remove clients without owner approval."

---

**REMEMBER:** This security model isn't paranoia - it's based on real license-loss incident from another Uganda EFRIS operator. Protect your business! 🛡️
