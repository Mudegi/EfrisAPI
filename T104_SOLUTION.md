# T104 Key Exchange - SOLUTION SUMMARY

## Problem
The T104 (Obtaining Symmetric Key and Signature) endpoint was not properly decoding and processing the server response, preventing the handshake sequence from completing.

## Root Causes Identified

### 1. Response Structure Mismatch
- **Expected:** `data.passwordDes` field containing encrypted key
- **Actual:** `data.content` field containing Base64-encoded JSON with nested `passowrdDes` (typo in EFRIS)
- **Issue:** The response is wrapped in an additional layer of Base64 encoding

### 2. Encrypted Key Encoding
- **Expected:** RSA decryption yields binary AES key
- **Actual:** RSA decryption yields Base64-encoded AES key string
- **Issue:** Two-stage decoding required: RSA decrypt → decode Base64

### 3. T103 Encryption Mode
- **Expected:** AES-128-CBC with IV prepended
- **Actual:** AES-128-ECB without IV
- **Issue:** EFRIS uses ECB mode for T103 responses instead of CBC

## Solutions Implemented

### 1. T104 Response Parsing
```python
# Decode Base64 wrapper to get nested JSON
content_json_str = base64.b64decode(data['data']['content']).decode('utf-8')
content_json = json.loads(content_json_str)

# Extract the RSA-encrypted key (note typo: passowrdDes not passwordDes)
password_des_b64 = content_json['passowrdDes']
self.server_sign = content_json['sign']
```

### 2. T104 Key Decryption (Two-Stage)
```python
# Stage 1: Base64 decode the RSA ciphertext
password_des_encrypted = base64.b64decode(password_des_b64)

# Stage 2: RSA-2048 decrypt (PKCS1v15 padding)
aes_key_b64_str = self.private_key.decrypt(
    password_des_encrypted,
    padding.PKCS1v15()
).decode('utf-8')

# Stage 3: Base64 decode the result to get the actual AES key
self.aes_key = base64.b64decode(aes_key_b64_str)
```

### 3. T101 Response Decoding
T101 response also uses the wrapped format:
```python
content_json_str = base64.b64decode(data['data']['content']).decode('utf-8')
content_json = json.loads(content_json_str)
server_time_str = content_json['currentTime']
```

### 4. T103 Decryption (ECB Mode)
Added new `_decrypt_aes_ecb()` method for ECB decryption:
```python
def _decrypt_aes_ecb(self, encrypted_text_b64):
    """Decrypt AES-ECB encrypted content (server uses ECB for T103)"""
    encrypted = base64.b64decode(encrypted_text_b64)
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    plain_data = unpadder.update(padded_data) + unpadder.finalize()
    return plain_data.decode()
```

## Test Results

### T104 Isolated Test
```
[T104] Key exchange successful!
       - AES key obtained: 16 bytes
       - Server signature length: 342
```

### Complete Handshake (T101 → T104 → T103)
```
[T101] Time sync successful - server time: 30/12/2025 19:35:17
[T104] Key exchange successful!
       - AES key obtained: 16 bytes
       - Server signature length: 342
[T103] Parameters fetched successfully
       - Fields received: 38
```

## EFRIS Quirks Discovered

1. **Field name typo:** `passowrdDes` instead of `passwordDes`
2. **Double Base64 encoding:** Response content is Base64-encoded JSON containing Base64-encoded key
3. **ECB mode for encryption:** T103 responses use AES-128-ECB instead of CBC
4. **Encrypted key format:** RSA-decrypted key is returned as Base64 string, not binary

## Files Modified

- `efris_client.py`:
  - Updated `_key_exchange()` to properly parse and decrypt T104 response
  - Updated `_time_sync()` to decode T101 response correctly
  - Updated `_get_parameters()` to use AES-ECB decryption
  - Added `_decrypt_aes_ecb()` method for T103 decryption

## Next Steps

Now that the handshake is complete and AES key is obtained, all subsequent requests can:
1. Use the AES key for encryption of outgoing payloads
2. Use the server signature for validation
3. Decrypt incoming responses that use encryptCode=2

All other endpoints (T109, T119, T123, etc.) are now unblocked and can use the established session with the symmetric key.
