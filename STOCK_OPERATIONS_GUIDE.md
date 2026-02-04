# Stock Operations Guide - T131 & T132

## Overview

This guide documents the stock management endpoints for EFRIS integration:
- **T131**: Stock Increase (add goods to inventory)
- **T132**: Stock Decrease (remove/adjust goods from inventory)

Both endpoints support AES encryption and are fully implemented in the API.

---

## T131 - Stock Increase (operationType 101)

**Purpose:** Increase inventory for registered goods using purchase invoices or opening stock
**Encryption Code:** 2 (AES encrypt + RSA sign)
**Interface Code:** T131
**Operation Type:** 101 (for increase)

### Features
- Add goods to inventory from suppliers or manufacturing
- Support for import, local purchase, manufacturing/assembling, and opening stock
- Track production batch numbers and dates
- Record loss quantities during receiving
- Support for fuel tank tracking
- Handles multiple goods in single request

### Usage Example

```python
manager.perform_handshake()

stock_increase_data = {
    "goodsStockIn": {
        "operationType": "101",  # 101 = Increase
        "supplierTin": "1010039929",  # Required for operationType 101
        "supplierName": "Supplier Company Ltd",
        "stockInType": "102",  # 101=Import, 102=Local Purchase, 103=Manufacturing, 104=Opening Stock
        "stockInDate": "2024-12-30",  # Format: yyyy-MM-dd
        "branchId": "207300908813650312",
        "remarks": "Monthly inventory replenishment",
        "isCheckBatchNo": "0",
        "rollBackIfError": "0",
        "goodsTypeCode": "101"  # 101=Goods, 102=Fuel
    },
    "goodsStockInItem": [
        {
            "commodityGoodsId": "287700992426868373",  # OR goodsCode
            "goodsCode": "SKU-001",
            "measureUnit": "101",  # Unit code from T115
            "quantity": 100,
            "unitPrice": 6999,  # Purchase price
            "remarks": "Item remarks"
        },
        {
            "goodsCode": "SKU-002",
            "measureUnit": "102",
            "quantity": 50,
            "unitPrice": 2500,
            "lossQuantity": 5,  # Optional: loss during receiving
            "originalQuantity": 55
        }
    ]
}

response = manager.stock_increase(stock_increase_data)
```

### HTTP Endpoint

```
POST /api/companies/{company_id}/stock-increase
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
    "goodsStockIn": {
        "operationType": "101",
        "supplierTin": "1010039929",
        "supplierName": "Supplier Company Ltd",
        "stockInType": "102",
        "stockInDate": "2024-12-30",
        "branchId": "207300908813650312",
        "remarks": "Monthly inventory replenishment"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "SKU-001",
            "measureUnit": "101",
            "quantity": 100,
            "unitPrice": 6999
        }
    ]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| operationType | String | Yes | 101 = Increase, 102 = Decrease |
| supplierTin | String | No* | TIN of supplier (*required if operationType = 101) |
| supplierName | String | No* | Name of supplier (*required if operationType = 101) |
| stockInType | String | No* | 101=Import, 102=Local Purchase, 103=Manufacturing, 104=Opening Stock (*required if operationType = 101) |
| stockInDate | Date | No | Format: yyyy-MM-dd |
| branchId | String | No | Branch identifier |
| commodityGoodsId | String | No* | EFRIS commodity ID (*commodityGoodsId OR goodsCode required) |
| goodsCode | String | No* | Product code (*commodityGoodsId OR goodsCode required) |
| measureUnit | String | No | Unit code (from T115) |
| quantity | Number | Yes | Stock quantity (max 12 integer, 8 decimal digits) |
| unitPrice | Number | Yes | Unit purchase price |
| lossQuantity | Number | No | Loss during receiving |
| originalQuantity | Number | No | Original quantity before loss |
| remarks | String | No | Additional notes |
| goodsTypeCode | String | No | 101=Goods, 102=Fuel (default: 101) |

### Stock In Types

| Code | Type | Description | Requires supplierTin |
|------|------|-------------|----------------------|
| 101 | Import | Goods imported from outside | Yes |
| 102 | Local Purchase | Purchased from local suppliers | Yes |
| 103 | Manufacturing | Goods produced/assembled internally | No |
| 104 | Opening Stock | Initial inventory at system setup | No |

### Response Format

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
                "goodsCode": "SKU-001",
                "measureUnit": "101",
                "quantity": "100",
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            }
        ]
    }
}
```

### Common Error Codes

