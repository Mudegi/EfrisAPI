# 🎨 Invoice Modal UI - Visual Quick Reference

## 📸 Modal Layout

```
╔══════════════════════════════════════════════════════════════════════════╗
║                          EDIT INVOICE MODAL                              ║
║                        (Width: 1200px)                                   ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  Invoice Details                                                         ║
║  ┌────────────────┬─────────────────┬────────────────┐                  ║
║  │ Invoice Number │ Customer        │ Date           │                  ║
║  │ (read-only)    │ (read-only)     │ (editable)     │                  ║
║  └────────────────┴─────────────────┴────────────────┘                  ║
║                                                                          ║
║  ┌────────────────┬─────────────────┐                                   ║
║  │ Buyer Type     │ Customer TIN    │                                   ║
║  │ (dropdown)     │ (text input)    │                                   ║
║  └────────────────┴─────────────────┘                                   ║
║                                                                          ║
║  LINE ITEMS DETAIL                                                       ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │ Item │ Qty │ Unit Price │ Discount │ Tax Rate │ Excise │ Total  │   ║
║  ├──────┼─────┼────────────┼──────────┼──────────┼────────┼────────┤   ║
║  │ Cement│ 10 │ UGX 35,000 │  [10%]   │  [18%]   │[LED050]│350,000 │   ║
║  │ 50kg │     │            │ -35,000  │  🟢     │ 5,000  │        │   ║
║  ├──────┼─────┼────────────┼──────────┼──────────┼────────┼────────┤   ║
║  │ Milk │ 20  │ UGX 2,500  │    -     │  [0%]    │   -    │ 50,000 │   ║
║  │Basic │     │            │          │  🔵     │        │        │   ║
║  ├──────┼─────┼────────────┼──────────┼──────────┼────────┼────────┤   ║
║  │Medical│ 5  │ UGX 10,000 │  [5%]    │ [EXEMPT] │   -    │ 50,000 │   ║
║  │ Kit  │     │            │ -2,500   │  🟠     │        │        │   ║
║  └──────┴─────┴────────────┴──────────┴──────────┴────────┴────────┘   ║
║                                                                          ║
║  INVOICE SUMMARY                                                         ║
║  ┌────────────────────────────────────────────────────────────────┐     ║
║  │ Subtotal:              UGX 450,000.00                          │     ║
║  │ Total Discount:       -UGX  37,500.00 🔴                       │     ║
║  │ Total Excise Duty:     UGX   5,000.00 🔴                       │     ║
║  │ Total VAT:             UGX  56,700.00 🟢                       │     ║
║  │ ───────────────────────────────────────                        │     ║
║  │ GRAND TOTAL:           UGX 474,200.00 💵                       │     ║
║  └────────────────────────────────────────────────────────────────┘     ║
║                                                                          ║
║  Totals (read-only)                                                     ║
║  ┌────────────────────────────────┐                                     ║
║  │ Subtotal: UGX 450,000.00       │                                     ║
║  └────────────────────────────────┘                                     ║
║  ┌────────────────────────────────┐                                     ║
║  │ Total Amount: UGX 450,000.00   │                                     ║
║  └────────────────────────────────┘                                     ║
║                                                                          ║
║  [💾 Save Changes]  [Cancel]                                            ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 🎨 Badge Color Guide

### Tax Rate Badges
```
┌─────────┬────────────────┬──────────────────────────┐
│ Badge   │ Color          │ Meaning                  │
├─────────┼────────────────┼──────────────────────────┤
│  [18%]  │ 🟢 Green       │ Standard VAT (18%)       │
│  [0%]   │ 🔵 Blue        │ Zero-rated (0%)          │
│[EXEMPT] │ 🟠 Orange      │ Tax Exempt               │
│[18%(*)] │ 🟣 Purple      │ Deemed VAT (18%)         │
└─────────┴────────────────┴──────────────────────────┘
* "(Deemed)" shown in badge
```

### Discount Badges
```
┌─────────┬────────────────┬──────────────────────────┐
│ Badge   │ Color          │ Meaning                  │
├─────────┼────────────────┼──────────────────────────┤
│  [10%]  │ 🔴 Red/Orange  │ 10% discount             │
│  [5%]   │ 🔴 Red/Orange  │ 5% discount              │
│ [FIXED] │ 🔴 Red/Orange  │ Fixed amount discount    │
│    -    │ ⚪ Gray        │ No discount              │
└─────────┴────────────────┴──────────────────────────┘
```

### Excise Badges
```
┌───────────┬────────────────┬──────────────────────────┐
│ Badge     │ Color          │ Meaning                  │
├───────────┼────────────────┼──────────────────────────┤
│[LED050000]│ 🔴 Pink        │ Cement excise            │
│[LED110000]│ 🔴 Pink        │ Mineral water excise     │
│[LED190100]│ 🔴 Pink        │ Fruit juice excise       │
│     -     │ ⚪ Gray        │ No excise                │
└───────────┴────────────────┴──────────────────────────┘
```

---

## 📐 Column Layout

### Line Items Table
```
Item          Qty    Unit Price    Discount      Tax Rate    Excise        Total
────────────  ─────  ────────────  ────────────  ──────────  ────────────  ──────────
Left-aligned  Center Right-aligned Center        Center      Center        Right-aligned
40% width     8%     15%           12%           12%         13%           10%
```

---

## 🎯 Interactive Elements

### Editable Fields
- ✏️ **Invoice Date**: Date picker
- ✏️ **Buyer Type**: Dropdown (Individual/Business/Foreign/Exempt)
- ✏️ **Customer TIN**: Text input

### Read-Only Fields
- 🔒 **Invoice Number**: Display only
- 🔒 **Customer**: Display only
- 🔒 **Line Items**: Display only (data from QuickBooks)
- 🔒 **Subtotal**: Calculated value
- 🔒 **Total Amount**: Calculated value

### Action Buttons
```
┌─────────────────┬──────────┐
│ 💾 Save Changes │ Success  │ → Saves edited buyer info
│ Cancel          │ Warning  │ → Closes modal without saving
└─────────────────┴──────────┘
```

---

## 📊 Data Display Examples

### Example 1: Standard Invoice with Discount
```
Line 1: Office Chair
  Qty: 5
  Price: UGX 150,000
  Discount: [10%] -UGX 75,000
  Tax: [18%] 🟢
  Excise: -
  Total: UGX 750,000
  
