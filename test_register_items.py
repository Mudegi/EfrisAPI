"""
Test script to register QB items to EFRIS
"""
import requests
import json

API_BASE = "http://localhost:8001"

def login():
    """Login to get auth token"""
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        data={
            "username": "admin@wandera.com",
            "password": "Admin2026!"
        }
    )
    
    if response.status_code == 200:
        print("✓ Logged in successfully\n")
        return response.json()['access_token']
    else:
        print(f"✗ Login failed: {response.status_code}")
        return None

def get_pending_items(token, company_id=1):
    """Get pending QB items"""
    response = requests.get(
        f"{API_BASE}/api/companies/{company_id}/qb-items",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        pending = [item for item in data['items'] if item['EfrisStatus'] == 'Pending']
        print(f"✓ Found {len(pending)} pending items to register")
        return pending
    return []

def register_items(token, item_ids, company_id=1):
    """Register items to EFRIS"""
    print(f"\nRegistering {len(item_ids)} item(s) to EFRIS...")
    
    response = requests.post(
        f"{API_BASE}/api/companies/{company_id}/qb-items/register-to-efris",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "item_ids": item_ids,
            "default_category_id": "50202306"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Registration completed!")
        print(f"  Success: {data['success_count']}")
        print(f"  Failed: {data['failed_count']}")
        
        if data['failed_items']:
            print("\nFailed items:")
            for item in data['failed_items']:
                print(f"  - {item['name']}: {item['error']}")
        
        return data
    else:
        print(f"✗ Registration failed: {response.status_code}")
        print(response.text)
        return None

def verify_registration(token, company_id=1):
    """Verify items are now registered"""
    response = requests.get(
        f"{API_BASE}/api/companies/{company_id}/qb-items",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Verification:")
        print(f"  Total items: {data['count']}")
        print(f"  Registered: {data['registered_count']}")
        print(f"  Pending: {data['pending_count']}")

if __name__ == "__main__":
    print("Testing QB Items Registration to EFRIS")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        exit(1)
    
    # Get pending items
    pending_items = get_pending_items(token)
    
    if pending_items:
        # Register first 3 pending items as a test
        test_items = pending_items[:3]
        print(f"\nTest items to register:")
        for item in test_items:
            print(f"  - {item['Name']} (Code: {item.get('Description', 'N/A')})")
        
        item_ids = [item['Id'] for item in test_items]
        result = register_items(token, item_ids)
        
        if result:
            # Verify registration
            verify_registration(token)
    else:
        print("\n⚠ No pending items found. All items are already registered!")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
