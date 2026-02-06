# 📋 EFRIS API Quick Reference Card

**Print this page and keep it handy while integrating!**

---

## 🔑 Authentication

```http
X-API-Key: efris_your_api_key_here
Content-Type: application/json
```

---

## 🌐 Base URLs

| Environment | URL |
|-------------|-----|
| **Production** | `https://efrisintegration.nafacademy.com/api/external/efris` |
| **Staging** | `https://staging.efrisintegration.nafacademy.com/api/external/efris` |
| **Swagger Docs** | `https://efrisintegration.nafacademy.com/docs` |
| **ReDoc** | `https://efrisintegration.nafacademy.com/redoc` |

---

## 🚀 Common Endpoints

### Submit Invoice
```http
POST /submit-invoice
{
  "invoice_number": "INV-001",
  "invoice_date": "2026-02-06",
  "customer_name": "ABC Company",
  "customer_tin": "1000000000",
  "items": [{
    "description": "Product",
    "quantity": 1,
    "unit_price": 10000,
    "tax_rate": 18
  }]
}
```

### Register Product
```http
POST /register-product
{
  "item_code": "PROD-001",
  "name": "Product Name",
  "unit_price": 10000,
  "tax_rate": 18,
  "category_code": "1010101010104"
}
```

### Query Invoice
```http
GET /query-invoice/{invoice_number}
```

### List Invoices
```http
GET /invoices?page=1&limit=20&start_date=2026-02-01
```

---

## ✅ Required Invoice Fields

| Field | Type | Example |
|-------|------|---------|
| `invoice_number` | string | "INV-2026-001" |
| `invoice_date` | string | "2026-02-06" |
| `customer_name` | string | "ABC Company" |
| `items` | array | See below |
| `items[].description` | string | "Laptop" |
| `items[].quantity` | number | 1 |
| `items[].unit_price` | number | 2500000 |
| `items[].tax_rate` | number | 18 |

---

## 📦 Optional Invoice Fields

| Field | Type | Example |
|-------|------|---------|
| `customer_tin` | string | "1000000000" |
| `customer_phone` | string | "0700123456" |
| `customer_email` | string | "email@company.com" |
| `customer_address` | string | "Kampala, Uganda" |
| `payment_mode` | string | "101" |
| `currency` | string | "UGX" (default) |
| `items[].discount` | number | 50000 |
| `items[].item_code` | string | "PROD-001" |
| `items[].excise_duty_code` | string | "104" |
| `items[].excise_rate` | number | 30 |

---

## 💰 Tax Calculation

```python
# Formula
subtotal = quantity * unit_price
discount_amount = discount
taxable = subtotal - discount_amount
tax_amount = taxable * (tax_rate / 100)
excise_amount = taxable * (excise_rate / 100)  # if excisable
total = taxable + tax_amount + excise_amount

# Example: 1 item, 10000 UGX, 18% tax
subtotal = 1 * 10000 = 10000
taxable = 10000 - 0 = 10000
tax = 10000 * 0.18 = 1800
total = 10000 + 1800 = 11800
```

---

## 🏷️ Common Product Categories

| Code | Description |
|------|-------------|
| `1010101010104` | General goods |
| `1010101010199` | Beverages |
| `1010101010201` | Food items |
| `1010101010301` | Electronics |
| `1010101010401` | Furniture |
| `1010101010501` | Clothing |

**Full list:** `GET /reference/product-categories`

---

## 💳 Payment Mode Codes

| Code | Description |
|------|-------------|
| `101` | Cash |
| `102` | Credit |
| `103` | Mobile Money |
| `104` | Bank Transfer |
| `105` | Check |

**Full list:** `GET /reference/payment-modes`

---

## 🍺 Excise Duty Codes

| Code | Product | Rate |
|------|---------|------|
| `102` | Cigarettes | 30% |
| `104` | Beer | 30% |
| `105` | Spirits | 60% |
| `106` | Wine | 20% |
| `107` | Fuel | Variable |
| `108` | Cement | 500 UGX/bag |

**Full list:** `GET /reference/excise-codes`

---

## 📐 Units of Measure

| Code | Description |
|------|-------------|
| `PCS` | Pieces |
| `BTL` | Bottles |
| `KG` | Kilograms |
| `LTR` | Liters |
| `MTR` | Meters |
| `BOX` | Boxes |

**Full list:** `GET /reference/units-of-measure`

---

## ✅ Success Response

```json
{
  "success": true,
  "fdn": "1000000000-ABC-12345678",
  "qr_code": "https://efris.ura.go.ug/verify/...",
  "verification_code": "123456",
  "invoice_id": "uuid-here",
  "submitted_at": "2026-02-06T14:30:00Z"
}
```

---

## ❌ Error Response

```json
{
  "success": false,
  "error": "Missing required field: customer_name",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "customer_name",
    "required": true
  }
}
```

---

## 🐛 Common Error Codes

| Code | Description | Fix |
|------|-------------|-----|
| `INVALID_API_KEY` | Bad API key | Check key, regenerate |
| `VALIDATION_ERROR` | Missing field | Check required fields |
| `RATE_LIMIT` | Too many requests | Wait 60s, retry |
| `NETWORK_ERROR` | Connection failed | Check internet, retry |
| `DUPLICATE_INVOICE` | Number exists | Use unique numbers |
| `EFRIS_ERROR` | EFRIS rejected | Check EFRIS error details |

---

