# Purchase Order to EFRIS Integration

## Overview
This feature allows users to select purchase orders from QuickBooks and send them to EFRIS as stock increases (T131 transactions).

## Implementation Details

### Backend Changes

#### 1. New API Endpoints (`api_multitenant.py`)

##### Import Purchase Orders
```
POST /api/companies/{company_id}/qb-purchase-orders/import
```
- Fetches purchase orders from QuickBooks
- Saves them to the database
- Supports date filtering with `start_date` and `end_date` query parameters
- Updates existing records or creates new ones

##### Get Saved Purchase Orders
```
GET /api/companies/{company_id}/qb-purchase-orders
```
- Retrieves all saved purchase orders for a company
- Returns formatted data including:
  - Database ID
  - QuickBooks PO ID
  - Document number
  - Vendor name
  - Transaction date
  - Total amount
  - Full QuickBooks data (qb_data)

##### Send Selected Purchase Orders to EFRIS
```
POST /api/companies/{company_id}/qb-purchase-orders/sync-to-efris
```
- Accepts: `{ "po_ids": [1, 2, 3] }` - array of database IDs
- Converts each PO to EFRIS T131 stock increase format
- Sends to EFRIS as stock increases
- Returns success/failure counts and detailed error information

#### 2. QuickBooks Client Enhancement (`quickbooks_client.py`)

Added `get_vendor_by_id()` method to fetch vendor details needed for EFRIS submission.

### Frontend Changes

#### 1. Purchase Order Display (`dashboard_multitenant.html`)

**New Features:**
- ✅ Checkbox selection for individual purchase orders
- ✅ "Select All" checkbox in table header
- ✅ "Send Selected to EFRIS" button
- ✅ Enhanced PO viewing with line item details
- ✅ Responsive display handling both database and QuickBooks data formats

#### 2. New JavaScript Functions

**`toggleSelectAllPOs(checkbox)`**
- Toggles all purchase order checkboxes

**`sendSelectedPOsToEFRIS()`**
- Collects selected PO IDs
- Sends them to EFRIS via API
- Shows success/error notifications
- Unchecks all checkboxes after successful submission

**`viewPurchaseOrder(po)`**
- Displays PO details in a modal/toast
- Shows vendor, date, total amount
- Lists all line items with quantities and prices

**Enhanced `displayQBPurchaseOrders(pos)`**
- Adds checkbox column
- Shows "Send Selected to EFRIS" button
- Handles both database and direct QuickBooks data formats

## Usage Flow

### 1. Import Purchase Orders
1. Navigate to "QuickBooks Purchase Orders" tab
2. Click "📥 Import from QuickBooks"
3. System fetches POs from QuickBooks and saves to database

### 2. Select and Send to EFRIS
1. Review the list of purchase orders
2. Check the boxes next to POs you want to send to EFRIS
3. Click "✅ Send Selected to EFRIS"
4. System converts each PO to T131 format and sends to EFRIS

### 3. View Results
- Success message shows how many POs were sent
- Failed POs are logged in the console with error details
- Checkboxes are cleared after successful submission

## EFRIS Integration Details

### T131 Stock Increase Format

Each purchase order is converted to:

```json
{
  "goodsStockIn": {
    "operationType": "101",
    "supplierTin": "",
    "supplierName": "Vendor Name",
    "remarks": "PO #12345",
    "stockInDate": "2026-01-19",
    "stockInType": "102"
  },
  "goodsStockInItem": [
    {
      "goodsCode": "PRODUCT_CODE",
      "quantity": "100",
      "unitPrice": "5000",
      "remarks": ""
    }
  ]
}
```

### Field Mappings

| QuickBooks Field | EFRIS Field | Notes |
|------------------|-------------|-------|
| VendorRef.name | supplierName | Vendor details fetched via API |
| DocNumber | remarks | PO # included in remarks |
| TxnDate | stockInDate | Transaction date |
| Line[].ItemRef.name | goodsCode | Product code from item |
| Line[].Qty | quantity | Item quantity |
| Line[].UnitPrice | unitPrice | Item unit price |

## Database Schema

The `purchase_orders` table stores:
- `company_id` - Links to company
- `qb_po_id` - QuickBooks purchase order ID
- `qb_doc_number` - PO document number
- `qb_vendor_name` - Vendor name
- `qb_txn_date` - Transaction date
- `qb_total_amt` - Total amount
- `qb_data` - Full QuickBooks JSON data
- `created_at`, `updated_at` - Timestamps

## Error Handling

The system handles various error scenarios:

1. **No POs Selected**: Warning message shown
2. **QuickBooks API Errors**: Caught and displayed to user
3. **EFRIS Submission Errors**: 
   - Individual PO failures are logged
   - Success/failure counts displayed
   - Detailed error messages in console
4. **Missing Product Codes**: Falls back to item name

## Benefits

✅ **Selective Submission**: Send only specific POs to EFRIS
✅ **Bulk Processing**: Select multiple POs at once
✅ **Audit Trail**: All POs saved in database
✅ **Error Recovery**: Failed POs can be resubmitted
✅ **Data Integrity**: Product codes looked up from database
✅ **User-Friendly**: Simple checkbox interface

## Next Steps

Potential enhancements:
- Add EFRIS submission status tracking in database
- Show which POs have already been sent to EFRIS
- Add filters (by date, vendor, amount)
- Export PO list to CSV
- Bulk edit capabilities before submission
