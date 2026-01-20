# Excise Rate Auto-Population System

## ✅ What Was Implemented

The system now **automatically populates excise rates** from the T125 Query Excise Duty reference data.

### How It Works

1. **Reference Data Storage** (`excise_duty_reference.json`)
   - Contains all 104 excise duty codes and their rates from EFRIS T125 query
   - Loaded automatically on server startup
   - Maps excise codes to their official rates

2. **Automatic Rate Lookup**
   - When you assign an excise duty code to a product, the system automatically:
     - Looks up the official rate from T125 reference data
     - Populates the `ExciseRate` field in product metadata
     - Uses this rate when creating T109 invoice submissions

3. **Product Metadata Enhancement**
   - **Before**: `{"HasExcise": true, "ExciseDutyCode": "LED050000"}`
   - **After**: `{"HasExcise": true, "ExciseDutyCode": "LED050000", "ExciseRate": "500"}`

---

## 🔍 Example: Cement (LED050000)

### From T125 Reference Data:
```json
{
  "exciseDutyCode": "LED050000",
  "goodService": "Cement",
  "exciseDutyDetailsList": [
    {
      "rate": "500",
      "type": "102",
      "unit": "107",
      "currency": "101"
    }
  ],
  "rateText": "UGX500 per 50kgs"
}
```

### Auto-Populated Metadata:
```json
{
  "20": {
    "HasExcise": true,
    "ExciseDutyCode": "LED050000",
    "ExciseUnit": "107",
    "ExciseRate": "500",  ← Automatically populated!
    "ProductCode": "Building Material",
    "Sku": "30111601"
  }
}
```

### Used in T109 Invoice:
```json
{
  "itemCode": "Building Material",
  "categoryId": "LED050000",
  "goodsCategoryId": "30111601",
  "exciseFlag": "1",
  "exciseRate": "500",  ← From auto-populated metadata
  "exciseRule": "1",
  "exciseUnit": "107"
}
```

---

## 📊 Available Excise Rates

The system now has **104 excise duty codes** with their official rates:

| Code | Product | Rate | Unit |
|------|---------|------|------|
| **LED050000** | **Cement** | **500 UGX** | **per 50kgs** |
| LED110000 | Mineral Water | 50 UGX | per Litre |
| LED190100 | Fruit Juice | 250 UGX | per Litre |
| LED190200 | Non-alcoholic Beverages | 250 UGX | per Litre |
| LED040100 | Beer (Imported Malt) | 2050 UGX | per Litre |
| LED040200 | Beer (Local Malt) | 2050 UGX | per Litre |
| LED090000 | Cooking Oil | 200 UGX | per Litre |
| LED130100 | Gas Oil (Automotive) | 1230 UGX | per Litre |
| LED130700 | Motor Spirit (Gasoline) | 1550 UGX | per Litre |
| LED210100 | Sugar | 100 UGX | per Kg |
| ... | ... | ... | ... |
| *(104 total codes)* | | | |

---

## 🚀 How to Use

### 1. Update Existing Products

For products that already have excise codes assigned (like Tororo Cement):

**Option A: Re-sync from Dashboard**
1. Go to Products tab
2. Select "Tororo Cement"
3. Click "Edit Product"
4. Click "Save Changes" (even without changing anything)
5. System will auto-populate `ExciseRate: "500"`

**Option B: Delete Metadata Cache**
```powershell
Remove-Item product_metadata.json
```
Then re-sync the product from dashboard.

### 2. Add New Excisable Products

1. In dashboard, select product
2. Check "Has Excise Tax"
3. Select excise duty code from dropdown
4. **System automatically populates the rate** from T125 reference
5. Click "Sync to EFRIS"

### 3. Verify Metadata

Check `product_metadata.json`:
```json
{
  "20": {
    "HasExcise": true,
    "ExciseDutyCode": "LED050000",
    "ExciseUnit": "107",
    "ExciseRate": "500",  ← Should show correct rate
    "ProductCode": "Building Material",
    "Sku": "30111601"
  }
}
```

---

## 🔧 Technical Details

### Files Modified

1. **`excise_duty_reference.json`** (NEW)
   - Stores T125 excise duty data
   - 104 excise codes with rates, units, descriptions

2. **`api_app.py`**
   - Added `load_excise_duty_reference()` function
   - Added `get_excise_rate(excise_code)` lookup function
   - Enhanced metadata to include `ExciseRate`

3. **`quickbooks_efris_mapper.py`**
   - Uses `ExciseRate` from metadata instead of hardcoded "200"
   - Automatically applies correct rate in T109 invoices

### Reference Data Lookup Logic

```python
def get_excise_rate(excise_code: str) -> str:
    """Get the excise rate for a given excise duty code"""
    if excise_code in excise_duty_reference:
        return excise_duty_reference[excise_code].get('rate', '0')
    return '0'
```

### Metadata Enhancement

```python
# OLD (manual rate)
metadata = {
    'HasExcise': True,
    'ExciseDutyCode': 'LED050000',
    'ExciseUnit': '107'
}

# NEW (auto-populated rate)
excise_rate = get_excise_rate('LED050000')  # Returns "500"
metadata = {
    'HasExcise': True,
    'ExciseDutyCode': 'LED050000',
    'ExciseUnit': '107',
    'ExciseRate': '500'  # ← Automatically populated from T125
}
```

---

## ⚠️ Important: Fixing Tororo Cement Rate

**Current State**: Cement metadata shows `ExciseRate: "200"` (WRONG)  
**Correct Rate**: Should be `"500"` (from T125 reference)

### Fix Now:
1. Delete old metadata cache
2. Re-sync Tororo Cement from dashboard
3. System will auto-populate correct rate: `"500"`

### Command to Fix:
```powershell
# 1. Delete old cache
Remove-Item D:\EfrisAPI\product_metadata.json

# 2. Server will regenerate metadata on next product sync
# Go to dashboard → Products → Select Tororo Cement → Edit → Save
```

---

## 📝 Next Steps

1. **Refresh Metadata for Tororo Cement**
   - Delete `product_metadata.json`
   - Re-sync product from dashboard
   - Verify `ExciseRate: "500"` in metadata

2. **Test Invoice 1038**
   - Sync invoice from dashboard
   - Check EFRIS response
   - Should pass Error 1231 with correct rate

3. **Add More Excisable Products** (if needed)
   - Select excise code from dropdown
   - Rate auto-populates from T125 reference
   - No manual rate entry needed

---

## ✅ Success Criteria

- ✅ Server loads 104 excise duty codes on startup
- ✅ Cement shows: `[EXCISE REF] LED050000: 500 per unit 107 - Cement`
- ✅ Product metadata includes `ExciseRate` field
- ✅ T109 invoices use auto-populated rates
- ✅ No hardcoded "200" in mapper code

---

## 🎯 Benefits

1. **Accuracy**: Rates come from official EFRIS T125 data
2. **Automatic**: No manual rate entry required
3. **Consistent**: All invoices use correct rates
4. **Maintainable**: Update `excise_duty_reference.json` to update all rates
5. **Scalable**: Add new excisable products with confidence

---

*Server is running with excise duty reference loaded.*  
*Ready to test with Invoice 1038!*
