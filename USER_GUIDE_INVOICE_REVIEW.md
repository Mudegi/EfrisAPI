# 📖 User Guide: Invoice Review Before EFRIS Submission

## 🎯 Purpose
This guide shows you how to review your invoice details (including tax rates, discounts, and excise duty) before submitting to EFRIS through the control panel.

---

## 🚀 Step-by-Step Guide

### Step 1: Create Invoice in QuickBooks
1. Open QuickBooks Desktop
2. Create a new invoice with:
   - Line items (products/services)
   - Apply discounts (if needed)
   - Select appropriate tax codes
   - Save the invoice

### Step 2: Load Invoice into Control Panel
1. Open the EFRIS Control Panel (`http://localhost:5000/dashboard.html`)
2. Navigate to **"Invoices"** tab
3. Click **"Load from QuickBooks"** button
4. Wait for invoices to load
5. Your invoice appears in the list

### Step 3: Review Invoice Details
1. Find your invoice in the list
2. Click the **"Edit"** button next to the invoice
3. **Invoice Edit Modal opens** showing:

---

## 📋 What You'll See in the Modal

### A. Basic Information (Top Section)
```
┌─────────────────────────────────────────┐
│ Invoice Number: 1001 (cannot edit)      │
│ Customer: ABC Company (cannot edit)     │
│ Date: 2025-01-28 (you can edit)        │
│ Buyer Type: Individual (dropdown)       │
│ Customer TIN: 1234567890 (text input)  │
└─────────────────────────────────────────┘
```

**What to check:**
- ✅ Invoice date is correct
- ✅ Buyer Type matches customer category
- ✅ Customer TIN entered (if Business type)

---

### B. Line Items Detail Table

```
┌──────────────┬────┬────────────┬──────────┬─────────┬────────┬──────────┐
│ Item         │Qty │ Unit Price │ Discount │Tax Rate │ Excise │  Total   │
├──────────────┼────┼────────────┼──────────┼─────────┼────────┼──────────┤
│ Cement 50kg  │ 10 │ UGX 35,000 │   10%    │  18%    │LED05000│ 350,000  │
│              │    │            │ -35,000  │  🟢    │  5,000 │          │
└──────────────┴────┴────────────┴──────────┴─────────┴────────┴──────────┘
```

#### Column Explanations:

**1. Item** 
- Product/service name from QuickBooks
- ❓ **Check**: Is the name correct?

**2. Qty**
- Quantity sold
- ❓ **Check**: Is the quantity right?

**3. Unit Price**
- Price per unit in UGX
- ❓ **Check**: Is the price correct?

**4. Discount**
- Shows discount badge and amount
- **Examples:**
  - `[10%] -UGX 35,000` = 10% percentage discount
  - `[FIXED] -UGX 5,000` = Fixed amount discount
  - `-` = No discount applied
- ❓ **Check**: Does the discount match what you intended?

**5. Tax Rate**
- Color-coded badge showing tax type
- **Badge Colors:**
  - 🟢 **[18%]** = Standard VAT (green)
  - 🔵 **[0%]** = Zero-rated items like basic food (blue)
  - 🟠 **[EXEMPT]** = Tax-exempt items like medicine (orange)
  - 🟣 **[18% (Deemed)]** = Deemed VAT for projects (purple)
- ❓ **Check**: Is the tax rate correct for this item?

**6. Excise**
- Shows excise duty code and amount (if applicable)
- **Examples:**
  - `[LED050000] UGX 5,000` = Cement excise
  - `[LED110000] UGX 500` = Mineral water excise
  - `-` = No excise duty
- ❓ **Check**: Excise items show correct code?

**7. Total**
- Line total in UGX
- Formula: (Qty × Price) - Discount = Total
- ❓ **Check**: Does the total look correct?

---

### C. Invoice Summary (Bottom Section)

```
╔═══════════════════════════════════════╗
║      INVOICE SUMMARY                  ║
╠═══════════════════════════════════════╣
║ Subtotal:           UGX 450,000.00    ║
║ Total Discount:    -UGX  37,500.00 🔴 ║
║ Total Excise Duty:  UGX   5,000.00 🔴 ║
║ Total VAT:          UGX  56,700.00 🟢 ║
║ ───────────────────────────────────── ║
║ GRAND TOTAL:        UGX 474,200.00 💵 ║
╚═══════════════════════════════════════╝
```

