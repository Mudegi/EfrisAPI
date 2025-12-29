# EFRIS API Client

This is a Python client for the EFRIS System to System API V3.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Obtain API credentials from URA:
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