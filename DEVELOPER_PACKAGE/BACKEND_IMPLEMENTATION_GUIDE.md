# Backend Implementation Guide - Custom ERP Integration

This guide shows you how to implement the backend API endpoints that your custom ERP will call.

## Overview

Your custom ERP needs to call REST API endpoints to:
1. Submit invoices to EFRIS
2. Register products with EFRIS
3. Submit purchase orders to EFRIS
4. Submit credit notes to EFRIS

This guide shows you how these endpoints are implemented in the backend.

---

## Prerequisites

**Already Completed:**
- ✅ Database schema has API key fields (Company model)
- ✅ API authentication middleware (`get_company_from_api_key`)
- ✅ All EFRIS client methods (invoice, product, PO, credit note)
- ✅ All external API endpoints are implemented

**You Need:**
- Your Company's API credentials (from database)
- Your custom ERP UI with buttons/forms

---

## Backend Architecture

### 1. Database Models Used

```python
# Company model (already has these fields)
class Company:
    id: int
    tin: str
    device_no: str
    efris_cert_path: str
    efris_cert_password: str
    is_test_mode: bool
    api_key: str          # For authentication
    api_secret: str       # For authentication
    api_enabled: bool     # Enable/disable API access
    api_last_used: datetime
```

```python
# EFRISInvoice model - stores fiscalized invoices
class EFRISInvoice:
    company_id: int
    invoice_number: str
    fdn: str              # Fiscal Document Number
    qr_code: str
    verification_code: str
    invoice_date: datetime
    total_amount: float
    efris_response: dict
```

```python
# PurchaseOrder model - stores submitted POs
class PurchaseOrder:
    company_id: int
    qb_po_id: str
    qb_doc_number: str
    qb_vendor_name: str
    qb_txn_date: datetime
    qb_total_amt: float
    qb_data: dict
    efris_status: str
    efris_sent_at: datetime
    efris_response: dict
```

```python
# CreditMemo model - stores credit notes
class CreditMemo:
    company_id: int
    qb_credit_memo_id: str
    qb_doc_number: str
    qb_customer_name: str
    qb_txn_date: datetime
    qb_total_amt: float
    qb_data: dict
```

---

## API Endpoints Implemented

### Base URL
```
http://your-server:8001/api/external/efris
```

### Authentication
All endpoints require:
```
X-API-Key: your_company_api_key
```

---

## Endpoint 1: Submit Invoice

**Location:** `api_multitenant.py` lines 5541-5790

```python
@app.post("/api/external/efris/submit-invoice")
async def external_submit_invoice(
    invoice_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
```

**What it does:**
1. Validates invoice data (required fields, items array)
2. Initializes EfrisManager with company credentials
3. Builds EFRIS T109 payload (fiscalization format)
4. Calls `efris.upload_invoice()`
5. Saves to EFRISInvoice table
6. Returns FDN, QR code, verification code

**Request format:**
```json
{
  "invoice_number": "INV-001",
  "invoice_date": "2024-01-24",
  "customer_name": "ABC Ltd",
  "customer_tin": "1234567890",
  "items": [
    {
      "item_name": "Product A",
      "item_code": "PROD001",
      "quantity": 2,
      "unit_price": 10000,
      "total": 20000,
      "tax_rate": 0.18,
      "tax_amount": 3600
    }
  ],
  "total_amount": 20000,
  "total_tax": 3600,
  "currency": "UGX"
}
```

**Response (success):**
```json
{
  "success": true,
  "fdn": "1234567890123456",
  "verification_code": "AB12CD34",
  "qr_code": "base64_encoded_qr_code",
  "invoice_number": "INV-001",
  "fiscalized_at": "2024-01-24T10:30:00"
}
```

---

## Endpoint 2: Register Product

**Location:** `api_multitenant.py` lines 5795-5868

```python
@app.post("/api/external/efris/register-product")
async def external_register_product(
    product_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
```

**What it does:**
1. Validates product data
2. Builds EFRIS T111 payload
3. Calls `efris.upload_goods()`
4. Returns registration status

**Request format:**
```json
{
  "product_code": "PROD001",
  "product_name": "Laptop Computer",
  "unit_price": 2000000,
  "commodity_code": "1010522",
  "unit_of_measure": "102",
  "currency": "UGX",
  "have_excise_tax": "102",
  "stock_quantity": 50
}
```

---

## Endpoint 3: Submit Purchase Order

**Location:** `api_multitenant.py` lines 5792-5905

