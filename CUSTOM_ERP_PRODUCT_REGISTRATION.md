# Custom ERP Product Registration Guide

## Fixed Issues (Feb 9, 2026)

### ✅ FINAL FIX - Aligned with QuickBooks Working Format
**User Insight:** "URA doesn't know QuickBooks or Custom ERP - as long as the data reaches EFRIS in the format they want, it should work."

**Critical Realization:** If QuickBooks endpoint works, Custom ERP should use the EXACT SAME T130 format!

**Solution Applied:** 
```python
# Custom ERP now MATCHES QuickBooks exactly
"havePieceUnit": "101",  # YES - same as QuickBooks
"pieceMeasureUnit": measure_unit,  # Same as QuickBooks
"pieceUnitPrice": str(unit_price),  # Same as QuickBooks
```

**Previous Attempts (Failed):**
- ❌ Error 645: Tried `havePieceUnit="102"` with `pieceMeasureUnit="102"`
- ❌ Error 646: Tried `havePieceUnit="102"` with `pieceUnitPrice=value`
- ✅ SUCCESS: Use `havePieceUnit="101"` like QuickBooks does

**Lesson Learned:** Don't overcomplicate - use what works! Both endpoints now send identical T130 structure to EFRIS.

### ✅ Excise Duty Code Handling
**Issue:** `exciseDutyCode` was being sent even when item doesn't have excise tax.

**Fix Applied:**
- `exciseDutyCode` is ONLY included when `have_excise_tax="101"` (YES)
- If `have_excise_tax="102"` (NO), field is not sent at all

---

## API Endpoint: `/api/external/efris/register-product`

### Request Format

```json
POST /api/external/efris/register-product
Headers:
  X-API-Key: your_api_key
  X-API-Secret: your_api_secret
  Content-Type: application/json

Body:
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

### Required Fields
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `item_code` | String | Unique product code | "PROD-001" |
| `item_name` | String | Product name | "HP Chromebook" |
| `unit_price` | Number | Unit price in UGX | 1000000 |
| `commodity_code` | String | EFRIS commodity category ID | "44102906" |

### Optional Fields
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `unit_of_measure` | String | "102" | 101=Box, 102=Pieces, 103=Kg, etc. |
| `have_excise_tax` | String | "102" | 101=Yes, 102=No |
| `excise_duty_code` | String | - | **REQUIRED if have_excise_tax="101"** |
| `stock_quantity` | Number | 0 | Stock pre-warning level |
| `description` | String | "" | Product description |
| `goods_type_code` | String | "101" | 101=Goods, 102=Fuel |

---

## EFRIS Validation Rules

### 1. Piece Unit Validation
```
EFRIS accepts: havePieceUnit='101' with values for pieceMeasureUnit and pieceUnitPrice
```

**Current Implementation (Aligned with QuickBooks):**
- `havePieceUnit="101"` (YES - use piece unit)
- `pieceMeasureUnit=measure_unit` (same as measureUnit)
- `pieceUnitPrice=unitPrice` (same as unitPrice)

**Why This Works:**
- QuickBooks endpoint has been working with this format
- EFRIS doesn't care about data source, only payload format
- Both endpoints now use identical T130 structure

### 2. Excise Duty Validation
```
Error 679: haveExciseTax is '101', excise duty has unit of measurement, 
           'pieceMeasureUnit' must be equals to excise duty measure unit!
```

**Rule:**
- If `have_excise_tax="101"` (YES):
  - `excise_duty_code` is **REQUIRED**
  - Get code from `/api/external/efris/excise-duty` endpoint
  - Must match product type (e.g., beer, cement, fuel)
- If `have_excise_tax="102"` (NO):
  - Do NOT send `excise_duty_code`

### 3. Measure Unit Codes
Common EFRIS unit codes:
- `101` = Box
- `102` = Pieces  
- `103` = Kilogram
- `104` = Litre
- `105` = Meter
- `106` = Carton
- `107` = Dozen
- `108` = Ton

Get full list: `/api/external/efris/measure-units`

---

## Example Requests

### 1. Regular Product (No Excise)
```json
{
  "item_code": "LAP-001",
  "item_name": "Dell Laptop",
  "unit_price": 2500000,
  "commodity_code": "44102906",
  "unit_of_measure": "102",
  "have_excise_tax": "102",
  "stock_quantity": 25,
  "description": "Dell Inspiron 15"
}
```

### 2. Excise Product (Beer)
```json
{
  "item_code": "BEER-500",
  "item_name": "Nile Special 500ml",
  "unit_price": 3500,
  "commodity_code": "21069010",
  "unit_of_measure": "104",
  "have_excise_tax": "101",
  "excise_duty_code": "102010401",
  "stock_quantity": 1000,
  "description": "Nile Special Beer 500ml bottle"
}
```

### 3. Service Item
```json
{
  "item_code": "SRV-CONSULT",
  "item_name": "IT Consulting",
  "unit_price": 50000,
  "commodity_code": "81111800",
  "unit_of_measure": "102",
  "have_excise_tax": "102",
  "stock_quantity": 0,
  "description": "Hourly IT consulting services",
  "goods_type_code": "101"
}
```

---

## Success Response
```json
{
  "success": true,
  "product_code": "PROD-001",
  "efris_status": "Registered",
  "message": "Product registered successfully"
}
```

## Error Response
```json
{
  "detail": "EFRIS error 645: havePieceUnit is '102', pieceMeasureUnit must be empty!"
}
```

---

## Getting Reference Data

### Commodity Codes
```bash
GET /api/external/efris/commodity-codes?search=computer
```

### Excise Duty Codes
```bash
GET /api/external/efris/excise-duty
```

### Measure Units
```bash
GET /api/external/efris/measure-units
```

---

## Deploy to Production

```bash
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com
git pull origin main
touch tmp/restart.txt
```

---

## Changelog

### 2026-02-09 (Final Fix - Aligned with QuickBooks)
- ✅ **CRITICAL INSIGHT:** User pointed out EFRIS doesn't care about data source
- ✅ Changed Custom ERP to use EXACT SAME T130 format as working QuickBooks endpoint
- ✅ Now uses `havePieceUnit="101"` with actual values (not empty)
- ✅ Both QuickBooks and Custom ERP send identical payload to EFRIS
- ✅ Lesson: Don't overcomplicate - use what already works!

### 2026-02-09 (Second Fix - Error 646)
- ❌ Attempted fix: Made `pieceUnitPrice` empty when `havePieceUnit="102"`
- ❌ Still didn't work - wrong approach

### 2026-02-09 (First Fix - Error 645)  
- ❌ Attempted fix: Made `pieceMeasureUnit` empty when `havePieceUnit="102"`
- ❌ Led to Error 646 - wrong approach

### 2026-02-08
- Created Custom ERP external API endpoint
- Initial product registration implementation