## 🔢 EFRIS Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `00` | Success | N/A |
| `01` | Missing field | Add required field |
| `02` | Invalid format | Check date/number format |
| `03` | Invalid TIN | Verify customer TIN |
| `100` | Taxpayer not found | Check TIN, test mode |
| `101` | Invalid certificate | Check .p12 file |
| `102` | Signature error | Update signature code |
| `110` | Duplicate | Use unique invoice number |

---

## 🚦 Rate Limits

| Tier | Requests/Min | Requests/Day |
|------|--------------|--------------|
| Free | 60 | 1,000 |
| Basic | 100 | 10,000 |
| Pro | 300 | 50,000 |
| Enterprise | Unlimited | Unlimited |

**Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

---

## 🔄 Retry Logic Template

```python
import time

def retry_request(func, max_retries=3):
    for attempt in range(max_retries):
        result = func()
        
        if result.get('success'):
            return result
        
        error_code = result.get('error_code')
        if error_code in ['NETWORK_ERROR', 'TIMEOUT', 'RATE_LIMIT']:
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                time.sleep(wait)
                continue
        
        return result
    
    return result
```

---

## 🎯 Python Quick Start

```python
import requests
import os

API_KEY = os.getenv('EFRIS_API_KEY')
BASE_URL = 'https://efrisintegration.nafacademy.com/api/external/efris'

def submit_invoice(invoice):
    response = requests.post(
        f'{BASE_URL}/submit-invoice',
        json=invoice,
        headers={
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
        },
        timeout=30
    )
    return response.json()

# Usage
invoice = {
    'invoice_number': 'INV-001',
    'invoice_date': '2026-02-06',
    'customer_name': 'ABC Company',
    'items': [{
        'description': 'Product',
        'quantity': 1,
        'unit_price': 10000,
        'tax_rate': 18
    }]
}

result = submit_invoice(invoice)
if result['success']:
    print(f"FDN: {result['fdn']}")
```

---

## 🔌 PHP Quick Start

```php
<?php
$apiKey = getenv('EFRIS_API_KEY');
$baseUrl = 'https://efrisintegration.nafacademy.com/api/external/efris';

$invoice = [
    'invoice_number' => 'INV-001',
    'invoice_date' => '2026-02-06',
    'customer_name' => 'ABC Company',
    'items' => [[
        'description' => 'Product',
        'quantity' => 1,
        'unit_price' => 10000,
        'tax_rate' => 18
    ]]
];

$ch = curl_init("$baseUrl/submit-invoice");
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($invoice));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "X-API-Key: $apiKey",
    'Content-Type: application/json'
]);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$response = curl_exec($ch);
$result = json_decode($response, true);

if ($result['success']) {
    echo "FDN: " . $result['fdn'];
}
curl_close($ch);
?>
```

---

## 🌐 JavaScript Quick Start

```javascript
const axios = require('axios');

const API_KEY = process.env.EFRIS_API_KEY;
const BASE_URL = 'https://efrisintegration.nafacademy.com/api/external/efris';

async function submitInvoice(invoice) {
    const response = await axios.post(
        `${BASE_URL}/submit-invoice`,
        invoice,
        {
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            timeout: 30000
        }
    );
    return response.data;
}

// Usage
const invoice = {
    invoice_number: 'INV-001',
    invoice_date: '2026-02-06',
    customer_name: 'ABC Company',
    items: [{
        description: 'Product',
        quantity: 1,
        unit_price: 10000,
        tax_rate: 18
    }]
};

submitInvoice(invoice)
    .then(result => {
        if (result.success) {
            console.log(`FDN: ${result.fdn}`);
        }
    });
```

---

## 🧪 Testing Checklist

- [ ] Health check passes
- [ ] Authentication works
- [ ] Simple invoice submits
- [ ] Multi-item invoice submits
- [ ] Invoice with discount
- [ ] Excise duty invoice
- [ ] Product registration
- [ ] Invoice query
- [ ] List invoices with pagination
- [ ] Error handling works
- [ ] Retry logic implemented
- [ ] Rate limiting handled
- [ ] Logging configured
- [ ] Monitoring set up

---

## 🔒 Security Checklist

- [ ] API key in environment variable
- [ ] Never commit .env to git
- [ ] HTTPS only (no HTTP)
- [ ] Timeout set (30s recommended)
- [ ] Input validation
- [ ] Error logs sanitized
- [ ] Certificate files secured
- [ ] Key rotation schedule
- [ ] Webhook signatures verified
- [ ] Rate limiting implemented

---

## 📞 Quick Support

| Channel | Contact |
|---------|---------|
| **Email** | support@efrisintegration.com |
| **WhatsApp** | +256 XXX XXX XXX |
| **Docs** | https://efrisintegration.nafacademy.com/docs |
| **Status** | https://status.efrisintegration.com |

---

## 📚 Full Documentation

- 📖 [Documentation README](DOCUMENTATION_README.md)
- 🔧 [Custom ERP Integration Guide](CUSTOM_ERP_INTEGRATION_GUIDE.md)
- ❓ [Troubleshooting FAQ](TROUBLESHOOTING_FAQ.md)
- 🎥 [Video Tutorial Scripts](VIDEO_TUTORIAL_SCRIPTS.md)
- 📮 [Postman Collection](EFRIS_API_Postman_Collection.json)

---

**Version:** 2.0.0 | **Last Updated:** February 6, 2026

**💡 Pro Tip:** Bookmark this page or print it for quick reference!
