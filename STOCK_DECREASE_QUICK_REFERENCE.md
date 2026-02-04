# Stock Decrease Endpoint - Quick Reference

## ✅ Status: FULLY IMPLEMENTED

The stock decrease endpoint is fully operational and integrated with the API.

---

## Quick Facts

| Property | Value |
|----------|-------|
| **Endpoint** | `POST /api/companies/{company_id}/stock-decrease` |
| **Interface Code** | T132 |
| **Operation Type** | 102 |
| **Encryption** | AES + RSA |
| **Authentication** | JWT Bearer Token |
| **Status** | ✅ Production Ready |
| **API File** | [api_multitenant.py](api_multitenant.py#L2285) |
| **Client File** | [efris_client.py](efris_client.py#L1063) |

---

## How It Works

### 1. Basic Request
```python
manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",      # Always 102 for decrease
        "adjustType": "102",         # Reason: 101=Expired, 102=Damaged, etc.
        "stockInDate": "2024-12-30",
        "remarks": "Reason for adjustment"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "SKU-001",
            "quantity": 10,
            "unitPrice": 5000
        }
    ]
})
```

### 2. Behind the Scenes
- Request JSON → AES encrypted → RSA signed → Sent to EFRIS
- EFRIS verifies signature → Decrypts AES → Processes stock reduction
- Response signed → Returned to client
- Client decrypts → Returns result

### 3. Response
```json
{
    "returnStateInfo": {
        "returnCode": "00",
        "returnMessage": "SUCCESS"
    },
    "data": {
        "decrypted_content": [...]
    }
}
```

---

## Adjustment Types

| Code | Type | Use Case | Remarks Required |
|------|------|----------|------------------|
| 101 | Expired | Items past expiration date | No |
| 102 | Damaged | Physical damage or defects | No |
| 103 | Personal Use | Employee used/consumed item | No |
| 104 | Others | Custom reason | **YES** |
| 105 | Raw Materials | Raw materials consumed | No |

---

## Common Use Cases

### Remove Damaged Goods
```python
manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "102",  # Damaged
        "remarks": "Water damaged in warehouse"
    },
    "goodsStockInItem": [{
        "goodsCode": "PROD-001",
        "quantity": 5,
        "unitPrice": 6999
    }]
})
```

### Remove Expired Items
```python
manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "101",  # Expired
        "remarks": "Items beyond shelf life"
    },
    "goodsStockInItem": [{
        "goodsCode": "PROD-002",
        "quantity": 20,
        "unitPrice": 2500
    }]
})
```

### Custom Adjustment with Remarks
```python
manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "104",  # Others (REQUIRES remarks)
        "remarks": "Inventory reconciliation - system correction"
    },
    "goodsStockInItem": [{
        "goodsCode": "PROD-003",
        "quantity": 15,
        "unitPrice": 7500
    }]
})
```

### Batch Adjustment (Multiple Items)
```python
manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "102",
        "remarks": "Damage from recent delivery"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "PROD-001",
            "quantity": 5,
            "unitPrice": 5000
        },
        {
            "goodsCode": "PROD-002",
            "quantity": 3,
            "unitPrice": 10000
        },
        {
            "goodsCode": "PROD-003",
            "quantity": 8,
            "unitPrice": 2500
        }
    ]
})
```

---

## cURL Example (One-Liner)

```bash
curl -X POST http://localhost:8001/api/companies/1/stock-decrease -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{"goodsStockIn":{"operationType":"102","adjustType":"102","remarks":"Water damaged"},"goodsStockInItem":[{"goodsCode":"SKU-001","quantity":5,"unitPrice":5000}]}'
```

---

## Python Integration

```python
from efris_client import EfrisManager

# Setup
manager = EfrisManager(tin='1014409555', test_mode=True)
manager.perform_handshake()

# Execute
response = manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "102",
        "remarks": "Warehouse damage"
    },
    "goodsStockInItem": [{
        "goodsCode": "PROD-001",
        "quantity": 10,
        "unitPrice": 5000
    }]
})

# Check result
success = response.get('returnStateInfo', {}).get('returnCode') == '00'
print("✓ Success!" if success else f"✗ Error: {response}")
```

---

## Error Codes

| Code | Message | Fix |
|------|---------|-----|
| 2076 | operationType cannot be empty | Use "102" |
| 2127 | adjustType cannot be empty | Provide adjustment reason |
| 2194 | goodsCode cannot be empty | Include valid product code |
| 2282 | Insufficient stock | Check available quantity |
| 2890 | remarks cannot be empty (adjustType 104) | Required for type 104 |

---

## Related Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/companies/{id}/stock-increase` | Add goods to inventory (T131) |
| `POST /api/companies/{id}/stock-decrease` | Remove goods from inventory (T132) |
| `GET /api/companies/{id}/goods-and-services` | List available goods (T127) |

---

## Documentation

- 📘 **[STOCK_OPERATIONS_GUIDE.md](STOCK_OPERATIONS_GUIDE.md)** - Complete reference guide
- 📋 **[STOCK_API_EXAMPLES.md](STOCK_API_EXAMPLES.md)** - API request/response examples
- 🔧 **[STOCK_DECREASE_IMPLEMENTATION.md](STOCK_DECREASE_IMPLEMENTATION.md)** - Implementation details
- 📖 **[Documentation/interface codes.py](Documentation/interface%20codes.py)** - EFRIS specification

---

## Quick Checklist

Before calling stock_decrease:

- [ ] Handshake completed: `manager.perform_handshake()`
- [ ] JWT token obtained and valid
- [ ] Company ID is correct
- [ ] operationType is "102"
- [ ] adjustType is specified
- [ ] If adjustType is "104", remarks are provided
- [ ] goodsCode exists in inventory
- [ ] quantity doesn't exceed available stock
- [ ] All dates in yyyy-MM-dd format

---

## Need Help?

1. **See examples:** Check [STOCK_API_EXAMPLES.md](STOCK_API_EXAMPLES.md)
2. **Read spec:** Review [STOCK_OPERATIONS_GUIDE.md](STOCK_OPERATIONS_GUIDE.md)
3. **Check EFRIS docs:** See [Documentation/interface codes.py](Documentation/interface%20codes.py)
4. **Test it:** Use the provided curl/Python examples
5. **Debug:** Check response error codes in error table above

---

## Implementation Summary

✅ **Endpoint:** Fully implemented and tested  
✅ **Encryption:** AES + RSA working  
✅ **Database:** Records persist correctly  
✅ **EFRIS Integration:** Connected and synced  
✅ **Error Handling:** Comprehensive error responses  
✅ **Documentation:** Complete with examples  

**The stock decrease endpoint is ready for production use.**
