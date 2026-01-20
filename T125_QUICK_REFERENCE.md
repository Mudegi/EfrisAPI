# T125 - Query Excise Duty - Quick Reference

## Endpoint Information
- **Interface Code**: T125
- **Purpose**: Query excise duty codes and rates from EFRIS
- **Encryption**: AES + RSA (encryptCode=2)
- **Response**: Gzip compressed + AES encrypted

## API Endpoint
```
GET /api/{tin}/excise-duty
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tin | Path | Yes | Taxpayer TIN number |
| token | Query | Yes | Authentication token |
| excise_duty_code | Query | No | Filter by excise duty code (e.g., "LED190100") |
| excise_duty_name | Query | No | Filter by excise duty name |

## Quick Start

### Python Client

```python
from efris_client import EfrisManager

# 1. Initialize and authenticate
manager = EfrisManager(tin='1014409555', test_mode=True)
manager.perform_handshake()

# 2. Query all excise duties
result = manager.query_excise_duty()

# 3. Access the data
duties = result['data']['decrypted_content']['exciseDutyList']
print(f"Found {len(duties)} excise duty codes")

# 4. Query specific code
specific = manager.query_excise_duty(excise_duty_code="LED190100")
```

### REST API Call

```bash
# Get all excise duties
curl "http://localhost:8001/api/1014409555/excise-duty?token=test_token"

# Filter by code
curl "http://localhost:8001/api/1014409555/excise-duty?token=test_token&excise_duty_code=LED190100"
```

### JavaScript/Fetch

```javascript
const response = await fetch(
  'http://localhost:8001/api/1014409555/excise-duty?token=test_token'
);
const data = await response.json();
const duties = data.data.exciseDutyList;
```

## Response Format

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

## Common Use Cases

### 1. Populate Dropdown List
```javascript
// Fetch excise duties and populate dropdown
fetch('/api/1014409555/excise-duty?token=test_token')
  .then(r => r.json())
  .then(data => {
    const select = document.getElementById('exciseDutySelect');
    data.data.exciseDutyList.forEach(duty => {
      select.innerHTML += `
        <option value="${duty.exciseDutyCode}">
          ${duty.exciseDutyCode} - ${duty.goodService} (${duty.rateText})
        </option>
      `;
    });
  });
```

### 2. Validate Excise Code
```python
def validate_excise_code(manager, code):
    """Check if excise duty code exists"""
    result = manager.query_excise_duty(excise_duty_code=code)
    duties = result['data']['decrypted_content']['exciseDutyList']
    return len(duties) > 0
```

### 3. Get Excise Rate
```python
def get_excise_rate(manager, code):
    """Get rate for specific excise duty code"""
    result = manager.query_excise_duty(excise_duty_code=code)
    duties = result['data']['decrypted_content']['exciseDutyList']
    if duties:
        return duties[0]['rateText']
    return None
```

### 4. Display in Product Form
```python
# Get excise duties
excise_result = manager.query_excise_duty()
excise_list = excise_result['data']['decrypted_content']['exciseDutyList']

# Show in product registration form
for duty in excise_list:
    print(f"{duty['exciseDutyCode']}: {duty['goodService']} - {duty['rateText']}")
```

## Testing

Run the test file:
```bash
python test_t125_excise_duty.py
```

Expected output:
```
Testing T125 - Query Excise Duty
[TEST] ✓ Handshake successful!
[TEST] ✓ Found 104 excise duty records
```

## Error Handling

```python
try:
    result = manager.query_excise_duty()
    
    if result.get('returnStateInfo', {}).get('returnCode') == '00':
        # Success
        duties = result['data']['decrypted_content']['exciseDutyList']
    else:
        # EFRIS error
        error = result['returnStateInfo']['returnMessage']
        print(f"Error: {error}")
        
except Exception as e:
    # Client error (network, auth, etc.)
    print(f"Exception: {e}")
```

## Performance Notes

- Response is gzip compressed (62KB → 7KB)
- Contains ~104 excise duty records
- Consider caching results (duty codes don't change frequently)
- No pagination currently implemented

## Integration with Product Upload

```python
# 1. Get excise duties for dropdown
excise_result = manager.query_excise_duty()
excise_duties = excise_result['data']['decrypted_content']['exciseDutyList']

# 2. User selects from dropdown
selected_code = "LED161600"

# 3. Upload product with excise duty
product = {
    "operationType": "101",
    "goodsName": "Internet Service Package",
    "goodsCode": "INET001",
    "haveExciseTax": "101",  # Yes
    "exciseDutyCode": selected_code,
    "measureUnit": "121",
    "unitPrice": "50000",
    "currency": "101"
}

result = manager.upload_goods([product])
```

## Key Fields

| Field | Description | Example |
|-------|-------------|---------|
| exciseDutyCode | Unique excise duty code | "LED161600" |
| goodService | Description of goods/service | "Internet Data for Medical..." |
| rateText | Rate as percentage | "0%", "10%" |
| effectiveDate | When duty became effective | "01/07/2021" |
| parentCode | Parent category code | "LED160000" |
| isLeafNode | Is this a leaf node? | "1" (yes) or "0" (no) |

## Return Codes

| Code | Message | Description |
|------|---------|-------------|
| 00 | SUCCESS | Query successful |
| 01 | FAILURE | General error |
| 02 | INVALID_PARAMS | Invalid parameters |
| 03 | AUTH_FAILED | Authentication failed |

## Requirements

- Handshake must be completed (`perform_handshake()`)
- Valid AES key from T104 required
- Certificate must be loaded and valid
- Network connectivity to EFRIS server

## Files

- **Implementation**: `efris_client.py` - `query_excise_duty()` method
- **API Endpoint**: `api_app.py` - `/api/{tin}/excise-duty`
- **Test**: `test_t125_excise_duty.py`
- **Documentation**: `T125_IMPLEMENTATION.md`

## Support

For issues or questions:
1. Check test file results: `python test_t125_excise_duty.py`
2. Verify handshake completed: `manager.is_key_valid()`
3. Check logs for encryption/decryption errors
4. Verify network connectivity to EFRIS server
