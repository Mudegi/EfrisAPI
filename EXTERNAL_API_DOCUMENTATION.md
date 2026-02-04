# EFRIS External API Documentation
## For Custom ERP Integration

This API allows your custom ERP system to directly submit invoices and products to EFRIS through our platform.

---

## Authentication

All requests must include an API key in the header:

```http
X-API-Key: efris_your_api_key_here
```

**Where to get your API key:**
- Provided when your account is created by the platform owner
- Available in your dashboard settings
- Format: `efris_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## Base URL

```
Production: https://yourdomain.com/api/external/efris
Development: http://127.0.0.1:8001/api/external/efris
```

---

## Endpoints

### 1. Submit Invoice to EFRIS

**Endpoint:** `POST /api/external/efris/submit-invoice`

**Description:** Submit an invoice directly to EFRIS and receive Fiscal Document Number (FDN) and QR code.

**Request Headers:**
```http
Content-Type: application/json
X-API-Key: efris_your_api_key_here
```

**Request Body:**
```json
{
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-24",
  "customer_name": "ABC Company Ltd",
  "customer_tin": "1234567890",
  "buyer_type": "0",
  "buyer_phone": "+256700000000",
  "buyer_email": "abc@example.com",
  "items": [
    {
      "item_name": "Product A",
      "item_code": "PROD-001",
      "quantity": 10,
      "unit_price": 5000,
      "total": 50000,
      "tax_rate": 0.18,
      "tax_amount": 9000,
      "discount": 0,
      "discount_amount": 0,
      "excise_duty": 0,
      "excise_amount": 0,
      "unit_of_measure": "102",
      "commodity_code": "1010101",
      "commodity_name": "General Goods"
    }
  ],
  "total_amount": 50000,
  "total_tax": 9000,
  "total_discount": 0,
  "total_excise": 0,
  "currency": "UGX",
  "reference_number": "REF-001"
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `invoice_number` | string | Yes | Your internal invoice number |
| `invoice_date` | string | Yes | Format: YYYY-MM-DD |
| `customer_name` | string | Yes | Customer/buyer name |
| `customer_tin` | string | No | Customer TIN (if business) |
| `buyer_type` | string | No | "0"=Business, "1"=Individual |
| `buyer_phone` | string | No | Customer phone number |
| `buyer_email` | string | No | Customer email |
| `items` | array | Yes | List of invoice items |
| `total_amount` | number | Yes | Total before tax |
| `total_tax` | number | No | Total VAT amount |
| `total_discount` | number | No | Total discount |
| `total_excise` | number | No | Total excise duty |
| `currency` | string | No | Default: "UGX" |

**Item Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_name` | string | Yes | Product/service name |
| `item_code` | string | No | Your internal product code |
| `quantity` | number | Yes | Quantity sold |
| `unit_price` | number | Yes | Price per unit |
| `total` | number | Yes | Line total (before tax) |
| `tax_rate` | number | No | VAT rate (e.g., 0.18 for 18%) |
| `tax_amount` | number | No | VAT amount for this line |
| `discount` | number | No | Discount percentage |
| `discount_amount` | number | No | Discount amount |
| `unit_of_measure` | string | No | "102"=Pieces, "101"=Kg, etc. |
| `commodity_code` | string | No | EFRIS commodity category |

**Success Response (200 OK):**
```json
{
  "success": true,
  "fdn": "1234567890123456",
  "verification_code": "ABC123XYZ",
  "qr_code": "iVBORw0KGgoAAAANSUhEUgAA...",
  "efris_invoice_id": "EFRIS_INTERNAL_ID",
  "invoice_number": "INV-2024-001",
  "fiscalized_at": "2024-01-24T10:30:00",
  "message": "Invoice fiscalized successfully"
}
```

**Response Fields:**

| Field | Description |
|-------|-------------|
| `fdn` | **Fiscal Document Number** - Print this on invoice |
| `verification_code` | Anti-fake code from EFRIS |
| `qr_code` | Base64 encoded QR code image - Print on invoice |
| `efris_invoice_id` | EFRIS internal tracking ID |
| `fiscalized_at` | Timestamp when invoice was fiscalized |

**Error Response (400 Bad Request):**
```json
{
  "detail": {
    "success": false,
    "error_code": "2122",
    "message": "Device not registered in EFRIS",
    "details": "EFRIS rejected the invoice"
  }
}
```

**Common Error Codes:**

| Code | Meaning | Solution |
|------|---------|----------|
| `2122` | Device not registered | Contact support to register device |
| `1002` | Invalid TIN | Check company TIN configuration |
| `0001` | Invalid data format | Check request payload format |
| `401` | Invalid API key | Check X-API-Key header |

---

### 2. Register Product/Item

**Endpoint:** `POST /api/external/efris/register-product`

**Description:** Register a product with EFRIS before invoicing.

**Request Headers:**
```http
Content-Type: application/json
X-API-Key: efris_your_api_key_here
```

**Request Body:**
```json
{
  "item_code": "PROD-001",
  "item_name": "Product A",
  "unit_price": 5000,
  "commodity_code": "1010101",
  "commodity_name": "General Goods",
  "unit_of_measure": "102",
  "have_excise_tax": "102",
  "stock_quantity": 100,
  "description": "Product description"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "product_code": "PROD-001",
  "efris_status": "Registered",
  "message": "Product registered successfully"
}
```

---

### 3. Query Invoice Status

**Endpoint:** `GET /api/external/efris/invoice/{invoice_number}`

**Description:** Check the status of a previously submitted invoice.

**Request Headers:**
```http
X-API-Key: efris_your_api_key_here
```

**Success Response (200 OK):**
```json
{
  "invoice_number": "INV-2024-001",
  "fdn": "1234567890123456",
  "status": "success",
  "customer_name": "ABC Company Ltd",
  "total_amount": 50000,
  "total_tax": 9000,
  "fiscalized_at": "2024-01-24T10:30:00",
  "error_message": null
}
```

**Status Values:**
- `success` - Invoice successfully fiscalized
- `failed` - EFRIS rejected the invoice
- `pending` - Submitted but waiting for EFRIS response

---

### 4. List Invoices

**Endpoint:** `GET /api/external/efris/invoices`

**Description:** Get a paginated list of invoices.

**Query Parameters:**
- `limit` - Number of results (max 100, default 50)
- `offset` - Pagination offset (default 0)
- `status` - Filter by status: `success`, `failed`, `pending`

**Example:**
```http
GET /api/external/efris/invoices?limit=20&offset=0&status=success
X-API-Key: efris_your_api_key_here
```

**Success Response (200 OK):**
```json
{
  "total": 150,
  "limit": 20,
  "offset": 0,
  "invoices": [
    {
      "invoice_number": "INV-2024-001",
      "fdn": "1234567890123456",
      "status": "success",
      "customer_name": "ABC Company Ltd",
      "total_amount": 50000,
      "fiscalized_at": "2024-01-24T10:30:00"
    }
  ]
}
```

---

## Code Examples

### Python Example

```python
import requests
import json

API_KEY = "efris_your_api_key_here"
BASE_URL = "http://127.0.0.1:8001/api/external/efris"

def submit_invoice(invoice_data):
    """Submit invoice to EFRIS"""
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/submit-invoice",
        headers=headers,
        json=invoice_data,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success! FDN: {result['fdn']}")
        print(f"Verification Code: {result['verification_code']}")
        return result
    else:
        error = response.json()
        print(f"❌ Error: {error['detail']}")
        return None

# Example usage
invoice = {
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-24",
    "customer_name": "ABC Company Ltd",
    "customer_tin": "1234567890",
    "buyer_type": "0",
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

result = submit_invoice(invoice)
```

### PHP Example

```php
<?php

function submitInvoice($invoiceData) {
    $apiKey = "efris_your_api_key_here";
    $baseUrl = "http://127.0.0.1:8001/api/external/efris";
    
    $ch = curl_init($baseUrl . "/submit-invoice");
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($invoiceData));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        "X-API-Key: " . $apiKey,
        "Content-Type: application/json"
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode == 200) {
        $result = json_decode($response, true);
        echo "✅ Success! FDN: " . $result['fdn'] . "\n";
        return $result;
    } else {
        $error = json_decode($response, true);
        echo "❌ Error: " . $error['detail'] . "\n";
        return null;
    }
}

