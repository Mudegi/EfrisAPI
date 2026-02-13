# Custom ERP - Complete EFRIS API Guide

**Everything you need to integrate your Custom ERP with EFRIS in one place.**

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Product Registration](#product-registration)
4. [Stock Management](#stock-management)
5. [Invoice Fiscalization](#invoice-fiscalization)
6. [Credit Notes](#credit-notes)
7. [Query Endpoints](#query-endpoints)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Get Your API Credentials
1. Login to the EFRIS Integration Dashboard as owner
2. Navigate to Settings → API Keys
3. Generate a new API Key and Secret
4. Save them securely - you'll need them for all API calls

### Base URL
- **Production**: `https://efrisintegration.nafacademy.com`
- **Testing**: `http://localhost:8001`

### Authentication Header
All external API requests must include:
```
X-API-Key: your_api_key_here
X-API-Secret: your_api_secret_here
```

---

## Authentication

Every API call requires authentication:

**Python Example:**
```python
import requests

headers = {
    "X-API-Key": "Cy3DwN9kVzXJtQHq8T7rLm4gP2sR6aFb",
    "X-API-Secret": "9fK3mX7pL2Q5nR8tW1vY4zC6hJ0bG3Sd",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://efrisintegration.nafacademy.com/api/external/efris/register-product",
    headers=headers,
    json=product_data
)
```

**Node.js Example:**
```javascript
const axios = require('axios');

const headers = {
    'X-API-Key': 'Cy3DwN9kVzXJtQHq8T7rLm4gP2sR6aFb',
    'X-API-Secret': '9fK3mX7pL2Q5nR8tW1vY4zC6hJ0bG3Sd',
    'Content-Type': 'application/json'
};

const response = await axios.post(
    'https://efrisintegration.nafacademy.com/api/external/efris/register-product',
    productData,
    { headers }
);
```

---

## Product Registration

### Endpoint: POST /api/external/efris/register-product

Before you can add products to invoices, you must register them with EFRIS first.

### Request Format

```json
{
    "item_code": "PROD-001",
    "item_name": "Cement 50kg Bag",
    "unit_price": 35000,
    "commodity_code": "1010524",
    "commodity_name": "Portland cement",
    "unit_of_measure": "102",
    "have_excise_tax": "102",
    "stock_quantity": 100,
    "description": "Portland cement 50kg bags"
}
```

### Field Reference

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `item_code` | Yes | Your internal product code | `"PROD-001"` |
| `item_name` | Yes | Product name (max 100 chars) | `"Cement 50kg Bag"` |
| `unit_price` | Yes | Price per unit | `35000` |
| `commodity_code` | Yes | EFRIS commodity code | `"1010524"` |
| `commodity_name` | Yes | Commodity name from EFRIS | `"Portland cement"` |
| `unit_of_measure` | No | Unit code (default: "102") | `"102"` |
| `have_excise_tax` | No | "101"=Yes, "102"=No (default: "102") | `"102"` |
| `excise_duty_code` | No* | Required ONLY if have_excise_tax="101" | `"130101"` |
| `stock_quantity` | No | Opening stock quantity | `100` |
| `description` | No | Product description | `"Portland cement"` |

### Common Unit of Measure Codes

**Get the complete list from:** `GET /api/external/efris/units-of-measure`

The API returns clean EFRIS data. Use this reference to understand what each code means:

**Most Common Codes:**
- `101` = Carton (products sold in boxes/cartons)
- `102` = Piece (individual items: computers, phones, furniture)
- `103` = Kilogram (products sold by weight)
- `104` = Litre (liquid products: water, fuel, beverages)
- `105` = Meter (length measurements: fabric, rope, cable)
- `106` = Tonne (heavy products sold by weight in tonnes)
- `107` = Gram (small quantities sold by weight)
- `112` = Pack (packaged products)
- `113` = Dozen (products sold in sets of 12)
- `115` = Pair (products sold in pairs: shoes, gloves)

**⚠️ Important:**
- Code 102 = **Piece** (NOT litres!)
- Code 104 = **Litre** (NOT pieces!)
- Always fetch the codes from EFRIS to ensure you're using current values
- Map your ERP's unit terminology to EFRIS codes correctly

### Response

**Success (200):**
```json
{
    "success": true,
    "message": "Product registered successfully",
    "item_code": "PROD-001"
}
```

**Error (400):**
```json
{
    "detail": {
        "success": false,
        "error_code": "645",
        "message": "Product already exists"
    }
}
```

### Complete Example

**Python:**
```python
import requests

BASE_URL = "https://efrisintegration.nafacademy.com"
headers = {
    "X-API-Key": "your_api_key",
    "X-API-Secret": "your_api_secret",
    "Content-Type": "application/json"
}

product_data = {
    "item_code": "CEMENT-001",
    "item_name": "Cement 50kg Bag",
    "unit_price": 35000,
    "commodity_code": "1010524",
    "commodity_name": "Portland cement",
    "unit_of_measure": "102",
    "have_excise_tax": "102",
    "stock_quantity": 100,
    "description": "Portland cement 50kg bags"
}

response = requests.post(
    f"{BASE_URL}/api/external/efris/register-product",
    headers=headers,
    json=product_data
)

print(response.json())
```

**Node.js:**
```javascript
const axios = require('axios');

const BASE_URL = 'https://efrisintegration.nafacademy.com';
const headers = {
    'X-API-Key': 'your_api_key',
    'X-API-Secret': 'your_api_secret',
    'Content-Type': 'application/json'
};

const productData = {
    item_code: 'CEMENT-001',
    item_name: 'Cement 50kg Bag',
    unit_price: 35000,
    commodity_code: '1010524',
    commodity_name: 'Portland cement',
    unit_of_measure: '102',
    have_excise_tax: '102',
    stock_quantity: 100,
    description: 'Portland cement 50kg bags'
};

try {
    const response = await axios.post(
        `${BASE_URL}/api/external/efris/register-product`,
        productData,
        { headers }
    );
    console.log(response.data);
} catch (error) {
    console.error(error.response.data);
}
```

### Excise Duty Products

For products with excise duty (beer, fuel, etc.):

```json
{
    "item_code": "BEER-001",
    "item_name": "Nile Beer 500ml",
    "unit_price": 3500,
    "commodity_code": "1010301",
    "commodity_name": "Beer",
    "unit_of_measure": "102",
    "have_excise_tax": "101",
    "excise_duty_code": "130101",
    "stock_quantity": 500
}
```

**IMPORTANT**: If `have_excise_tax="101"`, the `excise_duty_code` field is **REQUIRED**.

Get excise codes from: `GET /api/external/efris/excise-duty`

---

## 📋 COMPLETE T130 FIELD GUIDE (For ERP Developers)

### What You Need to Send to Register a Product

When you POST to `/api/external/efris/register-product`, send these fields:

#### ✅ REQUIRED FIELDS (Every Product Needs These)

```json
{
    "item_code": "YOUR-PRODUCT-CODE",
    "item_name": "Product Name",
    "unit_price": 10000,
    "commodity_code": "1010524"
}
```

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `item_code` | String | Your ERP's unique product code | `"CEMENT-001"` |
| `item_name` | String | Product name (max 100 characters) | `"Cement 50kg Bag"` |
| `unit_price` | Number | Selling price per unit | `35000` |
| `commodity_code` | String | EFRIS commodity category ID | `"1010524"` |

#### 📦 OPTIONAL FIELDS (But Recommended)

| Field | Type | Default | Description | Example |
|-------|------|---------|-------------|---------|
| `commodity_name` | String | - | Commodity category name | `"Portland cement"` |
| `unit_of_measure` | String | `"102"` | Unit code from EFRIS | `"102"` (Piece) |
| `description` | String | - | Product description | `"Portland cement 50kg bags"` |
| `stock_quantity` | Number | - | Opening/current stock balance | `100` |

#### 🚨 EXCISE DUTY FIELDS (Only for Excisable Products)

| Field | Type | Required When | Description | Example |
|-------|------|---------------|-------------|---------|
| `have_excise_tax` | String | - | `"101"` = Yes<br>`"102"` = No | `"101"` |
| `excise_duty_code` | String | **ONLY when `have_excise_tax="101"`** | Excise code from EFRIS T125 | `"130101"` |

### 🔴 CRITICAL RULES FOR EXCISE ITEMS

#### Rule 1: If Product Has Excise Tax
```json
{
    "item_code": "BEER-001",
    "item_name": "Nile Beer 500ml",
    "unit_price": 3500,
    "commodity_code": "1010301",
    "unit_of_measure": "104",     ← MUST match excise unit!
    "have_excise_tax": "101",     ← Set to "101" (YES)
    "excise_duty_code": "130101"  ← MUST provide this code
}
```

**What the API expects:**
- `have_excise_tax` MUST be `"101"` (string, not number)
- `excise_duty_code` is **REQUIRED** - API will reject without it
- **`unit_of_measure` MUST match the excise duty's unit from T125** ← CRITICAL!
- Get valid excise codes from: `GET /api/external/efris/excise-duty`

#### ⚠️ UNIT MATCHING REQUIREMENT (CRITICAL!)

**Each excise duty code has a specific unit of measure defined by EFRIS.**

When you fetch excise codes from `/api/external/efris/excise-duty`, you get:

```json
{
    "excise_codes": [
        {
            "exciseCode": "LED130100",
            "exciseName": "Gas oil (Diesel)",
            "unit": "104",        ← This is the REQUIRED unit
            "rate": "1230"
        },
        {
            "exciseCode": "LED190100",
            "exciseName": "Beer (local)",
            "unit": "104",        ← Beer must use unit 104 (Litre)
            "rate": "30"
        }
    ]
}
```

**📌 The Rule:**
```
If excise code LED130100 has unit="104" (Litre)
Then your product MUST be registered with unit_of_measure="104"
```

**Why This Matters:**
- Excise tax is calculated per specific unit (per litre, per kilogram, etc.)
- EFRIS rejects mismatched units
- Example: You can't register diesel (liquid) as "102" (Piece) - it MUST be "104" (Litre)

**Example Flow:**

1️⃣ **Fetch excise codes first:**
```python
response = requests.get(
    f"{BASE_URL}/api/external/efris/excise-duty",
    headers=headers
)
excise = response.json()
```

2️⃣ **Find your product's excise code and its unit:**
```python
# For diesel:
excise_code = "LED130100"  # Gas oil
excise_unit = "104"        # Litre (from T125 data)
```

3️⃣ **Register product with MATCHING unit:**
```python
product = {
    "item_code": "DIESEL-001",
    "item_name": "Diesel",
    "unit_price": 5500,
    "commodity_code": "1010401",
    "unit_of_measure": "104",        # ← MUST match excise unit
    "have_excise_tax": "101",
    "excise_duty_code": "LED130100"
}
```

#### Rule 2: If Product Does NOT Have Excise Tax
```json
{
    "item_code": "CEMENT-001",
    "item_name": "Cement 50kg Bag",
    "unit_price": 35000,
    "commodity_code": "1010524",
    "unit_of_measure": "102",
    "have_excise_tax": "102"      ← Set to "102" (NO)
    // DO NOT include excise_duty_code field at all
}
```

**What the API expects:**
- `have_excise_tax` set to `"102"` (or omit - defaults to "102")
- Do **NOT** send `excise_duty_code` field
- Sending excise_duty_code when have_excise_tax="102" may cause errors

### 📊 Complete Examples by Product Type

#### Example 1: Simple Product (No Excise)
```json
{
    "item_code": "CHAIR-001",
    "item_name": "Office Chair",
    "unit_price": 250000,
    "commodity_code": "5020101",
    "commodity_name": "Furniture",
    "unit_of_measure": "102",
    "description": "Ergonomic office chair",
    "stock_quantity": 50,
    "have_excise_tax": "102"
}
```

#### Example 2: Excisable Product (Beer)
```json
{
    "item_code": "BEER-NILE-500",
    "item_name": "Nile Special Beer 500ml",
    "unit_price": 3500,
    "commodity_code": "1010301",
    "commodity_name": "Beer",
    "unit_of_measure": "104",     ← Beer excise uses Litre
    "description": "Nile Special Beer 500ml bottle",
    "stock_quantity": 1000,
    "have_excise_tax": "101",
    "excise_duty_code": "LED190100"  ← Beer excise code
}
```

**Note:** Beer excise (LED190100) requires unit "104" (Litre), NOT "102" (Piece)

#### Example 3: Excisable Product (Fuel)
```json
{
    "item_code": "FUEL-DIESEL",
    "item_name": "Diesel",
    "unit_price": 5500,
    "commodity_code": "1010401",
    "commodity_name": "Petroleum products",
    "unit_of_measure": "104",      ← Diesel excise uses Litre
    "description": "Gas oil for automotive",
    "have_excise_tax": "101",
    "excise_duty_code": "LED130100",  ← Diesel excise code
    "goods_type_code": "102"
}
```

**Note:** All fuel products use unit "104" (Litre) because excise is charged per litre

### 🛠️ How to Get Excise Duty Codes

**Step 1: Fetch Available Excise Codes**
```python
import requests

headers = {
    "X-API-Key": "your_api_key",
    "X-API-Secret": "your_api_secret"
}

response = requests.get(
    "https://efrisintegration.nafacademy.com/api/external/efris/excise-duty",
    headers=headers
)

excise_data = response.json()
print(excise_data)
```

**Step 2: Response Format**
```json
{
    "status": "success",
    "excise_codes": [
        {
            "exciseCode": "130101",
            "exciseName": "Beer",
            "unit": "104",
            "rate": "0.30"
        },
        {
            "exciseCode": "130201",
            "exciseName": "Petrol",
            "unit": "104",
            "rate": "1200"
        }
    ]
}
```

**Step 3: Match Product to Excise Code**
- Beer products → `"130101"`
- Petrol → `"130201"`
- Diesel → `"130202"`
- Soft drinks → `"130301"`
- Cigarettes → Use specific cigarette excise codes

### ❌ Common Mistakes and Fixes

#### Mistake 1: Missing excise_duty_code
```json
// ❌ WRONG - Will fail
{
    "item_name": "Beer",
    "have_excise_tax": "101"
    // Missing excise_duty_code!
}

// ✅ CORRECT
{
    "item_name": "Beer",
    "have_excise_tax": "101",
    "excise_duty_code": "130101"
}
```

#### Mistake 2: Using number instead of string
```json
// ❌ WRONG - Use strings
{
    "have_excise_tax": 101
}

// ✅ CORRECT
{
    "have_excise_tax": "101"
}
```

#### Mistake 3: Including excise_duty_code for non-excise items
```json
// ❌ WRONG - Confusing
{
    "item_name": "Cement",
    "have_excise_tax": "102",
    "excise_duty_code": ""
}

// ✅ CORRECT - Omit the field
{
    "item_name": "Cement",
    "have_excise_tax": "102"
}
```

#### Mistake 4: Wrong unit of measure for excise items
```json
// ❌ WRONG - Diesel excise requires unit 104 (Litre)
{
    "item_name": "Diesel",
    "unit_of_measure": "102",
    "have_excise_tax": "101",
    "excise_duty_code": "LED130100"
}
// EFRIS will reject: Unit mismatch!

// ✅ CORRECT - Check excise code's unit first
{
    "item_name": "Diesel",
    "unit_of_measure": "104",      ← Match excise unit
    "have_excise_tax": "101",
    "excise_duty_code": "LED130100"
}
```

**Rule:** Always fetch the excise code first, check its unit, then use that same unit for your product.

### 📝 Quick Checklist Before Sending

- [ ] All 4 required fields present: `item_code`, `item_name`, `unit_price`, `commodity_code`
- [ ] If excisable: `have_excise_tax="101"` AND `excise_duty_code` provided
- [ ] **If excisable: `unit_of_measure` MATCHES the excise code's unit from T125** ← CRITICAL!
- [ ] If not excisable: `have_excise_tax="102"` OR omit field
- [ ] All code values are **strings** (in quotes: "101" not 101)
- [ ] Unit price is a **number** (no quotes: 5000 not "5000")
- [ ] Fetched excise codes from `/api/external/efris/excise-duty` before registering

**For Excise Items - Double Check:**
1. Fetch excise duty data: `GET /api/external/efris/excise-duty`
2. Find your excise code (e.g., LED130100 for diesel)
3. Note the `unit` field value (e.g., "104" for Litre)
4. Use that EXACT unit in `unit_of_measure` when registering product
5. EFRIS will reject if units don't match!

---

## Stock Management

### Stock Increase (T131)

**Endpoint:** `POST /api/external/efris/stock-increase`

Use this when receiving new stock (purchases, transfers in, opening stock).

**Request:**
```json
{
    "stock_movement_date": "2024-01-24",
    "items": [
        {
            "item_code": "PROD-001",
            "quantity": 100,
            "unit_price": 5000,
            "remarks": "Purchase from supplier"
        }
    ],
    "remarks": "Monthly stock purchase"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Stock upload successful"
}
```

### Stock Decrease (T131)

**Endpoint:** `POST /api/external/efris/stock-decrease`

Use this for stock reductions NOT from sales (wastage, theft, transfers out).

**Request:**
```json
{
    "stock_movement_date": "2024-01-24",
    "items": [
        {
            "item_code": "PROD-001",
            "quantity": 10,
            "unit_price": 5000,
            "remarks": "Damaged goods"
        }
    ],
    "remarks": "Monthly wastage writeoff"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Stock decrease recorded"
}
```

**Complete Example (Python):**
```python
# Stock Increase
stock_data = {
    "stock_movement_date": "2024-01-24",
    "items": [
        {
            "item_code": "CEMENT-001",
            "quantity": 500,
            "unit_price": 32000,
            "remarks": "Purchase from supplier ABC"
        },
        {
            "item_code": "PAINT-002",
            "quantity": 200,
            "unit_price": 15000,
            "remarks": "Purchase from supplier XYZ"
        }
    ],
    "remarks": "Weekly stock delivery"
}

response = requests.post(
    f"{BASE_URL}/api/external/efris/stock-increase",
    headers=headers,
    json=stock_data
)
print(response.json())
```

---

## Invoice Fiscalization

### Endpoint: POST /api/external/efris/submit-invoice

Fiscalize invoices with EFRIS to get FDN (Fiscal Document Number) and verification code.

### Tax-Inclusive Pricing

**Custom ERP uses simple tax-inclusive pricing** - all amounts already include tax.

The system automatically calculates:
- Net Amount (before tax)
- Tax Amount
- Gross Amount (total)

### Seller Information - Auto-Populated

**You do NOT send seller/company information with each invoice.**

The system automatically uses your company details from the API key:
- Company TIN
- Company Name

**What gets auto-filled:**
```json
{
    "sellerDetails": {
        "tin": "YOUR_TIN",           ← From API key
        "legalName": "YOUR_COMPANY", ← From API key
        "businessName": "YOUR_COMPANY"
    }
}
```

Your developers should **NOT** include fields like:
- ❌ `company_tin`
- ❌ `company_name`
- ❌ `company_address`
- ❌ `company_phone`
- ❌ `company_email`

The API key identifies your company - that's all you need!

### Request Format

```json
{
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-24",
    "customer_name": "ABC Company Ltd",
    "customer_tin": "1234567890",
    "items": [
        {
            "item_name": "Cement 50kg Bag",
            "item_code": "CEMENT-001",
            "quantity": 10,
            "unit_price": 35000,
            "tax_rate": 18,
            "discount": 0
        },
        {
            "item_name": "Paint 5L",
            "item_code": "PAINT-002",
            "quantity": 5,
            "unit_price": 20000,
            "tax_rate": 18,
            "discount": 0
        }
    ],
    "remarks": "Delivery to construction site"
}
```

### Field Reference

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `invoice_number` | Yes | Your invoice number | `"INV-2024-001"` |
| `invoice_date` | Yes | Date in YYYY-MM-DD format | `"2024-01-24"` |
| `customer_name` | Yes | Customer business/legal name | `"ABC Company Ltd"` |
| `customer_tin` | No | Customer TIN (recommended) | `"1234567890"` |
| `customer_phone` | No | Customer phone | `"+256700000000"` |
| `customer_email` | No | Customer email | `"abc@example.com"` |
| `items` | Yes | Array of invoice items | See below |
| `remarks` | No | Invoice notes | `"Thank you"` |

### Item Fields

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `item_name` | Yes | Product name | `"Cement 50kg Bag"` |
| `item_code` | Yes | Product code (must be registered) | `"CEMENT-001"` |
| `quantity` | Yes | Quantity sold | `10` |
| `unit_price` | Yes | Price per unit (tax inclusive) | `35000` |
| `tax_rate` | Yes | Tax % (18 for 18% VAT) | `18` |
| `discount` | No | Discount amount (default: 0) | `5000` |

### Tax Calculation Example

**Item:** 10 units @ UGX 35,000 each = UGX 350,000 (tax inclusive)
- Tax Rate: 18%
- **System calculates:**
  - Net Amount = 350,000 / 1.18 = UGX 296,610
  - Tax Amount = 350,000 - 296,610 = UGX 53,390
  - Gross Amount = UGX 350,000

You just send the tax-inclusive price, the system does the math!

### Response

**Success (200):**
```json
{
    "success": true,
    "fdn": "1014409555027202401240001",
    "verification_code": "ABC123XYZ",
    "qr_code": "base64_encoded_qr_code_image",
    "efris_invoice_id": "12345",
    "invoice_number": "INV-2024-001",
    "fiscalized_at": "2024-01-24T10:30:00",
    "message": "Invoice fiscalized successfully"
}
```

**Error (400):**
```json
{
    "detail": {
        "success": false,
        "error_code": "2122",
        "message": "Item not registered",
        "details": "EFRIS rejected the invoice"
    }
}
```

### Complete Example

**Python:**
```python
import requests
from datetime import date

BASE_URL = "https://efrisintegration.nafacademy.com"
headers = {
    "X-API-Key": "your_api_key",
    "X-API-Secret": "your_api_secret",
    "Content-Type": "application/json"
}

invoice_data = {
    "invoice_number": "INV-2024-001",
    "invoice_date": date.today().strftime("%Y-%m-%d"),
    "customer_name": "ABC Company Ltd",
    "customer_tin": "1234567890",
    "customer_phone": "+256700123456",
    "customer_email": "abc@example.com",
    "items": [
        {
            "item_name": "Cement 50kg Bag",
            "item_code": "CEMENT-001",
            "quantity": 10,
            "unit_price": 35000,  # Tax inclusive
            "tax_rate": 18
        },
        {
            "item_name": "Paint 5L White",
            "item_code": "PAINT-002",
            "quantity": 5,
            "unit_price": 20000,  # Tax inclusive
            "tax_rate": 18
        }
    ],
    "remarks": "Delivery to site A"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/external/efris/submit-invoice",
        headers=headers,
        json=invoice_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Invoice fiscalized successfully!")
        print(f"FDN: {result['fdn']}")
        print(f"Verification Code: {result['verification_code']}")
        
        # Save FDN to your database
        # Print FDN on invoice/receipt
    else:
        print(f"Error: {response.json()}")
        
except Exception as e:
    print(f"Request failed: {e}")
```

**Node.js:**
```javascript
const axios = require('axios');

const BASE_URL = 'https://efrisintegration.nafacademy.com';
const headers = {
    'X-API-Key': 'your_api_key',
    'X-API-Secret': 'your_api_secret',
    'Content-Type': 'application/json'
};

const invoiceData = {
    invoice_number: 'INV-2024-001',
    invoice_date: new Date().toISOString().split('T')[0],
    customer_name: 'ABC Company Ltd',
    customer_tin: '1234567890',
    items: [
        {
            item_name: 'Cement 50kg Bag',
            item_code: 'CEMENT-001',
            quantity: 10,
            unit_price: 35000,  // Tax inclusive
            tax_rate: 18
        },
        {
            item_name: 'Paint 5L White',
            item_code: 'PAINT-002',
            quantity: 5,
            unit_price: 20000,  // Tax inclusive
            tax_rate: 18
        }
    ],
    remarks: 'Delivery to site A'
};

try {
    const response = await axios.post(
        `${BASE_URL}/api/external/efris/submit-invoice`,
        invoiceData,
        { headers }
    );
    
    console.log('Invoice fiscalized successfully!');
    console.log('FDN:', response.data.fdn);
    console.log('Verification Code:', response.data.verification_code);
    
    // Save FDN to database
    // Print on invoice/receipt
    
} catch (error) {
    console.error('Error:', error.response.data);
}
```

### Invoice with Discount

```json
{
    "invoice_number": "INV-2024-002",
    "invoice_date": "2024-01-24",
    "customer_name": "XYZ Trading Ltd",
    "customer_tin": "9876543210",
    "items": [
        {
            "item_name": "Cement 50kg Bag",
            "item_code": "CEMENT-001",
            "quantity": 100,
            "unit_price": 35000,
            "tax_rate": 18,
            "discount": 50000
        }
    ],
    "remarks": "Bulk purchase discount applied"
}
```

**Calculation:**
- Subtotal: 100 × 35,000 = 3,500,000
- Discount: -50,000
- Total (tax inclusive): 3,450,000
- Net (before tax): 3,450,000 / 1.18 = 2,923,729
- Tax: 526,271

---

## Credit Notes

### Endpoint: POST /api/external/efris/submit-credit-note

Issue credit notes for returned goods or invoice corrections.

### Request Format

```json
{
    "credit_note_number": "CN-2024-001",
    "credit_note_date": "2024-01-25",
    "original_invoice_number": "INV-2024-001",
    "original_invoice_fdn": "1014409555027202401240001",
    "customer_name": "ABC Company Ltd",
    "customer_tin": "1234567890",
    "reason": "Damaged goods returned",
    "items": [
        {
            "item_name": "Cement 50kg Bag",
            "item_code": "CEMENT-001",
            "quantity": 2,
            "unit_price": 35000,
            "tax_rate": 18
        }
    ]
}
```

### Field Reference

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `credit_note_number` | Yes | Your credit note number | `"CN-2024-001"` |
| `credit_note_date` | Yes | Date in YYYY-MM-DD | `"2024-01-25"` |
| `original_invoice_number` | Yes | Original invoice number | `"INV-2024-001"` |
| `original_invoice_fdn` | Yes | Original invoice FDN | `"1014409555..."` |
| `customer_name` | Yes | Customer name | `"ABC Company Ltd"` |
| `customer_tin` | No | Customer TIN | `"1234567890"` |
| `reason` | Yes | Reason for credit note | `"Goods returned"` |
| `items` | Yes | Items being credited | Same as invoice |

### Response

```json
{
    "success": true,
    "fdn": "1014409555027202401250002",
    "verification_code": "XYZ789ABC",
    "credit_note_number": "CN-2024-001"
}
```

---

## Query Endpoints

### Get Units of Measure (CRITICAL)

**Endpoint:** `GET /api/external/efris/units-of-measure`

**This is the most important reference endpoint** - it maps your ERP units to EFRIS codes.

**Common Mistake:** Sending wrong unit codes causes EFRIS to misinterpret product types. For example:
- ❌ Code "102" = **Piece** (not litres!)
- ✅ Use "102" for computers, phones, furniture
- ✅ Use "104" for liquids (water, fuel, beverages)

**Request:**
```python
response = requests.get(
    f"{BASE_URL}/api/external/efris/units-of-measure",
    headers=headers
)
units = response.json()
```

**Response:**
```json
{
    "success": true,
    "units": [
        {
            "code": "101",
            "name": "Carton"
        },
        {
            "code": "102",
            "name": "Piece"
        },
        {
            "code": "103",
            "name": "Kilogram"
        },
        {
            "code": "104",
            "name": "Litre"
        }
    ],
    "total": 20,
    "last_updated": "2024-01-24T10:30:00"
}
```

**Important Notes:**
- The API returns **pure EFRIS data** (code and name only)
- Use the reference table below to understand what each code means
- **Code 102 = Piece** (for individual items like computers, phones, furniture)
- **Code 104 = Litre** (for liquids like water, fuel, beverages)
- **Code 103 = Kilogram** (for products sold by weight)

**Quick Reference:**

| Code | Unit Name | Description | Common Use Cases |
|------|-----------|-------------|------------------|
| 101 | Carton | Products sold in boxes/cartons | Boxed items, packaged goods |
| 102 | Piece | Individual items | Computers, phones, furniture, electronics |
| 103 | Kilogram | Products sold by weight | Cement, sugar, rice, flour |
| 104 | Litre | Liquid products | Water, fuel, beverages, oil |
| 105 | Meter | Length measurements | Fabric, rope, cable, pipes |
| 106 | Tonne | Heavy products by weight | Bulk materials, heavy machinery |
| 107 | Gram | Small quantities by weight | Spices, herbs, precious metals |
| 110 | Square Meter | Area measurements | Tiles, flooring, land, fabric |
| 112 | Pack | Packaged products | Multi-packs, bundles |
| 113 | Dozen | Sets of 12 | Eggs, bottles (by the dozen) |
| 115 | Pair | Products sold in pairs | Shoes, gloves, socks |

**Complete Example:**
```python
# Get units from EFRIS
response = requests.get(
    f"{BASE_URL}/api/external/efris/units-of-measure",
    headers=headers
)

units_data = response.json()

# Create a mapping for your ERP
# The API returns clean EFRIS data (code and name only)
# Add your own mappings based on your ERP's unit terminology
unit_mapping = {}
for unit in units_data.get('units', []):
    code = unit['code']
    name = unit['name'].lower()
    unit_mapping[name] = code
    
    # Add common aliases based on unit name
    if 'piece' in name:
        unit_mapping['pcs'] = code      # 102 - Pieces
        unit_mapping['each'] = code     # 102 - Each
        unit_mapping['item'] = code     # 102 - Item
    elif 'kilogram' in name:
        unit_mapping['kg'] = code       # 103 - Kilogram
        unit_mapping['kgs'] = code      # 103 - Kilograms
    elif 'litre' in name or 'liter' in name:
        unit_mapping['liter'] = code    # 104 - Litre
        unit_mapping['l'] = code        # 104 - L
        unit_mapping['litres'] = code   # 104 - Litres
    elif 'carton' in name:
        unit_mapping['box'] = code      # 101 - Box/Carton
        unit_mapping['ctn'] = code      # 101 - Carton
    elif 'meter' in name and 'square' not in name:
        unit_mapping['m'] = code        # 105 - Meter
        unit_mapping['metres'] = code   # 105 - Metres

# Example: Registering a computer (sold as individual pieces)
erp_unit = 'pcs'  # Your ERP uses 'pcs' for pieces
efris_unit_code = unit_mapping.get(erp_unit, '102')  # Maps to 102 (Piece)

product_data = {
    "item_code": "LAPTOP-001",
    "item_name": "Dell Laptop",
    "unit_price": 2500000,
    "commodity_code": "1010101",
    "commodity_name": "Computers",
    "unit_of_measure": efris_unit_code,  # 102 = Piece (from EFRIS)
    "have_excise_tax": "102"
}

# Example: Registering fuel (sold in litres)
erp_unit = 'l'  # Your ERP uses 'l' for litres
efris_unit_code = unit_mapping.get(erp_unit, '104')  # Maps to 104 (Litre)

fuel_data = {
    "item_code": "FUEL-PETROL",
    "item_name": "Petrol",
    "unit_price": 5500,
    "commodity_code": "1010201",
    "commodity_name": "Petroleum Products",
    "unit_of_measure": efris_unit_code,  # 104 = Litre (from EFRIS)
    "have_excise_tax": "101",
    "excise_duty_code": "130201"  # Excise for petrol
}
```

### Get Excise Duty Codes

**Endpoint:** `GET /api/external/efris/excise-duty`

Get all available excise duty codes from EFRIS.

**Python:**
```python
response = requests.get(
    f"{BASE_URL}/api/external/efris/excise-duty",
    headers=headers
)
excise_codes = response.json()
```

**Response:**
```json
{
    "exciseDutyCode": [
        {
            "exciseCode": "130101",
            "exciseName": "Beer"
        },
        {
            "exciseCode": "130201",
            "exciseName": "Petrol"
        }
    ]
}
```

### Get Single Invoice

**Endpoint:** `GET /api/external/efris/invoice/{invoice_number}`

**Python:**
```python
response = requests.get(
    f"{BASE_URL}/api/external/efris/invoice/INV-2024-001",
    headers=headers
)
invoice = response.json()
```

### Get All Invoices

**Endpoint:** `GET /api/external/efris/invoices`

**Python:**
```python
response = requests.get(
    f"{BASE_URL}/api/external/efris/invoices",
    headers=headers
)
invoices = response.json()
```

**Response:**
```json
{
    "invoices": [
        {
            "invoice_no": "INV-2024-001",
            "invoice_date": "2024-01-24",
            "customer_name": "ABC Company Ltd",
            "total_amount": 350000,
            "fdn": "1014409555027202401240001",
            "status": "success"
        }
    ]
}
```

---

## Troubleshooting

### Common Errors

#### Error: Wrong Unit of Measure / Product Validation Failed

**Problem:** Product registered with incorrect unit code (e.g., computers registered as "litres")

**Solution:**
```python
# Step 1: Fetch units from EFRIS
response = requests.get(f"{BASE_URL}/api/external/efris/units-of-measure", headers=headers)
units = response.json()['units']

# Step 2: See available units
print("Available EFRIS Units:")
for unit in units:
    print(f"  {unit['code']} = {unit['name']}")

# Step 3: Use the correct code
# For computers: code 102 (Piece)
# For liquids: code 104 (Litre)
# For weight: code 103 (Kilogram)
```

**Common Mistakes:**
- ❌ Using code "102" thinking it means "litres" → It means **Piece**
- ❌ Hardcoding unit codes without verifying → Codes may differ
- ✅ Always fetch units from EFRIS using the endpoint
- ✅ Create a mapping between your ERP terms and EFRIS codes

**Example Fix:**
```python
# Wrong: Hardcoded assumption
unit_code = "102"  # Thought this was litres!

# Correct: Fetch and map from EFRIS
units_response = requests.get(f"{BASE_URL}/api/external/efris/units-of-measure", headers=headers)
units = {u['name'].lower(): u['code'] for u in units_response.json()['units']}

# Now map correctly
unit_code = units.get('piece')  # Returns "102"
litre_code = units.get('litre')  # Returns "104"
```

#### Error 2122: "Item not registered"

**Problem:** Item code in invoice doesn't exist in EFRIS.

**Solution:**
```python
# First register the product
product_data = {
    "item_code": "PROD-001",
    "item_name": "Product A",
    "unit_price": 5000,
    "commodity_code": "1010101",
    "commodity_name": "General Goods"
}
requests.post(f"{BASE_URL}/api/external/efris/register-product", headers=headers, json=product_data)

# Then submit invoice
invoice_data = {...}
requests.post(f"{BASE_URL}/api/external/efris/submit-invoice", headers=headers, json=invoice_data)
```

#### Error 645: "Product already exists"

**Problem:** You're trying to register a product that already exists in EFRIS.

**Solution:** This is actually OK - just proceed with using the product in invoices. No need to register again.

#### Error 646: "pieceMeasureUnit validation failed"

**Problem:** Excise duty flag or unit measure settings conflict.

**Solution:** Use the working format:
```json
{
    "item_code": "PROD-001",
    "item_name": "Product",
    "unit_price": 5000,
    "commodity_code": "1010101",
    "commodity_name": "General Goods",
    "unit_of_measure": "102",
    "have_excise_tax": "102"
}
```

#### 401 Unauthorized

**Problem:** API key/secret is invalid or missing.

**Solution:**
1. Check headers include both `X-API-Key` and `X-API-Secret`
2. Verify credentials are correct (no extra spaces)
3. Generate new API keys from dashboard if needed

#### 500 Internal Server Error

**Problem:** Server error, usually invalid data format.

**Solution:**
1. Check JSON is valid
2. Verify dates are in "YYYY-MM-DD" format
3. Ensure all required fields are present
4. Check numeric fields are numbers, not strings

### Testing Tips

1. **Test Mode**: Make sure your company is set to EFRIS test mode during development
2. **Start Simple**: Register one product, submit one invoice first
3. **Check Logs**: Login to dashboard to see detailed error logs
4. **Validate Data**: Double-check commodity codes, tax rates before submission
5. **Keep FDNs**: Always save the FDN returned - you need it for credit notes

### Best Practices

1. **Register Products First**: Always register products before submitting invoices
2. **Use Item Codes Consistently**: Use the same item_code in registration, stock, and invoices
3. **Store FDNs**: Save FDN and verification code in your database
4. **Handle Errors Gracefully**: Show user-friendly error messages
5. **Test with Test Mode**: Use EFRIS test environment before going live

### Support

Contact the integration administrator or check the dashboard logs for detailed error information.

---

## Complete Workflow Example

Here's a complete workflow from product registration to invoice fiscalization:

```python
import requests
from datetime import date

BASE_URL = "https://efrisintegration.nafacademy.com"
headers = {
    "X-API-Key": "your_api_key",
    "X-API-Secret": "your_api_secret",
    "Content-Type": "application/json"
}

# Step 0: Get Units of Measure (CRITICAL FIRST STEP)
print("0. Fetching EFRIS units of measure...")
response = requests.get(f"{BASE_URL}/api/external/efris/units-of-measure", headers=headers)
units_data = response.json()

# Create mapping for your ERP
unit_mapping = {}
for unit in units_data.get('units', []):
    code = unit['code']
    name = unit['name'].lower()
    unit_mapping[name] = code
    # Add common aliases
    if 'piece' in name:
        unit_mapping['pcs'] = code
        unit_mapping['each'] = code
    elif 'kilogram' in name:
        unit_mapping['kg'] = code
    elif 'litre' in name:
        unit_mapping['liter'] = code
        unit_mapping['l'] = code

print(f"   Loaded {len(unit_mapping)} unit mappings")

# Step 1: Register Product
print("\n1. Registering product...")
erp_unit = 'pcs'  # Your ERP uses 'pcs' for pieces
efris_unit = unit_mapping.get(erp_unit, '102')  # Get EFRIS code or default to Piece

product = {
    "item_code": "CEMENT-001",
    "item_name": "Cement 50kg Bag",
    "unit_price": 35000,
    "commodity_code": "1010524",
    "commodity_name": "Portland cement",
    "unit_of_measure": efris_unit,  # Correct EFRIS code
    "stock_quantity": 100
}
response = requests.post(f"{BASE_URL}/api/external/efris/register-product", headers=headers, json=product)
print(f"   Result: {response.json()}")

# Step 2: Add Opening Stock
print("\n2. Adding opening stock...")
stock = {
    "stock_movement_date": date.today().strftime("%Y-%m-%d"),
    "items": [
        {
            "item_code": "CEMENT-001",
            "quantity": 100,
            "unit_price": 32000,
            "remarks": "Opening stock"
        }
    ]
}
response = requests.post(f"{BASE_URL}/api/external/efris/stock-increase", headers=headers, json=stock)
print(f"   Result: {response.json()}")

# Step 3: Create Invoice
print("\n3. Fiscalizing invoice...")
invoice = {
    "invoice_number": "INV-2024-001",
    "invoice_date": date.today().strftime("%Y-%m-%d"),
    "customer_name": "ABC Company Ltd",
    "customer_tin": "1234567890",
    "items": [
        {
            "item_name": "Cement 50kg Bag",
            "item_code": "CEMENT-001",
            "quantity": 10,
            "unit_price": 35000,
            "tax_rate": 18
        }
    ]
}
response = requests.post(f"{BASE_URL}/api/external/efris/submit-invoice", headers=headers, json=invoice)
result = response.json()
print(f"   FDN: {result.get('fdn')}")
print(f"   Verification Code: {result.get('verification_code')}")

print("\n✅ Workflow complete!")
```

---

**That's it! You now have everything you need to integrate your Custom ERP with EFRIS.**

**Remember:**
- Tax-inclusive pricing is simple - just send the total amount
- Register products before using them in invoices
- Save FDNs for credit notes later
- Test in test mode first, then switch to production

**Questions?** Check the dashboard logs or contact support.
