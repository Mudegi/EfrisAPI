# 🔧 Auto-Healing Metadata System

## Overview

The system now automatically generates missing product metadata when syncing invoices. This eliminates manual steps and prevents Error 2848 ("exciseFlag must be '1'").

---

## ✨ What Changed

### Before (Fragile)
1. Delete metadata cache
2. **Manually** edit each product in dashboard
3. Click "Save Changes" to regenerate metadata
4. **Then** sync invoice
5. ❌ Easy to forget, causes errors

### After (Self-Healing)
1. Sync invoice from dashboard
2. System **automatically** detects missing metadata
3. System **automatically** fetches product from QuickBooks
4. System **automatically** populates excise rate/rule from T125
5. System **automatically** saves metadata
6. ✅ Invoice syncs successfully - no manual steps

---

## 🎯 How It Works

### Auto-Metadata Generation Flow

```
Invoice Sync Request
        ↓
Check: Does product have metadata?
        ↓
    NO → Fetch product from QuickBooks
        ↓
    Parse excise info from Description
        ↓
    Auto-populate rate from T125 reference
        ↓
    Auto-populate rule from T125 reference
        ↓
    Save metadata to product_metadata.json
        ↓
    Continue with invoice sync
        ↓
    ✅ Success
```

### What Gets Auto-Generated

When metadata is missing for a product, the system automatically creates:

| Field | Source | Example |
|-------|--------|---------|
| **HasExcise** | Parsed from Description | `true` |
| **ExciseDutyCode** | Parsed from Description | `"LED050000"` |
| **ExciseUnit** | Parsed from Description or default | `"107"` |
| **ExciseRate** | Auto-populated from T125 reference | `"500"` |
| **ExciseRule** | Auto-populated from T125 reference | `"2"` |
| **ProductCode** | From Description or Name | `"Building Material"` |
| **Sku** | From QuickBooks or default | `"30111601"` |

---

## 📝 QuickBooks Description Format

For excise products, use this format in the **Description** field:

```
ProductName | ExciseCode:LED050000 | Unit:107
```

**Example (Tororo Cement):**
```
Building Material | ExciseCode:LED050000 | Unit:107
```

The system automatically:
- Detects `ExciseCode:LED050000` → Sets excise duty code
- Detects `Unit:107` → Sets excise unit (50kgs)
- Looks up `LED050000` in T125 reference → Gets rate=500, rule=2

---

## 🔍 Server Logs Example

When metadata is auto-generated, you'll see:

```
[AUTO-METADATA] Generating metadata for item 20 (Tororo Cement)
[AUTO-METADATA] Created metadata for item 20:
  - HasExcise: True
  - ExciseDutyCode: LED050000
  - ExciseUnit: 107
  - ExciseRate: 500 (from T125)
  - ExciseRule: 2 (from T125)
  - ProductCode: Building Material
  - Sku: 30111601
[Invoice Sync] Using metadata for item 20: {'HasExcise': True, 'ExciseDutyCode': 'LED050000', ...}
```

---

## ✅ Benefits

### 1. **Self-Healing**
- Missing metadata? System creates it automatically
- No manual intervention required
- Resilient to cache deletion

### 2. **Always Up-to-Date**
- Metadata regenerated from QuickBooks on-the-fly
- Reflects latest product configuration
- T125 reference ensures correct rates

### 3. **Error Prevention**
- Eliminates Error 2848 (exciseFlag must be '1')
- Eliminates Error 1231 (exciseRate empty)
- Eliminates Error 2795 (exciseRule incorrect)

### 4. **Audit Trail**
- Detailed console logs show metadata generation
- Easy debugging with clear output
- Transparent operation

---

## 🧪 Testing

### Test Auto-Metadata Generation

1. **Delete metadata cache** (optional - system handles missing metadata):
   ```powershell
   Remove-Item product_metadata.json
   ```

2. **Sync Invoice 1038** from dashboard

