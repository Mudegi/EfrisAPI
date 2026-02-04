# Stock Operations - API Examples

## T131 & T132 Endpoints - Ready to Use

Both stock increase and stock decrease endpoints are fully implemented and operational.

---

## Endpoint 1: Stock Increase (T131)

### URL
```
POST /api/companies/{company_id}/stock-increase
```

### Headers
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

### Request Example

```json
{
    "goodsStockIn": {
        "operationType": "101",
        "supplierTin": "1010039929",
        "supplierName": "Supplier Company Ltd",
        "stockInType": "102",
        "stockInDate": "2024-12-30",
        "branchId": "207300908813650312",
        "remarks": "Monthly inventory replenishment",
        "rollBackIfError": "0"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "PROD-001",
            "measureUnit": "101",
            "quantity": 200,
            "unitPrice": 5000,
            "remarks": "Standard purchase"
        },
        {
            "goodsCode": "PROD-002",
            "measureUnit": "102",
            "quantity": 50,
            "unitPrice": 10000,
            "lossQuantity": 2,
            "originalQuantity": 52
        }
    ]
}
```

### cURL Command

```bash
curl -X POST http://localhost:8001/api/companies/1/stock-increase \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "goodsStockIn": {
      "operationType": "101",
      "supplierTin": "1010039929",
      "supplierName": "Supplier Ltd",
      "stockInType": "102",
      "stockInDate": "2024-12-30",
      "branchId": "207300908813650312",
      "remarks": "Monthly purchase"
    },
    "goodsStockInItem": [
      {
        "goodsCode": "PROD-001",
        "measureUnit": "101",
        "quantity": 200,
        "unitPrice": 5000
      }
    ]
  }'
```

### Python Request

```python
import requests
import json

url = "http://localhost:8001/api/companies/1/stock-increase"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

payload = {
    "goodsStockIn": {
        "operationType": "101",
        "supplierTin": "1010039929",
        "supplierName": "Supplier Ltd",
        "stockInType": "102",
        "stockInDate": "2024-12-30",
        "branchId": "207300908813650312",
        "remarks": "Monthly purchase"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "PROD-001",
            "measureUnit": "101",
            "quantity": 200,
            "unitPrice": 5000
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)
print(json.dumps(response.json(), indent=2))
```

### Response

```json
{
    "returnStateInfo": {
        "returnCode": "00",
        "returnMessage": "SUCCESS"
    },
    "data": {
        "decrypted_content": [
            {
                "commodityGoodsId": "287700992426868373",
                "goodsCode": "PROD-001",
                "measureUnit": "101",
                "quantity": "200",
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            },
            {
                "commodityGoodsId": "287700992426868374",
                "goodsCode": "PROD-002",
                "measureUnit": "102",
                "quantity": "50",
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            }
        ]
    }
}
```

### Stock In Types

| Type | Code | Requires supplierTin | Use Case |
|------|------|----------------------|----------|
| Import | 101 | Yes | Goods imported internationally |
| Local Purchase | 102 | Yes | Goods bought from local supplier |
| Manufacturing | 103 | No | Goods produced internally |
| Opening Stock | 104 | No | Initial inventory setup |

---

## Endpoint 2: Stock Decrease (T132)

### URL
```
POST /api/companies/{company_id}/stock-decrease
```

### Headers
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

### Request Example - Damaged Goods

```json
{
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "102",
        "stockInDate": "2024-12-31",
        "branchId": "207300908813650312",
        "remarks": "Water damaged during warehouse flood",
        "rollBackIfError": "1"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "PROD-001",
            "measureUnit": "101",
            "quantity": 5,
            "unitPrice": 5000
        }
    ]
}
```

### Request Example - Expired Goods

```json
{
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "101",
        "stockInDate": "2025-01-15",
        "remarks": "Items beyond shelf life - disposal"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "PROD-002",
            "measureUnit": "102",
            "quantity": 10,
            "unitPrice": 10000
        }
    ]
}
```

### Request Example - Custom Adjustment (requires remarks)

```json
{
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "104",
        "stockInDate": "2025-01-20",
        "remarks": "Inventory reconciliation - count variance adjustment"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "PROD-003",
            "measureUnit": "103",
            "quantity": 15,
            "unitPrice": 7500
        }
    ]
}
```

### cURL Commands

**Damaged Goods:**
```bash
curl -X POST http://localhost:8001/api/companies/1/stock-decrease \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "goodsStockIn": {
      "operationType": "102",
      "adjustType": "102",
      "stockInDate": "2024-12-31",
      "branchId": "207300908813650312",
      "remarks": "Water damaged"
    },
    "goodsStockInItem": [
      {
        "goodsCode": "PROD-001",
        "measureUnit": "101",
        "quantity": 5,
        "unitPrice": 5000
      }
    ]
  }'
```

**Expired Goods:**
```bash
curl -X POST http://localhost:8001/api/companies/1/stock-decrease \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "goodsStockIn": {
      "operationType": "102",
      "adjustType": "101",
      "stockInDate": "2025-01-15",
      "remarks": "Expired items disposal"
    },
    "goodsStockInItem": [
      {
        "goodsCode": "PROD-002",
        "measureUnit": "102",
        "quantity": 10,
        "unitPrice": 10000
      }
    ]
  }'
```

**Custom Reason (type 104):**
```bash
curl -X POST http://localhost:8001/api/companies/1/stock-decrease \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "goodsStockIn": {
      "operationType": "102",
      "adjustType": "104",
      "remarks": "System reconciliation adjustment"
    },
    "goodsStockInItem": [
      {
        "goodsCode": "PROD-003",
        "measureUnit": "103",
        "quantity": 15,
        "unitPrice": 7500
      }
    ]
  }'
```

