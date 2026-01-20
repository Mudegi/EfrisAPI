# Purchase Order Status Tracking

## Overview
Added status tracking functionality to track which purchase orders have been successfully sent to EFRIS, which are pending, and which failed.

## Database Changes

### New Columns in `purchase_orders` Table

| Column | Type | Description |
|--------|------|-------------|
| `efris_status` | VARCHAR(50) | Status: 'pending', 'sent', or 'failed' |
| `efris_sent_at` | TIMESTAMP | Timestamp when sent to EFRIS |
| `efris_response` | JSON | Full EFRIS API response |
| `efris_error` | TEXT | Error message if failed |

### Migration
Run `migrate_add_po_status.py` to add these columns to existing databases.

## Status Flow

```
pending → sent (success)
        → failed (error)
```

## Backend Updates

### Status Tracking Logic
When sending POs to EFRIS:

1. **Success (returnCode = '00')**:
   - `efris_status` = 'sent'
   - `efris_sent_at` = current timestamp
   - `efris_response` = full API response
   - `efris_error` = NULL

2. **Failure (returnCode != '00')**:
   - `efris_status` = 'failed'
   - `efris_error` = error message
   - `efris_response` = full API response

3. **Exception**:
   - `efris_status` = 'failed'
   - `efris_error` = exception message

All status updates are committed to the database in a single transaction.

## Frontend Updates

### Visual Status Indicators

**Status Badges:**
- ⏳ Pending (yellow) - Not yet sent to EFRIS
- ✓ Sent (green) - Successfully sent to EFRIS
- ✗ Failed (red) - Failed to send, with error tooltip

**Status Counts:**
Display at the top shows:
- Total purchase orders
- Pending count
- Sent count
- Failed count (if any)

### User Experience

**Disabled Checkboxes:**
- Purchase orders with 'sent' status have disabled checkboxes
- Prevents accidental re-submission of already sent POs
- Faded appearance (opacity: 0.7) for sent POs

**Error Tooltips:**
- Hover over failed status badge to see error message
- Helps users understand why a PO failed

## API Response Format

### GET /api/companies/{company_id}/qb-purchase-orders

```json
[
  {
    "id": 1,
    "qb_po_id": "123",
    "doc_number": "PO-001",
    "vendor_name": "ABC Supplies",
    "txn_date": "2026-01-15",
    "total_amt": 50000,
    "qb_data": {...},
    "efris_status": "sent",
    "efris_sent_at": "2026-01-19T10:30:00Z",
    "efris_error": null,
    "created_at": "2026-01-15T08:00:00Z"
  }
]
```

## Usage Examples

### Checking Status
Users can quickly see which POs:
- Need to be sent (pending)
- Have been sent successfully (sent)
- Failed and need attention (failed)

### Retry Failed POs
1. Filter/identify failed POs by red ✗ badge
2. Check error message in tooltip
3. Fix the issue (e.g., register missing products)
4. Checkbox is enabled - select and retry

### Avoid Duplicates
- Already sent POs cannot be reselected
- Provides clear visual feedback
- Prevents duplicate stock increases in EFRIS

## Benefits

✅ **Audit Trail**: Complete history of which POs were sent and when
✅ **Error Tracking**: Detailed error messages for troubleshooting
✅ **Prevent Duplicates**: Sent POs cannot be accidentally resubmitted
✅ **Visual Feedback**: Clear status indicators for users
✅ **Retry Capability**: Failed POs can be easily retried
✅ **Reporting**: Status data available for reports and analytics

## Database Migration

To apply these changes to an existing database:

```bash
python migrate_add_po_status.py
```

The migration:
- Adds four new columns
- Sets default 'pending' status for existing records
- Is idempotent (safe to run multiple times)
- Uses transactions (rolls back on error)