Summary:
  Subtotal:       UGX 750,000
  Total Discount: -UGX 75,000
  Total VAT:      UGX 121,500
  Grand Total:    UGX 796,500
```

### Example 2: Cement with Excise
```
Line 1: Cement 50kg
  Qty: 100 bags
  Price: UGX 35,000/bag
  Discount: [5%] -UGX 175,000
  Tax: [18%] 🟢
  Excise: [LED050000] UGX 50,000 (UGX 500/bag)
  Total: UGX 3,500,000
  
Summary:
  Subtotal:          UGX 3,500,000
  Total Discount:    -UGX 175,000
  Total Excise Duty:  UGX 50,000
  Total VAT:          UGX 598,500
  Grand Total:        UGX 3,973,500
```

### Example 3: Mixed Tax Rates
```
Line 1: Laptop (Standard VAT)
  Tax: [18%] 🟢
  
Line 2: Basic Food (Zero-rated)
  Tax: [0%] 🔵
  
Line 3: Medical Supplies (Exempt)
  Tax: [EXEMPT] 🟠
  
Line 4: Construction Project (Deemed VAT)
  Tax: [18% (Deemed)] 🟣
```

---

## 🔍 Information Hierarchy

### Primary (Large, Bold)
- Item names
- Grand Total
- Column headers

### Secondary (Medium)
- Quantities
- Prices
- Subtotals
- Tax badges

### Tertiary (Small, Gray)
- Discount amounts
- Excise amounts
- Help text

---

## 📱 Responsive Design

### Desktop (> 1200px)
- Full table width
- All columns visible
- Modal: 1200px wide

### Tablet (768px - 1200px)
- Modal: 90% width
- Slightly compressed columns

### Mobile (< 768px)
- Modal: 95% width
- Table scrollable horizontally
- Maintain all information

---

## 🎨 CSS Classes Used

```css
.modal                  → Modal overlay
.modal-content          → Modal container
.form-row               → Horizontal form layout
.form-group             → Individual form field
.form-input             → Input field styling
.btn                    → Button base
.btn-success            → Green success button
.btn-warning            → Orange cancel button
```

---

## 🚀 Quick Test Checklist

Before submitting to EFRIS, verify:
- [ ] All line items display correctly
- [ ] Tax rate badges show correct colors
- [ ] Discount amounts calculate properly
- [ ] Excise codes display for applicable items
- [ ] Summary totals match calculations
- [ ] Buyer Type is selected
- [ ] Customer TIN entered (if Business type)
- [ ] Invoice date is correct

---

## 💡 Tips for Users

1. **Review Tax Rates**: Check each line item has correct tax badge color
2. **Verify Discounts**: Confirm discount percentages match your intent
3. **Check Excise Items**: Ensure excise codes show for regulated goods
4. **Confirm Totals**: Summary section should match your expectations
5. **Buyer Information**: Always verify TIN for business customers

---

## 📞 Troubleshooting

### Badge Not Showing
- **Issue**: Tax/discount/excise badge shows "-"
- **Cause**: Missing data in QuickBooks
- **Fix**: Update product metadata or invoice in QuickBooks

### Wrong Tax Rate
- **Issue**: Badge shows wrong percentage
- **Cause**: Incorrect TaxCodeRef in QuickBooks
- **Fix**: Assign correct tax code in QuickBooks

### Missing Excise
- **Issue**: Excise not displayed for regulated item
- **Cause**: Product metadata missing `HasExcise` or `ExciseDutyCode`
- **Fix**: Edit product and check "Has Excise Tax", select code

### Summary Totals Don't Match
- **Issue**: Grand total doesn't equal subtotal + VAT + excise - discount
- **Cause**: Calculation error or missing line items
- **Fix**: Reload invoice from QuickBooks

---

**Status**: ✅ UI COMPLETE - Ready for User Testing