3. **Check server logs** - should see:
   ```
   [AUTO-METADATA] Generating metadata for item 20 (Tororo Cement)
   [AUTO-METADATA] Created metadata for item 20:
     - ExciseRate: 500 (from T125)
     - ExciseRule: 2 (from T125)
   ```

4. **Verify product_metadata.json** created automatically:
   ```json
   {
     "20": {
       "HasExcise": true,
       "ExciseDutyCode": "LED050000",
       "ExciseUnit": "107",
       "ExciseRate": "500",
       "ExciseRule": "2",
       "ProductCode": "Building Material",
       "Sku": "30111601"
     }
   }
   ```

5. **Invoice should sync successfully** ✅

---

## 🔧 Manual Override

You can still manually sync products via dashboard if needed:

1. Dashboard → Products Tab
2. Select product → Edit
3. Update fields
4. Click "Save Changes"
5. Metadata updated immediately

This triggers the same metadata generation code, ensuring consistency.

---

## 📊 Excise Reference Data

The system uses the complete T125 excise duty reference with **104 excise codes**.

**Example codes:**

| Code | Product | Rate | Unit | Rule |
|------|---------|------|------|------|
| LED050000 | Cement | 500 | 107 (50kgs) | 2 (fixed) |
| LED040600 | Alcoholic Beverage | 150 | 102 (litre) | 2 (fixed) |
| LED161600 | Internet Data | 0% | - | 1 (percentage) |
| LED190400 | Non-alcoholic Beverage | 150 | 102 (litre) | 2 (fixed) |

**Rate/Rule Auto-Population:**
- System checks T125 reference on startup
- Detects type 102 (fixed-rate) → exciseRule = "2"
- Detects type 101 (percentage) → exciseRule = "1"
- Extracts rate from reference data
- No manual rate entry required

---

## 🚨 Error Resolution

### Error 2848: exciseFlag must be '1'
**Before:** Manual metadata regeneration required  
**Now:** System auto-generates metadata → Error prevented

### Error 1231: exciseRate cannot be empty
**Before:** Manual rate entry required  
**Now:** System auto-populates from T125 → Error prevented

### Error 2795: exciseRule should be '2'
**Before:** Hardcoded rule, often wrong  
**Now:** System auto-detects from T125 type → Error prevented

---

## 💡 Key Implementation Details

### Location: `api_app.py`

**Function: `sync_invoice_to_efris`** (Lines ~975-1050)

```python
# Auto-generate metadata if missing (self-healing system)
if item_id not in product_metadata:
    print(f"[AUTO-METADATA] Generating metadata for item {item_id}")
    
    # Parse excise info from QuickBooks Description
    # Auto-populate rate/rule from T125 reference
    # Create and save metadata
    
    metadata = {
        'HasExcise': has_excise,
        'ExciseDutyCode': excise_code,
        'ExciseRate': get_excise_rate(excise_code),  # From T125
        'ExciseRule': get_excise_rule(excise_code),  # From T125
        ...
    }
    
    product_metadata[item_id] = metadata
    save_product_metadata(product_metadata)
```

**Function: `sync_products_to_efris`** (Lines ~850-920)

```python
# Always save metadata after product sync
save_product_metadata(product_metadata)
print(f"[METADATA] Saved {len(product_metadata)} entries to disk")
```

---

## 📖 Related Documentation

- **[EXCISE_RATE_AUTO_POPULATION.md](EXCISE_RATE_AUTO_POPULATION.md)** - T125 reference system
- **[AES_KEY_CACHING.md](AES_KEY_CACHING.md)** - Key caching system
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[API_ENDPOINTS_GUIDE.md](API_ENDPOINTS_GUIDE.md)** - API endpoints

---

## ✨ Summary

**Auto-healing metadata system eliminates manual steps and prevents common EFRIS errors.**

Key features:
- ✅ Automatic metadata generation when missing
- ✅ Auto-population from T125 excise reference
- ✅ Self-healing on invoice sync
- ✅ Comprehensive error prevention
- ✅ Detailed audit logs

**Just sync invoices from the dashboard - the system handles the rest!**
