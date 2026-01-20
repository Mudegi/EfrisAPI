"""
Test EFRIS database persistence
"""
import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_efris_database():
    # Login
    print("Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": "admin@wandera.com",
            "password": "Admin2026!"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()['access_token']
    print("✓ Logged in successfully")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Import EFRIS goods
    print("\nImporting EFRIS goods...")
    goods_import = requests.post(
        f"{BASE_URL}/api/companies/1/efris-goods/import?page_size=10",
        headers=headers
    )
    
    if goods_import.status_code == 200:
        result = goods_import.json()
        print(f"✓ {result.get('message', 'Import successful')}")
        print(f"  Records imported: {len(result.get('records', []))}")
    else:
        print(f"❌ Goods import failed: {goods_import.status_code}")
        print(goods_import.text)
    
    # Get EFRIS goods from database
    print("\nRetrieving EFRIS goods from database...")
    goods_get = requests.get(
        f"{BASE_URL}/api/companies/1/efris-goods",
        headers=headers
    )
    
    if goods_get.status_code == 200:
        goods = goods_get.json()
        print(f"✓ Found {len(goods)} goods in database")
        if goods:
            print(f"  Sample: {goods[0].get('goodsName')} - UGX {goods[0].get('unitPrice')}")
    else:
        print(f"❌ Failed to retrieve goods: {goods_get.status_code}")
    
    # Import EFRIS invoices
    print("\nImporting EFRIS invoices...")
    invoice_import = requests.post(
        f"{BASE_URL}/api/companies/1/efris-invoices/import",
        headers=headers,
        json={
            "pageNo": "1",
            "pageSize": "10"
        }
    )
    
    if invoice_import.status_code == 200:
        result = invoice_import.json()
        print(f"✓ {result.get('message', 'Import successful')}")
        print(f"  Records imported: {len(result.get('records', []))}")
    else:
        print(f"❌ Invoice import failed: {invoice_import.status_code}")
        print(invoice_import.text)
    
    # Get EFRIS invoices from database
    print("\nRetrieving EFRIS invoices from database...")
    invoices_get = requests.get(
        f"{BASE_URL}/api/companies/1/efris-invoices",
        headers=headers
    )
    
    if invoices_get.status_code == 200:
        invoices = invoices_get.json()
        print(f"✓ Found {len(invoices)} invoices in database")
        if invoices:
            inv = invoices[0]
            print(f"  Sample: #{inv.get('invoiceNo')} - {inv.get('buyerLegalName')} - UGX {inv.get('grossAmount')}")
    else:
        print(f"❌ Failed to retrieve invoices: {invoices_get.status_code}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    time.sleep(5)  # Wait for server to start
    test_efris_database()
