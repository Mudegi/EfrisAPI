# EFRIS API Encrypted Endpoints Guide

## Overview
This guide shows how to use the implemented EFRIS API methods with proper T104 encryption and signing.

## Prerequisites

1. **Certificate Requirements:**
   - PKCS12 format certificate (.pfx file)
   - Contains both private key and certificate
   - Password: `123456` (default in code)
   - Location: `keys/wandera.pfx`

2. **Environment Setup:**
   ```
   EFRIS_CERT_PATH=keys/wandera.pfx
   ```

3. **Initial Setup:**
   ```python
   from efris_client import EfrisManager
   
   # Initialize with test mode
   manager = EfrisManager(tin='1014409555', test_mode=True)
   
   # Perform mandatory handshake (includes T104 key exchange)
   manager.perform_handshake()
   ```

## API Methods

### 1. T101 - Time Synchronization (`_time_sync`)
**Purpose:** Synchronize local time with server
**Encryption:** None (handshake step)
**Internal use:** Called during `perform_handshake()`

```python
manager._time_sync()
# Validates local time is within ±10 minutes of server
```

### 2. T104 - Key Exchange (`_key_exchange`)
**Purpose:** Obtain AES symmetric key for encryption
**Response:** 
- `passwordDes`: RSA-encrypted AES key
- `sign`: Server signature

**Implementation:**
```python
manager._key_exchange()
# Sets manager.aes_key for subsequent encryptions
```

**Flow Diagram:**
```
Client sends empty T104 request
    ↓
Server returns RSA-encrypted AES key
    ↓
Client RSA decrypts to get AES key
    ↓
Client uses AES key for all subsequent requests
```

### 3. T103 - Get Registration Details (`_get_parameters`)
**Purpose:** Get taxpayer registration and branch details
**Encryption Code:** 0 (no encryption for handshake)
**Response:** Registration details stored in `manager.registration_details`

```python
manager._get_parameters()
# Sets manager.registration_details with taxpayer info
```

### 4. T109 - Generate Invoice/Receipt (`generate_invoice`)
**Purpose:** Issue a new invoice with AES encryption
**Encryption Code:** 2 (AES encrypt + RSA sign)
**Requires:** T104 key exchange (handshake)

**Usage:**
```python
# Ensure handshake completed
manager.perform_handshake()

# Prepare invoice data
invoice_data = {
    "invoiceNumber": "INV001",
    "invoiceDate": "2024-12-30",
    "buyerTin": "1015264035",
    "buyerName": "Customer Name",
    "deviceId": "1015264035_04",
    "items": [
        {
            "itemCode": "001",
            "itemName": "Service A",
            "quantity": 2,
            "unitPrice": 50000,
            "taxRate": 18
        },
        {
            "itemCode": "002",
            "itemName": "Service B",
            "quantity": 1,
            "unitPrice": 100000,
            "taxRate": 18
        }
    ],
    "totalAmount": 218000  # 100000 + 100000 + 18000
}

# Send invoice with encryption
response = manager.generate_invoice(invoice_data)

# Response format
{
    "returnStateInfo": {
        "returnCode": "00",
        "returnMessage": "SUCCESS"
    },
    "data": {
        "invoiceId": "...",
        "receiptNumber": "...",
        ...
    }
}
```

### 5. T119 - Query Taxpayer (`query_taxpayer_by_tin`)
**Purpose:** Look up taxpayer information by TIN or NIN/BRN
**Encryption Code:** 1 (RSA sign only)

**Usage:**
```python
# Query by TIN
response = manager.query_taxpayer_by_tin(tin='1015264035')

# Query by NIN/BRN
response = manager.query_taxpayer_by_tin(tin='', ninBrn='123456789')

# Response
{
    "returnStateInfo": {"returnCode": "00"},
    "data": {
        "tin": "1015264035",
        "name": "Business Name",
        "status": "ACTIVE",
        ...
    }
}
```

