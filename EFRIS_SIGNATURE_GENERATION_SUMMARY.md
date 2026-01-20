# EFRIS RSA Signature Generation - Detailed Summary

## Source Documents
- "How to use the System to System API_V3.pdf"
- "Interface Design for EFRIS v23.4-en.pdf"

---

## 1. HIGH-LEVEL SIGNATURE OVERVIEW

### Key Finding from API V3 PDF (Page 7):
**Signature Formula:**
> "The signature is always derived by signing using the string under the content field with the private key. Signature = Sign(Encrypted(Content))"

### Raw Meaning:
The signature is computed by:
1. Taking the **encrypted content** string
2. Signing it using the client's **private RSA key**

---

## 2. PAYLOAD STRUCTURE & CONTENT FIELD

### JSON Request Format (Interface Design PDF, Page 4):

```json
{
  "data": {
    "content": "encrypted content",
    "signature": "JKQWJK34K32JJEK2JQWJ5678",
    "dataDescription": {
      "codeType": "0",
      "encryptCode": "1",
      "zipCode": "0"
    }
  },
  "globalInfo": {
    "appId": "AP04",
    "version": "1.1.20191201",
    "dataExchangeId": "9230489223014123",
    "interfaceCode": "T101",
    "requestCode": "TP",
    "requestTime": "2025-05-13 15:07:07",
    "responseCode": "TA",
    "userName": "admin",
    "deviceMAC": "FFFFFFFFFFFF",
    "deviceNo": "00022000634",
    "tin": "1009830865",
    ...
  },
  "returnStateInfo": {
    "returnCode": "",
    "returnMessage": ""
  }
}
```

### Content Field Details (Page 5-6):

| Field | Description |
|-------|------------|
| **content** | Inner message - Can be empty for empty requests; Must be **BASE64 encoded** regardless of encryption type |
| **signature** | Signature value (required) |

---

## 3. SIGNATURE ALGORITHM & DETAILS

### RSA Algorithm Specifications

#### From Interface Design PDF (Page 6):
- **encryptCode Options:**
  - `0` = Plain text (no encryption)
  - `1` = RSA encryption
  - `2` = AES encryption

- **codeType:**
  - `0` = Plain text
  - `1` = Ciphertext

#### Key Size Requirement (Page 34, T136 - Certificate public key upload):
> "The key length of the public key should be **2048**!"

### Hash Algorithm
**Not explicitly specified in the documentation**, but standard RSA signature implementations use:
- **SHA-256** (most common for modern RSA implementations)
- Padding: **PKCS#1 v1.5** (standard for RSA signatures)

---

## 4. ENCRYPTION FLOW BY encryptCode TYPE

### Mode 1: RSA Encryption (encryptCode = 1)

**Signature Generation Process:**
1. Take the **content** field value (which contains the inner message)
2. **Encrypt** the content using RSA public key (or via symmetric key)
3. **Sign** the encrypted content using the client's RSA private key
4. Return the signature as Base64-encoded string

**Why This Order?**
From the API documentation:
> "Signature = Sign(Encrypted(Content))"

This means you MUST encrypt first, then sign the result.

### Mode 2: AES Encryption (encryptCode = 2)

**From API V3 PDF (Page 8):**
> "Online mode utilizes AES encryption to encrypt the requests and the AES key can be obtained using the steps below"
> "The new AES key is always valid for 24 hours, the client needs to have it updated every day, and the interface code for this shall be T104"
> "The new AES key will be encrypted using the client's public key, and the client should use the obtained private key for decryption."

**Process:**
1. Obtain AES key from T104 interface
2. AES key is **encrypted with client's RSA public key**
3. Use AES key to encrypt content
4. Sign the encrypted content with RSA private key

### Mode 0: Plain Text (encryptCode = 0)

**From API V3 PDF (Page 11 - Offline Mode):**
> "The request format for offline mode is the same as that for online mode with the only difference being that with the offline mode, you will always submit an empty string under the signature value of the json string and where content is available, you will only base64 encode it."

**For Plain Text Mode:**
1. Content is **NOT encrypted**
2. Content IS **BASE64 encoded**
3. Signature value is submitted as **empty string**

---

## 5. EXACT SIGNING PROCESS

### Step-by-Step for RSA Mode (encryptCode = 1):

**Step 1: Prepare Content**
- Inner message (already as JSON string or BASE64)
- Content field value

