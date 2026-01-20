"""Test script to fetch goods from EFRIS and see full debug output"""
import requests
import json

# Login first
login_url = "http://localhost:8001/api/auth/login"
login_data = {
    "username": "admin@wandera.com",
    "password": "Admin2026!"
}

print("Logging in...")
response = requests.post(login_url, data=login_data)  # Use form data, not JSON
if response.status_code == 200:
    token_data = response.json()
    auth_token = token_data['access_token']
    print(f"✓ Logged in successfully")
    print(f"Token: {auth_token[:50]}...")
else:
    print(f"✗ Login failed: {response.status_code} - {response.text}")
    exit(1)

# Fetch goods and services
print("\nFetching goods and services from EFRIS...")
goods_url = "http://localhost:8001/api/companies/1/goods-and-services?page_size=10"
headers = {
    "Authorization": f"Bearer {auth_token}"
}

response = requests.get(goods_url, headers=headers)
print(f"\nResponse status code: {response.status_code}")
print(f"Response headers: {dict(response.headers)}")

if response.status_code == 200:
    result = response.json()
    print(f"\nResponse data:")
    print(json.dumps(result, indent=2))
else:
    print(f"Error: {response.text}")
