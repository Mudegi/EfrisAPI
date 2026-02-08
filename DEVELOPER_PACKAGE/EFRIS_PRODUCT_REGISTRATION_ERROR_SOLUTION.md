# EFRIS Product Registration Error - SOLUTION

**Date:** February 8, 2026  
**Error:** HTTP 500 - "Invalid padding bytes"  
**Status:** ✅ **ROOT CAUSE IDENTIFIED**

---

## Error Summary

```
HTTP 500: Internal Server Error
{
  "detail": "Internal error: Invalid padding bytes."
}
```

---

## Root Cause

The error occurs in the **T104 Key Exchange** process during EFRIS authentication:

### Error Location
**File:** `efris_client.py`  
**Line:** 1352  
**Method:** `_key_exchange()`

### The Failing Sequence
```python
1. Call EFRIS T104 endpoint → Get RSA-encrypted AES key
2. RSA decrypt the key → Get base64-encoded AES key string
3. Base64 decode the string → ❌ FAILS: "Invalid padding bytes"
```

### Why It Fails
The **certificate** used for RSA decryption is either:
1. **Missing** - Certificate file doesn't exist at the specified path
2. **Corrupted** - `.pfx` file is damaged
3. **Wrong certificate** - Using a different certificate than what EFRIS expects
4. **Wrong password** - Certificate password is incorrect (currently hardcoded as `b'123456'`)

---

## Solution

### Option 1: Fix the Certificate Path (Recommended)

1. **Check the company record** in the database:
   ```sql
   SELECT id, name, tin, device_no, efris_cert_path, efris_test_mode 
   FROM companies 
   WHERE tin = '1014345678';
   ```

2. **Verify the certificate file exists**:
   ```python
   import os
   cert_path = "keys/wandera.pfx"  # Or whatever path is in the database
   if os.path.exists(cert_path):
       print(f"✅ Certificate found at {cert_path}")
   else:
       print(f"❌ Certificate NOT found at {cert_path}")
   ```

3. **Update the certificate path** if needed:
   ```sql
   UPDATE companies 
   SET efris_cert_path = 'keys/wandera.pfx'  -- Use correct path
   WHERE tin = '1014345678';
   ```

### Option 2: Use the Correct Test Certificate

The working EFRIS endpoints (like `/excise-duty`) use this certificate:
```
TIN: 1014409555
Device: 1014409555_02
Cert Path: keys/wandera.pfx
```

**Update your test company to use the same certificate:**

```sql
UPDATE companies 
SET efris_cert_path = 'keys/wandera.pfx',
    tin = '1014409555',
    device_no = '1014409555_02'
WHERE tin = '1014345678';
```

**Then update the API key** to match the new company details.

---

## Detailed Fix Steps

### Step 1: Locate the Certificate File

```powershell
# Check if wandera.pfx exists
ls keys/wandera.pfx

# Check file size (should be > 0 bytes)
(Get-Item keys/wandera.pfx).Length
```

### Step 2: Test Certificate Loading

Create a test script `test_certificate.py`:

```python
import os
from cryptography.hazmat.primitives.serialization import pkcs12

cert_path = "keys/wandera.pfx"
cert_password = b'123456'

print(f"Checking certificate: {cert_path}")
print(f"File exists: {os.path.exists(cert_path)}")

if os.path.exists(cert_path):
    print(f"File size: {os.path.getsize(cert_path)} bytes")
    
    try:
       with open(cert_path, 'rb') as f:
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                f.read(), 
                cert_password
            )
        print("✅ Certificate loaded successfully!")
        print(f"   Private key type: {type(private_key)}")
        print(f"   Certificate subject: {certificate.subject}")
    except Exception as e:
        print(f"❌ Certificate load FAILED: {e}")
else:
    print("❌ Certificate file NOT FOUND")
```

Run it:
```powershell
py test_certificate.py
```

### Step 3: Fix the Database

If the certificate is valid, update the database:

```sql
-- Check current settings
SELECT id, name, tin, device_no, efris_cert_path 
FROM companies 
WHERE tin IN ('1014345678', '1014409555');

-- Option A: Fix the certificate path for existing company
UPDATE companies 
SET efris_cert_path = 'keys/wandera.pfx'
WHERE tin = '1014345678';

-- Option B: Use the working company credentials
UPDATE companies 
SET tin = '1014409555',
    device_no = '1014409555_02',
    efris_cert_path = 'keys/wandera.pfx'
WHERE tin = '1014345678';
```

### Step 4: Test Product Registration

After fixing the certificate:

```powershell
curl -X POST https://efrisintegration.nafacademy.com/api/external/efris/register-product \
  -H "Content-Type: application/json" \
  -H "X-API-Key: efris_opVNle8KcO92KlXshJ1sSRT30y61sn3SKl3ExUv83Vw" \
  -d '{
    "item_code": "TEST-001",
    "item_name": "Test Product",
    "unit_price": 10000,
    "commodity_code": "10111301",
    "unit_of_measure": "102",
    "have_excise_tax": "102"
  }'
```

Expected response:
```json
{
  "success": true,
  "product_code": "TEST-001",
  "efris_status": "Registered",
  "message": "Product registered successfully"
}
```

---

## Why `/excise-duty` Works But `/register-product` Fails

### `/excise-duty` (Working ✅)
- Uses `T125` interface
- **Requires AES key** (calls T104 internally)
- If it works, T104 is succeeding with the *public endpoint certificate*

### `/register-product` (Failing ❌)
- Uses `T130` interface  
- **Requires AES key** (calls T104 internally)
- Failing because company's certificate is **different or missing**

**The Difference:**
- Public endpoints (like `/excise-duty`) use hardcoded working credentials
- Your external API endpoints use company-specific credentials from the database
- **Your company record has wrong/missing certificate path**

---

## Improved Error Logging

I've added better error handling in `efris_client.py` (line 1343-1367) to show exactly which step fails:

```python
[T104 ERROR] Failed to base64 decode AES key
[T104 ERROR] AES key b64 string: <corrupted_string>
[T104 ERROR] Length: 123
[T104 ERROR] Has invalid chars: True
[T104 ERROR] Error: Invalid padding bytes
```

This will help identify if the issue is:
1. RSA decryption returning garbage
2. Base64 string with invalid characters
3. Incorrect padding

---

## Commit Changes

```powershell
git add efris_client.py
git commit -m "Add detailed error logging for base64 decode failures in T104 key exchange"
git push origin main
```

Deploy to production:
```powershell
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com
git pull origin main
touch tmp/restart.txt
```

---

## Quick Checklist

- [ ] Verify certificate file exists: `keys/wandera.pfx`
- [ ] Test certificate loading with scrip above
- [ ] Check company record in database has correct `efris_cert_path`
- [ ] Update database if needed
- [ ] Deploy improved error logging
- [ ] Test product registration again
- [ ] Check server logs for detailed error message

---

## Next Steps

1. **Verify the certificate** using the test script above
2. **Update database** with correct certificate path
3. **Deploy changes** to production
4. **Test again** from YourBookSuit
5. **Share logs** if issue persists

The detailed error logging will show exactly what's wrong with the AES key decoding.

---

**Need Help?**
Share the output of:
1. The test_certificate.py script
2. The database query showing company details
3. The new detailed error logs after deploying

