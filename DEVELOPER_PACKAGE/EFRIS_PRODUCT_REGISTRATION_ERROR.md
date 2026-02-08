# EFRIS Product Registration Error - Base64 Padding Issue

**Date:** February 8, 2026  
**Error:** HTTP 500 - "Invalid padding bytes"  
**Endpoint:** `POST /api/external/efris/register-product`  
**System:** YourBookSuit → EFRIS External API

---

## Error Summary

When YourBookSuit attempts to register a product with EFRIS, the EFRIS API backend returns:

```
HTTP 500: Internal Server Error
{
  "detail": "Internal error: Invalid padding bytes."
}
```

This is a **base64 decoding error** occurring on the EFRIS API backend server, not in YourBookSuit.

---

## Request Details from YourBookSuit

### HTTP Request
- **Method:** `POST`
- **URL:** `https://efrisintegration.nafacademy.com/api/external/efris/register-product`
- **Headers:**
  ```http
  Content-Type: application/json
  X-API-Key: <efrisApiKey_from_eInvoiceConfig_credentials>
  ```

### Request Body (JSON)
```json
{
  "item_code": "Product description or name (unique identifier)",
  "item_name": "Product name",
  "unit_price": 0,
  "commodity_code": "Product SKU (EFRIS commodity code)",
  "unit_of_measure": "102",
  "have_excise_tax": "101",  // or "102" for no excise
  "excise_duty_code": "LED270200",  // present only if have_excise_tax = "101"
  "stock_quantity": 10,  // optional
  "description": "Product description"  // optional
}
```

### Field Mapping
- `item_code` = Product Description (or Name as fallback) - **must be unique**
- `item_name` = Product Name
- `commodity_code` = Product SKU (EFRIS commodity category)
- `unit_of_measure` = Unit code (default "102" for Pieces)
- `have_excise_tax` = "101" (Yes) or "102" (No)
- `excise_duty_code` = EFRIS excise duty code (e.g., LED270200, LED190400)

---

## Error Analysis

### Error Type: Base64 Decoding Error
The error message "Invalid padding bytes" indicates a **base64.b64decode()** operation is failing somewhere in the EFRIS API backend.

### Most Likely Causes

1. **API Key Validation Issue**
   - The `X-API-Key` header is being decoded as base64 but it's not base64-encoded
   - Or vice versa: expecting plain text but receiving base64

2. **Credential Decryption**
   - If EFRIS API decrypts stored credentials before forwarding to URA
   - The encrypted data might have incorrect padding

3. **Data Encoding Mismatch**
   - EFRIS API expects certain fields to be base64-encoded
   - YourBookSuit is sending plain text (or vice versa)

---

## What to Check on EFRIS API Backend

### 1. API Key Processing
Look for where you process the `X-API-Key` header:

```python
# Somewhere in your code:
api_key = request.headers.get('X-API-Key')

# CHECK: Are you doing this?
decoded_key = base64.b64decode(api_key)  # <-- This might be failing

# Or validating against stored keys?
company = Company.objects.get(api_key=api_key)
```

**Question:** Is the API key supposed to be:
- Plain text (e.g., `abc123def456`)?
- Base64-encoded (e.g., `YWJjMTIzZGVmNDU2`)?

### 2. Search for Base64 Operations
Search your EFRIS API codebase for:

```python
base64.b64decode(...)
base64.decodebytes(...)
```

One of these is throwing "Invalid padding bytes".

### 3. Check T130 (Goods Upload) Implementation
In your product registration endpoint:

```python
# /api/external/efris/register-product

def register_product(request):
    # ... your code ...
    
    # CHECK: Are you encoding/decoding anything here?
    # - Product data
    # - Credentials for URA API
    # - Signatures or tokens
```

### 4. URA EFRIS Integration
If you're forwarding to URA's EFRIS system:

```python
# CHECK: How are you preparing credentials for URA?
ura_request = {
    "data": {
        # ... product data ...
    },
    # Are you encoding credentials here?
    "privateKey": base64.b64decode(company.private_key),  # <-- Check this
}
```

