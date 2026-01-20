# Discount and Tax Handling - QuickBooks to EFRIS Integration

## Overview

This document explains how discounts and taxes are handled when sending invoices from QuickBooks to URA through EFRIS.

## QuickBooks Invoice Structure

When you create an invoice in QuickBooks with:
- **10% discount**
- **18% VAT (Standard Tax)**

QuickBooks calculates the final amount as:
```
Original Price: 10,000 UGX
Discount (10%): -1,000 UGX
Subtotal: 9,000 UGX
VAT (18%): 1,620 UGX
Total: 10,620 UGX
```

## EFRIS Format Requirements

EFRIS requires each line item to include:

### 1. **Discount Fields**
- `discountFlag`: 
  - `"1"` = Item has discount
  - `"2"` = No discount
- `discountTotal`: The discount amount (positive number, e.g., "1000.00")
- `discountTaxRate`: Tax rate applied to the discount (usually "0.18" for 18% VAT)

### 2. **Tax Fields**
- `taxRate`: "0.18" (18% VAT)
- `tax`: Actual VAT amount calculated on the discounted price
- `total`: Final line amount including VAT but after discount

## Implementation Details

### How Discounts Are Detected

The mapper checks for discounts in three ways:

1. **Explicit Discount Rate**: `DiscountRate` field in QuickBooks
   ```python
   discount_amount = (unit_price * quantity * discount_percent) / 100
   ```

2. **Explicit Discount Amount**: `DiscountAmt` field
   ```python
   discount_amount = detail.get('DiscountAmt', 0)
   ```

3. **Implicit Discount**: When line amount differs from qty × price
   ```python
   expected_amount = unit_price * quantity
   discount_amount = expected_amount - actual_amount
   ```

### Tax Calculation

Tax is calculated on the **discounted amount**:

```python
# Amount from QuickBooks already includes VAT
tax_rate = 0.18
net_amount = amount / (1 + tax_rate)  # Amount before VAT
vat_amount = amount - net_amount      # VAT on discounted price
```

### Example Mapping

**QuickBooks Line Item:**
```json
{
  "Qty": 1,
  "UnitPrice": 10000,
  "Amount": 10620,
  "DiscountRate": 10
}
```

**EFRIS goodsDetails:**
```json
{
  "item": "Product Name",
  "qty": "1",
  "unitPrice": "10000",
  "total": "10620",
  "discountFlag": "1",
  "discountTotal": "1000.00",
  "discountTaxRate": "0.18",
  "taxRate": "0.18",
  "tax": "1620.00"
}
```

## URA Validation

URA's EFRIS system validates:

1. ✅ **Discount consistency**: If `discountFlag = "1"`, `discountTotal` must be present
2. ✅ **Tax calculation**: VAT must be correctly calculated on post-discount amount
3. ✅ **Total accuracy**: `total` must match (price - discount) × (1 + tax rate)

## Code Location

The discount and tax handling is implemented in:
- **File**: [quickbooks_efris_mapper.py](quickbooks_efris_mapper.py)
- **Function**: `map_invoice_to_efris()`
- **Lines**: ~140-250

## Testing

To test discount handling:

1. Create an invoice in QuickBooks with a 10% discount
2. Submit the invoice through the API
3. Check the EFRIS response

Example API call:
```python
POST http://localhost:8001/api/invoices/submit?invoice_id=123
```

## Common Scenarios

### Scenario 1: Line-Level Discount (10%)
- QuickBooks applies 10% discount to specific items
- Mapper detects discount and sets `discountFlag = "1"`
- Tax calculated on discounted amount

### Scenario 2: Invoice-Level Discount
- QuickBooks applies discount to entire invoice
- Each line item gets proportional discount
- Each line sent to EFRIS with appropriate discount values

### Scenario 3: No Discount
- `discountFlag = "2"`
- `discountTotal = ""` (empty string)
- `discountTaxRate = ""` (empty string)
- Tax calculated on full amount

## Important Notes

1. **Discount Amount Format**: Always use positive numbers for `discountTotal`
2. **Empty vs Zero**: Use empty string `""` when no discount, not `"0"`
3. **Tax Rate**: Standard VAT is `"0.18"` (18%)
4. **Rounding**: All amounts rounded to 2 decimal places

## Excise Duty and Discounts

If a product has both excise duty and discount:
1. Excise duty calculated on original price
2. Discount applied after excise
3. VAT calculated on (price + excise - discount)

## Troubleshooting

### Error: "discountTotal must not be empty when discountFlag is 1"
**Solution**: Ensure discount amount is being calculated correctly

### Error: "Tax calculation mismatch"
**Solution**: Verify tax is calculated on discounted amount, not original

### Error: "Invalid discountFlag value"
**Solution**: Must be "1" (has discount) or "2" (no discount)

## Summary

✅ **Discounts**: Properly extracted and formatted for EFRIS  
✅ **Tax (18% VAT)**: Calculated on discounted amounts  
✅ **Validation**: Passes EFRIS requirements  
✅ **QuickBooks Integration**: Automatic detection and mapping  

---

*For questions or issues, refer to [QUICKBOOKS_INTEGRATION.md](QUICKBOOKS_INTEGRATION.md)*
