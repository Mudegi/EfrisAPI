# T104 Interface Implementation Summary

## Overview
Implemented the complete T104 (Obtaining Symmetric Key and Signature) interface according to EFRIS documentation. This enables secure communication with the EFRIS server using:
1. RSA encryption/decryption with certificates
2. AES symmetric encryption for data payload
3. Digital signatures for authentication

## Implementation Details

### 1. **T104 Key Exchange (`_key_exchange` method)**
The method performs the following steps:

```
Client → Server (T104 request with no payload)
Server → Client (response with passwordDes and sign)
```

**Response Structure:**
```json
{
  "passwordDes": "RSA_encrypted_AES_key_base64",
  "sign": "signature_value"
}
```

**Processing Steps:**
1. Base64 decode `passwordDes`
2. RSA decrypt using private key to obtain AES key
3. Store AES key for all subsequent data encryption

**Code:**
```python
def _key_exchange(self):
    # Call T104
    # Extract passwordDes and decrypt with private key
    password_des_encrypted = base64.b64decode(password_des_b64)
    self.aes_key = self.private_key.decrypt(
        password_des_encrypted,
        padding.PKCS1v15()
    )
```

### 2. **RSA Signing (`_sign` method)**
Implements RSA signature generation as per documentation:

**Algorithm:** RSA with SHA256 hash and PKCS1v15 padding

**Steps:**
1. Hash content with SHA256
2. Sign with private key using PKCS1v15 padding
3. Base64 encode the signature

**Code:**
```python
def _sign(self, data_str):
    signature = self.private_key.sign(
        data_bytes,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')
```

### 3. **AES Encryption (`_encrypt_aes` method)**
Implements AES-128-CBC encryption for request content:

**Steps:**
1. Generate random 16-byte IV
2. Encrypt plain text using AES-128-CBC
3. Apply PKCS7 padding
4. Prepend IV to encrypted data
5. Base64 encode the result

**Code:**
```python
def _encrypt_aes(self, plain_text):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), ...)
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(iv + encrypted).decode()
```

### 4. **Request Payload Building (`_build_request_payload` method)**

Implements the complete encryption and signing flow:

**For encrypt_code = 0 (No encryption):**
- Content sent as plain JSON
- RSA sign the plain content

**For encrypt_code = 1 (RSA sign only):**
- Content sent as plain JSON
- RSA sign the content

**For encrypt_code = 2 (AES + RSA sign):**
1. Encrypt plain JSON with AES key
2. Base64 encode encrypted content
3. RSA sign the encrypted content
4. Add both to request

**Request Structure:**
```json
{
  "data": {
    "content": "base64_encoded_encrypted_or_plain_json",
    "signature": "rsa_signature_of_content",
    "dataDescription": {
      "codeType": "0",
      "encryptCode": "0|1|2",
      "zipCode": "0"
    }
  },
  "globalInfo": { /* metadata */ },
  "returnStateInfo": {}
}
```

### 5. **Handshake Flow (`perform_handshake` method)**

Complete initialization sequence before making API calls:

```
1. _time_sync()       → Call T101 for time synchronization
2. _key_exchange()    → Call T104 to get AES key
3. _get_parameters()  → Call T103 to get registration details
```

## Usage Example

```python
# Initialize manager
manager = EfrisManager(tin='1014409555', test_mode=True)

# Perform mandatory handshake to get AES key
manager.perform_handshake()

# Now encrypt_code=2 methods will work
invoice_data = {
    "tin": "1014409555",
    "items": [...],
    "totalAmount": 118000
}

# Generates invoice with AES encryption and RSA signature
response = manager.generate_invoice(invoice_data)
```

## File Changes

### Modified: `efris_client.py`

**New/Updated Methods:**
1. `_key_exchange()` - Enhanced with RSA decryption of passwordDes
2. `_sign()` - Improved error handling and documentation
3. `_encrypt_aes()` - Added validation and documentation
4. `_build_request_payload()` - Added proper encrypt_code handling
5. `_decrypt_aes()` - Already implemented, used for response decryption
6. `generate_invoice()` - Now uses proper AES encryption with T109

**New Attributes:**
- `self.aes_key` - Stores AES key obtained from T104
- `self.server_sign` - Stores server signature from T104 response

### New: `test_t104_encryption.py`

Comprehensive test suite demonstrating:
- T104 key exchange
- AES encryption with T104 key
- RSA signing of encrypted content
- Complete request payload building

## Security Flow Diagram

```
┌─────────────────┐
│   Client Init   │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│  Call T104       │◄─────────────────────┐
│ (key exchange)   │                      │
└────────┬─────────┘                      │
         │                                │
         ▼                                │
┌──────────────────────────┐              │
│ Receive passwordDes      │              │
│ (RSA encrypted AES key)  │              │
└────────┬─────────────────┘              │
         │                                │
         ▼                                │
┌──────────────────────────┐              │
│ RSA Decrypt with         │              │
│ private key              │              │
└────────┬─────────────────┘              │
         │                                │
         ▼                                │
┌──────────────────────────┐              │
│ Store AES Key            │              │
│ (for all future requests)│              │
└────────┬─────────────────┘              │
         │                                │
         ▼                                │
┌──────────────────────────┐              │
│ For each API call:       │              │
│ 1. JSON encode data      │              │
│ 2. AES encrypt           │              │
│ 3. Base64 encode         │              │
│ 4. RSA sign encrypted    │              │
│ 5. Send request          │              │
└──────────────────────────┘              │
         │                                │
         └────────────────────────────────┘
              (repeat as needed)
```

## Compliance

✓ Implements all documented T104 flow steps
✓ Proper AES-128-CBC with PKCS7 padding
✓ RSA signatures with SHA256 and PKCS1v15
✓ Base64 encoding for binary data
✓ Proper error handling and validation
✓ Certificate loading from PKCS12 format

## Testing

Run the test suite:
```bash
python test_t104_encryption.py
```

This tests:
- T104 key exchange
- AES encryption
- RSA signing
- Complete request payload building
