#!/usr/bin/env python3
"""Debug T104 response structure"""

from efris_client import EfrisManager
import json
import base64

def debug_t104():
    print("=" * 80)
    print("DEBUG T104 RESPONSE STRUCTURE")
    print("=" * 80)
    
    try:
        # Initialize manager in test mode
        manager = EfrisManager(
            tin="1014409555",
            test_mode=True,
            cert_path="keys/wandera.pfx"
        )
        print("[STEP 1] Manager initialized")
        
        # Build and send T104 request
        payload = manager._build_handshake_payload("T104", "")
        print("[STEP 2] T104 payload built")
        print(f"         Payload keys: {payload.keys()}")
        
        response = manager.session.post(manager.base_url, json=payload, headers=manager._get_headers())
        print(f"[STEP 3] Response received: {response.status_code}")
        
        data = response.json()
        print("[STEP 4] Response parsed as JSON")
        
        # Print response structure
        print()
        print("RESPONSE STRUCTURE:")
        print("=" * 80)
        print(json.dumps(data, indent=2))
        print("=" * 80)
        print()
        
        # Check data.content
        if 'data' in data and 'content' in data['data']:
            content_b64 = data['data']['content']
            print(f"data.content type: {type(content_b64)}")
            print(f"data.content length: {len(content_b64)}")
            print(f"data.content (first 100 chars): {content_b64[:100]}")
            
            if content_b64:
                try:
                    decoded = base64.b64decode(content_b64).decode('utf-8')
                    print(f"Decoded content: {decoded}")
                    
                    content_json = json.loads(decoded)
                    print(f"Content JSON keys: {content_json.keys()}")
                    print(f"Content JSON: {json.dumps(content_json, indent=2)}")
                except Exception as e:
                    print(f"Error decoding content: {e}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_t104()
