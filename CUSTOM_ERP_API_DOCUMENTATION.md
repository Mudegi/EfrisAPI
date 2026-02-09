# Custom ERP EFRIS API Documentation

## Overview
Complete API reference for Custom ERP systems to integrate with EFRIS. All endpoints follow the same proven format as the working QuickBooks integration.

**Base URL:** `https://efrisintegration.nafacademy.com`

**Authentication:** API Key + Secret (provided when you create your company)

---

## Authentication

All requests require these headers:
```
X-API-Key: your_api_key
X-API-Secret: your_api_secret
Content-Type: application/json
```

---

## Endpoints

### 1. Register Product/Service (T130✅
**Endpoint:** `POST /api/external/efris/register-product`
**Status:** ✅ Working - Aligned with QuickBooks

**Request:**
```json
{
  "item_code": "PROD-001",
  "item_name": "HP Chromebook",
  "unit_price": 1000000,
  "commodity_code": "44102906",
  "unit_of_measure": "102",
  "have_excise_tax": "102",
  "stock_quantity": 50,
  "description": "HP Chromebook 14"
}
```

**Response:**
```json
{
  "success": true,
  "product_code": "PROD-001",
  "efris_status": "Registered",
  "message": "Product registered successfully"
}
```

**See:** [CUSTOM_ERP_PRODUCT_REGISTRATION.md](CUSTOM_ERP_PRODUCT_REGISTRATION.md) for detailed guide

---

### 2. Stock Increase (T131) ✅
**Endpoint:** `POST /api/external/efris/stock-increase`
**Status:** ✅ Working - Aligned with QuickBooks

**Request:**
```json
{
  "goodsStockIn": {
    "operationType": "101",
    "supplierTin": "1234567890",
    "supplierName": "Supplier Ltd",
    "stockInType": "102",
    "stockInDate": "2026-02-09",
    "remarks": "Stock replenishment"
  },
  "goodsStockInItem": [
    {
      "goodsCode": "PROD-001",
      "quantity": "100",
      "unitPrice": "5000",
      "measureUnit": "102",
      "remarks": "Received from supplier"
    }
  ]
}
```

**Field Codes:**
- `operationType`: "101" = Increase
- `stockInType`: 
  - "101" = Import  
  - "102" = Local Purchase
  - "103" = Manufacture/Assembling
  - "104" = Opening Stock

**Response:**
```json
{
  "success": true,
  "message": "Stock increase submitted successfully",
  "efris_response": {...}
}
```

---

### 3. Stock Decrease (T131) ✅
**Endpoint:** `POST /api/external/efris/stock-decrease`
**Status:** ✅ Working - Aligned with QuickBooks

**Request:**
```json
{
  "goodsStockIn": {
    "operationType": "102",
    "adjustType": "102",
    "remarks": "Damaged goods"
  },
  "goodsStockInItem": [
    {
      "goodsCode": "PROD-001",
      "quantity": "10",
      "unitPrice": "5000",
      "measureUnit": "102",
      "remarks": "Water damage"
    }
  ]
}
```

**Field Codes:**
- `operationType`: "102" = Decrease
- `adjustType`:
  - "101" = Expired Goods
  - "102" = Damaged Goods
  - "103" = Personal Uses
  - "104" = Others (specify in remarks)
  - "105" = Raw Material(s)

**Response:**
```json
{
  "success": true,
  "stock_id": 123,
  "message": "Stock decrease submitted successfully",
  "efris_response": {...}
}
```

---

### 4. Submit Invoice (T109) 🔧
**Endpoint:** `POST /api/external/efris/submit-invoice`
**Status:** 🔧 Working - May need QuickBooks alignment

**Request:**
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
      "quantity": 10,
      "unit_price": 5000,
      "total": 50000,
      "tax_rate": 0.18,
      "tax_amount": 9000,
      "discount": 0,
      "discount_amount": 0,
      "excise_duty": 0,
      "unit_of_measure": "102"
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

**Response:**
```json
{
  "success": true,
  "fdn": "1234567890123456",
  "verification_code": "ABC123",
  "qr_code": "base64_qr_code_here",
  "efris_invoice_id": "internal_id",
  "invoice_number": "INV-2024-001",
  "fiscalized_at": "2024-01-24T10:30:00",
  "message": "Invoice fiscalized successfully"
}
```

