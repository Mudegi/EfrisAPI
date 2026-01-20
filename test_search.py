"""Test search functionality for all modules"""
import requests

BASE_URL = "http://localhost:8001"

print("=" * 80)
print("SEARCH FUNCTIONALITY TEST")
print("=" * 80)

# Test 1: Search products
print("\n1. SEARCH PRODUCTS for 'spice'")
print("-" * 80)
response = requests.get(f"{BASE_URL}/api/companies/1/products?search=spice")
if response.status_code == 200:
    products = response.json()
    print(f"Found {len(products)} products")
    for p in products[:5]:
        print(f"  - {p['qb_name']} (SKU: {p.get('qb_sku', 'N/A')})")
else:
    print(f"Error: {response.status_code}")

# Test 2: Search invoices
print("\n2. SEARCH INVOICES for 'Cool'")
print("-" * 80)
response = requests.get(f"{BASE_URL}/api/companies/1/qb-invoices?search=Cool")
if response.status_code == 200:
    data = response.json()
    invoices = data.get('invoices', [])
    print(f"Found {len(invoices)} invoices")
    for inv in invoices[:5]:
        print(f"  - Doc #{inv['DocNumber']}: {inv['CustomerRef']['name']} (Date: {inv['TxnDate']})")
else:
    print(f"Error: {response.status_code}")

# Test 3: Search EFRIS goods
print("\n3. SEARCH EFRIS GOODS for 'Fanta'")
print("-" * 80)
response = requests.get(f"{BASE_URL}/api/companies/1/efris-goods?search=Fanta")
if response.status_code == 200:
    goods = response.json()
    print(f"Found {len(goods)} goods")
    for g in goods[:5]:
        print(f"  - {g['goodsCode']}: {g['goodsName']}")
else:
    print(f"Error: {response.status_code}")

# Test 4: Search purchase orders
print("\n4. SEARCH PURCHASE ORDERS for 'Bob'")
print("-" * 80)
response = requests.get(f"{BASE_URL}/api/companies/1/qb-purchase-orders?search=Bob")
if response.status_code == 200:
    pos = response.json()
    print(f"Found {len(pos)} purchase orders")
    for po in pos[:5]:
        print(f"  - Doc #{po['doc_number']}: {po['vendor_name']} (Date: {po['txn_date']})")
else:
    print(f"Error: {response.status_code}")

# Test 5: Search by invoice number
print("\n5. SEARCH INVOICES for doc number '1044'")
print("-" * 80)
response = requests.get(f"{BASE_URL}/api/companies/1/qb-invoices?search=1044")
if response.status_code == 200:
    data = response.json()
    invoices = data.get('invoices', [])
    print(f"Found {len(invoices)} invoices")
    for inv in invoices:
        print(f"  - Doc #{inv['DocNumber']}: {inv['CustomerRef']['name']} (Status: {inv['EfrisStatus']})")
else:
    print(f"Error: {response.status_code}")

print("\n" + "=" * 80)
print("✓ Search functionality test complete!")
print("=" * 80)
print("\nUSAGE:")
print("  - Products: GET /api/companies/1/products?search=keyword")
print("  - Invoices: GET /api/companies/1/qb-invoices?search=keyword")
print("  - EFRIS Goods: GET /api/companies/1/efris-goods?search=keyword")
print("  - EFRIS Invoices: GET /api/companies/1/efris-invoices?search=keyword")
print("  - Purchase Orders: GET /api/companies/1/qb-purchase-orders?search=keyword")
print("  - QB Items: GET /api/companies/1/qb-items?search=keyword")
print("  - Credit Memos: GET /api/companies/1/qb-credit-memos?search=keyword")