**What each means:**

- **Subtotal**: Sum of all line totals (before VAT)
- **Total Discount**: Sum of all discounts across all lines (shown in red)
- **Total Excise Duty**: Sum of excise on all applicable items (shown in pink)
- **Total VAT**: Sum of VAT calculated on all taxable items (shown in green)
- **Grand Total**: Final amount customer pays

❓ **Check**: Does the Grand Total match your expectations?

---

## ✅ Verification Checklist

Before clicking "Save Changes", verify:

### Customer Information
- [ ] Invoice date is correct
- [ ] Buyer Type selected correctly:
  - **Individual** → General customer (no TIN needed)
  - **Business** → Company with TIN (TIN required)
  - **Foreign** → International customer
  - **Tax Exempt** → Exempt organization
- [ ] Customer TIN entered (if Business type)

### Line Items
- [ ] All items listed correctly
- [ ] Quantities are accurate
- [ ] Unit prices match your records
- [ ] Discount badges show correct percentages
- [ ] Tax rate badges show correct colors:
  - 🟢 Green for 18% standard items
  - 🔵 Blue for 0% zero-rated items
  - 🟠 Orange for exempt items
  - 🟣 Purple for deemed VAT
- [ ] Excise codes display for regulated products

### Summary Totals
- [ ] Subtotal looks correct
- [ ] Total discount matches expected
- [ ] Total excise seems reasonable
- [ ] Total VAT calculated properly
- [ ] Grand total matches invoice

---

## 💾 Saving and Submitting

### To Save Changes
1. Review all details in the modal
2. Make any needed edits to:
   - Invoice date
   - Buyer type
   - Customer TIN
3. Click **"💾 Save Changes"** button
4. Modal closes
5. Changes saved to local storage

### To Submit to EFRIS
1. After saving, go back to invoice list
2. Check the checkbox next to your invoice
3. Click **"Submit to EFRIS"** button
4. System sends invoice to URA
5. Wait for confirmation
6. FDN (Fiscal Document Number) will appear

---

## 🎨 Understanding the Color Codes

### Tax Rate Colors
| Color  | Badge    | Meaning           | Examples                |
|--------|----------|-------------------|-------------------------|
| 🟢 Green | [18%]    | Standard VAT      | Computers, furniture    |
| 🔵 Blue  | [0%]     | Zero-rated        | Basic food, books       |
| 🟠 Orange| [EXEMPT] | Tax exempt        | Medical supplies        |
| 🟣 Purple| [18% (Deemed)] | Deemed VAT | Construction projects |

### Other Colors
| Color  | Used For      | Meaning                    |
|--------|---------------|----------------------------|
| 🔴 Red  | Discounts     | Money deducted from price  |
| 🔴 Pink | Excise        | Additional duty on item    |
| 🟢 Green| VAT Total     | Tax amount                 |
| 💵 Black| Grand Total   | Final amount               |

---

## 🔍 Common Scenarios

### Scenario 1: Simple Invoice (No Discount, Standard VAT)
```
Line Item:
  Office Chair × 5
  Price: UGX 150,000 each
  Discount: - (none)
  Tax: [18%] 🟢
  Total: UGX 750,000

Summary:
  Subtotal: UGX 750,000
  VAT: UGX 135,000
  Grand Total: UGX 885,000
```
✅ **Verify**: Total VAT = 750,000 × 18% = 135,000

---

### Scenario 2: Invoice with Discount
```
Line Item:
  Laptop × 2
  Price: UGX 2,000,000 each
  Discount: [10%] -UGX 400,000
  Tax: [18%] 🟢
  Total: UGX 4,000,000

Summary:
  Subtotal: UGX 4,000,000
  Total Discount: -UGX 400,000
  VAT: UGX 648,000
  Grand Total: UGX 4,248,000
```
✅ **Verify**: 
- Discount = 4,000,000 × 10% = 400,000 ✓
- VAT = (4,000,000 - 400,000) × 18% = 648,000 ✓