```python
@app.post("/api/external/efris/submit-purchase-order")
async def external_submit_purchase_order(
    po_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
```

**What it does:**
1. Validates PO data
2. Builds EFRIS T130 payload
3. Calls `efris.send_purchase_order()`
4. Saves to PurchaseOrder table
5. Returns reference number

**Request format:**
```json
{
  "po_number": "PO-2024-001",
  "po_date": "2024-01-24",
  "vendor_name": "Supplier XYZ Ltd",
  "vendor_tin": "1234567890",
  "items": [
    {
      "item_name": "Raw Material A",
      "item_code": "RAW001",
      "quantity": 100,
      "unit_price": 5000,
      "total": 500000,
      "unit_of_measure": "102"
    }
  ],
  "total_amount": 500000,
  "currency": "UGX",
  "delivery_date": "2024-02-15"
}
```

**Response (success):**
```json
{
  "success": true,
  "po_number": "PO-2024-001",
  "efris_status": "submitted",
  "reference_number": "REF123456",
  "message": "Purchase order submitted successfully"
}
```

---

## Endpoint 4: Submit Credit Note

**Location:** `api_multitenant.py` lines 5908-6095

```python
@app.post("/api/external/efris/submit-credit-note")
async def external_submit_credit_note(
    credit_note_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
```

**What it does:**
1. Validates credit note data
2. Builds EFRIS T109 payload with invoiceType="2"
3. References original invoice FDN
4. Calls `efris.upload_invoice()` (same endpoint, different type)
5. Saves to CreditMemo table
6. Returns FDN for credit note

**Request format:**
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
      "item_code": "PROD001",
      "quantity": 1,
      "unit_price": 10000,
      "total": 10000,
      "tax_rate": 0.18,
      "tax_amount": 1800
    }
  ],
  "total_amount": 10000,
  "total_tax": 1800,
  "currency": "UGX"
}
```

---

## How Your Custom ERP Calls These Endpoints

### Step 1: Get Your API Key

Run this query to get your API key:
```sql
SELECT api_key, api_secret FROM companies WHERE tin = 'YOUR_TIN';
```

Or check in your admin panel (if you have one).

### Step 2: Create Button Click Handlers

**Example: Invoice Submit Button (Python/Flask)**

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Your backend server URL
EFRIS_API_URL = "http://localhost:8001/api/external/efris"
API_KEY = "your_api_key_from_database"

@app.route('/submit-invoice', methods=['POST'])
def submit_invoice():
    """Handle invoice submit button click"""
    
    # Get invoice data from your ERP form
    invoice_data = request.json
    
    # Call the EFRIS backend
    headers = {"X-API-Key": API_KEY}
    response = requests.post(
        f"{EFRIS_API_URL}/submit-invoice",
        json=invoice_data,
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        # Save FDN, QR code to your database
        # Display success message to user
        return jsonify({
            "status": "success",
            "fdn": result["fdn"],
            "qr_code": result["qr_code"]
        })
    else:
        # Show error to user
        return jsonify({
            "status": "error",
            "message": response.json()["detail"]
        }), 400
```

**Example: Invoice Submit Button (JavaScript/Node.js)**

```javascript
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

const EFRIS_API_URL = "http://localhost:8001/api/external/efris";
const API_KEY = "your_api_key_from_database";

// Handle invoice submit button click
app.post('/submit-invoice', async (req, res) => {
  try {
    const invoiceData = req.body;
    
    const response = await axios.post(
      `${EFRIS_API_URL}/submit-invoice`,
      invoiceData,
      {
        headers: { 'X-API-Key': API_KEY },
        timeout: 30000
      }
    );
    
    // Success - save FDN and QR code
    res.json({
      status: 'success',
      fdn: response.data.fdn,
      qr_code: response.data.qr_code
    });
    
  } catch (error) {
    // Error handling
    res.status(400).json({
      status: 'error',
      message: error.response?.data?.detail || error.message
    });
  }
});

app.listen(3000);
```

**Example: Invoice Submit Button (PHP)**

```php
<?php
function submitInvoiceToEfris($invoiceData) {
    $apiUrl = "http://localhost:8001/api/external/efris/submit-invoice";
    $apiKey = "your_api_key_from_database";
    
    $ch = curl_init($apiUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($invoiceData));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'X-API-Key: ' . $apiKey
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode == 200) {
        $result = json_decode($response, true);
        return [
            'success' => true,
            'fdn' => $result['fdn'],
            'qr_code' => $result['qr_code']
        ];
    } else {
        return [
            'success' => false,
            'error' => json_decode($response, true)['detail']
        ];
    }
}

// When user clicks "Save and Send to EFRIS" button
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $invoiceData = json_decode(file_get_contents('php://input'), true);
    $result = submitInvoiceToEfris($invoiceData);
    
    header('Content-Type: application/json');
    echo json_encode($result);
}
?>
```

