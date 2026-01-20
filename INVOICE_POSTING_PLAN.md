# 📋 EFRIS Invoice Posting Implementation Plan

## 🎯 Overview

Based on your documentation review, here's the comprehensive plan for implementing invoice posting to EFRIS. Your system already has **95% of the backend logic** completed! We just need to build the **frontend UI** for reviewing and submitting invoices.

---

## ✅ What You Already Have (Backend Complete!)

### 1. **QuickBooks to EFRIS Mapper** (`quickbooks_efris_mapper.py`)
- ✅ **Tax Handling**: Standard VAT (18%), Zero-rated (0%), Exempt, Deemed VAT
- ✅ **Discount Support**: Line-level & invoice-level discounts
- ✅ **Excise Duty**: Fixed-rate and percentage-based calculations
- ✅ **Tax Category Detection**: Auto-detects from QuickBooks tax codes
- ✅ **EFRIS T109 Format**: Complete payload generation
- ✅ **Validation**: EFRIS rule compliance (e.g., last line cannot be discounted)

### 2. **EFRIS Client** (`efris_client.py`)
- ✅ **T109 Interface**: Invoice upload with AES encryption
- ✅ **Handshake**: Time sync, key exchange, parameters
- ✅ **Signature & Encryption**: RSA + AES-128-CBC
- ✅ **Response Handling**: Decryption and FDN extraction

### 3. **Multi-Tenant API** (`api_multitenant.py`)
- ✅ **QuickBooks Integration**: Fetch invoices
- ✅ **Sync Endpoint**: `/api/quickbooks/sync-invoice/{invoice_id}`
- ✅ **Database**: EFRISInvoice model for tracking

---

## 🚧 What Needs to Be Built (Frontend UI Only!)

### **Invoice Review & Submission Dashboard**

#### **Step 1: Invoice List View**
Currently showing basic info - needs enhancement:

```
Current:
┌──────────────────────────────────────────────┐
│ Invoice # │ Customer │ Date │ Amount │ View  │
└──────────────────────────────────────────────┘

Needs to become:
┌────────────────────────────────────────────────────────────────┐
│ Invoice # │ Customer │ Date │ Amount │ Status │ Edit & Submit │
└────────────────────────────────────────────────────────────────┘
```

**New Features:**
- Status badge (e.g., "Draft", "Submitted", "Success", "Failed")
- "Edit & Submit" button (similar to QB Items)
- Filter by status
- Bulk select for multiple submissions

#### **Step 2: Invoice Edit Modal**
Similar to the QB Items edit modal we just built, but for invoices:

**Modal Sections:**

**A. Basic Information** (Top)
```html
┌─────────────────────────────────────────────┐
│ Invoice #: 1001 (read-only)                 │
│ Customer: ABC Company (read-only)           │
│ Date: [2026-01-19] (editable)              │
│ Buyer Type: [Individual ▼]                 │
│ Customer TIN: [optional, required if B2B]  │
└─────────────────────────────────────────────┘
```

**B. Line Items Table** (Middle)
```html
┌──────────────────────────────────────────────────────────────────┐
│ Item          │ Qty │ Price   │ Discount │ Tax  │ Excise │ Total│
├──────────────────────────────────────────────────────────────────┤
│ Coffee        │  10 │  10,000 │   10%    │ 18% │   -    │90,000│
│ Bell Lager    │ 100 │   1,000 │    5%    │ 18% │  200   │...   │
│ Medical       │  50 │   2,000 │    -     │  0% │   -    │...   │
└──────────────────────────────────────────────────────────────────┘
```

**Visual Features:**
- Color-coded tax badges (like you saw in USER_GUIDE):
  - 🟢 [18%] = Standard VAT
  - 🔵 [0% Zero] = Zero-rated
  - 🟠 [EXEMPT] = Tax-exempt
  - 🟣 [18% Deemed] = Deemed VAT
- Discount badges: `[10%]` or `[FIXED]`
- Excise codes: `[LED050000] UGX 5,000`
- Editable fields: Qty, Price, Discount% (recalculates on change)