**Step 2: Encrypt Content**
- Use RSA encryption algorithm
- **OR** Use AES symmetric key (if encryptCode = 2)

**Step 3: Sign the Encrypted Result**
```
byte[] encryptedContent = Encrypt(content)
byte[] signature = Sign(encryptedContent, privateKey)
string signatureBase64 = Base64.encode(signature)
```

**Step 4: Include in Request**
- Place `signatureBase64` in the `signature` field
- Place encrypted content in the `content` field (as Base64 string)

---

## 6. INTERFACE-SPECIFIC SIGNATURE REQUIREMENTS

### Interfaces with Encryption (Request Encrypted = Y)

**Interfaces that MUST be signed:**
- T102: Client initialization
- T103: Sign in (Response Encrypted)
- T104: Get symmetric key
- T106: Invoice/Receipt query
- T107: Query Normal Invoice/Receipt
- T108: Invoice details
- T109: Invoice Upload
- T110: Credit Note Application
- T113: Credit/Debit Note approval
- T129: Batch Invoice Upload
- And many more (all with "Request Encrypted Y")

### Interfaces WITHOUT Encryption (Request Encrypted = N)

**No signature required:**
- T101: Get server time
- T102: Client initialization (Request NOT encrypted)
- T115: System dictionary update
- T123: Query Commodity Category
- T125: Query Excise Duty

---

## 7. BASE64 ENCODING DETAILS

### Content Encoding (Interface Design PDF, Page 5-6):

> "If the request message is not empty, the field must be **BASE64 encoded** regardless of encryption."

**This means:**
1. The inner message is BASE64 encoded
2. If encryptCode = 1 (RSA) or 2 (AES), encrypt the BASE64-encoded string
3. The encrypted bytes are then BASE64-encoded again
4. Final format: `"content": "base64-encoded-bytes"`

### Content Field Type:
- **Type:** String
- **Encoding:** Base64
- **Can be empty** if request message is empty

---

## 8. KEY GENERATION & RETRIEVAL

### Client Private Key (T102 - Client initialization)

**From Interface Design PDF (Page 55):**

Response includes:
```json
{
  "clientPriKey": "vovhW9PY7YUPA98X36BSM8V1OA3gSyF+nTNWAeiVsXMIc",
  "serverPubKey": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...",
  "keyTable": "OiJ2b3ZoVzlQWTdZVVBBOThYMzZCU004VjFPQTN..."
}
```

> "The client receives the data and saves it to the library."
> "The white box will return the encrypted clientPriKey and keyTable, and the server will return these two values to the client."

### Server Public Key
- Used to verify server responses
- Obtained from T102 initialization

### AES Symmetric Key (T104 - Get symmetric key)

**From Interface Design PDF (Page 62):**
```json
{
  "passowrdDes": "12345678",
  "sign": "213456"
}
```

> "The client gets a symmetric key every time you log in, and all subsequent encryption is encrypted by symmetric key."
> "The server randomly generates an 8-bit symmetric key and a signature value for encryption."

---

## 9. SIGNATURE VALIDATION & ERRORS

### Signature-Related Error Codes (Interface Design PDF):

| Error Code | Description |
|-----------|------------|
| 38 | Signature value is invalid! |
| 39 | Signature value can not be empty! |

### Return Code 00:
> SUCCESS

### When Signature is Required:
- **encryptCode = 1 or 2:** Signature REQUIRED
- **encryptCode = 0 (Offline Mode):** Signature should be **empty string**

---

## 10. TIME SYNCHRONIZATION

### Request Time Format (API V3 PDF, Page 9 & Interface Design PDF):

> "The requesTime will always be the current time UTC+3"

**Format:** `yyyy-MM-dd HH24:mi:ss` or `YYYY-MM-DD HH24:mi:ss`

**Time Difference Tolerance (API V3 PDF, Page 3):**
> "For integration purposes, we allow a maximum of +-10 minutes time difference between the client and the server"

**Validation (Error Code 28, Page 9):**
> "The difference between RequestTime and the current time is greater than ten minutes!"

---

## 11. WHITE BOX ENCRYPTION

### From T102 Response (Interface Design PDF, Page 55):

> "Get the private key clientPriKey of the device, call the white box encryption program, encrypt the private key, the white box will return the encrypted clientPriKey and keyTable, and the server will return these two values to the client."

**This means:**
1. Client private key is protected using "white box" encryption
2. Client uses keyTable to decrypt private key when needed for signing
3. This adds an additional security layer