---

### 5. Submit Credit Note (T110) 🔧
**Endpoint:** `POST /api/external/efris/submit-credit-note`
**Status:** 🔧 Working - May need QuickBooks alignment

**Request:**
```json
{
  "credit_note_number": "CN-2024-001",
  "credit_note_date": "2024-01-24",
  "original_invoice_number": "INV-001",
  "original_fdn": "1234567890123456",
  "customer_name": "ABC Ltd",
  "reason": "Product return - defective item",
  "items": [...],
  "total_amount": 10000,
  "total_tax": 1800,
  "currency": "UGX"
}
```

**Response:**
```json
{
  "success": true,
  "fdn": "9876543210987654",
  "message": "Credit note submitted successfully"
}
```

---

### 6. Get Excise Duty Codes ✅
**Endpoint:** `GET /api/external/efris/excise-duty`
**Status:** ✅ Working

**Response:**
```json
[
  {
    "excise_duty_code": "102010401",
    "excise_duty_name": "Beer (Bottled)",
    "unit_of_measure": "104",
    "excise_rate": 0.30,
    "description": "Bottled beer products"
  }
]
```

---

### 7. Query Invoice ✅
**Endpoint:** `GET /api/external/efris/invoice/{invoice_number}`
**Status:** ✅ Working

**Response:**
```json
{
  "invoice_number": "INV-001",
  "fdn": "1234567890123456",
  "status": "fiscalized",
  "customer_name": "ABC Ltd",
  "total_amount": 50000,
  "created_at": "2024-01-24T10:30:00"
}
```

---

### 8. List Invoices ✅
**Endpoint:** `GET /api/external/efris/invoices`
**Status:** ✅ Working

**Query Parameters:**
- `limit`: Number of records (default: 100)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "total": 150,
  "invoices": [...]
}
```

---

## Getting Reference Data

### Commodity Codes
```bash
GET /api/external/efris/commodity-codes?search=computer
```

### Measure Units
```bash
GET /api/external/efris/measure-units
```

---

## Error Handling

**400 Bad Request:**
```json
{
  "detail": "Missing required field: item_code"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid API credentials"
}
```

**500 Internal Error:**
```json
{
  "detail": "EFRIS error 601: MeasureUnit invalid field value!"
}
```

---

## Code Examples

### Python Example
```python
import requests

API_BASE = "https://efrisintegration.nafacademy.com"
API_KEY = "efris_your_api_key"
API_SECRET = "your_api_secret"

headers = {
    "X-API-Key": API_KEY,
    "X-API-Secret": API_SECRET,
    "Content-Type": "application/json"
}

# Register a product
product_data = {
    "item_code": "PROD-001",
    "item_name": "Dell Laptop",
    "unit_price": 2500000,
    "commodity_code": "44102906",
    "unit_of_measure": "102"
}

response = requests.post(
    f"{API_BASE}/api/external/efris/register-product",
    headers=headers,
    json=product_data
)

print(response.json())
```

### Node.js Example
```javascript
const axios = require('axios');

const API_BASE = 'https://efrisintegration.nafacademy.com';
const API_KEY = 'efris_your_api_key';
const API_SECRET = 'your_api_secret';

const headers = {
  'X-API-Key': API_KEY,
  'X-API-Secret': API_SECRET,
  'Content-Type': 'application/json'
};

// Register a product
const productData = {
  item_code: 'PROD-001',
  item_name: 'Dell Laptop',
  unit_price: 2500000,
  commodity_code: '44102906',
  unit_of_measure: '102'
};

axios.post(`${API_BASE}/api/external/efris/register-product`, productData, { headers })
  .then(response => console.log(response.data))
  .catch(error => console.error(error.response.data));
```

---

## Deployment

**Production Server:**
```bash
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com
git pull origin main
touch tmp/restart.txt
```

---

## Support

For issues or questions, refer to:
- [CUSTOM_ERP_PRODUCT_REGISTRATION.md](CUSTOM_ERP_PRODUCT_REGISTRATION.md) - Product registration guide
- [CUSTOM_ERP_ENDPOINTS_COMPLETE.md](CUSTOM_ERP_ENDPOINTS_COMPLETE.md) - Implementation plan
- Check EFRIS interface documentation in `Documentation/interface codes.py`
