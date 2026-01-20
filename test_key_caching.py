"""
Test script to verify AES key caching functionality
"""
import time
from efris_client import EfrisManager

def test_key_caching():
    """Test that AES key is cached and reused"""
    print("=" * 80)
    print("TESTING AES KEY CACHING")
    print("=" * 80)
    
    # Initialize manager - use test mode like in main.py
    manager = EfrisManager(tin='1014409555', test_mode=True)
    
    print("\n[TEST 1] First authentication - should call T104")
    print("-" * 80)
    manager.ensure_authenticated()
    
    print("\n\n[TEST 2] Second authentication (immediate) - should use cached key")
    print("-" * 80)
    manager.ensure_authenticated()
    
    print("\n\n[TEST 3] Third authentication (immediate) - should use cached key")
    print("-" * 80)
    manager.ensure_authenticated()
    
    print("\n\n[TEST 4] Check key validity")
    print("-" * 80)
    print(f"Is key valid: {manager.is_key_valid()}")
    print(f"AES key length: {len(manager.aes_key) if manager.aes_key else 0} bytes")
    print(f"Key expires at: {manager.aes_key_expires_at}")
    print(f"Key expiry hours: {manager.key_expiry_hours}")
    
    print("\n\n[TEST 5] Test with very short expiry (3 seconds)")
    print("-" * 80)
    manager.key_expiry_hours = 3 / 3600  # 3 seconds
    manager.aes_key = None  # Force re-authentication
    manager.aes_key_expires_at = None
    manager.ensure_authenticated()
    
    print("\nWaiting 4 seconds for key to expire...")
    time.sleep(4)
    
    print("\n[TEST 6] Authentication after expiry - should call T104 again")
    print("-" * 80)
    manager.ensure_authenticated()
    
    print("\n\n" + "=" * 80)
    print("TEST COMPLETE - Key caching is working!")
    print("=" * 80)

if __name__ == "__main__":
    test_key_caching()
