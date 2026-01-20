#!/usr/bin/env python3
"""Debug T103 response structure"""

from efris_client import EfrisManager
import json
import base64

def debug_t103():
    print("=" * 80)
    print("DEBUG T103 RESPONSE STRUCTURE")
    print("=" * 80)
    
    try:
        manager = EfrisManager(
            tin="1014409555",
            test_mode=True,
            cert_path="keys/wandera.pfx"
        )
        print("[STEP 1] Manager initialized")
        
        # First do T101 and T104
        print("[STEP 2] Performing T101 and T104...")
        manager._time_sync()
        manager._key_exchange()
        print("         T101 and T104 complete")
        print()
        
        # Build and send T103 request
        payload = manager._build_handshake_payload("T103", "")
        print("[STEP 3] T103 payload built")
        
        response = manager.session.post(manager.base_url, json=payload, headers=manager._get_headers())
        print(f"[STEP 4] Response received: {response.status_code}")
        
        data = response.json()
        print("[STEP 5] Response parsed")
        
        print()
        print("FULL T103 RESPONSE:")
        print("=" * 80)
        print(json.dumps(data, indent=2))
        print("=" * 80)
        print()
        
        # Check data.content
        if 'data' in data and 'content' in data['data']:
            content_b64 = data['data']['content']
            if content_b64:
                print(f"data.content (Base64): {content_b64[:100]}...")
                try:
                    decoded = base64.b64decode(content_b64).decode('utf-8')
                    print(f"data.content (decoded): {decoded[:200]}...")
                    content_json = json.loads(decoded)
                    print(f"data.content (JSON):")
                    print(json.dumps(content_json, indent=2))
                except Exception as e:
                    print(f"Error decoding content: {e}")
            else:
                print("data.content is empty")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_t103()
