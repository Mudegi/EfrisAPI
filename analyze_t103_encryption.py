#!/usr/bin/env python3
"""Analyze T103 encrypted content structure"""

import base64
from efris_client import EfrisManager

def analyze_t103_encryption():
    print("=" * 80)
    print("ANALYZING T103 ENCRYPTED CONTENT")
    print("=" * 80)
    
    manager = EfrisManager(
        tin="1014409555",
        test_mode=True,
        cert_path="keys/wandera.pfx"
    )
    
    # Do T101 and T104 first
    manager._time_sync()
    manager._key_exchange()
    print(f"T104 complete - AES key: {manager.aes_key.hex()}")
    print(f"AES key length: {len(manager.aes_key)}")
    print()
    
    # Get T103 response
    payload = manager._build_handshake_payload("T103", "")
    response = manager.session.post(manager.base_url, json=payload, headers=manager._get_headers())
    data = response.json()
    
    encrypted_content_b64 = data['data']['content']
    encrypted_bytes = base64.b64decode(encrypted_content_b64)
    
    print(f"Encrypted content (Base64 length): {len(encrypted_content_b64)}")
    print(f"Encrypted content (binary length): {len(encrypted_bytes)}")
    print(f"First 20 bytes (hex): {encrypted_bytes[:20].hex()}")
    print()
    
    # Try to decrypt WITHOUT assuming IV prefix
    # The server might not prepend IV to the encrypted data
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding as sym_padding
    
    # Try decrypting assuming NO IV (direct decryption)
    print("Attempting decryption without IV...")
    try:
        # Try each possible IV (0x00...00, random, etc.)
        # First try: IV of all zeros
        zero_iv = b'\x00' * 16
        cipher = Cipher(algorithms.AES(manager.aes_key), modes.CBC(zero_iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        unpadder = sym_padding.PKCS7(128).unpadder()
        plain = unpadder.update(decrypted) + unpadder.finalize()
        
        print(f"SUCCESS with IV=00...00!")
        print(f"Decrypted (first 200 chars): {plain[:200]}")
    except Exception as e:
        print(f"Failed: {e}")
    
    print()
    print("Attempting decryption with IV extracted from first 16 bytes...")
    try:
        # Try: first 16 bytes as IV
        iv = encrypted_bytes[:16]
        ciphertext = encrypted_bytes[16:]
        cipher = Cipher(algorithms.AES(manager.aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(ciphertext) + decryptor.finalize()
        
        unpadder = sym_padding.PKCS7(128).unpadder()
        plain = unpadder.update(decrypted) + unpadder.finalize()
        
        print(f"SUCCESS with IV from first 16 bytes!")
        print(f"IV (hex): {iv.hex()}")
        print(f"Decrypted (first 200 chars): {plain[:200]}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    analyze_t103_encryption()