---

### Scenario 3: Invoice with Excise Duty (Cement)
```
Line Item:
  Cement 50kg × 100 bags
  Price: UGX 35,000 per bag
  Discount: [5%] -UGX 175,000
  Tax: [18%] 🟢
  Excise: [LED050000] UGX 50,000
  Total: UGX 3,500,000

Summary:
  Subtotal: UGX 3,500,000
  Total Discount: -UGX 175,000
  Total Excise: UGX 50,000
  VAT: UGX 598,500
  Grand Total: UGX 3,973,500
```
✅ **Verify**:
- Discount = 3,500,000 × 5% = 175,000 ✓
- Excise = 100 bags × UGX 500/bag = 50,000 ✓
- VAT = (3,500,000 - 175,000) × 18% = 598,500 ✓

---

### Scenario 4: Mixed Tax Rates
```
Line 1: Laptop (Standard VAT)
  Tax: [18%] 🟢

Line 2: Rice (Zero-rated)
  Tax: [0%] 🔵

Line 3: Medicine (Exempt)
  Tax: [EXEMPT] 🟠

Summary will show:
  - VAT only from Line 1 (laptop)
  - No VAT from Lines 2 & 3
```

---

## ⚠️ Troubleshooting

### Problem: Badge shows "-" instead of tax rate
**Cause**: Tax code not set in QuickBooks  
**Solution**: 
1. Go to QuickBooks
2. Edit the invoice
3. Select correct tax code for each line item
4. Save invoice
5. Reload in control panel

---

### Problem: Discount not showing
**Cause**: Discount not properly applied in QuickBooks  
**Solution**:
1. Open invoice in QuickBooks
2. Apply discount using proper field
3. Ensure discount percentage or amount is entered
4. Save invoice
5. Reload in control panel

---

### Problem: Wrong excise code
**Cause**: Product metadata not configured  
**Solution**:
1. Go to "Products" tab in control panel
2. Find the product
3. Click "Edit"
4. Check "Has Excise Tax"
5. Select correct excise duty code
6. Save product
7. Reload invoice

---

### Problem: Totals don't add up
**Cause**: Calculation error or missing data  
**Solution**:
1. Close modal
2. Click "Load from QuickBooks" again
3. Re-open invoice to review
4. If still wrong, check QuickBooks invoice for errors

---

## 📞 Support

If you see unexpected values:
1. Take a screenshot of the modal
2. Note which values look wrong
3. Check the corresponding invoice in QuickBooks
4. Contact support with:
   - Invoice number
   - Screenshot
   - Expected vs. actual values

---

## 🎯 Best Practices

### Before Creating Invoice in QuickBooks
- ✅ Ensure products have correct tax codes assigned
- ✅ Set up excise duty codes for regulated products
- ✅ Define discount policies clearly

### While Reviewing in Control Panel
- ✅ Check every tax rate badge color
- ✅ Verify discount percentages/amounts
- ✅ Confirm excise codes for applicable items
- ✅ Match Grand Total with your expectations
- ✅ Ensure Buyer Type and TIN are correct

### After Submission to EFRIS
- ✅ Wait for FDN confirmation
- ✅ Save FDN for records
- ✅ Print fiscalized invoice for customer

---

## ✨ Benefits of This Review Feature

1. **Transparency**: See exactly what URA receives
2. **Error Prevention**: Catch mistakes before submission
3. **Compliance**: Verify tax codes are correct
4. **Confidence**: Know your invoice is accurate
5. **Audit Trail**: Clear documentation of calculations

---

## 📚 Related Documentation
- [DISCOUNT_AND_TAX_HANDLING.md](DISCOUNT_AND_TAX_HANDLING.md) - Technical details
- [UI_ENHANCEMENT_COMPLETE.md](UI_ENHANCEMENT_COMPLETE.md) - Implementation summary
- [UI_VISUAL_REFERENCE.md](UI_VISUAL_REFERENCE.md) - Visual guide

---

**Last Updated**: January 2025  
**Version**: 1.0  
**Status**: ✅ Feature Active
