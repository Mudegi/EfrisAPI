# 📝 Invoice Submission Example: 10% Discount + 18% Tax

## Scenario

You created an invoice in QuickBooks for:
- **Customer**: ABC Company
- **Item**: Office Supplies
- **Quantity**: 50 units
- **Unit Price**: 2,000 UGX
- **Discount**: 10%
- **Tax**: 18% VAT

---

## 📊 QuickBooks Calculation

```
Line Item: Office Supplies
Quantity: 50 units
Unit Price: 2,000 UGX
─────────────────────────
Subtotal: 100,000 UGX

Discount (10%): -10,000 UGX
─────────────────────────
After Discount: 90,000 UGX

VAT (18%): 16,200 UGX
─────────────────────────
TOTAL: 106,200 UGX
```

---

## 📤 What Gets Sent to URA/EFRIS

### Complete Invoice Payload

```json
{
  "sellerDetails": {
    "tin": "1014409555",
    "legalName": "My Company Ltd",
    "businessName": "My Company Ltd",
    "address": "Plot 100, Kampala",
    "mobilePhone": "0700123456",
    "emailAddress": "info@mycompany.com",
    "placeOfBusiness": "Uganda",
    "referenceNo": "INV-001"
  },
  
  "buyerDetails": {
    "buyerTin": "1017196396",
    "buyerLegalName": "ABC Company",
    "buyerBusinessName": "ABC Company",
    "buyerAddress": "123 Main Street, Kampala",
    "buyerMobilePhone": "0700987654",
    "buyerEmail": "abc@company.com",
    "buyerType": "0"
  },
  
  "basicInformation": {
    "operator": "admin",
    "invoiceNo": "",
    "deviceNo": "1014409555_01",
    "issuedDate": "2026-01-18 12:00:00",
    "currency": "UGX",
    "invoiceType": "1",
    "invoiceKind": "1",
    "dataSource": "106",
    "invoiceIndustryCode": "101",
    "isBatch": "0"
  },
  
  "goodsDetails": [
    {
      "item": "Office Supplies",
      "itemCode": "SUPPLY001",
      "qty": "50",
      "unitOfMeasure": "101",
      "unitPrice": "2000",
      
      "total": "106200",
      
      "discountFlag": "1",
      "discountTotal": "10000",
      "discountTaxRate": "0.18",
      
      "taxRate": "0.18",
      "tax": "16200",
      
      "orderNumber": "0",
      "deemedFlag": "2",
      "exciseFlag": "2",
      "categoryId": "",
      "categoryName": "",
      "goodsCategoryId": "50202306",
      "goodsCategoryName": "Office supplies",
      "exciseRate": "",
      "exciseRule": "2",
      "exciseUnit": "",
      "exciseCurrency": "",
      "exciseTax": "",
      "pack": "1",
      "stick": "1",
      "exciseRateName": ""
    }
  ],
  
  "taxDetails": [
    {
      "taxCategoryCode": "01",
      "netAmount": "90000",
      "taxRate": "0.18",
      "taxAmount": "16200",
      "grossAmount": "106200",
      "tax": "16200",
      "currencyType": "UGX"
    }
  ],
  
  "summary": {
    "netAmount": "90000",
    "taxAmount": "16200",
    "grossAmount": "106200",
    "itemCount": "1",
    "modeCode": "0",
    "remarks": "",
    "qrCode": ""
  },
  
  "payWay": [
    {
      "paymentMode": "101",
      "paymentAmount": 106200,
      "orderNumber": "a"
    }
  ],
  
  "extend": {
    "reason": "",
    "reasonCode": ""
  }
}
```

---

## 🔍 Key Fields Explained

### Discount Information
```json
"discountFlag": "1"           // Indicates this item HAS a discount
"discountTotal": "10000"      // Discount amount: 10,000 UGX (10%)
"discountTaxRate": "0.18"     // Tax rate applied: 18%
```

