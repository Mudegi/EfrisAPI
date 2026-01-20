#!/usr/bin/env python3
"""Debug T101 response structure"""

from efris_client import EfrisManager
import json

def debug_t101():
    print("=" * 80)
    print("DEBUG T101 RESPONSE STRUCTURE")
    print("=" * 80)
    
    try:
        manager = EfrisManager(
            tin="1014409555",
            test_mode=True,
            cert_path="keys/wandera.pfx"
        )
        print("[STEP 1] Manager initialized")
        
        # Build and send T101 request
        payload = manager._build_handshake_payload("T101", "")
        print("[STEP 2] T101 payload built")
        
        response = manager.session.post(manager.base_url, json=payload, headers=manager._get_headers())
        print(f"[STEP 3] Response received: {response.status_code}")
        
        data = response.json()
        print("[STEP 4] Response parsed")
        
        print()
        print("FULL T101 RESPONSE:")
        print("=" * 80)
        print(json.dumps(data, indent=2))
        print("=" * 80)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_t101()
