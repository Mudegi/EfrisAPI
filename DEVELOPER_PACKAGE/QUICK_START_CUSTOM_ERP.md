# Quick Start Guide - Custom ERP Integration

## For Developers Integrating with EFRIS Platform

### 🚀 5-Minute Integration

#### Step 1: Get Your Credentials
Your platform administrator will provide:
```
API Key: efris_abc123xyz...
API Endpoint: https://efrisintegration.nafacademy.com/api/external/efris
```

#### Step 2: Add Buttons to Your ERP
Add EFRIS submission buttons to your forms:

**Invoice Form:**
```html
<button onclick="sendInvoiceToEFRIS()">Save and Send to EFRIS</button>
```

**Product/Item Form:**
```html
<button onclick="registerProductWithEFRIS()">Register with EFRIS</button>
```

**Purchase Order Form:**
```html
<button onclick="sendPOToEFRIS()">Submit PO to EFRIS</button>
```

**Credit Note/Return Form:**
```html
<button onclick="sendCreditNoteToEFRIS()">Submit Credit Note to EFRIS</button>
```

#### Step 3: Implement the Functions

**Python Examples:**

```python
import requests

API_KEY = "efris_your_api_key_here"
BASE_URL = "https://efrisintegration.nafacademy.com/api/external/efris"

# 1. SUBMIT INVOICE TO EFRIS
def send_invoice_to_efris(invoice):
    response = requests.post(
        f"{BASE_URL}/submit-invoice",
        headers={"X-API-Key": API_KEY},
        json={
            "invoice_number": invoice['number'],
            "invoice_date": invoice['date'],
            "customer_name": invoice['customer'],
            "customer_tin": invoice.get('customer_tin', ''),
            "items": invoice['items'],
            "total_amount": invoice['total'],
            "total_tax": invoice['tax'],
            "currency": "UGX"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        update_invoice(invoice['id'], {
            'fdn': result['fdn'],
            'qr_code': result['qr_code'],
            'status': 'fiscalized'
        })s:**

```javascript
const API_KEY = 'efris_your_api_key_here';
const BASE_URL = 'https://efrisintegration.nafacademy.com/api/external/efris';

