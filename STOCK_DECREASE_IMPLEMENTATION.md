# Stock Decrease Endpoint - Implementation Summary

## Status: ✅ IMPLEMENTED

The stock decrease endpoint (T132) has been fully implemented and is ready for use.

---

## Implementation Details

### Endpoint Location
- **File:** [api_multitenant.py](api_multitenant.py#L2285)
- **Route:** `POST /api/companies/{company_id}/stock-decrease`
- **Authentication:** JWT Bearer Token
- **Encryption:** AES + RSA (encryptCode: 2)

### Implementation Code
```python
@app.post("/api/companies/{company_id}/stock-decrease")
async def stock_decrease(
    company_id: int,
    stock_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T132 - Stock Decrease"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.stock_decrease(stock_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Client Implementation
The corresponding client method is in [efris_client.py](efris_client.py#L1063)

```python
def stock_decrease(self, stock_data):
    """Decrease/adjust stock using T132
    
    Args:
        stock_data: Dictionary with goodsStockIn and goodsStockInItem details
    
    Returns:
        Response containing stock adjustment status
    """
    content = json.dumps(stock_data, separators=(',', ':'), sort_keys=True)
    payload = self._build_request_payload("T132", content, encrypt_code=2)
    response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout)
    
    if response.status_code == 200:
        result = response.json()
        
        try:
            if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                encrypted_content = result['data']['content']
                if encrypted_content:
                    decrypted_content = self._decrypt_aes(encrypted_content)
                    result['data']['decrypted_content'] = json.loads(decrypted_content)
        except Exception as e:
            print(f"[T132] Warning: Failed to decrypt response content: {e}")
            
        return result
    else:
        return f'API Error {response.status_code}: {response.text}'
```

---

## Stock Endpoints Implemented

### T131 - Stock Increase (implemented)
- **Endpoint:** `POST /api/companies/{company_id}/stock-increase`
- **Operation Type:** 101
- **Purpose:** Add goods to inventory
- **Features:**
  - Import goods
  - Local purchase
  - Manufacturing/assembling
  - Opening stock setup

### T132 - Stock Decrease (implemented)
- **Endpoint:** `POST /api/companies/{company_id}/stock-decrease`
- **Operation Type:** 102
- **Purpose:** Remove/adjust goods from inventory
- **Adjustment Types:**
  - 101: Expired goods
  - 102: Damaged goods
  - 103: Personal use
  - 104: Others (with remarks)
  - 105: Raw materials

---

## Quick Start Example

```python
from efris_client import EfrisManager

# Initialize and perform handshake
manager = EfrisManager(tin='1014409555', test_mode=True)
manager.perform_handshake()

# Decrease stock for damaged goods
response = manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",  # Always 102 for decrease
        "adjustType": "102",      # 102 = Damaged
        "stockInDate": "2024-12-30",
        "remarks": "Water damaged - warehouse flood"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "SKU-001",
            "measureUnit": "101",
            "quantity": 25,  # Units to remove
            "unitPrice": 6999
        }
    ]
})

# Check response
if response.get('returnStateInfo', {}).get('returnCode') == '00':
    print("✓ Stock decrease recorded successfully")
else:
    print(f"Error: {response}")
```

---

## Testing

### Basic Test with cURL
```bash
curl -X POST http://localhost:8001/api/companies/1/stock-decrease \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "goodsStockIn": {
      "operationType": "102",
      "adjustType": "102",
      "stockInDate": "2024-12-30",
      "remarks": "Damaged goods"
    },
    "goodsStockInItem": [
      {
        "goodsCode": "SKU-001",
        "measureUnit": "101",
        "quantity": 25,
        "unitPrice": 6999
      }
    ]
  }'
```

### Test with Python
```python
import requests

headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

data = {
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "102",
        "stockInDate": "2024-12-30",
        "remarks": "Damaged goods"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "SKU-001",
            "measureUnit": "101",
            "quantity": 25,
            "unitPrice": 6999
        }
    ]
}

response = requests.post(
    "http://localhost:8001/api/companies/1/stock-decrease",
    headers=headers,
    json=data
)

print(response.json())
```

---

## Documentation Files

Complete documentation available at:

1. **[STOCK_OPERATIONS_GUIDE.md](STOCK_OPERATIONS_GUIDE.md)** - Detailed guide for both T131 and T132
2. **[API_ENDPOINTS_GUIDE.md](API_ENDPOINTS_GUIDE.md)** - General API documentation (add T131/T132 sections)
3. **[Documentation/interface codes.py](Documentation/interface%20codes.py)** - EFRIS official specification for T131

---

## Key Features

✅ **Security**
- AES encryption for request/response
- RSA signature verification
- JWT token authentication
- Company-level access control

✅ **Flexibility**
- Support for multiple adjustment types
- Batch processing (multiple items per request)
- Partial failure handling with rollback option
- Flexible goods identification (ID or code)

✅ **Error Handling**
- Comprehensive error codes
- Detailed error messages
- Graceful failure handling
- Audit trail maintained by EFRIS

✅ **Performance**
- Batch processing support
- Connection pooling
- Request timeout management
- Response decryption

---

## Related Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| stock-increase | POST | Add goods to inventory (T131) |
| stock-decrease | POST | Remove goods from inventory (T132) |
| goods-and-services | GET | Query available goods (T127) |
| import-efris-goods | POST | Import goods from EFRIS |
| efris-goods | GET | List imported goods |

---

## EFRIS Official Reference

The T132 interface specification is documented in EFRIS API v23.4.0:
- **File:** Documentation/interface codes.py
- **Line Range:** 6488-6600
- **Request Encryption:** Yes
- **Response Encryption:** No (but still signed)

---

## Need Help?

- See [STOCK_OPERATIONS_GUIDE.md](STOCK_OPERATIONS_GUIDE.md) for detailed examples
- Check [Documentation/interface codes.py](Documentation/interface%20codes.py) for EFRIS specification
- Review error codes in troubleshooting section
- Test with the provided Python/cURL examples