### Tax Information
```json
"taxRate": "0.18"             // 18% VAT
"tax": "16200"                // VAT amount on discounted price
"total": "106200"             // Final amount (including VAT)
```

### Amounts Breakdown
```json
"netAmount": "90000"          // Amount before VAT (after discount)
"taxAmount": "16200"          // VAT amount
"grossAmount": "106200"       // Total amount (net + VAT)
```

---

## 📐 Calculation Steps

### Step 1: Original Amount
```
50 units × 2,000 UGX = 100,000 UGX
```

### Step 2: Apply Discount
```
Discount = 100,000 × 10% = 10,000 UGX
Amount after discount = 100,000 - 10,000 = 90,000 UGX
```

### Step 3: Calculate VAT
```
VAT = 90,000 × 18% = 16,200 UGX
```

### Step 4: Final Total
```
Total = 90,000 + 16,200 = 106,200 UGX
```

---

## ✅ URA Validation

URA's EFRIS system checks:

1. ✅ `discountFlag = "1"` → `discountTotal` must have a value
2. ✅ `discountTotal = "10000"` → Valid positive number
3. ✅ `tax = "16200"` → Matches 18% of net amount (90,000)
4. ✅ `total = "106200"` → Equals netAmount + tax
5. ✅ All amounts properly formatted as strings

**Result**: Invoice accepted by URA ✅

---

## 🎯 Multiple Items Example

If your invoice has multiple items with different discounts:

```json
"goodsDetails": [
  {
    "item": "Office Supplies",
    "qty": "50",
    "unitPrice": "2000",
    "discountFlag": "1",
    "discountTotal": "10000",    // 10% discount
    "tax": "16200",
    "total": "106200"
  },
  {
    "item": "Printer Paper",
    "qty": "20",
    "unitPrice": "1000",
    "discountFlag": "1",
    "discountTotal": "4000",     // 20% discount
    "tax": "2880",
    "total": "18880"
  },
  {
    "item": "Pens",
    "qty": "100",
    "unitPrice": "500",
    "discountFlag": "2",         // No discount
    "discountTotal": "",
    "tax": "9000",
    "total": "59000"
  }
]
```

**Invoice Totals:**
- Net Amount: 90,000 + 16,000 + 50,000 = 156,000 UGX
- VAT: 16,200 + 2,880 + 9,000 = 28,080 UGX
- **Gross Total: 184,080 UGX**

---

## 🚀 How to Submit

### Using API

```bash
POST http://localhost:8001/api/invoices/submit
```

**Parameters:**
```
invoice_id: YOUR_QUICKBOOKS_INVOICE_ID
```

**Response:**
```json
{
  "success": true,
  "invoiceNo": "2600118000123456",
  "fiscalDocumentNumber": "FDN123456789",
  "message": "Invoice submitted successfully"
}
```

---

## 📞 API Server

Start the server:
```bash
cd d:\EfrisAPI
py api_app.py
```

Server runs at: **http://localhost:8001**

View documentation: **http://localhost:8001/docs**

---

## 🔗 Related Documentation

- [DISCOUNT_AND_TAX_HANDLING.md](DISCOUNT_AND_TAX_HANDLING.md) - Complete technical guide
- [DISCOUNT_TAX_QUICK_REF.md](DISCOUNT_TAX_QUICK_REF.md) - Quick reference
- [QUICKBOOKS_INTEGRATION.md](QUICKBOOKS_INTEGRATION.md) - QuickBooks setup

---

## ✨ Summary

When you submit an invoice with:
- ✅ **10% discount** → Automatically detected and formatted
- ✅ **18% tax** → Correctly calculated on discounted amount
- ✅ **Multiple items** → Each handled independently
- ✅ **EFRIS compliance** → All validations pass

**Just create your invoice in QuickBooks, the system handles the rest!**

---

*Example generated: January 18, 2026*