**C. Invoice Summary** (Bottom)
```html
╔═══════════════════════════════════════╗
║      INVOICE SUMMARY                  ║
╠═══════════════════════════════════════╣
║ Subtotal:           UGX 450,000.00    ║
║ Total Discount:    -UGX  37,500.00 🔴 ║
║ Total Excise Duty:  UGX   5,000.00 🔴 ║
║ Total VAT:          UGX  56,700.00 🟢 ║
║ ───────────────────────────────────── ║
║ GRAND TOTAL:        UGX 474,200.00 💵 ║
╚═══════════════════════════════════════╝
```

**D. Action Buttons** (Footer)
```html
[Cancel] [Save Draft] [💾 Save & Submit to EFRIS]
```

#### **Step 3: Submission Flow**

**When user clicks "Save & Submit to EFRIS":**

1. **Validation**
   - Check customer TIN (required for Business type)
   - Verify all line items have product codes
   - Ensure tax rates are valid
   - Check excise items have correct codes

2. **API Call**
   ```javascript
   POST /api/companies/{id}/invoices/{invoice_id}/submit-to-efris
   Body: { edited invoice data }
   ```

3. **Backend Processing**
   - Update invoice with edited data
   - Call `mapper.qb_invoice_to_efris_t109()`
   - Call `manager.upload_invoice(efris_invoice)`
   - Handle EFRIS response
   - Save FDN (Fiscal Document Number)
   - Update invoice status

4. **Response Handling**
   ```javascript
   if (success) {
       showToast("✅ Invoice submitted! FDN: " + fdn)
       updateInvoiceStatus(id, "Submitted", fdn)
       reloadInvoices()
   } else {
       showToast("❌ Submission failed: " + error)
       showErrorDetails(response)
   }
   ```

#### **Step 4: Error Handling**

**Common EFRIS Errors:**
- `602`: Item not registered → Show "Register product first"
- `1174`: Last line has discount → Auto-fix by redistributing
- `Invalid TIN`: Show "Check customer TIN"
- `Tax mismatch`: Show details of expected vs actual

**Error Modal:**
```html
╔═══════════════════════════════════════╗
║     ❌ EFRIS Submission Error          ║
╠═══════════════════════════════════════╣
║ Error Code: 602                       ║
║ Message: BedBugSpr not registered     ║
║                                       ║
║ Solution:                             ║
║ 1. Go to QB Items tab                 ║
║ 2. Register "BedBugSpr" to EFRIS      ║
║ 3. Come back and retry submission     ║
║                                       ║
║ [Go to QB Items] [Retry] [Close]      ║
╚═══════════════════════════════════════╝
```

---

## 📊 Database Schema Addition

**EFRISInvoice Table** (already exists, may need fields):
```python
class EFRISInvoice(Base):
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'))
    qb_invoice_id = Column(String)
    qb_invoice_number = Column(String)
    invoice_date = Column(Date)
    customer_name = Column(String)
    customer_tin = Column(String)
    buyer_type = Column(String)  # 0=Business, 1=Individual, etc.
    total_amount = Column(Float)
    total_tax = Column(Float)
    total_excise = Column(Float)
    total_discount = Column(Float)
    status = Column(String)  # Draft, Submitted, Success, Failed
    fdn = Column(String)  # Fiscal Document Number from EFRIS
    efris_invoice_id = Column(String)
    submission_date = Column(DateTime)
    error_message = Column(Text)
    efris_payload = Column(JSON)  # Full EFRIS request
    efris_response = Column(JSON)  # Full EFRIS response
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

## 🔄 Complete User Flow

```
1. User opens dashboard → QB Invoices tab
   ↓
2. Loads invoices from QuickBooks
   ↓
3. Sees list with statuses (Draft, Submitted, etc.)
   ↓
4. Clicks "Edit & Submit" on an invoice
   ↓
5. Modal opens showing:
   - Customer info (editable: TIN, buyer type)
   - Line items (editable: qty, price, discount)
   - Real-time calculations
   - Tax breakdown with color coding
   - Excise duty details
   ↓
6. User reviews and makes any adjustments
   ↓
7. Clicks "Save & Submit to EFRIS"
   ↓
8. System validates and submits
   ↓
9. Shows success with FDN or error details
   ↓
