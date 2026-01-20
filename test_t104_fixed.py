#!/usr/bin/env python3
"""Test T104 key exchange with corrected response parsing"""

from efris_client import EfrisManager

def test_t104():
    print("=" * 80)
    print("T104 KEY EXCHANGE TEST - FIXED RESPONSE PARSING")
    print("=" * 80)
    
    try:
        # Initialize manager in test mode
        manager = EfrisManager(
            tin="1014409555",
            test_mode=True,
            cert_path="keys/wandera.pfx"
        )
        print("[STEP 1] Manager initialized ✓")
        
        # Perform key exchange
        manager._key_exchange()
        print("[STEP 2] T104 Key exchange completed ✓")
        
        # Verify AES key was obtained
        if manager.aes_key:
            print(f"[STEP 3] AES Key obtained ✓")
            print(f"         - AES key length: {len(manager.aes_key)} bytes")
            print(f"         - Expected: 16 bytes (128-bit)")
            print(f"         - Match: {len(manager.aes_key) == 16}")
            
            import binascii
            print(f"         - AES key (hex): {binascii.hexlify(manager.aes_key).decode()}")
        else:
            print("[STEP 3] ERROR: AES key is None ✗")
            return False
        
        if manager.server_sign:
            print(f"[STEP 4] Server signature obtained ✓")
            print(f"         - Signature length: {len(manager.server_sign)}")
        else:
            print("[STEP 4] ERROR: Server signature is None ✗")
            return False
        
        print()
        print("=" * 80)
        print("SUCCESS! T104 key exchange working correctly")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_t104()
    exit(0 if success else 1)
