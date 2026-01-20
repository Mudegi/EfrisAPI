#!/usr/bin/env python3
"""Analyze T104 AES key"""

import base64
import binascii

# This is the encrypted AES key from T104 response
encrypted_b64 = "Unpm6PzCSNynM/a4+B4nENhk+wJWFcorVy4U8yKpvtoSSgmMFlHEYvTwmkGu0cjc4V13XMwsDsJRxC6zi3w6WXpz1HgujGRjRJSsCwH1pwV6BUtMRMDb2OdjOECs2gWINOuvk0nBGYIm1F/BqpUX2gqtFW41TsHLtMyG3akuSu5xFDGfsfXGJPQk2XeD1Ywr/05Ca2yHg/khuSrIgmvAxtXDl3V5mzhS7NJY2eOMLuGg3SLnIG5cIa1Xj7tX6lf6NSwGUOoB4LND5Y8lcrQQWe86c7r8qqN1/ShDOj2TkKiqKAKJVIHlaYLvbEwAsCqTH8296kTuzqlAXRJon1XSVA=="

print("=" * 80)
print("ANALYZING T104 ENCRYPTED AES KEY")
print("=" * 80)

# Decode from Base64
encrypted_bytes = base64.b64decode(encrypted_b64)
print(f"Encrypted key (Base64): {encrypted_b64[:80]}...")
print(f"Encrypted key (Base64) length: {len(encrypted_b64)}")
print(f"Encrypted key (binary) length: {len(encrypted_bytes)}")
print(f"Encrypted key (hex): {binascii.hexlify(encrypted_bytes).decode()}")
print()

# RSA-2048 produces 256-byte ciphertext
print(f"Expected RSA-2048 ciphertext size: 256 bytes")
print(f"Actual encrypted key size: {len(encrypted_bytes)} bytes")
print()

# Check what we might have gotten from decryption
# The test showed: 'AES key (hex): 794162637561577576592b663864334b6d6f2b7178513d3d'
# Let's decode that
decrypted_hex = "794162637561577576592b663864334b6d6f2b7178513d3d"
decrypted_bytes = binascii.unhexlify(decrypted_hex)
print(f"What we got after 'decryption': {decrypted_bytes}")
print(f"That's: {decrypted_bytes.decode('latin-1')}")
print()

# It looks like we got Base64-encoded data... Let's check
try:
    maybe_b64 = decrypted_bytes.decode('latin-1')
    decoded_again = base64.b64decode(maybe_b64)
    print(f"If that's Base64, decoded: {decoded_again}")
    print(f"Decoded hex: {binascii.hexlify(decoded_again).decode()}")
    print(f"Decoded length: {len(decoded_again)}")
except Exception as e:
    print(f"Not Base64: {e}")