---

## Debugging Steps

### Step 1: Enable Detailed Logging
In your EFRIS API backend, add logging to the `/register-product` endpoint:

```python
import logging
logger = logging.getLogger(__name__)

def register_product(request):
    logger.info(f"Received X-API-Key: {request.headers.get('X-API-Key')[:20]}...")
    logger.info(f"Request body: {request.body}")
    
    try:
        # ... your code ...
    except Exception as e:
        logger.error(f"Error at line: {e.__traceback__.tb_lineno}")
        logger.error(f"Error message: {str(e)}")
        raise
```

### Step 2: Find the Exact Line
The error stack trace should show which line is failing. Look for:
- Line number in your code
- The specific `base64.b64decode()` call that's failing

### Step 3: Check API Key Format
Log the API key being received and check:
- Does it have whitespace or newlines?
- Is it missing padding characters (`=`)?
- Does it match what's stored in your database?

```python
api_key = request.headers.get('X-API-Key')
logger.info(f"API Key length: {len(api_key)}")
logger.info(f"Has whitespace: {bool(re.search(r'\s', api_key))}")
logger.info(f"First 20 chars: {api_key[:20]}")
logger.info(f"Last 20 chars: {api_key[-20:]}")
```

### Step 4: Test Base64 Decode
Try decoding the API key manually:

```python
import base64

api_key = request.headers.get('X-API-Key')

# Test if it's base64
try:
    decoded = base64.b64decode(api_key)
    logger.info(f"API key decoded successfully: {decoded[:20]}")
except Exception as e:
    logger.error(f"API key is NOT valid base64: {e}")
    # Maybe it's supposed to be plain text?
```

---

## Expected Behavior

### Successful Registration Flow

1. **YourBookSuit sends:**
   ```http
   POST /api/external/efris/register-product
   X-API-Key: <company_api_key>
   Content-Type: application/json
   
   {product_data}
   ```

2. **EFRIS API should:**
   - Validate the API key
   - Lookup the company
   - Prepare T130 request for URA
   - Forward to URA EFRIS system
   - Return success response

3. **Expected Response:**
   ```json
   {
     "success": true,
     "product_code": "PRD123456",
     "efris_status": "Registered",
     "message": "Product registered successfully"
   }
   ```

---

## Similar Working Endpoints

These endpoints are working correctly with the same API key:

✅ **GET /api/external/efris/excise-duty**
- Uses same `X-API-Key` header
- Returns 200 OK
- Successfully returns 87 excise duty codes

This proves:
1. API key authentication is working for GET requests
2. The API key format is correct
3. The issue is specific to the `/register-product` endpoint

**Question:** Does `/register-product` do additional base64 operations that `/excise-duty` doesn't?

---

## Quick Fix Checklist

- [ ] Check EFRIS API backend logs for the exact error line
- [ ] Verify if API key is being decoded as base64 (should it be?)
- [ ] Check if any product data fields are being decoded as base64
- [ ] Verify URA credential preparation (private keys, signatures)
- [ ] Check for whitespace in base64 strings
- [ ] Ensure base64 strings have correct padding (`=`)
- [ ] Compare `/register-product` implementation with `/excise-duty` (working)

---

## Additional Context

### YourBookSuit Setup
- **Framework:** Next.js 14.2.35 + TypeScript
- **Database:** PostgreSQL with Prisma ORM
- **Configuration:** `eInvoiceConfig` table stores:
  - `apiEndpoint`: `https://efrisintegration.nafacademy.com/api/external/efris`
  - `credentials.efrisApiKey`: The API key being sent in `X-API-Key` header

### Other EFRIS Endpoints Working
- ✅ GET `/excise-duty` - Returns 87 codes successfully
- ❌ POST `/register-product` - Fails with base64 error

---

## Contact

If you need more information:
- Full request logs from YourBookSuit
- Sample product data being sent
- API key format verification
- Additional debugging output

Let me know what specific information would help debug this issue.