// 1. SUBMIT INVOICE TO EFRIS
async function sendInvoiceToEFRIS(invoice) {
    try {
        const response = await fetch(`${BASE_URL}/submit-invoice`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                invoice_number: invoice.number,
                invoice_date: invoice.date,
                customer_name: invoice.customer,
                customer_tin: invoice.customer_tin || '',
                items: invoice.items,
                total_amount: invoice.total,
                total_tax: invoice.tax,
                currency: 'UGX'
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            updateInvoice(invoice.id, {
                fdn: result.fdn,
                qr_code: result.qr_code,
                status: 'fiscalized'
            });
            alert(`✅ Invoice Fiscalized! FDN: ${result.fdn}`);
            return result;
        } else {
            const error = await response.json();
            alert(`❌ Error: ${error.detail}`);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    }
}

// 2. REGISTER PRODUCT WITH EFRIS
async function registerProductWithEFRIS(product) {
    try {
        const response = await fetch(`${BASE_URL}/register-product`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                item_code: product.code,
                item_name: product.name,
                unit_price: product.price,
                commodity_code: product.commodity_code || '1010101',
                unit_of_measure: product.unit || '102',
                have_excise_tax: product.has_excise || '102',
                stock_quantity: product.stock || 0,
                description: product.description || ''
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            updateProduct(product.id, { efris_status: 'Registered' });
            alert(`✅ Product Registered: ${product.name}`);
            return result;
        } else {
            const error = await response.json();
            alert(`❌ Error: ${error.detail}`);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    }
}

// 3. SUBMIT PURCHASE ORDER TO EFRIS
async function sendPOToEFRIS(purchaseOrder) {
    try {
        const response = await fetch(`${BASE_URL}/submit-purchase-order`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                po_number: purchaseOrder.number,
                po_date: purchaseOrder.date,
                vendor_name: purchaseOrder.vendor,
                vendor_tin: purchaseOrder.vendor_tin || '',
                items: purchaseOrder.items,
                total_amount: purchaseOrder.total,
                currency: 'UGX'
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            updatePO(purchaseOrder.id, { 
                efris_status: 'submitted',
                efris_reference: result.reference_number 
            });
            alert(`✅ Purchase Order Submitted!`);
            return result;
        } else {
            const error = await response.json();
            alert(`❌ Error: ${error.detail}`);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    }
}

// 4. SUBMIT CREDIT NOTE TO EFRIS
async function sendCreditNoteToEFRIS(creditNote) {
    try {
        const response = await fetch(`${BASE_URL}/submit-credit-note`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                credit_note_number: creditNote.number,
                credit_note_date: creditNote.date,
                original_invoice_number: creditNote.original_invoice,
                original_fdn: creditNote.original_fdn || '',
                customer_name: creditNote.customer,
                reason: creditNote.reason,
                items: creditNote.items,
                total_amount: creditNote.total,
                total_tax: creditNote.tax,
                currency: 'UGX'
            })
        });

**Invoice/Credit Note - Show FDN and QR code:**
```html
<div class="invoice-efris">
    <p>FDN: {{ invoice.fdn }}</p>
    <img src="data:image/png;base64,{{ invoice.qr_code }}" />
    <p>Verification Code: {{ invoice.verification_code }}</p>
</div>
```

**Product - Show Registration Status:**
```html
<div class="product-status">
    <span class="badge badge-success">✅ Registered with EFRIS</span>
</div>
```

**Purchase Order - Show Submission Status:**
```html
<div class="po-status">
    <p>EFRIS Status: {{ po.efris_status }}</p>
    <p>Reference: {{ po.efris_reference }}</p>
</div>
```

---

## 📝 Request Formats for All Operations

### 1. Submit Invoice (Minimal)

```json
{
  "invoice_number": "INV-001",
  "invoice_date": "2024-01-24",
  "customer_name": "ABC Ltd",
  "items": [
    {
      "item_name": "Product A",
      "quantity": 10,
      "unit_price": 5000,
      "total": 50000,
      "tax_rate": 0.18,
      "tax_amount": 9000
    }
  ],
  "total_amount": 50000,
  "total_tax": 9000,
  "currency": "UGX"
}
```

### 2. Register Product

```json
{
  "item_code": "PROD-001",
  "item_name": "Laptop Computer",
  "unit_price": 2500000,
  "commodity_code": "1010101",
  "commodity_name": "Electronics",
  "unit_of_measure": "102",
  "have_excise_tax": "102",
  "stock_quantity": 50,
  "description": "Dell Latitude 15 inch"
}
```

### 3. Submit Purchase Order

```json
{
  "po_number": "PO-2024-001",
  "po_date": "2024-01-24",
  "vendor_name": "Supplier XYZ Ltd",
  "vendor_tin": "1234567890",
  "items": [
    {
      "item_name": "Raw Material A",
      "item_code": "RAW-001",
      "quantity": 100,
      "unit_price": 5000,
      "total": 500000
    }
  ],
  "total_amount": 500000,
  "currency": "UGX",
  "delivery_date": "2024-02-15"
}
```

### 4. Submit Credit Note

```json
{
  "credit_note_number": "CN-2024-001",
  "credit_note_date": "2024-01-24",
  "original_invoice_number": "INV-001",
  "original_fdn": "1234567890123456",
  "customer_name": "ABC Ltd",
  "reason": "Product return - defective item",
  "items": [
    {
      "item_name": "Product A",
      "quantity": 2,
      "unit_price": 5000,
      "total": 10000,
      "tax_rate": 0.18,
      "tax_amount": 1800
    }
  ],
  "total_amount": 10000,
  "total_tax": 18or_tin": purchase_order.get('vendor_tin', ''),
            "items": purchase_order['items'],
            "total_amount": purchase_order['total'],
            "currency": "UGX",
            "delivery_date": purchase_order.get('delivery_date', '')
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        update_po(purchase_order['id'], {
            'efris_status': 'submitted',
            'efris_reference': result.get('reference_number', ''),
            'submitted_at': datetime.now()
        })
        print(f"✅ Purchase Order Submitted!")
        return result
    else:
        print(f"❌ Error: {response.json()['detail']}")
        return None

# 4. SUBMIT CREDIT NOTE (RETURN/REFUND) TO EFRIS
def send_credit_note_to_efris(credit_note):
    response = requests.post(
        f"{BASE_URL}/submit-credit-note",
        headers={"X-API-Key": API_KEY},
        json={
            "credit_note_number": credit_note['number'],
            "credit_note_date": credit_note['date'],
            "original_invoice_number": credit_note['original_invoice'],
            "original_fdn": credit_note.get('original_fdn', ''),
            "customer_name": credit_note['customer'],
            "reason": credit_note['reason'],
            "items": credit_note['items'],
            "total_amount": credit_note['total'],
            "total_tax": credit_note['tax'],
            "currency": "UGX"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        update_credit_note(credit_note['id'], {
            'fdn': result['fdn'],
            'qr_code': result['qr_code'],
            'status': 'fiscalized'
### Invoice Response
```json
{
  "success": true,
  "fdn": "1234567890123456",
  "verification_code": "ABC123",
  "qr_code": "base64_encoded_image",
  "efris_invoice_id": "efris_id",
  "invoice_number": "INV-001",
  "fiscalized_at": "2024-01-24T10:30:00",
  "message": "Invoice fiscalized successfully"
}
```

**Important for Invoices:**
- `fdn` - **Must be printed on invoice** (legal requirement)
- `qr_code` - **Must be printed on invoice** (customer verification)
- `verification_code` - Anti-fake code

### Product Registration Response
```json
{
  "success": true,
  "product_code": "PROD-001",
  "efris_status": "Registered",
  "message": "Product registered successfully"
}
```

### Purchase Order Response
```json

**For Invoices:**
```python
Required: invoice_number, invoice_date, customer_name, items, total_amount, currency
Optional: customer_tin, buyer_type, buyer_phone, buyer_email
```

**For Products:**
```python
Required: item_code, item_name, unit_price, commodity_code
Optional: unit_of_measure, have_excise_tax, stock_quantity, description
```

**For Purchase Orders:**
```python
Required: po_number, po_date, vendor_name, items, total_amount, currency
Optional: vendor_tin, delivery_date
```

**For Credit Notes:**
```python
Required: credit_note_number, credit_note_date, original_invoice_number, 
          customer_name, reason, items, total_amount, currency
Optional: original_fdn

### Credit Note Response
```json
{
  "success": true,
  "fdn": "CN-9876543210987654",
  "verification_code": "XYZ789",
  "qr_code": "base64_encoded_image",
  "credit_note_number": "CN-2024-001",
  "fiscalized for All Operations

**1. Test Invoice:**
```python
test_invoice = {
    "invoice_number": "TEST-INV-001",
    "invoice_date": "2024-01-24",
    "customer_name": "Test Customer Ltd",
    "customer_tin": "1000000000",
    "items": [{
        "item_name": "Test Product",
        "quantity": 1,
        "unit_price": 1000,
        "total": 1000,
        "tax_rate": 0.18,
        "tax_amount": 180
    }],
    "total_amount": 1000,
    "total_tax": 180,
    "currency": "UGX"
}
```

**2. Test Product:**
```python
test_product = {
    "item_code": "TEST-PROD-001",
    "item_name": "Test Product",
    "unit_price": 5000,
    "commodity_code": "1010101",
    "commodity_name": "General Goods",
    "unit_of_measure": "102",
    "have_excise_tax": "102",
    "stock_quantity": 10,
    "description": "Test product for integration"
}
```

**3. Test Purchase Order:**
```python
test_po = {
    "po_number": "TEST-PO-001",
    "po_date": "2024-01-24",
    "vendor_name": "Test Vendor Ltd",
    "vendor_tin": "2000000000",
    "items": [{
        "item_name": "Raw Material",
        "item_code": "RAW-001",
        "quantity": 50,
        "unit_price": 2000,
        "total": 100000
    }],
    "total_amount": 100000,
    "currency": "UGX"
}
```

**4. Test Credit Note:**
```python
test_credit_note = {
    "credit_note_number": "TEST-CN-001",
    "credit_note_date": "2024-01-24",
    "original_invoice_number": "TEST-INV-001",
    "original_fdn": "1234567890123456",
    "customer_name": "Test Customer Ltd",
    "reason": "Product return - test scenario",
    "items": [{
        "item_name": "Test Product",
        "quantity": 1,
        "unit_price": 1000,
        "total": 1000,
        "tax_rate": 0.18,
        "tax_amount": 180
    }],
    "total_amount": 1000,
    "total_tax": 180,
    "currency": "UGX"
}
```

### Verify Responses

```python
# Test 1: Invoice
invoice_result = submit_invoice(test_invoice)
assert invoice_result['success'] == True
assert 'fdn' in invoice_result
assert 'qr_code' in invoice_result
print("✅ Invoice test passed!")

# Test 2: Product
product_result = register_product(test_product)
assert product_result['success'] == True
assert product_result['efris_status'] == 'Registered'
print("✅ Product registration test passed!")

# Test 3: Purchase Order
po_result = submit_po(test_po)
assert po_result['success'] == True
assert 'reference_number' in po_result
print("✅ Purchase Order test passed!")

# Test 4: Credit Note
cn_result = submit_credit_note(test_credit_note)
assert cn_result['success'] == True
assert 'fdn' in cn_result
print("✅ Credit Note test passed!")

print("\n🎉 All integration tests
    } catch (error) {
        alert('Network error: ' + error.message);
    }
}
```

#### Step 4: Display Results
Show FDN and QR code on the invoice:
```html
<div class="invoice-efris">
    <p>FDN: {{ invoice.fdn }}</p>
    <img src="data:image/png;base64,{{ invoice.qr_code }}" />
</div>
```

---

## 📝 Minimal Request Format

```json
{
  "invoice_number": "INV-001",
  "invoice_date": "2024-01-24",
  "customer_name": "ABC Ltd",
  "items": [
    {
      "item_name": "Product A",
      "quantity": 10,
      "unit_price": 5000,
      "total": 50000,
      "tax_rate": 0.18,
      "tax_amount": 9000
    }
  ],
  "total_amount": 50000,
  "total_tax": 9000,
  "currency": "UGX"
}
```

---

## 🎯 What You Get Back

```json
{
  "success": true,
  "fdn": "1234567890123456",
  "verification_code": "ABC123",
  "qr_code": "base64_encoded_image",
  "efris_invoice_id": "efris_id",
  "invoice_number": "INV-001",
  "fiscalized_at": "2024-01-24T10:30:00",
  "message": "Invoice fiscalize for all operations:

```python
# Overall Success Rate
total_successful_operations / total_operations * 100

# Success Rate by Operation Type
metrics = {
    'invoices': {
        'total': 150,
        'successful': 145,
        'failed': 5,
        'success_rate': 96.7
    },
    'products': {
        'total': 50,
        'successful': 48,
        'failed': 2,
        'success_rate': 96.0
    },
    'purchase_orders': {
        'total': 30,
        'successful': 29,
        'failed': 1,
        'success_rate': 96.7
    },
    'credit_notes': {
        'total': 10,
        'successful': 10,
        'failed': 0,
        'success_rate': 100.0
    }
}

# Average Response Time by Operation
response_times = {
    'invoice_submission': 3.2,  # seconds
    'product_registration': 2.1,
    'po_submission': 2.8,
    'credit_note': 3.5
}

# Error Distribution
error_breakdown = {
    'timeout': 5,
    'validation_error': 3,
    'efris_rejected': 2,
    'network_error': 1
}

# Daily Activity Summary
daily_summary = {
    'date': '2024-01-24',
    'invoices_sent': 25,
    'products_registered': 8,
    'pos_submitted': 5,
    'credit_notes_sent': 2,
    'total_revenue_fiscalized': 15000000  # UGXPI key"
**Solution:** Check your X-API-Key header
```python
headers = {"X-API-Key": "efris_your_key_here"}  # ✅ Correct
headers = {"API-Key": "efris_your_key_here"}     # ❌ Wrong
```

### Issue 2: "Missing required field"
**Solution:** Ensure all required fields are present
```python
# Required fields:
- invoice_number
- invoice_date
- customer_name
- items (must have at least 1)
- total_amount
- currency
```

### Issue 3: "Device not registered"
**Solution:** Contact platform administrator to register EFRIS device

### Issue 4: Timeout
**Solution:** Implement retry logic
```python
import time

def submit_with_retry(data, max_retries=3):
    for i in range(max_retries):
        try:
            return submit_invoice(data)
        except requests.Timeout:
            if i < max_retries - 1:
                time.sleep(2)
                continue
            raise
```

---

## 🧪 Testing

### Test Data
```python
test_invoice = {
    "invoice_number": "TEST-001",
    "invoice_date": "2024-01-24",
    "customer_name": "Test Customer",
    "customer_tin": "1000000000",
    "items": [{
        "item_name": "Test Product",
        "quantity": 1,
        "unit_price": 1000,
        "total": 1000,
        "tax_rate": 0.18,
        "tax_amount": 180
    }],
    "total_amount": 1000,
    "total_tax": 180,
    "currency": "UGX"
}
```

### Verify Response
```python
result = submit_invoice(test_invoice)

assert result['success'] == True
assert 'fdn' in result
assert 'qr_code' in result
assert len(result['fdn']) > 0

print("✅ Integration test passed!")
```

---

## 📱 Mobile/Offline Support

### Queue for Later Submission
If your ERP works offline:

```python
def save_invoice_for_later(invoice_data):
    # Save to queue when offline
    queue.append({
        'invoice': invoice_data,
        'status': 'pending',
        'attempts': 0,
        'created_at': datetime.now()
    })

def process_queue():
    # Run periodically when online
    for item in queue:
        if item['attempts'] < 3:
            try:
                result = submit_invoice(item['invoice'])
                if result['success']:
                    queue.remove(item)
                    update_invoice_status(item['invoice']['invoice_number'], 'fiscalized')
            except:
                item['attempts'] += 1
```

---

## 🔒 Security Checklist

- ✅ Store API key in environment variables (not in code)
- ✅ Use HTTPS in production
- ✅ Validate data before sending
- ✅ Log all API calls for audit
- ✅ Handle errors gracefully (don't expose keys in error messages)
- ✅ Implement rate limiting in your ERP

---

## 📊 Monitoring

Track these metrics in your ERP:

```python
# Success rate
fiscalized_count / total_invoices * 100

# Average response time
sum(response_times) / len(response_times)

# Error rate by type
{
    'timeout': 5,
    'validation_error': 2,
    'efris_rejected': 1
}
```

---

## 🆘 Support

**API Issues:**
- Check `/health` endpoint: `GET https://efrisintegration.nafacademy.com/health`
- Email: support@platform.com

**EFRIS Issues:**
- URA Support: https://efris.ura.go.ug
- Phone: +256-XXX-XXXXXX

---

## 📚 Full Documentation

See: `EXTERNAL_API_DOCUMENTATION.md`

---

**That's it! Your ERP is now EFRIS-ready.** 🎉
