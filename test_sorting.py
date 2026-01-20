"""Test sorting implementation"""
import requests
import json

BASE_URL = "http://localhost:8001"

# Login
login_data = {
    "email": "admin@wandera.com",
    "password": "Admin2026!"
}
response = requests.get(f"{BASE_URL}/?email={login_data['email']}&password={login_data['password']}")
print("Login:", response.status_code)

# Re-import invoices to populate dates
print("\n=== Re-importing QB Invoices ===")
response = requests.post(f"{BASE_URL}/api/companies/1/qb-invoices/import")
if response.status_code == 200:
    result = response.json()
    print(f"✓ {result.get('message')}")
else:
    print(f"✗ Error: {response.status_code} - {response.text}")

# Fetch invoices and check sorting
print("\n=== Testing Invoice Sorting ===")
response = requests.get(f"{BASE_URL}/api/companies/1/qb-invoices")
if response.status_code == 200:
    data = response.json()
    invoices = data.get('invoices', [])
    print(f"Total invoices: {len(invoices)}")
    print("\nFirst 10 invoices (should be sorted by date DESC):")
    for i, inv in enumerate(invoices[:10], 1):
        print(f"{i}. DocNum: {inv.get('DocNumber')}, TxnDate: {inv.get('TxnDate')}, Status: {inv.get('EfrisStatus')}")
else:
    print(f"✗ Error: {response.status_code}")

# Test products sorting
print("\n=== Testing Product Sorting ===")
response = requests.get(f"{BASE_URL}/api/companies/1/products")
if response.status_code == 200:
    products = response.json()
    print(f"Total products: {len(products)}")
    print("\nFirst 5 products (should be sorted by updated_at DESC):")
    for i, p in enumerate(products[:5], 1):
        print(f"{i}. Name: {p.get('qb_name')}, ID: {p.get('id')}")
else:
    print(f"✗ Error: {response.status_code}")

# Test EFRIS goods sorting
print("\n=== Testing EFRIS Goods Sorting ===")
response = requests.get(f"{BASE_URL}/api/companies/1/efris-goods")
if response.status_code == 200:
    goods = response.json()
    print(f"Total goods: {len(goods)}")
    print("\nFirst 5 goods (should be sorted by updated_at DESC):")
    for i, g in enumerate(goods[:5], 1):
        print(f"{i}. Code: {g.get('goodsCode')}, Name: {g.get('goodsName')}")
else:
    print(f"✗ Error: {response.status_code}")

print("\n✓ Sorting test complete!")
