"""Test script to fetch invoices from EFRIS and see full debug output"""
import requests
import json

# Login first
login_url = "http://localhost:8001/api/auth/login"
login_data = {
    "username": "admin@wandera.com",
    "password": "Admin2026!"
}

print("Logging in...")
response = requests.post(login_url, data=login_data)
if response.status_code == 200:
    token_data = response.json()
    auth_token = token_data['access_token']
    print(f"✓ Logged in successfully")
else:
    print(f"✗ Login failed: {response.status_code} - {response.text}")
    exit(1)

# Query invoices from EFRIS
print("\nQuerying invoices from EFRIS...")
invoices_url = "http://localhost:8001/api/companies/1/query-invoices"
headers = {
    "Authorization": f"Bearer {auth_token}",
    "Content-Type": "application/json"
}

query_params = {
    "pageNo": "1",
    "pageSize": "10"
}

response = requests.post(invoices_url, headers=headers, json=query_params)
print(f"\nResponse status code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"\nResponse data:")
    print(json.dumps(result, indent=2)[:2000])  # First 2000 chars
    
    # Count records if available
    if isinstance(result, dict):
        if 'records' in result:
            print(f"\n✓ Found {len(result['records'])} invoice records")
        elif 'invoiceList' in result:
            print(f"\n✓ Found {len(result['invoiceList'])} invoices")
else:
    print(f"Error: {response.text}")