### 6. T123 - Get Goods and Services (`get_goods_and_services`)
**Purpose:** Retrieve list of goods and services
**Encryption Code:** 1 (RSA sign only)

**Usage:**
```python
request_data = {
    "pageNumber": 1,
    "pageSize": 100
}

response = manager.get_goods_and_services(request_data)

# Response
{
    "returnStateInfo": {"returnCode": "00"},
    "data": {
        "goods": [
            {
                "code": "001",
                "name": "Product A",
                "category": "...",
                ...
            }
        ]
    }
}
```

### 7. T103 - Get Registration Details (`get_registration_details`)
**Purpose:** Get current registration and branch details
**Encryption Code:** 1 (RSA sign only)

**Usage:**
```python
response = manager.get_registration_details()

# Response
{
    "returnStateInfo": {"returnCode": "00"},
    "data": {
        "tin": "1014409555",
        "name": "Business Name",
        "branches": [...],
        "devices": [...]
    }
}
```

### 8. T125 - Query Excise Duty (`query_excise_duty`)
**Purpose:** Query excise duty codes and rates from EFRIS
**Encryption Code:** 2 (AES encrypt + RSA sign)
**Response:** Gzip compressed + AES encrypted

**Usage:**
```python
# Ensure handshake completed
manager.perform_handshake()

# Query all excise duties
response = manager.query_excise_duty()

# Query specific excise duty by code
response = manager.query_excise_duty(excise_duty_code="LED190100")

# Query by name
response = manager.query_excise_duty(excise_duty_name="Internet Data")

# Response
{
    "returnStateInfo": {
        "returnCode": "00",
        "returnMessage": "SUCCESS"
    },
    "data": {
        "decrypted_content": {
            "exciseDutyList": [
                {
                    "exciseDutyCode": "LED161600",
                    "goodService": "Internet Data for provision of Medical and Education services",
                    "effectiveDate": "01/07/2021",
                    "rateText": "0%",
                    "exciseDutyDetailsList": [
                        {
                            "rate": "0",
                            "type": "101"
                        }
                    ]
                },
                ...
            ]
        }
    }
}
```

**API Endpoint:**
```bash
GET /api/{tin}/excise-duty?token=test_token
GET /api/{tin}/excise-duty?token=test_token&excise_duty_code=LED190100
GET /api/{tin}/excise-duty?token=test_token&excise_duty_name=Internet+Data
```

**Response Example:**
```json
{
  "returnStateInfo": {
    "returnCode": "00",
    "returnMessage": "SUCCESS"
  },
  "data": {
    "exciseDutyList": [
      {
        "exciseDutyCode": "LED161600",
        "goodService": "Internet Data for provision of Medical and Education services",
        "effectiveDate": "01/07/2021",
        "parentCode": "LED160000",
        "rateText": "0%",
        "isLeafNode": "1",
        "exciseDutyDetailsList": [
          {
            "exciseDutyId": "120453215404593459",
            "rate": "0",
            "type": "101"
          }
        ]
      }
    ]
  }
}
```

**Use Cases:**
- Get list of all excise duty codes for product registration
- Lookup excise rates for specific products
- Verify excise duty codes before uploading goods with excise tax
- Display excise duty options in product management UI

## Encryption Details

### Data Flow with T104 Key

```
Request Data
    ↓
JSON Encode
    ↓
AES Encrypt (with key from T104)
    ↓
Base64 Encode
    ↓
RSA Sign (with private key)
    ↓
Build Payload
    ↓
Send to Server
```

### Example Request Structure (T109)