| Code | Message | Resolution |
|------|---------|-----------|
| 2076 | operationType cannot be empty | Ensure operationType is included |
| 2126 | stockInType cannot be empty | Provide stockInType for increase operation |
| 2191 | branchId cannot be empty | Include valid branchId |
| 2194 | goodsCode cannot be empty | Provide either commodityGoodsId or goodsCode |
| 2176 | Product already stored cannot use opening stock | Use different stockInType |
| 2243 | Measurement unit inconsistent | Verify unit matches commodity definition |

---

## T132 - Stock Decrease (operationType 102)

**Purpose:** Decrease or adjust inventory (removals, losses, damages, returns)
**Encryption Code:** 2 (AES encrypt + RSA sign)
**Interface Code:** T132
**Operation Type:** 102 (for decrease)

### Features
- Remove goods from inventory
- Track adjustment reasons (expired, damaged, personal use, etc.)
- Support for multiple adjustment types
- Bulk adjust multiple products
- Full audit trail maintained by EFRIS

### Usage Example

```python
manager.perform_handshake()

stock_decrease_data = {
    "goodsStockIn": {
        "operationType": "102",  # 102 = Decrease
        "adjustType": "101,102",  # 101=Expired, 102=Damaged, 103=Personal, 104=Others, 105=Raw Materials
        "stockInDate": "2024-12-30",
        "branchId": "207300908813650312",
        "remarks": "Damaged goods disposal - warehouse flood",
        "isCheckBatchNo": "0",
        "rollBackIfError": "0",
        "goodsTypeCode": "101"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "SKU-001",
            "measureUnit": "101",
            "quantity": 25,  # Quantity to remove
            "unitPrice": 6999,
            "remarks": "Water damaged - inventory count"
        },
        {
            "goodsCode": "SKU-003",
            "measureUnit": "103",
            "quantity": 10,
            "unitPrice": 15000,
            "remarks": "Expired items - beyond shelf life"
        }
    ]
}

response = manager.stock_decrease(stock_decrease_data)
```

### HTTP Endpoint

```
POST /api/companies/{company_id}/stock-decrease
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "102",
        "stockInDate": "2024-12-30",
        "branchId": "207300908813650312",
        "remarks": "Damaged goods disposal"
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
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| operationType | String | Yes | Must be "102" for decrease |
| adjustType | String | Yes* | 101=Expired, 102=Damaged, 103=Personal Use, 104=Others, 105=Raw Materials (*required for decrease) |
| stockInDate | Date | No | Format: yyyy-MM-dd |
| branchId | String | No | Branch identifier |
| commodityGoodsId | String | No* | EFRIS commodity ID (*OR goodsCode required) |
| goodsCode | String | No* | Product code (*OR commodityGoodsId required) |
| measureUnit | String | No | Unit code (from T115) |
| quantity | Number | Yes | Quantity to remove (max 12 integer, 8 decimal digits) |
| unitPrice | Number | Yes | Unit price for valuation |
| remarks | String | No* | Reason for adjustment (*required if adjustType = 104 "Others") |
| goodsTypeCode | String | No | 101=Goods, 102=Fuel (default: 101) |

### Adjustment Types

| Code | Type | Usage | Remarks Required |
|------|------|-------|------------------|
| 101 | Expired Goods | Items past expiry date | No |
| 102 | Damaged Goods | Physical damage or defects | No |
| 103 | Personal Use | Employee usage | No |
| 104 | Others | Custom reason | **Yes** |
| 105 | Raw Materials | Raw materials consumed | No |

### Response Format

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
                "goodsCode": "SKU-001",
                "measureUnit": "101",
                "quantity": "25",
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            }
        ]
    }
}
```

### Common Error Codes

| Code | Message | Resolution |
|------|---------|-----------|
| 2076 | operationType cannot be empty | Ensure operationType is "102" |
| 2127 | adjustType cannot be empty | Required for decrease operation |
| 2191 | branchId cannot be empty | Include valid branchId |
| 2194 | goodsCode cannot be empty | Provide either commodityGoodsId or goodsCode |
| 2243 | Measurement unit inconsistent | Verify unit matches commodity definition |
| 2282 | Insufficient stock | Cannot decrease more than available |

### Error Case - Adjust Type 104 (Others) Missing Remarks

