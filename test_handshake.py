#!/usr/bin/env python3
"""Test complete EFRIS handshake sequence"""

from efris_client import EfrisManager

def test_handshake():
    print("=" * 80)
    print("EFRIS HANDSHAKE SEQUENCE TEST")
    print("=" * 80)
    print()
    
    try:
        # Initialize manager in test mode
        manager = EfrisManager(
            tin="1014409555",
            test_mode=True,
            cert_path="keys/wandera.pfx"
        )
        print("[STEP 1] Manager initialized ✓")
        print()
        
        # Perform complete handshake
        print("[HANDSHAKE] Starting handshake sequence...")
        manager.perform_handshake()
        print("[HANDSHAKE] Complete! ✓")
        print()
        
        # Verify results
        print("[VERIFICATION]")
        if manager.aes_key:
            print(f"  ✓ AES Key obtained: {len(manager.aes_key)} bytes")
        else:
            print(f"  ✗ AES Key is None")
            return False
        
        if manager.server_sign:
            print(f"  ✓ Server signature: {len(manager.server_sign)} chars")
        else:
            print(f"  ✗ Server signature is None")
            return False
        
        if manager.registration_details:
            print(f"  ✓ Registration details obtained: {len(manager.registration_details)} fields")
            for key in list(manager.registration_details.keys())[:3]:
                print(f"      - {key}")
        else:
            print(f"  ✗ Registration details is empty")
        
        print()
        print("=" * 80)
        print("SUCCESS! Complete handshake working")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_handshake()
    exit(0 if success else 1)