---

## UI Implementation Examples

### Example 1: Simple Invoice Form with Submit Button

**HTML:**
```html
<form id="invoiceForm">
  <input type="text" name="invoice_number" placeholder="Invoice Number" required>
  <input type="date" name="invoice_date" required>
  <input type="text" name="customer_name" placeholder="Customer Name" required>
  
  <div id="itemsContainer">
    <div class="item-row">
      <input type="text" name="item_name[]" placeholder="Item Name">
      <input type="number" name="quantity[]" placeholder="Qty">
      <input type="number" name="unit_price[]" placeholder="Unit Price">
    </div>
  </div>
  
  <button type="button" onclick="addItem()">Add Item</button>
  <button type="submit">Save and Send to EFRIS</button>
</form>

<script>
document.getElementById('invoiceForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  // Collect form data
  const formData = new FormData(e.target);
  const invoiceData = {
    invoice_number: formData.get('invoice_number'),
    invoice_date: formData.get('invoice_date'),
    customer_name: formData.get('customer_name'),
    items: [],
    currency: 'UGX'
  };
  
  // Collect items
  const itemNames = formData.getAll('item_name[]');
  const quantities = formData.getAll('quantity[]');
  const unitPrices = formData.getAll('unit_price[]');
  
  for (let i = 0; i < itemNames.length; i++) {
    const qty = parseFloat(quantities[i]);
    const price = parseFloat(unitPrices[i]);
    const total = qty * price;
    const taxRate = 0.18;
    const taxAmount = total * taxRate;
    
    invoiceData.items.push({
      item_name: itemNames[i],
      quantity: qty,
      unit_price: price,
      total: total,
      tax_rate: taxRate,
      tax_amount: taxAmount
    });
  }
  
  // Calculate totals
  invoiceData.total_amount = invoiceData.items.reduce((sum, item) => sum + item.total, 0);
  invoiceData.total_tax = invoiceData.items.reduce((sum, item) => sum + item.tax_amount, 0);
  
  // Submit to your backend (which calls EFRIS API)
  try {
    const response = await fetch('/submit-invoice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(invoiceData)
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
      alert(`Invoice fiscalized! FDN: ${result.fdn}`);
      // Display QR code
      document.getElementById('qrCode').src = result.qr_code;
    } else {
      alert(`Error: ${result.message}`);
    }
  } catch (error) {
    alert('Failed to submit invoice: ' + error.message);
  }
});
</script>
```

---

## Testing Your Implementation

### 1. Test Invoice Submission

**Using cURL:**
```bash
curl -X POST http://localhost:8001/api/external/efris/submit-invoice \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "invoice_number": "TEST-001",
    "invoice_date": "2024-01-24",
    "customer_name": "Test Customer",
    "items": [
      {
        "item_name": "Test Product",
        "quantity": 1,
        "unit_price": 10000,
        "total": 10000,
        "tax_rate": 0.18,
        "tax_amount": 1800
      }
    ],
    "total_amount": 10000,
    "total_tax": 1800,
    "currency": "UGX"
  }'
```

**Using Python:**
```python
import requests

API_KEY = "your_api_key"
url = "http://localhost:8001/api/external/efris/submit-invoice"

invoice_data = {
    "invoice_number": "TEST-001",
    "invoice_date": "2024-01-24",
    "customer_name": "Test Customer",
    "items": [{
        "item_name": "Test Product",
        "quantity": 1,
        "unit_price": 10000,
        "total": 10000,
        "tax_rate": 0.18,
        "tax_amount": 1800
    }],
    "total_amount": 10000,
    "total_tax": 1800,
    "currency": "UGX"
}

response = requests.post(
    url,
    json=invoice_data,
    headers={"X-API-Key": API_KEY}
)

print(response.json())
```

### 2. Test Product Registration

```python
product_data = {
    "product_code": "TEST001",
    "product_name": "Test Product",
    "unit_price": 50000,
    "commodity_code": "1010101",
    "unit_of_measure": "102",
    "currency": "UGX",
    "have_excise_tax": "102",
    "stock_quantity": 100
}

response = requests.post(
    "http://localhost:8001/api/external/efris/register-product",
    json=product_data,
    headers={"X-API-Key": API_KEY}
)
```

