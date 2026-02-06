# Client Login Guide - EFRIS Platform

## 🔐 Three Account Types & Their Dashboards

### 1. **OWNER (Platform Administrator)**
   - **Role:** Manages the entire platform
   - **Login Page:** `http://localhost:8001/login`
   - **Dashboard:** `http://localhost:8001/owner`
   - **Capabilities:**
     - View all resellers and their performance
     - Approve client referrals from resellers
     - Add direct clients (bypass resellers)
     - Upload client EFRIS certificates
     - Configure client ERP integrations
     - Manage platform settings

### 2. **RESELLER (Business Partners)**
   - **Role:** Refers clients to the platform
   - **Login Page:** `http://localhost:8001/login` or `http://localhost:8001` (landing page)
   - **Dashboard:** `http://localhost:8001/reseller`
   - **Signup:** Available on landing page (`http://localhost:8001`)
   - **Capabilities:**
     - Refer new clients to platform
     - Track referral status
     - View commission/earnings
     - Monitor client activity
     - Generate referral links

### 3. **CLIENT (Taxpayers)**
   - **Role:** Uses EFRIS integration for their business
   - **Login Page:** `http://localhost:8001/client/login` (unique custom URL)
   - **Dashboard:** `http://localhost:8001/dashboard`
   - **How Created:** 
     - By Reseller (referral) → Owner approves
     - OR by Owner directly
   - **Capabilities:**
     - Fiscalize invoices with EFRIS
     - Sync products/goods from ERP
     - View fiscal history
     - Generate reports
     - Manage company settings

---

## 📝 How Clients Are Created

### **Method 1: Through Reseller (Referral Flow)**

1. **Reseller** refers a client:
   - Goes to Reseller Portal
   - Fills client referral form:
     - Client name, email, phone
     - Company name, TIN, device number
   - Submits referral

2. **Owner** approves referral:
   - Goes to Owner Portal
   - Sees pending referrals
   - Reviews referral details
   - **Most Important:** Uploads client's EFRIS certificate (.pfx file)
   - Sets certificate password
   - Creates client password
   - Approves referral

3. **Client account is created:**
   - Client receives login credentials
   - Client uses custom login page: `/client/login`
   - Client logs into their dashboard

### **Method 2: Owner Adds Direct Client**

1. **Owner** adds client directly:
   - Goes to Owner Portal
   - Clicks "Add Direct Client"
   - Fills form:
     - Client details (email, phone)
     - Company details (name, TIN, device)
     - EFRIS certificate upload
     - ERP configuration (QuickBooks, Xero, etc.)
   - Creates account

2. **Client receives:**
   - Login credentials via owner
   - Custom login URL: `/client/login`
   - Access to their dashboard

---

## 🚀 Setup Instructions

### Step 1: Create Owner Account

Run the setup script:
```bash
py setup_owner_account.py
```

This creates:
- **Email:** owner@efrisplatform.com
- **Password:** OwnerSecure2026!
- **Login:** http://localhost:8001/login

### Step 2: Login as Owner

1. Go to: http://localhost:8001/login
2. Enter owner credentials
3. You'll be redirected to: http://localhost:8001/owner

### Step 3: Test the Flow

**Option A - Add Reseller:**
1. Open new browser/incognito: http://localhost:8001
2. Click "Sign Up" (creates reseller account)
3. Login to reseller portal
4. Create a client referral
5. Back to owner portal → approve referral
6. Send client their login details

**Option B - Add Direct Client:**
1. In owner portal, click "Add Client"
2. Fill client details + upload certificate
3. Configure their ERP (optional)
4. Client receives login URL and credentials

---

## 🔑 Important Client Login Details

### Clients Use Different Login Page
- ❌ NOT: `/login` (for owners/resellers)
- ✅ YES: `/client/login` (for taxpayers)

### Why Separate?
- Security: Clients isolated from platform management
- Branding: Can customize client login page
- Tracking: Different analytics per user type

### After Login:
- Owner → `/owner` portal
- Reseller → `/reseller` portal  
- Client → `/dashboard` (EFRIS operations)

---

## 🔧 Current Setup Status

Run this to check/create owner account:
```bash
py setup_owner_account.py
```

Then login at: http://localhost:8001/login

Your platform is ready! 🎉
