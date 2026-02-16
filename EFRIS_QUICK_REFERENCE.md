# EFRIS Integration Quick Reference Card

## API Endpoint
```
POST https://efrisintegration.nafacademy.com/api/external/efris/submit-invoice
Header: X-API-Key: your-api-key
```

---

## ⚠️ CRITICAL RULES

### 1. Tax Rate Format (Most Common Error!)
```javascript
// VAT (taxCategoryCode: "01")
taxRate: "0.18"  // ✅ CORRECT - String, exactly "0.18"
taxRate: 0.18    // ❌ WRONG - Number
taxRate: "0.1800" // ❌ WRONG - Too many decimals

// Excise (taxCategoryCode: "05") - Fixed Rate
taxRate: "0"     // ✅ CORRECT - String "0"
taxRate: "0.05"  // ❌ WRONG - Unless it's percentage-based
```

### 2. Discount Fields
```javascript
// No discount
discountFlag: "2"
// DO NOT send discountTotal or discountTaxRate!

// With discount
discountFlag: "1"
discountTotal: "5000"
```

### 3. All Values as Strings
```javascript
qty: "10"          // ✅ String
unitPrice: "2500"  // ✅ String
total: "25000"     // ✅ String
orderNumber: "1"   // ✅ String
```

---

## Buyer Type Codes
| Code | Type | TIN Required |
|------|------|--------------|
| "0" | Business (B2B) | Yes |
| "1" | Individual (B2C) | No |
| "2" | Government (B2G) | Yes |

---

## Payment Method Codes
| Code | Method |
|------|--------|
| "101" | Cash |
| "102" | Credit |
| "103" | Mobile Money |
| "104" | Card/POS |
| "105" | Bank Transfer |

---

## Unit of Measure Codes
| Code | Unit |
|------|------|
| "101" | Piece |
| "102" | Litre |
| "103" | Millilitre |
| "105" | Gram |
| "106" | Kilogram |

---

## Tax Category Codes
| Code | Category | taxRate |
|------|----------|---------|
| "01" | Standard VAT | "0.18" |
| "02" | Zero-rated | "0" |
| "03" | Exempt | "-" |
| "05" | Excise Duty | "0" (fixed) |

---

## Minimal Invoice Payload
```json
{
  "invoice_number": "INV-001",
  "invoice_date": "2026-02-16",
  "currency": "UGX",
  "buyer_type": "1",
  "customer_name": "John Doe",
  "payment_method": "101",
  "items": [{
    "item": "Product Name",
    "itemCode": "PROD001",
    "qty": "1",
    "unitOfMeasure": "101",
    "unitPrice": "11800.00",
    "total": "11800.00",
    "taxRate": "0.18",
    "tax": "1800.00",
    "orderNumber": "1",
    "discountFlag": "2",
    "deemedFlag": "2",
    "exciseFlag": "2",
    "goodsCategoryId": "44102906",
    "vatApplicableFlag": "1"
  }],
  "tax_details": [{
    "taxCategoryCode": "01",
    "netAmount": "10000.00",
    "taxRate": "0.18",
    "taxAmount": "1800.00",
    "grossAmount": "11800.00"
  }],
  "total_amount": 10000,
  "total_tax": 1800
}
```

---

## Excise Invoice - Additional Fields
```javascript
// In items array:
{
  "exciseFlag": "1",
  "categoryId": "LED110000",
  "categoryName": "Excise Duty",
  "exciseRate": "50",
  "exciseRule": "2",        // "1"=Percentage, "2"=Fixed
  "exciseTax": "500.00",
  "exciseUnit": "102",      // Must match unitOfMeasure
  "exciseCurrency": "UGX",
  "exciseRateName": "UGX50 per litre",
  "pack": "1",
  "stick": "1"
}

// In tax_details array - ADD excise entry:
{
  "taxCategoryCode": "05",
  "netAmount": "10000.00",
  "taxRate": "0",           // "0" for fixed rate!
  "taxAmount": "500.00",
  "grossAmount": "10500.00",
  "taxRateName": "UGX50 per litre"
}
```

---

## Excise Tax Formula
```
Fixed Rate (exciseRule = "2"):
  exciseTax = exciseRate × quantity
  
Percentage (exciseRule = "1"):
  exciseTax = netAmount × (exciseRate / 100)

VAT on Excise Products:
  vatBase = netAmount + exciseTax
  vatAmount = vatBase × 0.18
```

---

## Common Errors

| Error | Fix |
|-------|-----|
| 2833: taxRate must be '0.18' | Use string "0.18" not number |
| 1205: discountTotal must be empty | Remove discountTotal when discountFlag="2" |
| 2124: itemCode mismatch | Register product first with T130 |
| 2268: paymentAmount cannot be 0 | Check total_amount calculation |

---

## Response Keys for Invoice Display
```javascript
response.fiscal_data.fdn              // Fiscal Document Number
response.fiscal_data.verification_code // Verification Code
response.fiscal_data.qr_code           // Base64 QR image
response.fiscal_data.device_number     // Device ID
response.fiscal_data.issued_date       // Date (DD/MM/YYYY)
response.fiscal_data.issued_time       // Time (HH:MM:SS)
response.summary.gross_amount_words    // Amount in words
```

---

## Contact
API Issues: Check server logs or contact integration team