```json
{
  "data": {
    "content": "base64_encrypted_invoice_json",
    "signature": "rsa_signature_of_encrypted_content",
    "dataDescription": {
      "codeType": "0",
      "encryptCode": "2",
      "zipCode": "0"
    }
  },
  "globalInfo": {
    "appId": "AP04",
    "version": "1.1.20191201",
    "dataExchangeId": "uuid",
    "interfaceCode": "T109",
    "requestCode": "TP",
    "requestTime": "2024-12-30 10:30:45",
    "responseCode": "TA",
    "userName": "admin",
    "deviceMAC": "FFFFFFFFFFFF",
    "deviceNo": "1014409555_02",
    "tin": "1014409555",
    ...
  },
  "returnStateInfo": {
    "returnCode": "",
    "returnMessage": ""
  }
}
```

## Error Handling

```python
from efris_client import EfrisManager

try:
    manager = EfrisManager(tin='1014409555', test_mode=True)
    manager.perform_handshake()
    
    invoice_response = manager.generate_invoice(invoice_data)
    
    if invoice_response.get('returnStateInfo', {}).get('returnCode') == '00':
        print("Invoice created successfully")
        print(f"Invoice ID: {invoice_response['data']['invoiceId']}")
    else:
        print(f"Error: {invoice_response}")
        
except Exception as e:
    print(f"API Error: {e}")
    print("Common causes:")
    print("- Certificate not found or expired")
    print("- Network connectivity issue")
    print("- Time out of sync with server (±10 minutes)")
    print("- Invalid credentials")
```

## Encryption Code Values

| Code | Description | Content Format | Signature |
|------|-------------|-----------------|-----------|
| 0 | No encryption | Plain JSON | RSA sign |
| 1 | RSA sign only | Plain JSON | RSA sign |
| 2 | AES + RSA sign | AES encrypted JSON | RSA sign |

## Working Example

Complete working flow:

```python
from efris_client import EfrisManager
import json

# Step 1: Initialize
manager = EfrisManager(tin='1014409555', test_mode=True)

# Step 2: Perform handshake (T101 + T104 + T103)
print("Performing handshake...")
manager.perform_handshake()
print(f"✓ AES Key obtained: {len(manager.aes_key)} bytes")

# Step 3: Get registration details
print("\nGetting registration details...")
reg_response = manager.get_registration_details()
print(f"✓ Registered as: {reg_response['data'].get('tin')}")

# Step 4: Generate invoice with AES encryption
print("\nGenerating invoice with T109...")
invoice_data = {
    "invoiceNumber": "INV-2024-001",
    "invoiceDate": "2024-12-30",
    "buyerTin": "1015264035",
    "buyerName": "Test Customer",
    "items": [
        {
            "itemCode": "ITEM001",
            "description": "Service",
            "quantity": 1,
            "unitPrice": 100000,
            "taxRate": 18
        }
    ],
    "totalAmount": 118000
}

response = manager.generate_invoice(invoice_data)

if response.get('returnStateInfo', {}).get('returnCode') == '00':
    print("✓ Invoice created successfully")
    print(f"  Invoice ID: {response['data'].get('invoiceId')}")
    print(f"  Receipt: {response['data'].get('receiptNumber')}")
else:
    print(f"✗ Error: {response}")
```

## Security Notes

1. **Private Key Protection:**
   - Private key is loaded from PKCS12 certificate
   - Never log or expose the private key
   - Ensure certificate password is secure

2. **AES Key Rotation:**
   - New AES key obtained from T104 on each handshake
   - Rotate by calling `perform_handshake()` periodically

3. **Time Synchronization:**
   - Server validates that client time is within ±10 minutes
   - Ensure NTP is properly configured on the system
   - T101 will fail if time is out of sync

4. **Signature Verification:**
   - All requests are signed with private key
   - Server verifies signature using public key from certificate
   - Tampering with request data will invalidate signature

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Certificate load error | Check cert path, ensure PKCS12 format, verify password |
| Time sync failed | Check system time, enable NTP |
| Key exchange failed | Verify network connectivity, check certificate validity |
| Encryption errors | Ensure handshake completed before using AES methods |
| Signature verification failed | Check private key, ensure data not modified after signing |