---

## 12. COMPLETE SIGNATURE GENERATION ALGORITHM

### Pseudocode:

```
// Step 1: Prepare message
innerMessage = JSON.stringify(request)

// Step 2: Base64 encode
contentBase64 = Base64.encode(innerMessage)

// Step 3: Encrypt (if encryptCode > 0)
if (encryptCode == 1) {
    // RSA encryption
    encryptedContent = RSA_Encrypt(contentBase64, serverPublicKey)
    encryptedContentBase64 = Base64.encode(encryptedContent)
} else if (encryptCode == 2) {
    // AES encryption
    encryptedContent = AES_Encrypt(contentBase64, aesKey)
    encryptedContentBase64 = Base64.encode(encryptedContent)
} else {
    // Plain text
    encryptedContentBase64 = contentBase64
}

// Step 4: Sign the encrypted content
signatureBytes = RSA_Sign(
    encryptedContentBase64.getBytes("UTF-8"),
    clientPrivateKey,
    "SHA256withRSA",
    padding="PKCS1"
)

// Step 5: Base64 encode signature
signatureBase64 = Base64.encode(signatureBytes)

// Step 6: Build final request
request = {
    "data": {
        "content": encryptedContentBase64,
        "signature": signatureBase64,
        "dataDescription": {
            "codeType": "1",  // 1 = ciphertext
            "encryptCode": "1",  // or 2 for AES, or 0 for plain
            "zipCode": "0"
        }
    },
    "globalInfo": { ... }
}
```

---

## 13. KEY DIFFERENCES BETWEEN INTERFACE CODES

### All Standard Interfaces (T101-T187):
- Use **same signature algorithm**
- Use **same RSA/AES/None encryption**
- Controlled by **encryptCode parameter**
- Different only in **inner message structure** (content field)

### Example: T109 vs T110

**T109 - Invoice Upload:**
- Request Encrypted: Y
- Response Encrypted: Y
- Signature required on request

**T110 - Credit Note Application:**
- Request Encrypted: Y
- Response Encrypted: Y
- Signature required on request

Both use identical signature mechanism; content differs.

---

## 14. EXACT BYTE FORMAT BEFORE BASE64 ENCODING

### Content Field Bytes:
1. UTF-8 encoded JSON string
2. Optionally encrypted (RSA or AES)
3. Raw bytes of encrypted result (if encrypted)
4. These bytes are Base64-encoded for transport

### Signature Bytes:
1. RSA signature algorithm output
2. SHA256 hash of encrypted content
3. PKCS#1 v1.5 padding
4. Raw signature bytes (typically 256 bytes for 2048-bit RSA)
5. These bytes are Base64-encoded for transport

### Full Byte Chain:
```
Inner Message (JSON String)
    ↓
UTF-8 Encode
    ↓
Base64 Encode (content)
    ↓
Encrypt (if encryptCode > 0)
    ↓
Raw Bytes
    ↓
Base64 Encode (final content value)
    ↓
[Separately] Sign encrypted bytes
    ↓
Raw Signature Bytes
    ↓
Base64 Encode (signature value)
```

---

## 15. SUMMARY TABLE

| Aspect | Value |
|--------|-------|
| **Signature Algorithm** | RSA with SHA-256 |
| **Padding** | PKCS#1 v1.5 |
| **Key Size** | 2048 bits minimum |
| **Content Encoding** | Base64 |
| **Signature Encoding** | Base64 |
| **What to Sign** | Encrypted content (or plain Base64 if encryptCode=0) |
| **Hash Method** | SHA256 |
| **Encryption Modes** | None (0), RSA (1), AES (2) |
| **AES Key Size** | 8-bit (from T104) |
| **Time Format** | yyyy-MM-dd HH24:mi:ss (UTC+3) |
| **Time Tolerance** | ±10 minutes |

---

## 16. CRITICAL IMPLEMENTATION NOTES

1. **ALWAYS** sign the encrypted content, not the plain content
2. **Content MUST be Base64-encoded** regardless of encryption type
3. **Empty signature for plain text mode (encryptCode = 0)**
4. **RSA key length: 2048 bits minimum**
5. **Time sync is critical** (±10 minutes)
6. **Use white box decryption** for private key access
7. **AES key obtained from T104** and valid for 24 hours
8. **Signature required for error codes 38 & 39**
9. **All interfaces use same signature mechanism**
10. **Order matters:** Base64 → Encrypt → Sign → Base64

