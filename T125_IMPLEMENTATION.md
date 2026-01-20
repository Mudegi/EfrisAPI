# T125 - Query Excise Duty Implementation

## Overview

The T125 interface is used to query excise duty codes and rates from the EFRIS system. This endpoint is essential for:
- Getting a list of all available excise duty codes
- Looking up excise rates for specific products subject to excise tax
- Validating excise duty codes before registering goods
- Displaying excise duty options in product management interfaces

## Implementation Details

### Interface Code
- **Interface Code:** T125
- **Interface Name:** Query Excise Duty
- **Request Method:** POST
- **Encryption Code:** 2 (AES encryption + RSA signature)
- **Response Format:** Gzip compressed + AES encrypted JSON

### Request Parameters

```json
{
  "exciseDutyCode": "LED190100",  // Optional: Filter by excise duty code
  "exciseDutyName": "Internet Data"  // Optional: Filter by name
}
```

**Note:** Both parameters are optional. If no parameters are provided, all excise duties are returned.

### Response Structure

```json
{
  "returnStateInfo": {
    "returnCode": "00",
    "returnMessage": "SUCCESS"
  },
  "data": {
    "content": "base64_gzip_aes_encrypted_data",
    "signature": "rsa_signature",
    "dataDescription": {
      "codeType": "0",
      "encryptCode": "2",
      "zipCode": "1"
    },
    "decrypted_content": {
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
              "id": "120453871950290403",
              "rate": "0",
              "type": "101"
            }
          ]
        }
      ]
    }
  }
}
```

## Code Implementation

### Python Client Method

Located in `efris_client.py`:

```python
def query_excise_duty(self, excise_duty_code=None, excise_duty_name=None):
    """Query excise duty information using T125 - Excise Duty Inquiry
    
    Args:
        excise_duty_code: Optional filter by excise duty code (e.g., "LED190100")
        excise_duty_name: Optional filter by excise duty name
        
    Returns:
        Response containing list of excise duty codes and rates
    """
    # Ensure we have a valid AES key for decryption
    self.ensure_authenticated()
    
    # Build request content
    request_content = {}
    if excise_duty_code:
        request_content["exciseDutyCode"] = excise_duty_code
    if excise_duty_name:
        request_content["exciseDutyName"] = excise_duty_name
        
    content = json.dumps(request_content, separators=(',', ':'), sort_keys=True)
    
    # T125 requires AES encryption (encryptCode=2)
    payload = self._build_request_payload("T125", content, encrypt_code=2)
    
    response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
    
    if response.status_code == 200:
        result = response.json()
        
        # Decrypt the response content (gzip + AES encrypted)
        if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
            encrypted_content = result['data']['content']
            if encrypted_content:
                # Check if gzip compressed
                if encrypted_content.startswith('H4sI'):
                    compressed_data = base64.b64decode(encrypted_content)
                    decompressed_data = gzip.decompress(compressed_data)
                    decrypted_content = decompressed_data.decode('utf-8')
                else:
                    decrypted_content = self._decrypt_aes(encrypted_content)
                
                parsed_content = json.loads(decrypted_content)
                result['data']['decrypted_content'] = parsed_content
                
        return result
    else:
        return f'API Error {response.status_code}: {response.text}'
```

### FastAPI Endpoint

Located in `api_app.py`:

```python
@app.get("/api/{tin}/excise-duty")
async def query_excise_duty(
    tin: str,
    token: str = Query(...),
    excise_duty_code: str = Query(None, description="Excise duty code filter"),
    excise_duty_name: str = Query(None, description="Excise duty name filter")
):
    """T125 - Query Excise Duty"""
    if token != "test_token":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        result = manager.query_excise_duty(
            excise_duty_code=excise_duty_code,
            excise_duty_name=excise_duty_name
        )
        
        # Extract decrypted content if available
        if isinstance(result, dict) and 'data' in result:
            if 'decrypted_content' in result['data']:
                decrypted = result['data']['decrypted_content']
                return {
                    "returnStateInfo": result.get('returnStateInfo', {}),
                    "data": decrypted
                }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Usage Examples

### Python Client

```python
from efris_client import EfrisManager

# Initialize
manager = EfrisManager(tin='1014409555', test_mode=True)

# Perform handshake (required for AES encryption)
manager.perform_handshake()

# Query all excise duties
all_duties = manager.query_excise_duty()
print(f"Found {len(all_duties['data']['decrypted_content']['exciseDutyList'])} excise duties")

# Query specific excise duty by code
specific_duty = manager.query_excise_duty(excise_duty_code="LED190100")

# Query by name
by_name = manager.query_excise_duty(excise_duty_name="Internet Data")
```

### REST API

```bash
# Query all excise duties
curl "http://localhost:8001/api/1014409555/excise-duty?token=test_token"

# Query by excise duty code
curl "http://localhost:8001/api/1014409555/excise-duty?token=test_token&excise_duty_code=LED190100"

# Query by name
curl "http://localhost:8001/api/1014409555/excise-duty?token=test_token&excise_duty_name=Internet+Data"
```

### JavaScript/Frontend

```javascript
// Fetch all excise duties
const response = await fetch(
  'http://localhost:8001/api/1014409555/excise-duty?token=test_token'
);
const data = await response.json();

