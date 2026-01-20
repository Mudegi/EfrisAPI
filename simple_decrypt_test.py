#!/usr/bin/env python3
"""Simple T103 decryption test"""

import base64
from efris_client import EfrisManager
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as sym_padding

print("Starting...")

manager = EfrisManager(
    tin="1014409555",
    test_mode=True,
    cert_path="keys/wandera.pfx"
)

print("Manager created")

# Do T101 and T104 first
manager._time_sync()
print("T101 done")

manager._key_exchange()
print(f"T104 done - AES key: {manager.aes_key.hex()}")

# Get T103 response
payload = manager._build_handshake_payload("T103", "")
response = manager.session.post(manager.base_url, json=payload, headers=manager._get_headers())
data = response.json()

encrypted_content_b64 = data['data']['content']
encrypted_bytes = base64.b64decode(encrypted_content_b64)

print(f"Encrypted size: {len(encrypted_bytes)} bytes")

# Try ECB
print("Trying ECB...")
cipher = Cipher(
    algorithms.AES(manager.aes_key),
    modes.ECB(),
    backend=default_backend()
)
decryptor = cipher.decryptor()
decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()

# Check if first few bytes look like JSON
print(f"Decrypted first 50 bytes: {decrypted[:50]}")

# Try removing padding
unpadder = sym_padding.PKCS7(128).unpadder()
try:
    plain = unpadder.update(decrypted) + unpadder.finalize()
    result = plain.decode('utf-8')
    print(f"SUCCESS with ECB!")
    print(f"Result (first 200 chars): {result[:200]}")
except Exception as e:
    print(f"Padding removal failed: {e}")
    # Try without padding removal
    try:
        result = decrypted.decode('utf-8', errors='ignore')
        print(f"Decoded without padding removal: {result[:200]}")
    except Exception as e2:
        print(f"Decoding failed: {e2}")
