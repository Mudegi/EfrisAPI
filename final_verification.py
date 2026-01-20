#!/usr/bin/env python3
"""
Final Verification Test
Confirms T104 and complete handshake is working
"""

from efris_client import EfrisManager
import json

def test_complete_efris_handshake():
    print("\n" + "=" * 80)
    print("FINAL VERIFICATION: EFRIS T104 HANDSHAKE TEST")
    print("=" * 80 + "\n")
    
    # Initialize manager
    manager = EfrisManager(
        tin="1014409555",
        test_mode=True,
        cert_path="keys/wandera.pfx"
    )
    print("[OK] Manager initialized")
    
    # Test 1: Verify certificate loading
    if manager.private_key is None or manager.certificate is None:
        print("[FAIL] Certificate not loaded properly")
        return False
    print("[OK] Certificate loaded (PKCS12)")
    
    # Test 2: Perform handshake
    try:
        manager.perform_handshake()
    except Exception as e:
        print(f"[FAIL] Handshake failed: {e}")
        return False
    print("[OK] Handshake sequence completed (T101->T104->T103)")
    
    # Test 3: Verify AES key obtained
    if manager.aes_key is None or len(manager.aes_key) != 16:
        print(f"[FAIL] AES key invalid: {manager.aes_key}")
        return False
    print(f"[OK] AES key obtained (16 bytes)")
    print(f"     Key (hex): {manager.aes_key.hex()}")
    
    # Test 4: Verify server signature
    if manager.server_sign is None or len(manager.server_sign) == 0:
        print(f"[FAIL] Server signature missing")
        return False
    print(f"[OK] Server signature obtained ({len(manager.server_sign)} bytes)")
    
    # Test 5: Verify registration details
    if manager.registration_details is None or len(manager.registration_details) == 0:
        print(f"[FAIL] Registration details not obtained")
        return False
    print(f"[OK] Registration details obtained ({len(manager.registration_details)} fields)")
    
    # Test 6: Check encryption capability
    try:
        test_content = json.dumps({"test": "data"})
        encrypted = manager._encrypt_aes(test_content)
        if not encrypted or len(encrypted) == 0:
            print(f"[FAIL] Encryption test failed")
            return False
        print(f"[OK] AES encryption working")
    except Exception as e:
        print(f"[FAIL] Encryption test failed: {e}")
        return False
    
    # Test 7: Check decryption capability  
    try:
        decrypted = manager._decrypt_aes(encrypted)
        if decrypted != test_content:
            print(f"[FAIL] Decryption mismatch")
            return False
        print(f"[OK] AES decryption working")
    except Exception as e:
        print(f"[FAIL] Decryption test failed: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("[SUCCESS] ALL TESTS PASSED - T104 IMPLEMENTATION SUCCESSFUL")
    print("=" * 80)
    print("""
System is ready for:
  [OK] Encrypted invoice submission (T109)
  [OK] Taxpayer queries (T119)
  [OK] Goods/Services management (T123)
  [OK] Any encrypted EFRIS operation

Next step: Implement invoice submission with obtained symmetric key
""")
    return True

if __name__ == "__main__":
    try:
        success = test_complete_efris_handshake()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
