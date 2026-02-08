# Response to EFRIS API Team - Excise Duty Endpoint

---

## Current Issue

Thank you for responding! The response structure you've shown is perfect, but when we call the `/excise-duty` endpoint, we're receiving **empty `name` fields** for all 87 codes.

### What We're Actually Receiving:
```json
{
  "success": true,
  "excise_codes": [
    {
      "code": "LED190100",
      "name": "",              ← EMPTY - This is the problem!
      "rate": "250",
      "unit": "102",
      "currency": "UGX",
      "excise_rule": "2"
    },
    {
      "code": "LED161600",
      "name": "",              ← EMPTY
      "rate": "0",
      "unit": "%",
      "currency": "UGX",
      "excise_rule": "1"
    }
    // ... all 87 codes have empty names
  ],
  "total": 87,
  "last_updated": "2026-02-08T03:50:17.655395"
}
```

### What We Need (Example from Your T125 Endpoint):
```json
{
  "success": true,
  "excise_codes": [
    {
      "code": "LED190100",
      "name": "Fruit juice and vegetable juice, except juice made from at least 30% pulp or at least 30% juice by weight or volume of the total composition of the drink from fruits and vegetables grown locally",
      "rate": "250",
      "unit": "102",
      "currency": "UGX",
      "excise_rule": "2"
    },
    {
      "code": "LED161600",
      "name": "Internet Data for provision of Medical and Education services",
      "rate": "0",
      "unit": "%",
      "currency": "UGX",
      "excise_rule": "1"
    }
  ],
  "total": 87,
  "last_updated": "2026-02-08T03:50:17.655395"
}
```

---

## Specific Request

**The `name` field needs to be populated with the excise duty descriptions.**

Your T125 public test endpoint (`/api/public/efris/test/t125`) already returns the correct data with the `goodService` field containing these descriptions. 

**Please map the `goodService` field from T125 to the `name` field in your `/excise-duty` response.**

### Field Mapping Needed:

| Your Current Field | Should Contain | Source from T125 |
|-------------------|----------------|------------------|
| `code` | ✅ Working | `exciseDutyCode` |
| `name` | ❌ Currently empty | `goodService` |
| `rate` | ✅ Working | Derived from `rateText` |
| `unit` | ✅ Working | From `exciseDutyDetailsList` |
| `currency` | ✅ Working | From `exciseDutyDetailsList` |

---

## Why We Need This

In our product form, users need to:
1. **Search by excise code** (e.g., "LED190100") - ✅ Works
2. **Search by product description** (e.g., "beer", "juice", "plastic") - ❌ Blocked (empty names)
3. **Display meaningful descriptions** in dropdowns - ❌ Blocked (empty names)

Currently, users see:
```
LED190100 -                      ← No description, confusing!
LED161600 - 
LED040600 - 
```

We need them to see:
```
LED190100 - Fruit juice and vegetable juice (UGX250/Litre, 10%)
LED161600 - Internet Data for Medical/Education services (0%)
LED040600 - Other Alcoholic Beverage Locally Produced (10%, UGX150/Litre)
```

---

## Implementation Suggestion

If you need guidance, here's what we believe needs to happen on your backend:

```python
# When building the /excise-duty response:

# 1. Fetch T125 data (you already have this for the public test endpoint)
t125_data = fetch_ura_t125_excise_codes()

# 2. Transform each code
excise_codes = []
for item in t125_data['exciseDutyList']:
    excise_codes.append({
        'code': item['exciseDutyCode'],
        'name': item['goodService'],  # ← This is the key change!
        'rate': parse_rate(item['rateText']),
        'unit': determine_unit(item['exciseDutyDetailsList']),
        'currency': determine_currency(item['exciseDutyDetailsList']),
        'excise_rule': determine_rule(item)
    })

# 3. Return formatted response
return {
    'success': True,
    'excise_codes': excise_codes,
    'total': len(excise_codes)
}
```

---

## Testing After Fix

Once implemented, we should see responses like this:

**Request:**
```bash
GET https://efrisintegration.nafacademy.com/api/external/efris/excise-duty
```

**Expected Response:**
```json
{
  "success": true,
  "excise_codes": [
    {
      "code": "LED040600",
      "name": "Other Alcoholic Beverage Locally Produced",
      "rate": "10",
      "unit": "101",
      "currency": "UGX",
      "excise_rule": "2"
    },
    {
      "code": "LED110000",
      "name": "Mineral Water, bottled water and other water purposely for drinking",
      "rate": "10",
      "unit": "101",
      "currency": "UGX",
      "excise_rule": "2"
    },
    {
      "code": "LED260100",
      "name": "Plastic product and Plastic Granules",
      "rate": "2.5",
      "unit": "101",
      "currency": "USD",
      "excise_rule": "2"
    }
    // ... all 87 codes with proper names
  ],
  "total": 87
}
```

---

## Summary

✅ **Response structure**: Perfect, no changes needed  
✅ **Field names**: Perfect, no changes needed  
❌ **Data quality**: The `name` field is empty, needs to be populated from T125's `goodService`

**Action Required**: Populate the `name` field with excise duty descriptions from the T125 interface data.

---

**Thank you for your help with this!** Once the `name` field is populated, our excise duty feature will be complete and ready for production use.
