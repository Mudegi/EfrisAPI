# 🚀 Quick Reference: Sending Invoices with Discounts and Tax to URA

## ✅ What's Been Implemented

Your EFRIS integration now **fully supports**:
- ✅ **ANY discount percentage** (5%, 10%, 15%, 20%, 50%, etc.)
- ✅ **ANY tax rate**: Standard (18%), Zero-rated (0%), Deemed VAT, Exempt
- ✅ **Automatic detection** of discounts and tax types
- ✅ **EFRIS-compliant formatting**

---

## 📋 How It Works

When you create an invoice in QuickBooks with:
- **Items with prices**
- **ANY discount applied** (5%, 10%, 20%, 50%, or fixed amount)
- **ANY tax rate** (Standard 18%, Zero-rated 0%, Exempt, Deemed VAT)

The system automatically:
1. Detects the discount amount and percentage
2. Detects the tax type and rate
3. Calculates tax on the discounted price
4. Formats everything for EFRIS
5. Submits to URA

---

## 🎯 Example
 (Example with 15% discount)
```
Item: Coffee Beans
Quantity: 10 kg
Price: 1,000 UGX/kg
Subtotal: 10,000 UGX
Discount (15%): -1,500 UGX
After Discount: 8,500 UGX
VAT (18%): 1,530 UGX
Total: 10,030 UGX
```

### Sent to URA/EFRIS
```json
{
  "item": "Coffee Beans",
  "qty": "10",
  "unitPrice": "1000.0",
  "discountFlag": "1",          ← Has discount
  "discountTotal": "1500.0",    ← 15% discount (ANY %)
  "discountTaxRate": "0.18",    ← Tax rate on discount
  "taxRate": "0.18",            ← 18% VAT (or ANY rate)
  "tax": "1530.0",              ← VAT amount
  "total": "10030.0",           ← Final total
  "taxCategoryCode": "01",      ← 01=Standard, 02=Zero-rated, 03=Exempt
  "isZeroRate": "102",          ← 101=Yes, 102=No
  "isExempt": "102"             ← 101=Yes, 102=No
  "total": "10620.0"            ← Final total
}
```

---

## 🔧 How to Use

### Option 1: Through API (Recommended)

Start the server:
```bash
cd d:\EfrisAPI
py api_app.py
```

Submit invoice:
```bash
POST http://localhost:8001/api/invoices/submit?invoice_id=YOUR_QB_INVOICE_ID
```

### Option 2: Direct Code

```python
from quickbooks_client import QuickBooksClient
from quickbooks_efris_mapper import QuickBooksEfrisMapper
from efris_client import EfrisManager

# 1. Get invoice from QuickBooks
qb = QuickBooksClient()
invoice = qb.get_invoice(invoice_id="123")
customer = qb.get_customer(customer_id=invoice['Customer']['value'])

# 2. Map to EFRIS format (handles discounts automatically)
efris_invoice = QuickBooksEfrisMapper.map_invoice_to_efris(
    invoice, customer, company_info
)

# 3. Submit to EFRIS
manager = EfrisManager(tin="1014409555", test_mode=True)
manager.perform_handshake()
result = manager.submit_invoice(efris_invoice)

print(f"Invoice submitted: {result['invoiceNo']}")
```

---

## 🧪 Test the Implementation

Run the test script:
```bash
cd d:\EfrisAPI
py test_discount_example.py
```

**Expected Output:**
```
✅ HAS DISCOUNT:
   - Discount Amount: 1000.0 UGX
   - Discount Percentage: 10.0%

📊 TAX INFORMATION:
   - Tax Rate: 0.18 (18% VAT)
   - VAT Amount: 1620.0 UGX

🎉 ALL VALIDATIONS PASSED - Ready to send to EFRIS!
```

---

## 📊 Discount Detection

The system detects discounts from QuickBooks in 3 ways:

1. **Explicit Discount Rate** (e.g., 10% off)
2. **Explicit Discount Amount** (e.g., 1000 UGX off)
3. **Implicit Discount** (calculated from price difference)

---

## ✨ Key Features

| Feature | Status |
|---------|--------|
| Any discount percentage (1-100%) | ✅ Supported |
| Fixed amount discounts | ✅ Supported |
| Multiple items with different discounts | ✅ Supported |
| Items without discounts | ✅ Supported |
| Standard VAT (18%) | ✅ Supported |
| Zero-rated (0%) | ✅ Supported |
| Exempt items | ✅ Supported |
| Deemed VAT | ✅ Supported |
| Excise duty + discount | ✅ Supported |
| Mixed tax rates in one invoice | ✅ Supported |

---

## 🔍 Validation

The system validates:
- ✅ Discount flag consistency
- ✅ Tax calculation accuracy
- ✅ EFRIS format compliance
- ✅ Total amount correctness

---

## 📄 Files Modified

1. **[quickbooks_efris_mapper.py](quickbooks_efris_mapper.py)** - Discount detection and mapping
2. **[DISCOUNT_AND_TAX_HANDLING.md](DISCOUNT_AND_TAX_HANDLING.md)** - Full documentation
3. **[test_discount_example.py](test_discount_example.py)** - Test script

---

## 🐛 Troubleshooting

### Issue: Discount not detected
**Check:** QuickBooks invoice has discount applied correctly

### Issue: Tax calculation incorrect
**Check:** Tax is 18% in QuickBooks

### Issue: EFRIS validation error
**Check:** Run `py test_discount_example.py` to verify format

---

## 📞 Quick Commands

```bash
# Start API server
py api_app.py

# Test discount handling
py test_discount_example.py

# Test full integration
py final_verification.py

# View API documentation
# Open: http://localhost:8001/docs
```

---

## 📚 Documentation

- **Full Details**: [DISCOUNT_AND_TAX_HANDLING.md](DISCOUNT_AND_TAX_HANDLING.md)
- **QuickBooks Integration**: [QUICKBOOKS_INTEGRATION.md](QUICKBOOKS_INTEGRATION.md)
- **Getting Started**: [QUICK_START.md](QUICK_START.md)

---

## ✅ Summary

✨ **Your invoices with 10% discount and 18% tax are now fully supported!**

Just create your invoices in QuickBooks as normal, and the system will:
1. Detect the discount automatically
2. Calculate the 18% VAT correctly
3. Format for EFRIS
4. Submit to URA

**No additional configuration needed!**

---

*Last Updated: January 18, 2026*
