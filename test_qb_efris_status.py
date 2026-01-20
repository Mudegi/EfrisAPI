"""
Test script to verify QB items EFRIS registration status matching
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
        print(response.text)
        return None

def get_qb_items(token, company_id=1):
    """Get QB items with EFRIS status"""
    response = requests.get(
        f"{API_BASE}/api/companies/{company_id}/qb-items",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved QB items")
        print(f"  Total items: {data['count']}")
        print(f"  Registered in EFRIS: {data.get('registered_count', 0)}")
        print(f"  Pending registration: {data.get('pending_count', 0)}\n")
        
        print("Sample items:")
        for item in data['items'][:5]:
            status_icon = "✓" if item['EfrisStatus'] == 'Registered' else "⚠"
            print(f"  {status_icon} {item['Name'][:30]:30} | Code: {item.get('EfrisProductCode', 'N/A'):15} | Status: {item['EfrisStatus']}")
        
        return data
    else:
        print(f"✗ Failed to get QB items: {response.status_code}")
        print(response.text)
        return None

def get_efris_goods(token, company_id=1):
    """Get EFRIS goods for comparison"""
    response = requests.get(
        f"{API_BASE}/api/companies/{company_id}/efris-goods",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ EFRIS goods in database: {len(data)}")
        if data:
            print("Sample EFRIS product codes:")
            for good in data[:5]:
                print(f"  - {good['goodsCode']}")
        return data
    else:
        print(f"✗ Failed to get EFRIS goods: {response.status_code}")
        return None

if __name__ == "__main__":
    print("Testing QB Items EFRIS Registration Status\n")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        exit(1)
    
    # Get EFRIS goods first to show what's registered
    efris_goods = get_efris_goods(token)
    
    # Get QB items with status
    qb_items = get_qb_items(token)
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
