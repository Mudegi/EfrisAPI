# EFRIS Multi-Tenant API

A complete multi-tenant EFRIS (Electronic Fiscal Receipting and Invoicing Solution) API with full QuickBooks integration.

## 🚀 Quick Start

### Start the Server

```bash
py main.py
```

Or directly with uvicorn:
```bash
py -m uvicorn api_multitenant:app --host 0.0.0.0 --port 8001
```

### Access the Dashboard

Open your browser: **http://localhost:8001**

Default credentials:
- Email: `admin@wandera.com`
- Password: `Admin2026!`

## ✨ Features

### Multi-Tenant Architecture
- ✅ **User authentication** with JWT tokens
- ✅ **Company management** (multiple companies per user)
- ✅ **Role-based access control**
- ✅ **Isolated data** (each company has separate products, invoices, etc.)

### EFRIS Integration
- ✅ **Full T104 handshake** (AES key exchange)
- ✅ **Product registration** (T130 with automatic opening stock via T131)
- ✅ **Invoice submission** (T109)
- ✅ **Credit notes** (T110)
- ✅ **Stock management** (T131 increase, T132 decrease)
- ✅ **Excise duty support** (automatic extraction from QB prices)
- ✅ **Discount handling** (item-level and invoice-level)
- ✅ **18% VAT tax** (automatic calculation on taxable amounts)

### QuickBooks Integration
- ✅ **OAuth 2.0 authentication**
- ✅ **Product sync** (with EFRIS metadata enrichment)
- ✅ **Invoice sync** (automatic EFRIS submission)
- ✅ **Purchase orders** (stock increase via T131)
- ✅ **Credit memos support**
- ✅ **Excise price extraction** (for items with excise duty)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables (optional, has defaults):
   ```
   QB_CLIENT_ID=your_quickbooks_client_id
   QB_CLIENT_SECRET=your_quickbooks_client_secret
   QB_REDIRECT_URI=http://localhost:8001/api/quickbooks/callback
   QB_ENVIRONMENT=sandbox
   ```
   - Client ID and Secret
   - Digital certificate and private key

3. Create a `.env` file with:
   ```
   EFRIS_CLIENT_ID=your_client_id
   EFRIS_CLIENT_SECRET=your_client_secret
   EFRIS_CERT_PATH=path/to/cert.pem
   EFRIS_KEY_PATH=path/to/key.pem
   ```

4. For production, ensure mTLS is configured (modify the client for full certificate authentication).

## 💰 Discount & Tax Support

**Full support for QuickBooks invoices with ANY discount, ANY tax rate, and EXCISE DUTY!**

- **Discounts**: ANY percentage (5%, 10%, 15%, 20%, 50%, etc.) or fixed amounts
- **Tax Types**: 
  - ✅ Standard VAT (18% or custom %)
  - ✅ Zero-rated (0%)
  - ✅ Exempt
  - ✅ Deemed VAT (with project tracking)
- **Excise Duty**:
  - ✅ Fixed-rate excise (200 UGX per unit, etc.)
  - ✅ Percentage excise (30% of price, etc.)
  - ✅ Beer, Spirits, Cigarettes, Soft drinks, Fuel
  - ✅ Works with discounts and all tax types
- **Mixed Invoices**: Different tax types, excise items, and discounts in one invoice
- **Format**: Fully EFRIS-compliant submission

📖 **Read more:**
- [Quick Reference](DISCOUNT_TAX_QUICK_REF.md) - Fast guide
- [Complete Guide](COMPLETE_EXCISE_DISCOUNT_TAX.md) - Excise + Discount + Tax
- [Detailed Documentation](DISCOUNT_AND_TAX_HANDLING.md) - Full technical details
- [UI Enhancement](UI_ENHANCEMENT_COMPLETE.md) - Invoice review feature
- [User Guide](USER_GUIDE_INVOICE_REVIEW.md) - How to review invoices before submission

🧪 **Test it:**
```bash
# Test excise + discount + tax
py test_excise_discount_complete.py

# Test any discount + any tax
py test_comprehensive_tax_discount.py
```

## Usage

Run the example:
```
python main.py
```

## API Methods

- `validate_taxpayer(tin)`: Validate a taxpayer by TIN.
- `issue_receipt(data)`: Issue a new receipt.
- `query_receipt(receipt_id)`: Query receipt details.
- `void_receipt(receipt_id, data)`: Void a receipt.
- `submit_sales_report(data)`: Submit sales report.
- `register_branch(data)`: Register a branch.

## Troubleshooting

- Ensure certificates are valid and paths are correct.
- Check network connectivity to the API.
- For errors, refer to EFRIS documentation for status codes.