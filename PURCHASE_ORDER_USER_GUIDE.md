# Purchase Order to EFRIS - User Guide

## Quick Start Guide

### Step 1: Navigate to Purchase Orders
1. Log in to the EFRIS Dashboard
2. Select your company from the dropdown
3. Click on "QuickBooks Purchase Orders" in the left sidebar

### Step 2: Import Purchase Orders
1. Click the **"📥 Import from QuickBooks"** button
2. Wait for the import to complete
3. You'll see a success message showing how many POs were imported

### Step 3: Select Purchase Orders
1. Review the list of purchase orders
2. **Check the boxes** next to the POs you want to send to EFRIS
   - You can select one or multiple POs
   - Use the checkbox in the header to select all POs at once

### Step 4: Send to EFRIS
1. Click the **"✅ Send Selected to EFRIS"** button
2. The system will:
   - Convert each PO to EFRIS T131 format
   - Send them as stock increase transactions
   - Show success/failure notification

### Step 5: Review Results
- Success message shows count of POs sent
- If any failed, check the browser console for details
- Failed POs can be reselected and resubmitted

## Features

### Individual Selection
✅ Select specific purchase orders to send to EFRIS
✅ No need to send all POs at once
✅ Skip POs that have already been processed

### Bulk Operations
✅ Select multiple POs with checkboxes
✅ "Select All" option for quick selection
✅ Send all selected POs in one batch

### Smart Data Mapping
✅ Vendor information automatically looked up
✅ Product codes mapped from database
✅ Line items properly formatted for EFRIS

### Error Handling
✅ Clear error messages for failed POs
✅ Can retry failed POs individually
✅ Successful POs are processed even if some fail

## Understanding the Purchase Order Table

| Column | Description |
|--------|-------------|
| ☐ | Checkbox to select PO for sending to EFRIS |
| PO # | Purchase order document number from QuickBooks |
| Vendor | Supplier/vendor name |
| Date | Transaction date |
| Amount | Total PO amount in UGX |
| Actions | **👁️ View** - See PO details and line items |

## Tips

💡 **Before Sending to EFRIS:**
- Ensure all products in the PO are registered in EFRIS
- Verify product codes match between QuickBooks and EFRIS
- Check that vendor information is correct

💡 **Selecting Multiple POs:**
- Use Shift+Click to select a range (in most browsers)
- Use the header checkbox to select/deselect all at once
- Selected count is shown at the top

💡 **If a PO Fails:**
- Check the browser console (F12) for detailed error
- Common issues:
  - Product not registered in EFRIS
  - Product code mismatch
  - Invalid quantity or price values
- Fix the issue and try again

## What Happens in EFRIS?

When you send a purchase order to EFRIS:

1. **Creates a Stock Increase (T131)**
   - Transaction type: Purchase (102)
   - Supplier: From QuickBooks vendor
   - Date: PO transaction date

2. **Records Line Items**
   - Product code from QuickBooks description
   - Quantity from PO line
   - Unit price from PO line

3. **Updates Stock Levels**
   - EFRIS increases stock for each product
   - Stock is tracked per product code

## Troubleshooting

### ❌ "Please select at least one purchase order"
**Solution:** Check at least one checkbox before clicking "Send to EFRIS"

### ❌ "Failed to fetch purchase orders"
**Solution:** Make sure QuickBooks is connected and purchase orders are imported

### ❌ "Product not found in EFRIS"
**Solution:** Register the product in EFRIS first (Products tab)

### ❌ "Invalid product code"
**Solution:** 
1. Go to QuickBooks Items tab
2. Edit the item's EFRIS metadata
3. Set the correct product code
4. Re-import the purchase order

## Best Practices

1. **Import Regularly**: Import POs from QuickBooks weekly/monthly
2. **Review Before Sending**: Check PO details before sending to EFRIS
3. **Batch Processing**: Select multiple related POs and send together
4. **Track Failures**: Keep note of failed POs and resolve issues
5. **Keep Codes Synchronized**: Ensure product codes match between systems

## Support

For issues or questions:
- Check the browser console (F12) for detailed errors
- Review the PURCHASE_ORDER_EFRIS_INTEGRATION.md file
- Contact your system administrator
