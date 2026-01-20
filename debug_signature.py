#!/usr/bin/env python3
"""
Debug script to test signature generation
"""

import json
from efris_client import EfrisManager

try:
    print("Initializing manager...")
    manager = EfrisManager(tin='1014409555', test_mode=True)
    print(f"✓ Manager initialized")
    print(f"✓ Private key available: {manager.private_key is not None}")
    
    print("\n--- Test T101 Payload ---")
    t101_payload = manager._build_handshake_payload("T101", "")
    print(json.dumps(t101_payload, indent=2)[:500])
    
    print("\n--- Test T103 Payload ---")
    t103_content = json.dumps({"tin": manager.tin}, separators=(',', ':'), sort_keys=True)
    t103_payload = manager._build_handshake_payload("T103", t103_content)
    print(json.dumps(t103_payload, indent=2)[:500])
    
    print("\nDebug complete!")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