// Display in dropdown
const select = document.getElementById('exciseDutySelect');
data.data.exciseDutyList.forEach(duty => {
  const option = document.createElement('option');
  option.value = duty.exciseDutyCode;
  option.text = `${duty.exciseDutyCode} - ${duty.goodService} (${duty.rateText})`;
  select.appendChild(option);
});
```

## Test Results

The test file `test_t125_excise_duty.py` demonstrates successful implementation:

```
================================================================================
Testing T125 - Query Excise Duty
================================================================================

[TEST] Performing handshake (T101 + T104 + T103)...
[TEST] ✓ Handshake successful!

Test 1: Query all excise duties (no filter)
[T125] Response returnCode: 00
[T125] Response returnMessage: SUCCESS
[TEST] ✓ Found 104 excise duty records

Sample record:
{
  "exciseDutyCode": "LED161600",
  "goodService": "Internet Data for provision of Medical and Education services",
  "effectiveDate": "01/07/2021",
  "parentCode": "LED160000",
  "rateText": "0%",
  "exciseDutyDetailsList": [...]
}

Test 2: Query with excise duty code filter
[T125] Response returnCode: 00
[T125] Response returnMessage: SUCCESS
[TEST] ✓ Successfully queried specific excise duty code
```

## Common Excise Duty Codes

Based on the test results, here are some common excise duty codes:

| Code | Description | Rate |
|------|-------------|------|
| LED161600 | Internet Data for Medical/Education | 0% |
| LED190100 | (Various) | Varies |
| LED190200 | (Various) | Varies |

**Note:** Run the query endpoint to get the complete list of available codes.

## Integration with Product Registration

When registering products (T130 - Upload Goods), you can use T125 to populate the excise duty dropdown:

```python
# Step 1: Get excise duty list
excise_duties = manager.query_excise_duty()
excise_list = excise_duties['data']['decrypted_content']['exciseDutyList']

# Step 2: User selects excise duty from dropdown
selected_duty = "LED161600"  # Example

# Step 3: Register product with excise duty
product_data = {
    "operationType": "101",
    "goodsName": "Internet Service",
    "goodsCode": "INET001",
    "haveExciseTax": "101",  # Yes
    "exciseDutyCode": selected_duty,
    # ... other fields
}

response = manager.upload_goods([product_data])
```

## Response Field Descriptions

### exciseDutyList Item Fields

- **exciseDutyCode**: Unique code for the excise duty (e.g., "LED161600")
- **goodService**: Description of goods/service subject to this duty
- **effectiveDate**: Date when this duty became effective
- **parentCode**: Parent category code (for hierarchical structure)
- **rateText**: Human-readable rate (e.g., "0%", "10%")
- **isLeafNode**: "1" if leaf node (actual duty), "0" if category
- **exciseDutyDetailsList**: Array of detailed rate information

### exciseDutyDetailsList Item Fields

- **exciseDutyId**: Unique ID for this duty
- **id**: Record ID
- **rate**: Numeric rate value
- **type**: Rate type code (101, 102, etc.)

## Encryption Flow

```
Client Side:
1. Build request content: {"exciseDutyCode": "LED190100"}
2. JSON stringify (sorted keys, no spaces)
3. AES encrypt using key from T104
4. Base64 encode
5. RSA sign encrypted content
6. Send to server

Server Side:
7. Verify RSA signature
8. AES decrypt content
9. Process query
10. Build response JSON
11. Gzip compress
12. Base64 encode
13. Send to client

Client Side:
14. Base64 decode
15. Gzip decompress
16. Parse JSON
17. Return to caller
```

## Error Handling

```python
try:
    result = manager.query_excise_duty()
    
    if result.get('returnStateInfo', {}).get('returnCode') == '00':
        duties = result['data']['decrypted_content']['exciseDutyList']
        print(f"Success: Found {len(duties)} excise duties")
    else:
        error_msg = result.get('returnStateInfo', {}).get('returnMessage')
        print(f"EFRIS Error: {error_msg}")
        
except Exception as e:
    print(f"Exception: {e}")
    # Check: Is handshake completed?
    # Check: Is AES key valid?
    # Check: Network connectivity?
```

## Notes

1. **Authentication Required**: Must call `perform_handshake()` before using this endpoint
2. **AES Key**: Uses the AES key obtained from T104 key exchange
3. **Compression**: Response is gzip compressed for efficiency (104 records compressed to 7KB)
4. **Caching**: Consider caching the excise duty list as it doesn't change frequently
5. **Pagination**: Currently returns all records; EFRIS may add pagination in future versions

## Files Modified

1. **efris_client.py**: Added `query_excise_duty()` method
2. **api_app.py**: Added `/api/{tin}/excise-duty` endpoint
3. **test_t125_excise_duty.py**: Created test file
4. **API_ENDPOINTS_GUIDE.md**: Updated with T125 documentation

## Status

✅ **Implementation Complete**
- Client method implemented
- API endpoint created
- Encryption/decryption working
- Gzip decompression working
- Tests passing
- Documentation complete
