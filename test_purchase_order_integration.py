"""
Test script to verify Purchase Order to EFRIS integration
Run this after importing POs to test the sync functionality
"""
import requests
import json

BASE_URL = "http://localhost:8001"
TOKEN = None  # Will be set after login

def login():
    """Login and get auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": "admin@example.com",
        "password": "admin123"
    })
    if response.status_code == 200:
        data = response.json()
        global TOKEN
        TOKEN = data['access_token']
        print("✓ Login successful")
        return True
    else:
        print(f"✗ Login failed: {response.status_code}")
        return False

def get_companies():
    """Get list of companies"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/api/companies", headers=headers)
    if response.status_code == 200:
        companies = response.json()
        print(f"✓ Found {len(companies)} companies")
        return companies
    else:
        print(f"✗ Failed to get companies: {response.status_code}")
        return []

def import_purchase_orders(company_id):
    """Import purchase orders from QuickBooks"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(
        f"{BASE_URL}/api/companies/{company_id}/qb-purchase-orders/import",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✓ {data['message']}")
        return True
    else:
        print(f"✗ Failed to import POs: {response.status_code} - {response.text}")
        return False

def get_purchase_orders(company_id):
    """Get saved purchase orders"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/api/companies/{company_id}/qb-purchase-orders",
        headers=headers
    )
    if response.status_code == 200:
        pos = response.json()
        print(f"✓ Retrieved {len(pos)} purchase orders")
        for po in pos[:3]:  # Show first 3
            print(f"  - PO #{po['doc_number']}: {po['vendor_name']} - UGX {po['total_amt']}")
        return pos
    else:
        print(f"✗ Failed to get POs: {response.status_code}")
        return []

def send_pos_to_efris(company_id, po_ids):
    """Send selected POs to EFRIS"""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{BASE_URL}/api/companies/{company_id}/qb-purchase-orders/sync-to-efris",
        headers=headers,
        json={"po_ids": po_ids}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✓ EFRIS Sync Results:")
        print(f"  - Succeeded: {data['synced_count']}")
        print(f"  - Failed: {data['failed_count']}")
        if data['failed']:
            print(f"  - Failures:")
            for fail in data['failed']:
                print(f"    - PO {fail['po']}: {fail['error']}")
        return True
    else:
        print(f"✗ Failed to sync to EFRIS: {response.status_code} - {response.text}")
        return False

def main():
    print("=" * 60)
    print("Purchase Order to EFRIS Integration Test")
    print("=" * 60)
    print()
    
    # Login
    if not login():
        return
    
    # Get companies
    companies = get_companies()
    if not companies:
        print("No companies found. Please create a company first.")
        return
    
    company_id = companies[0]['id']
    company_name = companies[0]['name']
    print(f"Using company: {company_name} (ID: {company_id})")
    print()
    
    # Import POs
    print("Step 1: Import Purchase Orders from QuickBooks")
    if not import_purchase_orders(company_id):
        print("Note: Make sure QuickBooks is connected and has purchase orders")
        return
    print()
    
    # Get POs
    print("Step 2: Retrieve Saved Purchase Orders")
    pos = get_purchase_orders(company_id)
    if not pos:
        print("No purchase orders found")
        return
    print()
    
    # Send to EFRIS (send first 2 POs as test)
    print("Step 3: Send Selected POs to EFRIS")
    test_po_ids = [po['id'] for po in pos[:2]]  # Test with first 2
    if test_po_ids:
        print(f"Sending {len(test_po_ids)} POs to EFRIS...")
        send_pos_to_efris(company_id, test_po_ids)
    else:
        print("No PO IDs available to test")
    
    print()
    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
