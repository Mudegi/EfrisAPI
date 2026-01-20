# QuickBooks Online to EFRIS Integration

This integration allows you to sync data from QuickBooks Online to Uganda's EFRIS system.

## Setup

### 1. QuickBooks App Configuration

1. Go to [QuickBooks Developer Portal](https://developer.intuit.com/)
2. Create a new app
3. Get your **Client ID** and **Client Secret**
4. Set redirect URI to: `http://localhost:8001/api/quickbooks/callback`
5. Add the credentials to `.env` file:
   ```
   QB_CLIENT_ID=your_client_id
   QB_CLIENT_SECRET=your_client_secret
   QB_REDIRECT_URI=http://localhost:8001/api/quickbooks/callback
   QB_ENVIRONMENT=sandbox
   ```

### 2. Connect to QuickBooks

1. Start the server: `python api_app.py`
2. Get authorization URL: `GET http://localhost:8001/api/quickbooks/auth?token=test_token`
3. Visit the `authUrl` returned in your browser
4. Sign in to QuickBooks and authorize the app
5. You'll be redirected back with tokens automatically saved

### 3. Check Connection

```
GET http://localhost:8001/api/quickbooks/status
```

## Available Endpoints

### QuickBooks Data Retrieval

#### Get Products/Services
```
GET /api/quickbooks/items?token=test_token
```

#### Get Invoices
```
GET /api/quickbooks/invoices?token=test_token&start_date=2026-01-01&end_date=2026-01-31
```

#### Get Credit Memos
```
GET /api/quickbooks/credit-memos?token=test_token&start_date=2026-01-01&end_date=2026-01-31
```

#### Get Purchase Orders
```
GET /api/quickbooks/purchase-orders?token=test_token&start_date=2026-01-01
```

### QuickBooks to EFRIS Sync

#### Sync Products
Syncs all products/services from QuickBooks to EFRIS:
```
POST /api/quickbooks/sync-products?token=test_token&default_category_id=50202306
```

#### Sync Specific Invoice
Syncs a specific QuickBooks invoice to EFRIS for fiscalization:
```
POST /api/quickbooks/sync-invoice/{invoice_id}?token=test_token
```

## Data Mapping

### Products
- QuickBooks **Item** → EFRIS **Product**
- SKU or ID → `goodsCode`
- Name → `goodsName`
- UnitPrice → `unitPrice`

### Invoices
- QuickBooks **Invoice** → EFRIS **T109 Invoice**
- Customer → `buyerDetails`
- Line items → `goodsDetails`
- Tax calculated automatically

### Credit Memos
- QuickBooks **Credit Memo** → EFRIS **T111 Credit Note**
- Original invoice reference required
- Line items mapped to goods details

### Stock Tracking
- QuickBooks **Purchase Order** → EFRIS **T131 Stock Increase**
- Vendor → Supplier details
- PO items → Stock items

## Workflow Examples

### 1. Initial Product Setup
```bash
# 1. Sync all products from QuickBooks to EFRIS
POST /api/quickbooks/sync-products?token=test_token

# 2. Verify products in EFRIS
GET /api/1014409555/goods-and-services?token=test_token
```

### 2. Invoice Fiscalization
```bash
# 1. Get QuickBooks invoices
GET /api/quickbooks/invoices?token=test_token&start_date=2026-01-01

# 2. Sync specific invoice to EFRIS
POST /api/quickbooks/sync-invoice/123?token=test_token

# 3. Get fiscalized invoice details from EFRIS
GET /api/1014409555/invoice/{invoice_no}?token=test_token
```

### 3. Credit Note Flow
```bash
# 1. Get credit memos from QuickBooks
GET /api/quickbooks/credit-memos?token=test_token

# 2. Create credit note in EFRIS
POST /api/1014409555/credit-note?token=test_token
{
  "oriInvoiceNo": "original_invoice_number",
  ...
}
```

## Important Notes

### QuickBooks Limitations
- Token expires after 1 hour (automatically refreshed)
- Refresh token valid for 100 days
- Sandbox environment for testing

### EFRIS Requirements
- Products must be registered before invoicing
- Invoice details must match EFRIS format
- VAT calculations must be accurate
- Commodity category IDs must be valid

### Data Synchronization
- QuickBooks is the source of truth
- Sync is one-way: QB → EFRIS
- Manual mapping may be needed for:
  - Commodity categories
  - Tax codes
  - Unit of measure codes

## Troubleshooting

### "Not connected to QuickBooks"
- Run authorization flow again
- Check if tokens expired
- Verify credentials in `.env`

### "Invalid commodity category"
- Update `default_category_id` parameter
- Get valid categories from EFRIS T127

### "Token refresh failed"
- Re-authorize the application
- Check if app credentials are correct

## Development vs Production

**Sandbox (Development):**
- Use test QuickBooks company
- No real data submitted to EFRIS test server

**Production:**
- Change `QB_ENVIRONMENT=production` in `.env`
- Use production QuickBooks company
- Submit to real EFRIS server
