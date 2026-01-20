#!/usr/bin/env python3
"""Try different decryption approaches for T103"""

import base64
from efris_client import EfrisManager
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as sym_padding
import json

def try_decrypt_with_key(aes_key, encrypted_bytes, mode_name, **mode_kwargs):
    """Try to decrypt with given parameters"""
    try:
        cipher = Cipher(
            algorithms.AES(aes_key),
            mode_kwargs['mode'](aes_key) if mode_name == "ECB" else mode_kwargs['mode'],
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        # Try to remove PKCS7 padding
        unpadder = sym_padding.PKCS7(128).unpadder()
        plain = unpadder.update(decrypted) + unpadder.finalize()
        
        result = plain.decode('utf-8', errors='ignore')
        return True, result
    except Exception as e:
        return False, str(e)

manager = EfrisManager(
    tin="1014409555",
    test_mode=True,
    cert_path="keys/wandera.pfx"
)

# Do T101 and T104 first
manager._time_sync()
manager._key_exchange()
print(f"AES key: {manager.aes_key.hex()}")
print()

# Get T103 response
payload = manager._build_handshake_payload("T103", "")
response = manager.session.post(manager.base_url, json=payload, headers=manager._get_headers())
data = response.json()

encrypted_content_b64 = data['data']['content']
encrypted_bytes = base64.b64decode(encrypted_content_b64)

print("=" * 80)
print("TRYING DIFFERENT DECRYPTION APPROACHES")
print("=" * 80)
print(f"Encrypted data size: {len(encrypted_bytes)} bytes")
print(f"First 32 bytes (hex): {encrypted_bytes[:32].hex()}")
print()

# Approach 1: ECB mode (no IV)
print("[Approach 1] ECB mode (no IV)...")
success, result = try_decrypt_with_key(
    manager.aes_key,
    encrypted_bytes,
    "ECB",
    mode=modes.ECB()
)
if success:
    print("SUCCESS!")
    print(f"Decrypted (first 200 chars): {result[:200]}")
    # Try to parse as JSON
    try:
        json_data = json.loads(result)
        print(f"Parsed as JSON - keys: {list(json_data.keys())[:5]}")
    except:
        print("Not valid JSON")
else:
    print(f"FAILED: {result}")
print()

# Approach 2: CBC with known IV
print("[Approach 2] CBC with specific IV from server...")
# Maybe the server uses the signature as IV? Or a static IV?
# Try the server signature's first 16 bytes
server_sig = data['data']['signature']
sig_bytes = base64.b64decode(server_sig)[:16]
print(f"Using server signature's first 16 bytes as IV: {sig_bytes.hex()}")
try:
    cipher = Cipher(
        algorithms.AES(manager.aes_key),
        modes.CBC(sig_bytes),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()
    
    unpadder = sym_padding.PKCS7(128).unpadder()
    plain = unpadder.update(decrypted) + unpadder.finalize()
    result = plain.decode('utf-8')
    
    print("SUCCESS!")
    print(f"Decrypted (first 200 chars): {result[:200]}")
except Exception as e:
    print(f"FAILED: {e}")
