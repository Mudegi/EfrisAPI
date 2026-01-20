"""
Check if a specific item exists in EFRIS
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

def search_efris_goods(token, company_id=1, search_term="BedBugSpr"):
    """Search for goods in EFRIS"""
    print(f"Searching EFRIS for: '{search_term}'")
    print("=" * 60)
    
    response = requests.get(
        f"{API_BASE}/api/companies/{company_id}/efris-goods",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        goods = response.json()
        
        # Handle both list and dict responses
        if isinstance(goods, dict):
            goods = goods.get('goods', [])
        
        print(f"\n✓ Total goods in database: {len(goods)}")
        
        # Search for the specific item
        found_items = [g for g in goods if search_term.lower() in g.get('goods_code', '').lower() or 
                                           search_term.lower() in g.get('goods_name', '').lower()]
        
        if found_items:
            print(f"\n✓ Found {len(found_items)} matching item(s):\n")
            for item in found_items:
                print(f"  ID: {item.get('id')}")
                print(f"  Code: {item.get('goods_code')}")
                print(f"  Name: {item.get('goods_name')}")
                print(f"  Type: {item.get('goods_type_code')}")
                print(f"  Unit: {item.get('measure_unit')}")
                print(f"  Price: {item.get('unit_price')}")
                print(f"  Category: {item.get('commodity_category_code')}")
                print(f"  Service Mark: {item.get('service_mark', 'N/A')}")
                print("-" * 60)
        else:
            print(f"\n✗ Item '{search_term}' NOT FOUND in EFRIS database")
            print("\nLet's check the first few items in the database:")
            for i, item in enumerate(goods[:5], 1):
                print(f"\n{i}. Code: {item.get('goods_code')} | Name: {item.get('goods_name')}")
        
        return found_items
    else:
        print(f"✗ Failed to fetch goods: {response.status_code}")
        print(f"Response: {response.text}")
        return []

def import_fresh_from_efris(token, company_id=1):
    """Import fresh data from EFRIS"""
    print("\n\n" + "=" * 60)
    print("Importing fresh data from EFRIS...")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE}/api/companies/{company_id}/efris-goods/import",
        headers={"Authorization": f"Bearer {token}"},
        json={"page_no": 1, "page_size": 50}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Import successful!")
        print(f"  Imported: {data.get('imported', 0)} items")
        print(f"  Updated: {data.get('updated', 0)} items")
        print(f"  Total: {data.get('total', 0)} items")
        return True
    else:
        print(f"✗ Import failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    print("Checking if 'BedBugSpr' exists in EFRIS")
    print("=" * 60 + "\n")
    
    token = login()
    if not token:
        exit(1)
    
    # First check database
    found = search_efris_goods(token, search_term="BedBugSpr")
    
    if not found:
        # Import fresh from EFRIS
        if import_fresh_from_efris(token):
            print("\n\nSearching again after import...")
            found = search_efris_goods(token, search_term="BedBugSpr")
    
    print("\n" + "=" * 60)
    if found:
        print("✅ CONCLUSION: Item EXISTS in EFRIS")
    else:
        print("❌ CONCLUSION: Item DOES NOT EXIST in EFRIS")
        print("\nThis means the error 602 'goodsCode already exists' is misleading.")
        print("It might be a different validation error from EFRIS.")
    print("=" * 60)
