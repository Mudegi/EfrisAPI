"""
Test T125 - Query Excise Duty endpoint

This test verifies the T125 endpoint implementation for querying excise duty codes and rates.
"""

from efris_client import EfrisManager
import json

def test_query_excise_duty():
    """Test the T125 Query Excise Duty endpoint"""
    
    print("\n" + "="*80)
    print("Testing T125 - Query Excise Duty")
    print("="*80 + "\n")
    
    # Initialize the EFRIS manager
    manager = EfrisManager(tin='1014409555', test_mode=True)
    print("[TEST] EFRIS Manager initialized")
    
    # Perform handshake to get AES key
    try:
        print("\n[TEST] Performing handshake (T101 + T104 + T103)...")
        manager.perform_handshake()
        print("[TEST] ✓ Handshake successful!")
    except Exception as e:
        print(f"[TEST] ✗ Handshake failed: {e}")
        return
    
    # Test 1: Query all excise duties (no filter)
    print("\n" + "-"*80)
    print("Test 1: Query all excise duties (no filter)")
    print("-"*80)
    
    try:
        result = manager.query_excise_duty()
        print(f"\n[TEST] Response received:")
        print(f"  - Return Code: {result.get('returnStateInfo', {}).get('returnCode')}")
        print(f"  - Return Message: {result.get('returnStateInfo', {}).get('returnMessage')}")
        
        if 'data' in result and 'decrypted_content' in result['data']:
            decrypted = result['data']['decrypted_content']
            print(f"\n[TEST] Decrypted content structure:")
            print(json.dumps(decrypted, indent=2)[:500])
            
            # Check if we have excise duty list
            if isinstance(decrypted, dict):
                if 'exciseDutyList' in decrypted:
                    excise_list = decrypted['exciseDutyList']
                    print(f"\n[TEST] ✓ Found {len(excise_list)} excise duty records")
                    if excise_list:
                        print(f"\n[TEST] Sample record:")
                        print(json.dumps(excise_list[0], indent=2))
                else:
                    print(f"\n[TEST] Decrypted keys: {decrypted.keys()}")
        else:
            print(f"\n[TEST] Raw response:")
            print(json.dumps(result, indent=2)[:1000])
            
    except Exception as e:
        print(f"[TEST] ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Query with excise duty code filter
    print("\n" + "-"*80)
    print("Test 2: Query with excise duty code filter")
    print("-"*80)
    
    try:
        # Try a sample excise duty code (LED codes are common in EFRIS)
        result = manager.query_excise_duty(excise_duty_code="LED190100")
        print(f"\n[TEST] Response for code 'LED190100':")
        print(f"  - Return Code: {result.get('returnStateInfo', {}).get('returnCode')}")
        print(f"  - Return Message: {result.get('returnStateInfo', {}).get('returnMessage')}")
        
        if 'data' in result and 'decrypted_content' in result['data']:
            decrypted = result['data']['decrypted_content']
            print(f"\n[TEST] ✓ Successfully queried specific excise duty code")
            print(json.dumps(decrypted, indent=2)[:500])
        else:
            print(f"\n[TEST] Response:")
            print(json.dumps(result, indent=2)[:500])
            
    except Exception as e:
        print(f"[TEST] Note: Specific code query returned: {e}")
    
    print("\n" + "="*80)
    print("T125 Test Complete")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_query_excise_duty()