// Example usage
$invoice = [
    "invoice_number" => "INV-2024-001",
    "invoice_date" => "2024-01-24",
    "customer_name" => "ABC Company Ltd",
    "items" => [
        [
            "item_name" => "Product A",
            "quantity" => 10,
            "unit_price" => 5000,
            "total" => 50000,
            "tax_rate" => 0.18,
            "tax_amount" => 9000
        ]
    ],
    "total_amount" => 50000,
    "total_tax" => 9000,
    "currency" => "UGX"
];

$result = submitInvoice($invoice);
?>
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const API_KEY = 'efris_your_api_key_here';
const BASE_URL = 'http://127.0.0.1:8001/api/external/efris';

async function submitInvoice(invoiceData) {
    try {
        const response = await axios.post(
            `${BASE_URL}/submit-invoice`,
            invoiceData,
            {
                headers: {
                    'X-API-Key': API_KEY,
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            }
        );
        
        console.log('✅ Success! FDN:', response.data.fdn);
        console.log('Verification Code:', response.data.verification_code);
        return response.data;
        
    } catch (error) {
        if (error.response) {
            console.error('❌ Error:', error.response.data.detail);
        } else {
            console.error('❌ Network Error:', error.message);
        }
        return null;
    }
}

// Example usage
const invoice = {
    invoice_number: 'INV-2024-001',
    invoice_date: '2024-01-24',
    customer_name: 'ABC Company Ltd',
    items: [
        {
            item_name: 'Product A',
            quantity: 10,
            unit_price: 5000,
            total: 50000,
            tax_rate: 0.18,
            tax_amount: 9000
        }
    ],
    total_amount: 50000,
    total_tax: 9000,
    currency: 'UGX'
};

submitInvoice(invoice);
```

---

## Integration Workflow

### Typical Flow in Your Custom ERP

```
1. User creates invoice in your ERP
   ↓
2. User clicks "Save and Send to EFRIS"
   ↓
3. Your ERP saves invoice to local database
   ↓
4. Your ERP calls POST /api/external/efris/submit-invoice
   ↓
5. Our platform handles EFRIS communication
   ↓
6. Response received (2-5 seconds)
   ↓
7. Your ERP updates invoice with FDN and QR code
   ↓
8. Invoice printed with QR code
```

---

## Best Practices

### 1. Error Handling

Always handle these scenarios:

```python
try:
    response = submit_invoice(invoice_data)
    
    if response:
        # Success - save FDN to your database
        save_fdn_to_db(invoice_id, response['fdn'])
    
except requests.Timeout:
    # Timeout - mark for retry
    mark_invoice_as_pending(invoice_id)
    show_message("EFRIS request timeout. Will retry automatically.")

except requests.HTTPError as e:
    if e.response.status_code == 400:
        # Validation error - show to user
        error = e.response.json()
        show_error(f"Invalid data: {error['detail']}")
    
    elif e.response.status_code == 401:
        # Auth error
        show_error("Invalid API credentials. Contact administrator.")
```

### 2. Retry Logic

For transient failures:

```python
import time

def submit_with_retry(invoice_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            return submit_invoice(invoice_data)
        except requests.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                raise
```

### 3. QR Code Display

The QR code is returned as base64. To display:

```python
import base64
from PIL import Image
from io import BytesIO

# Decode base64 QR code
qr_data = base64.b64decode(result['qr_code'])
qr_image = Image.open(BytesIO(qr_data))

# Display in UI or print on invoice
qr_image.show()

# Or save to file
qr_image.save(f"invoice_{invoice_number}_qr.png")
```

### 4. Security

- **Never hardcode API keys** in your source code
- Store API keys in environment variables or config files
- Use HTTPS in production
- Rotate API keys periodically

---

## Testing

### Test Mode

When your account is configured with `test_mode=True`:
- All requests go to EFRIS test/sandbox environment
- Use test data and test TINs
- FDNs are not valid for real transactions

### Production Mode

When `test_mode=False`:
- Requests go to live EFRIS production
- Use real company TIN and device number
- FDNs are legally valid fiscal documents

---

## Rate Limits

- **100 requests per minute** per API key
- **1000 requests per hour** per API key
- Exceeding limits returns HTTP 429 (Too Many Requests)

---

## Support

**Technical Issues:**
- Email: support@yourplatform.com
- Check API status: `/health` endpoint

**EFRIS-Specific Issues:**
- URA EFRIS Support: https://efris.ura.go.ug
- Phone: +256 (0) 417 123456

---

## Changelog

**v1.0.0 (2024-01-24)**
- Initial release
- Submit invoice endpoint
- Register product endpoint
- Query invoice endpoint
- List invoices endpoint

---

## Appendix

### Unit of Measure Codes

| Code | Description |
|------|-------------|
| 101 | Kilogram (Kg) |
| 102 | Pieces (Pcs) |
| 103 | Liter (L) |
| 104 | Meter (M) |
| 105 | Box |

### Buyer Type Codes

| Code | Description |
|------|-------------|
| 0 | Business/Company |
| 1 | Individual |
| 2 | Government |
| 3 | Foreigner |

### Tax Rate Codes

| Code | Rate |
|------|------|
| 18 | 18% VAT (Standard) |
| 0 | 0% VAT (Zero-rated) |
| - | Tax Exempt |

---

**End of Documentation**