10. Invoice status updated in list
```

---

## 🎨 UI Components to Build

### **1. Invoice Edit Modal** (similar to QB Items modal)
- Full-screen overlay
- Three sections: header, body, footer
- Live calculation as user edits
- Color-coded badges for tax types
- Validation before submit

### **2. Invoice Summary Card**
- Clean summary table
- Color-coded totals
- Visual hierarchy (subtotal → discount → excise → VAT → grand total)

### **3. Status Badges**
```javascript
const statusColors = {
    'draft': 'gray',
    'pending': 'yellow',
    'submitted': 'blue',
    'success': 'green',
    'failed': 'red'
}
```

### **4. Discount & Tax Badges**
```javascript
// Tax badges
🟢 [18%]        → Standard VAT
🔵 [0% Zero]    → Zero-rated
🟠 [EXEMPT]     → Tax-exempt
🟣 [18% Deemed] → Deemed VAT

// Discount badges
[10%] -UGX 1,000    → Percentage discount
[FIXED] -UGX 500    → Fixed amount
```

---

## 📝 Implementation Order

### **Phase 1: Basic UI (Day 1)**
1. ✅ Invoice list with "Edit & Submit" buttons
2. ✅ Invoice edit modal structure
3. ✅ Basic info section (customer, date, buyer type)
4. ✅ Line items table display (read-only first)

### **Phase 2: Calculation Engine (Day 2)**
1. ✅ Real-time calculation on qty/price change
2. ✅ Discount calculation (line & invoice-level)
3. ✅ Tax calculation (different rates)
4. ✅ Excise duty calculation
5. ✅ Summary totals update

### **Phase 3: Submission (Day 3)**
1. ✅ Validation before submit
2. ✅ API integration
3. ✅ Success/error handling
4. ✅ FDN display
5. ✅ Status update

### **Phase 4: Polish (Day 4)**
1. ✅ Color-coded badges
2. ✅ Error modals with solutions
3. ✅ Loading states
4. ✅ Confirmation dialogs
5. ✅ Responsive design

---

## 🚀 API Endpoints Needed

### **1. Get Invoice Details**
```
GET /api/companies/{id}/invoices/{invoice_id}
Response: Full invoice with enriched item details
```

### **2. Update Invoice**
```
PUT /api/companies/{id}/invoices/{invoice_id}
Body: { edited invoice data }
Response: Updated invoice
```

### **3. Submit to EFRIS**
```
POST /api/companies/{id}/invoices/{invoice_id}/submit-to-efris
Response: { success, fdn, error }
```

### **4. Get Submission Status**
```
GET /api/companies/{id}/invoices/{invoice_id}/efris-status
Response: { status, fdn, submission_date, error }
```

---

## 🧪 Testing Scenarios

### **Scenario 1: Simple Invoice (Standard VAT)**
- 1 item, no discount, 18% VAT
- Expected: Clean submission, FDN returned

### **Scenario 2: Invoice with Discounts**
- Multiple items, 10% line discount
- Expected: Discount in EFRIS payload

### **Scenario 3: Mixed Tax Rates**
- Standard (18%) + Zero-rated (0%) + Exempt
- Expected: Separate tax details per category

### **Scenario 4: Excise Items**
- Beer with 200 UGX/unit excise + 18% VAT
- Expected: exciseTax calculated, included in total

### **Scenario 5: Invoice-Level Discount**
- Multiple items, 15% invoice discount
- Expected: Distributed to items except last

### **Scenario 6: Error Handling**
- Item not registered in EFRIS
- Expected: Error 602, clear message, link to register

---

## 📦 Ready to Start?

**Backend:** ✅ 95% Complete
**Frontend:** 🚧 To be built

**Your Mapper Already Handles:**
- ✅ All tax types
- ✅ All discount types
- ✅ Excise duty (fixed & percentage)
- ✅ Tax category detection
- ✅ EFRIS validation rules
- ✅ T109 payload generation

**We Just Need To Build:**
- Invoice list UI
- Invoice edit modal
- Calculation display
- Submit button & flow
- Status tracking
- Error handling

Ready to proceed? I'll start building the frontend components! 🚀
