# Product Code Fix - EFRIS Registration

## 🎯 Problem Identified

EFRIS was rejecting duplicate product registrations because the code was using **UNSPC/Category Code** as the **Product Code** (goodsCode).

### The Issue:
- Multiple products can share the same **category code** (e.g., Tororo Cement and Kampala Cement both use UNSPC code `30111601` for cement)
- When registering Tororo Cement, it succeeds
- When registering Kampala Cement, EFRIS returns "Product already exists" error
- This happens because both products were being sent with the same `goodsCode` (the shared category code)

## ✅ Solution Implemented

### Key Concepts:
1. **Product Code (goodsCode)**: Must be **UNIQUE** for each product
2. **Category Code (commodityCategoryId/SKU)**: Can be **SHARED** across products in the same category

### Changes Made:

#### 1. QuickBooks Field Mapping
| QuickBooks Field | EFRIS Field | Purpose |
|------------------|-------------|---------|
| **Description** | `goodsCode` | Unique product identifier |
| **SKU** | `commodityCategoryId` | UNSPC/category code (can be shared) |
| **Name** | `goodsName` | Product display name |

#### 2. Fallback Logic
If QuickBooks `Description` is empty:
- Use `Name` as the `goodsCode`
- This ensures every product has a unique identifier

#### 3. Files Modified

**quickbooks_efris_mapper.py**:
```python
# Use Description as goodsCode (unique product code), fallback to Name
goods_code = qb_item.get('Description') or qb_item.get('Name', '')

product = {
    "goodsCode": goods_code,  # Unique product code
    "commodityCategoryId": qb_item.get('Sku'),  # Category code (shared)
    "goodsName": qb_item.get('Name')
}
```

**api_app.py** (Product Sync):
```python
# Use Description (product code) if available, otherwise use Name
goods_code = item.get('ProductCode') or item.get('Description') or item.get('Name', '')
```

**api_app.py** (Stock Increase Sync):
```python
# Enrich with ProductCode from QuickBooks Description field
product_code = item.get('Description') or item.get('Name', '')
item_ref['productCode'] = product_code
```

**static/dashboard.html**:
- Added **Product Code** field in edit modal
- Placed before Category Code (SKU) field
- Auto-populates from QuickBooks Description
- Saves to both `ProductCode` and `Description` fields

## 📝 How to Use

### Option 1: Set Product Codes in QuickBooks
1. Open QuickBooks
2. Go to Products & Services
3. Edit each product
4. Set the **Description** field to a unique code (e.g., "TOR-CEM-001" for Tororo Cement)
5. Set the **SKU** field to the UNSPC category code (e.g., "30111601" for cement)

### Option 2: Edit in Dashboard
1. Open the EFRIS Dashboard
2. Select a product and click **Edit**
3. Enter a unique **Product Code** (will be saved to Description in QuickBooks)
4. Enter the **Category Code (SKU)** (UNSPC code like 30111601)
5. Save changes

## 🔍 Example

### Tororo Cement:
```json
{
  "goodsCode": "TOR-CEM-001",           // Unique product code
  "goodsName": "Tororo Cement",         // Display name
  "commodityCategoryId": "30111601"     // UNSPC cement category
}
```

### Kampala Cement:
```json
{
  "goodsCode": "KAM-CEM-001",           // Different unique code
  "goodsName": "Kampala Cement",        // Different name
  "commodityCategoryId": "30111601"     // Same category code (OK!)
}
```

Both can now be registered successfully because they have unique `goodsCode` values!

## ✨ Benefits

1. **No More Duplicate Errors**: Each product has a unique identifier
2. **Proper Categorization**: Products can share category codes
3. **Flexible Naming**: Product code can be anything (descriptive or sequential)
4. **QuickBooks Compatible**: Uses standard Description field
5. **Dashboard Support**: Easy editing without switching to QuickBooks

## 🚀 Testing

1. Restart the server: `py api_app.py`
2. Load products from QuickBooks
3. Edit products to set unique Product Codes
4. Sync to EFRIS
5. Verify no duplicate errors

## 📊 Before vs After

| Scenario | Before | After |
|----------|--------|-------|
| Tororo Cement | goodsCode: "30111601" | goodsCode: "TOR-CEM-001" |
| Kampala Cement | goodsCode: "30111601" ❌ DUPLICATE | goodsCode: "KAM-CEM-001" ✅ UNIQUE |
| Stock Increase | Uses QuickBooks ID | Uses product code from Description |

---

**Status**: ✅ Fixed and Ready for Testing

The system now correctly distinguishes between **Product Code** (unique per product) and **Category Code** (shared across products in same category).