### 3. Test Purchase Order

```python
po_data = {
    "po_number": "PO-TEST-001",
    "po_date": "2024-01-24",
    "vendor_name": "Test Supplier",
    "vendor_tin": "1234567890",
    "items": [{
        "item_name": "Raw Material",
        "quantity": 50,
        "unit_price": 10000,
        "total": 500000,
        "unit_of_measure": "102"
    }],
    "total_amount": 500000,
    "currency": "UGX"
}

response = requests.post(
    "http://localhost:8001/api/external/efris/submit-purchase-order",
    json=po_data,
    headers={"X-API-Key": API_KEY}
)
```

### 4. Test Credit Note

```python
credit_note_data = {
    "credit_note_number": "CN-TEST-001",
    "credit_note_date": "2024-01-24",
    "original_invoice_number": "INV-001",
    "original_fdn": "1234567890123456",
    "customer_name": "Test Customer",
    "reason": "Product return",
    "items": [{
        "item_name": "Test Product",
        "quantity": 1,
        "unit_price": 10000,
        "total": 10000,
        "tax_rate": 0.18,
        "tax_amount": 1800
    }],
    "total_amount": 10000,
    "total_tax": 1800,
    "currency": "UGX"
}

response = requests.post(
    "http://localhost:8001/api/external/efris/submit-credit-note",
    json=credit_note_data,
    headers={"X-API-Key": API_KEY}
)
```

---

## Error Handling

### Common Errors

**1. Authentication Error (401)**
```json
{
  "detail": "Invalid or missing API key"
}
```
**Fix:** Check your X-API-Key header

**2. Validation Error (400)**
```json
{
  "detail": "Missing required field: invoice_number"
}
```
**Fix:** Ensure all required fields are present

**3. EFRIS Error (400)**
```json
{
  "success": false,
  "error_code": "01004",
  "message": "Duplicate invoice number"
}
```
**Fix:** Use unique invoice numbers

### Error Handling in Your Code

```python
try:
    response = requests.post(url, json=data, headers=headers, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    if result.get("success"):
        # Success
        print(f"FDN: {result['fdn']}")
    else:
        # EFRIS error
        print(f"Error {result['error_code']}: {result['message']}")
        
except requests.exceptions.HTTPError as e:
    # HTTP error (400, 401, 500, etc.)
    print(f"HTTP Error: {e.response.status_code}")
    print(f"Details: {e.response.json()}")
    
except requests.exceptions.Timeout:
    # Request timeout
    print("Request timed out")
    
except requests.exceptions.ConnectionError:
    # Server not reachable
    print("Cannot connect to EFRIS server")
```

---

## Deployment Checklist

### Before Going Live:

- [ ] Server is running (`python api_multitenant.py` or `uvicorn`)
- [ ] Port 8001 is accessible from your custom ERP
- [ ] API keys are generated for your company
- [ ] Database has all required tables
- [ ] EFRIS certificates are installed
- [ ] Test mode is disabled (`is_test_mode = False`)
- [ ] Firewall allows connections to port 8001
- [ ] SSL/HTTPS is configured (for production)
- [ ] Error logging is set up
- [ ] Backup system is in place

### Start the Server:

```bash
# Development
python api_multitenant.py

# Production (with Gunicorn)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_multitenant:app --bind 0.0.0.0:8001
```

---

## Summary

**Backend Status: ✅ FULLY IMPLEMENTED**

All 4 endpoints are ready:
1. ✅ Submit Invoice (`/submit-invoice`)
2. ✅ Register Product (`/register-product`)
3. ✅ Submit Purchase Order (`/submit-purchase-order`)
4. ✅ Submit Credit Note (`/submit-credit-note`)

**What You Need to Do:**

1. **Get your API key** from the database
2. **Create buttons/forms** in your custom ERP
3. **Add click handlers** that call the backend endpoints
4. **Display results** (FDN, QR code, errors)
5. **Test** with sample data
6. **Go live!**

**Need Help?**
- Check `EXTERNAL_API_DOCUMENTATION.md` for detailed API reference
- Check `QUICK_START_CUSTOM_ERP.md` for quick examples
- Test endpoints with cURL or Postman first
- Use the error codes to debug issues

---

## Next Steps

1. Open your custom ERP code
2. Find where your "Save" button is
3. Add a new button: "Save and Send to EFRIS"
4. Add a click handler (see examples above)
5. Test with a sample invoice
6. Deploy to production

**That's it! Your custom ERP is now connected to EFRIS!**