```python
# This will FAIL - missing remarks for adjustType 104
incorrect_data = {
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "104",  # Others
        "remarks": "",  # REQUIRED for adjustType 104!
        "branchId": "207300908813650312"
    },
    "goodsStockInItem": [...]
}

# This will SUCCEED - remarks provided
correct_data = {
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "104",  # Others
        "remarks": "Inventory adjustment due to system reconciliation",  # Required!
        "branchId": "207300908813650312"
    },
    "goodsStockInItem": [...]
}
```

---

## Complete Inventory Cycle Example

```python
from efris_client import EfrisManager
import json

# Initialize
manager = EfrisManager(tin='1014409555', test_mode=True)
manager.perform_handshake()

# Step 1: Receive goods from supplier (T131 increase)
print("1. Recording goods receipt...")
receipt = manager.stock_increase({
    "goodsStockIn": {
        "operationType": "101",
        "supplierTin": "1010039929",
        "supplierName": "Supplier Ltd",
        "stockInType": "102",  # Local Purchase
        "stockInDate": "2024-12-30",
        "remarks": "December monthly purchase"
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
    print("✓ Stock receipt recorded")

# Step 2: Handle damaged goods (T132 decrease)
print("\n2. Recording damaged goods adjustment...")
adjustment = manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "102",  # Damaged
        "stockInDate": "2024-12-31",
        "remarks": "Damaged during storage"
    },
    "goodsStockInItem": [
        {
            "goodsCode": "PROD-001",
            "measureUnit": "101",
            "quantity": 5,  # 5 units damaged
            "unitPrice": 5000
        }
    ]
})

if adjustment.get('returnStateInfo', {}).get('returnCode') == '00':
    print("✓ Damage adjustment recorded")
    print(f"✓ Effective stock: 200 - 5 = 195 units")

# Step 3: Record expired goods
print("\n3. Recording expired goods...")
expiry_adjustment = manager.stock_decrease({
    "goodsStockIn": {
        "operationType": "102",
        "adjustType": "101",  # Expired
        "stockInDate": "2025-01-15",
        "remarks": "Stock expired - disposal"
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

if expiry_adjustment.get('returnStateInfo', {}).get('returnCode') == '00':
    print("✓ Expiry adjustment recorded")
    print(f"✓ Final effective stock: 195 - 10 = 185 units")
```

---

## Best Practices

### Stock Increase
- Always provide `supplierTin` for audit trail
- Use appropriate `stockInType` (not all 101)
- Include `invoiceNo` when available
- Record `lossQuantity` during receiving verification
- Use proper measurement units

### Stock Decrease
- Always provide `adjustType` (don't use null)
- For `adjustType` 104 (Others), always provide detailed `remarks`
- Use consistent measurement units across batch
- Group related adjustments for batch processing
- Verify sufficient stock before submitting

### General
- Validate goods exist before sending (use T127 query)
- Use `branchId` for multi-branch operations
- Set `rollBackIfError` = "1" to prevent partial updates
- Monitor response codes for inventory reconciliation
- Maintain local backup of all stock adjustments

---

## Performance Considerations

- **Batch Size:** Recommend 50-100 items per request (varies by EFRIS server)
- **Partial Failures:** Use `rollBackIfError = "0"` for large batches to continue on individual item failures
- **Retry Logic:** Implement retry for network timeouts
- **Caching:** Cache response codes for offline reconciliation

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| operationType not recognized | Ensure it's "101" (increase) or "102" (decrease) |
| Stock decrease fails - insufficient inventory | Verify available quantity before submitting |
| Supplier not found error | Validate supplierTin is correct and active in EFRIS |
| Measurement unit mismatch | Ensure unit code matches the commodity's defined unit |
| Adjustment type 104 without remarks | Always provide remarks field when using adjustType 104 |
| Handshake required error | Call manager.perform_handshake() before stock operations |

---

## API Response Examples

### Successful Stock Increase
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
                "goodsCode": "SKU-001",
                "quantity": "100",
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            }
        ]
    }
}
```

### Partial Failure (1 of 2 items failed)
```json
{
    "returnStateInfo": {
        "returnCode": "00",
        "returnMessage": "SUCCESS"
    },
    "data": {
        "decrypted_content": [
            {
                "goodsCode": "SKU-001",
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            },
            {
                "goodsCode": "SKU-002",
                "returnCode": "2243",
                "returnMessage": "Measurement unit: inconsistent with the maintained commodity unit!"
            }
        ]
    }
}
```

### Error Response
```json
{
    "returnStateInfo": {
        "returnCode": "2127",
        "returnMessage": "adjustType cannot be empty!"
    }
}
```