### Python Examples

```python
import requests
import json

def stock_decrease(company_id, adjustment_type, quantity, goods_code, reason):
    """Generic stock decrease function"""
    url = f"http://localhost:8001/api/companies/{company_id}/stock-decrease"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "goodsStockIn": {
            "operationType": "102",
            "adjustType": adjustment_type,
            "stockInDate": "2024-12-31",
            "remarks": reason
        },
        "goodsStockInItem": [
            {
                "goodsCode": goods_code,
                "measureUnit": "101",
                "quantity": quantity,
                "unitPrice": 5000
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# Example: Damaged goods
result = stock_decrease(
    company_id=1,
    adjustment_type="102",  # Damaged
    quantity=5,
    goods_code="PROD-001",
    reason="Water damaged during warehouse flood"
)
print(json.dumps(result, indent=2))

# Example: Expired goods
result = stock_decrease(
    company_id=1,
    adjustment_type="101",  # Expired
    quantity=10,
    goods_code="PROD-002",
    reason="Items beyond shelf life"
)
print(json.dumps(result, indent=2))
```

### Adjustment Types

| Code | Type | Remarks Required | Example Use |
|------|------|------------------|-------------|
| 101 | Expired Goods | No | Items past expiration date |
| 102 | Damaged Goods | No | Water damaged, dented, broken |
| 103 | Personal Use | No | Employee consumed/used |
| 104 | Others | **Yes** | Any other reason (must explain) |
| 105 | Raw Materials | No | Raw materials consumed in production |

### Response

```json
{
    "returnStateInfo": {
        "returnCode": "00",
        "returnMessage": "SUCCESS"
    },
    "data": {
        "decrypted_content": [
            {
                "commodityGoodsId": "287700992426868373",
                "goodsCode": "PROD-001",
                "measureUnit": "101",
                "quantity": "5",
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            }
        ]
    }
}
```

---

## Complete Workflow Example

```python
from efris_client import EfrisManager
import json

# Initialize
manager = EfrisManager(tin='1014409555', test_mode=True)
manager.perform_handshake()

# 1. Receive 200 units of PROD-001
print("Step 1: Stock Increase - Receiving goods")
receipt = manager.stock_increase({
    "goodsStockIn": {
        "operationType": "101",
        "supplierTin": "1010039929",
        "supplierName": "Main Supplier",
        "stockInType": "102",
        "stockInDate": "2024-12-30",
        "remarks": "Monthly purchase"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "PROD-001",
            "measureUnit": "101",
            "quantity": 200,
            "unitPrice": 5000
        }
    ]
})

if receipt.get('returnStateInfo', {}).get('returnCode') == '00':
    print("✓ Stock increase successful")
    print(f"  Added: 200 units @ UGX 5000")

# 2. 5 units damaged during warehouse operations
print("\nStep 2: Stock Decrease - Damaged goods")
damage = manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "102",
        "stockInDate": "2024-12-31",
        "remarks": "Damaged during warehouse operations"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "PROD-001",
            "measureUnit": "101",
            "quantity": 5,
            "unitPrice": 5000
        }
    ]
})

if damage.get('returnStateInfo', {}).get('returnCode') == '00':
    print("✓ Damage adjustment recorded")
    print(f"  Removed: 5 damaged units")
    print(f"  Effective stock: 200 - 5 = 195 units")

# 3. 10 units expired
print("\nStep 3: Stock Decrease - Expired items")
expiry = manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "101",
        "stockInDate": "2025-01-15",
        "remarks": "Items expired - disposal required"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "PROD-001",
            "measureUnit": "101",
            "quantity": 10,
            "unitPrice": 5000
        }
    ]
})

if expiry.get('returnStateInfo', {}).get('returnCode') == '00':
    print("✓ Expiry adjustment recorded")
    print(f"  Removed: 10 expired units")
    print(f"  Final effective stock: 195 - 10 = 185 units")

print("\n✓ Inventory management complete!")
```

---

## Error Handling

### Example: Missing Required Field

```json
{
    "returnStateInfo": {
        "returnCode": "2127",
        "returnMessage": "adjustType cannot be empty!"
    }
}
```

**Fix:** Ensure `adjustType` is provided for all decrease operations.

### Example: Adjustment Type 104 Without Remarks

```json
{
    "returnStateInfo": {
        "returnCode": "2890",
        "returnMessage": "Remarks: cannot be empty! (required for adjustType 104)"
    }
}
```

**Fix:** When using `adjustType: "104"`, always provide `remarks` field.

### Example: Insufficient Stock

```json
{
    "returnStateInfo": {
        "returnCode": "2282",
        "returnMessage": "Insufficient stock - Cannot decrease more than available"
    }
}
```

**Fix:** Verify available inventory before submitting decrease request.

---

## Testing Checklist

- [ ] Handshake completed successfully (perform_handshake)
- [ ] JWT token is valid and not expired
- [ ] Company ID is correct and accessible
- [ ] Goods code exists in EFRIS
- [ ] Measurement unit matches commodity definition
- [ ] For stock increase: supplier TIN is valid
- [ ] For stock decrease: adjustType is provided
- [ ] For adjustType 104: remarks are provided
- [ ] Quantity doesn't exceed available stock
- [ ] All dates in yyyy-MM-dd format

---

## See Also

- [STOCK_OPERATIONS_GUIDE.md](STOCK_OPERATIONS_GUIDE.md) - Detailed API documentation
- [STOCK_DECREASE_IMPLEMENTATION.md](STOCK_DECREASE_IMPLEMENTATION.md) - Implementation details
- [api_multitenant.py](api_multitenant.py) - API source code
- [efris_client.py](efris_client.py) - EFRIS client implementation
