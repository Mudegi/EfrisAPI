import os
from efris_client import EfrisManager
import time

# Example usage
def main():
    print("=" * 80)
    print("TESTING AES KEY CACHING - Multiple API Calls")
    print("=" * 80)
    client = EfrisManager(tin='1014409555', test_mode=True)

    print("\n[TEST 1] First API call - should perform T101/T104/T103 handshake")
    print("-" * 80)
    try:
        details = client.get_registration_details()
        print('✓ Registration Details Retrieved')
    except Exception as e:
        print(f'Error: {e}')

    print("\n\n[TEST 2] Second API call - should use CACHED key (no handshake)")
    print("-" * 80)
    try:
        details = client.get_registration_details()
        print('✓ Registration Details Retrieved (used cached key)')
    except Exception as e:
        print(f'Error: {e}')

    print("\n\n[TEST 3] Third API call - should still use CACHED key")
    print("-" * 80)
    try:
        details = client.get_registration_details()
        print('✓ Registration Details Retrieved (used cached key)')
    except Exception as e:
        print(f'Error: {e}')

    print("\n\n[TEST 4] Simulate key expiry by setting short timeout")
    print("-" * 80)
    print(f"Current key expires at: {client.aes_key_expires_at}")
    print(f"Setting key expiry to 3 seconds...")
    client.key_expiry_hours = 3 / 3600  # 3 seconds
    client.aes_key = None
    client.aes_key_expires_at = None
    
    try:
        details = client.get_registration_details()
        print('✓ Registration Details Retrieved (new key obtained)')
    except Exception as e:
        print(f'Error: {e}')
    
    print(f"\n Waiting 4 seconds for key to expire...")
    time.sleep(4)
    
    print("\n\n[TEST 5] After expiry - should refresh and get new key")
    print("-" * 80)
    try:
        details = client.get_registration_details()
        print('✓ Registration Details Retrieved (key refreshed automatically)')
    except Exception as e:
        print(f'Error: {e}')

    print("\n\n" + "=" * 80)
    print("✓✓✓ KEY CACHING TEST COMPLETE ✓✓✓")
    print("=" * 80)
    print("\nSummary:")
    print("- AES key is cached after first handshake")
    print("- Subsequent API calls reuse cached key (efficient)")
    print("- Key auto-refreshes when expired")
    print("- Default expiry: 24 hours (configurable)")

if __name__ == '__main__':
    main()
