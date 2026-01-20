# ❌ Error 2122: Product Not Registered with URA

## Error Message
```
goodsDetails-->itemCode: Item code and Name is not configured with URA.
Complete the configuration process for this item using your system or from the URA portal to proceed.
```

---

## 🎯 Root Cause

**Error 2122 means the product hasn't been uploaded to EFRIS yet.**

Before you can use a product in invoices, you **must register it with URA** using the **T123 Upload Goods** interface.

---

## ✅ Solution: 2-Step Process

### Step 1: Upload Product to EFRIS ⚠️ **REQUIRED FIRST**

1. **Dashboard → Products Tab**
2. **Find "Tororo Cement"**
3. **Click "Edit Product"**
4. **Verify settings:**
   - ✅ Has Excise Tax: **Checked**
   - ✅ Excise Duty Code: **LED050000 - Cement**
   - ✅ Unit of Measure: **107** (50kgs)
   - ✅ SKU/Category: **30111601** (or your commodity code)
   - ✅ Description: **Building Material | ExciseCode:LED050000 | Unit:107**
5. **Click "Save Changes"**
6. **Wait for success message**

**What happens:**
- System sends T123 request to EFRIS
- Product registered with URA
- EFRIS assigns product ID
- Product now available for invoices

---

### Step 2: Sync Invoice

**Only after Step 1 succeeds:**

1. **Dashboard → Invoices Tab**
2. **Select Invoice 1038**
3. **Click "Sync to EFRIS"**

**Expected:**
- ✅ Auto-metadata generated
- ✅ Product code: "Building Material" (not "Cement:Tororo Cement")
- ✅ Excise rate: 500 (from T125)
- ✅ Excise rule: 2 (from T125)
- ✅ Invoice synced successfully
- ✅ FDN generated

---

## 🔍 What Was Fixed

### Issue 1: Product Code Extraction
**Before:**
- Product code: "Cement:Tororo Cement | ExciseCode:LED050000 | Unit:107" ❌
- Used full Description field as itemCode ❌

**After:**
- Product code: "Building Material" ✅
- Extracts name before first `|` character ✅

### Issue 2: Product Not Registered
**Before:**
- Tried to use product in invoice without uploading to EFRIS ❌

**After:**
- Upload product first via Products tab ✅
- Then use in invoices ✅

---

## 📊 Server Logs - What to Expect

### When Uploading Product (Step 1):
```
[METADATA] Updated metadata for item 20 (Tororo Cement):
  - HasExcise: True
  - ExciseDutyCode: LED050000
  - ExciseRate: 500 (from T125)
  - ExciseRule: 2 (from T125)
  - ProductCode: Building Material
[T123] Uploading product to EFRIS...
✅ Product uploaded successfully
```

### When Syncing Invoice (Step 2):
```
[AUTO-METADATA] Using metadata for item 20
[T109] Processing item: Tororo Cement
[T109] Item code: Building Material
[T109] Has excise: True, Code: LED050000, Rate: 500, Rule: 2
✅ Invoice synced successfully
✅ FDN: xxxxxxxxxxxxx
```

---

## 🚨 Common Mistakes

### ❌ Mistake 1: Skipping Product Upload
```
❌ Dashboard → Invoices → Sync Invoice 1038
Result: Error 2122 (product not registered)
```

### ✅ Correct Flow:
```
✅ Dashboard → Products → Edit Tororo Cement → Save
✅ Wait for success
✅ Dashboard → Invoices → Sync Invoice 1038
Result: Success! FDN generated
```

### ❌ Mistake 2: Wrong Description Format
```
Description: "Cement:Tororo Cement"
Result: itemCode = "Cement:Tororo Cement" (wrong)
```

### ✅ Correct Format:
```
Description: "Building Material | ExciseCode:LED050000 | Unit:107"
Result: itemCode = "Building Material" (correct)
```

---

## 🔧 QuickBooks Product Setup

For excise products, use this format in the **Description** field:

```
ProductName | ExciseCode:LEDXXXXXX | Unit:XXX
```

**Example for Tororo Cement:**
```
Building Material | ExciseCode:LED050000 | Unit:107
```

**What each part does:**
- **Building Material** → Used as itemCode in EFRIS
- **ExciseCode:LED050000** → Auto-detected, excise rate/rule populated from T125
- **Unit:107** → Auto-detected as excise unit (50kgs)

**System automatically:**
- Extracts "Building Material" as product code ✅
- Detects LED050000 and looks up rate=500, rule=2 from T125 ✅
- Sets excise unit to 107 ✅

---

## 📖 Related Documentation

- **[METADATA_AUTO_HEALING.md](METADATA_AUTO_HEALING.md)** - Auto-metadata system
- **[EXCISE_RATE_AUTO_POPULATION.md](EXCISE_RATE_AUTO_POPULATION.md)** - T125 reference
- **[API_ENDPOINTS_GUIDE.md](API_ENDPOINTS_GUIDE.md)** - API endpoints

---

## ✨ Summary

**Error 2122 = Product not registered with URA**

**Fix:**
1. ✅ Upload product via Products tab (T123 Upload Goods)
2. ✅ Then sync invoice (T109 Upload Invoice)

**Product code now correctly extracted:**
- ❌ Old: "Cement:Tororo Cement | ExciseCode:LED050000 | Unit:107"
- ✅ New: "Building Material"

**Server running on port 8001 with fixes applied.**

---

## 🎯 Next Steps

1. **Dashboard → Products → Edit Tororo Cement → Save** ⚠️ **DO THIS FIRST**
2. Wait for success message
3. **Dashboard → Invoices → Sync Invoice 1038**
4. ✅ Should now work!

If you get another error after completing Step 1, check the server logs and share the error message.
