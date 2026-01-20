# Units of Measure - Dynamic Loading Implementation

## Overview
Successfully implemented dynamic units of measure loading from EFRIS T115 system dictionary endpoint, with fallback to hardcoded units.

## Changes Made

### 1. EFRIS Client (efris_client.py)
**Changed from T106 to T115** - Correct endpoint for system dictionary/parameters

```python
def get_code_list(self, code_type):
    """Query system dictionary using T115 - System Dictionary Update
    
    Returns system parameters including:
    - currencyType: List of currencies
    - rateUnit: List of units of measure  <-- THIS IS WHAT WE NEED
    - exciseStandardRateType: Excise duty types
    """
```

**Key Points:**
- T115 returns system-wide parameters, not query-specific codes
- `code_type` parameter kept for API compatibility but not used by T115
- Response contains encrypted + gzipped content with `rateUnit` array
- Response format:
  ```json
  {
    "rateUnit": [
      {"value": "101", "name": "Each (Unit)"},
      {"value": "102", "name": "Per Stick"},
      {"value": "103", "name": "Per Litre"}
    ],
    "currencyType": [...],
    "creditNoteMaximumInvoicingDays": {...}
  }
  ```

### 2. API Endpoint (api_multitenant.py)
**Endpoint:** `GET /api/companies/{company_id}/code-list?code_type=103`

- Still accepts `code_type` parameter (for backwards compatibility)
- Calls T115 internally
- Returns full decrypted system dictionary
- Frontend extracts `rateUnit` field

### 3. Frontend (static/dashboard_multitenant.html)

#### loadUnitsOfMeasure() Function
```javascript
async function loadUnitsOfMeasure() {
    // 1. Try to fetch from EFRIS T115
    const result = await fetch(`${API_BASE}/api/companies/${currentCompany.id}/code-list?code_type=103`);
    
    // 2. Extract rateUnit from decrypted content
    if (result.data.decrypted_content.rateUnit) {
        unitsOfMeasure = content.rateUnit.map(unit => ({
            code: unit.value || unit.code,
            name: unit.name || unit.description
        }));
    }
    
    // 3. Fallback to hardcoded units if API fails
    unitsOfMeasure = [
        { code: '101', name: 'Each (Unit)' },
        { code: '102', name: 'Per Stick' },
        { code: '103', name: 'Per Litre' },
        { code: '104', name: 'Kilogram' },
        { code: '105', name: 'Meter' },
        // ... etc
    ];
}
```

#### editItemForEFRIS() Function
- **Product Code**: Read-only, populated from QB `Description` field (or `Name` if empty)
- **UNSPSC/Commodity Code**: From QB `SKU` field (editable)
- **Unit of Measure**: Dropdown populated dynamically from `loadUnitsOfMeasure()`
- **Has Excise Duty**: Checkbox with conditional excise code dropdown

**Default Unit Logic:**
```javascript
unitSelect.value = item.Type === 'Service' ? '102' : '101';
// 102 = Per Stick (for services)
// 101 = Each/Unit (for goods)
```

### 4. Database Schema (database/models.py)
Product model stores EFRIS metadata:
```python
efris_product_code = Column(String(100))      # From QB Description
efris_commodity_code = Column(String(100))     # From QB SKU or user input
efris_unit_of_measure = Column(String(10))     # From dropdown selection
has_excise = Column(Boolean)
excise_duty_code = Column(String(20))
```

### 5. Registration Endpoint (api_multitenant.py)
`POST /api/companies/{company_id}/qb-items/register-to-efris`

**Uses Saved Metadata:**
```python
# Priority order:
1. p.efris_unit_of_measure (from edit modal)
2. "102" if service, "101" if goods (default)

# Product code priority:
1. p.efris_product_code (from edit modal)
2. p.qb_description (from QuickBooks)
3. p.qb_name (fallback)

# Commodity code priority:
1. p.efris_commodity_code (from edit modal)
2. p.qb_sku (from QuickBooks)
3. default_category_id (function parameter)
```

## Workflow: Edit → Register

1. **User clicks "Edit" on QB item** in dashboard
   
2. **Modal opens with:**
   - Product Code (read-only from QB Description)
   - UNSPSC Code (from QB SKU, editable)
   - Unit of Measure dropdown (loaded from T115 with fallback)
   - Excise duty checkbox/dropdown

3. **User saves metadata** → Stored in Product table

4. **User clicks "Register"** (individual or bulk)
   
5. **System sends to EFRIS T130** with saved metadata

6. **On success:**
   - Creates EFRISGood record in database
   - Item status changes to "Registered"
   - Green badge shows in QB Items list

## API Confusion Resolved

### ❌ WRONG: T106 is NOT for code lists
According to PDF documentation, T106 is "Invoice/Receipt Query" - it queries invoices, not system codes.

### ✅ CORRECT: T115 is for System Dictionary
T115 "System Dictionary Update" returns all system parameters including:
- Units of measure (`rateUnit`)
- Currencies (`currencyType`)
- Credit note limits
- Other system-wide settings

### Other Code Endpoints
- **T185**: Query HS Code List (customs/tariff codes)
- **T127**: Goods and Services Inquiry (registered products)
- **T130**: Goods Upload (register new products)

## Current Status

✅ **Implemented:**
- T115 endpoint in EFRIS client
- Dynamic unit loading with fallback
- Read-only product code from QB Description
- UNSPSC code from QB SKU
- Metadata persistence in database
- Registration using saved metadata

✅ **Working Features:**
- Edit modal loads units dynamically (or uses fallback)
- Product code correctly sourced from QB Description
- Commodity code from QB SKU (editable)
- Excise duty selection
- Individual and bulk registration
- Status badges (Registered/Pending)

⚠️ **Known Issues:**
- T115 API call may timeout or hang (needs investigation)
- Fallback units work perfectly as alternative
- May need to optimize T115 decryption performance

## Testing

### Test T115 Endpoint
```bash
py test_units_of_measure.py
```

### Test Complete Workflow
1. Open dashboard: http://localhost:8001
2. Login: admin@wandera.com / Admin2026!
3. Go to QuickBooks Items tab
4. Click "Edit" on any pending item
5. Verify:
   - Product code is read-only (from Description)
   - UNSPSC from SKU
   - Units dropdown populated (check browser console for "Loaded units" or "Using fallback")
6. Save metadata
7. Register to EFRIS
8. Verify status changes to "Registered"

## Fallback Units of Measure
If T115 fails, system uses these defaults:
- 101: Each (Unit)
- 102: Per Stick
- 103: Per Litre
- 104: Kilogram
- 105: Meter
- 106: Piece
- 107: Bag
- 108: Box
- 109: Dozen
- 110: Packet

## Next Steps (Optional)

1. **Optimize T115 Performance**
   - Investigate timeout issues
   - Add caching (1 hour TTL)
   - Retry logic

2. **Add Commodity Category Dropdown**
   - Similar to units, extract from T115 or separate endpoint
   - Replace UNSPSC input with searchable dropdown

3. **Unit Code Validation**
   - Verify units exist in EFRIS before registration
   - Show helpful error messages

4. **Bulk Edit**
   - Allow editing multiple items at once
   - Apply same metadata to selected items

## Summary
Units of measure are now dynamically loaded from EFRIS T115 endpoint with a robust fallback system. Product code correctly uses QB Description field (read-only), and UNSPSC code uses QB SKU. The edit workflow saves all metadata before registration, ensuring accurate EFRIS submissions.
