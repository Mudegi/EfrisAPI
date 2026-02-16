# EFRIS Integration Debug Instructions

## **Issue Summary**
- **Problem**: Invoice fiscalization failing with EFRIS error `2124: "goodsDetails-->itemCode:Does not match the 'goodsCategoryId'!"`
- **Status**: Product IS correctly registered in EFRIS portal with matching codes
- **Root Cause**: **FOUND AND FIXED** - Field name format mismatch (`goods_category_id` vs `goodsCategoryId`)

## **FIXES APPLIED (February 16, 2026)**

### ✅ Fix 1: Field Name Support
The API now supports ALL these field name formats for goods category:
- `goodsCategoryId` (EFRIS camelCase format)
- `goods_category_id` (snake_case format)
- `commodity_code` (alternative name)
- `commodityCategoryId` (alternative camelCase)

### ✅ Fix 2: Debug Logging Added
The API now logs detailed T109 payload information:
```
[T109 DEBUG] ===== INCOMING INVOICE DATA =====
[T109 DEBUG] Invoice Number: INV-2026-0012
[T109 DEBUG] Items count: 1
[T109 DEBUG] === Processing Item 1 ===
[T109 DEBUG] Raw itemCode: 'HP Pavilion'
[T109 DEBUG] Raw goodsCategoryId: '44102906'
[T109 DEBUG] Final goodsCategoryId: '44102906'
[T109 DEBUG] ===== FINAL GOODS DETAILS =====
[T109 DEBUG] Item 1:
[T109 DEBUG]   item: 'HP Pavilion'
[T109 DEBUG]   itemCode: 'HP Pavilion'
[T109 DEBUG]   goodsCategoryId: '44102906'
```

### ✅ Fix 3: taxRate Normalization
- VAT (`taxCategoryCode: "01"`) auto-corrected to `"0.18"`
- Excise fixed rate auto-corrected to `"0"`

## **DEPLOYMENT REQUIRED**

```bash
# On production server
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com
git pull origin main
touch passenger_wsgi.py
# Wait 60 seconds for Passenger to reload
```

## **After Deployment - Test Again**

1. Submit the same failing invoice (HP Pavilion)
2. Check server logs for `[T109 DEBUG]` entries
3. The logs will show exactly:
   - What values came in from YourBookSuit
   - What values are being sent to EFRIS

## **What We Know**
✅ **YourBookSuit client** sends correct payload:
```json
{
  "item_code": "HP Pavilion",
  "goods_category_id": "44102906"
}
```

✅ **EFRIS portal** shows product registered with:
- Commodity Category: `(44102906) Computer or office equipment`
- My Product Code: `HP Pavilion`

⚠️ **EFRIS API** was rejecting because API looked for `goodsCategoryId` but YourBookSuit sent `goods_category_id`

## **Correct Payload Format**

Your ERP should send items in ONE of these formats:

### Format A: EFRIS camelCase (Recommended)
```json
{
  "items": [
    {
      "item": "HP Pavilion",
      "itemCode": "HP Pavilion",
      "qty": "2",
      "unitOfMeasure": "101",
      "unitPrice": "2500000.00",
      "total": "5000000.00",
      "taxRate": "0.18",
      "tax": "762711.86",
      "orderNumber": "1",
      "discountFlag": "2",
      "deemedFlag": "2",
      "exciseFlag": "2",
      "goodsCategoryId": "44102906",
      "vatApplicableFlag": "1"
    }
  ]
}
```

### Format B: snake_case (Also Supported)
```json
{
  "items": [
    {
      "item_name": "HP Pavilion",
      "item_code": "HP Pavilion",
      "quantity": 2,
      "unit_price": 2500000,
      "tax_rate": 18,
      "goods_category_id": "44102906"
    }
  ]
}
```

## **Critical Rules**

| Field | Requirement |
|-------|-------------|
| `itemCode` | MUST exactly match T130 registration |
| `goodsCategoryId` | MUST exactly match T130 registration |
| `taxRate` | MUST be string `"0.18"` for VAT |
| `discountFlag: "2"` | DON'T send `discountTotal` |

## **If Still Failing After Deployment**

Check server logs for these values:
```
[T109 DEBUG] Raw goodsCategoryId: '???'
[T109 DEBUG] Final goodsCategoryId: '???'
```

If `Raw goodsCategoryId` is `N/A` or empty:
- Your ERP is not sending the field
- Add `goodsCategoryId` or `goods_category_id` to your payload

If `Final goodsCategoryId` is empty but `Raw` had a value:
- The validation cleared it (too long, invalid pattern)
- Check the value format

## **Contact**
Report findings with the debug log output for further analysis.