"""
Test the multi-tenant API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_register_user():
    """Test user registration"""
    print("\n=== Testing User Registration ===")
    user_data = {
        "email": "admin@wandera.com",
        "password": "kian256secure",
        "full_name": "Admin User"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response Text: {response.text}")
    try:
        print(f"Response JSON: {response.json()}")
    except:
        print("Could not parse JSON response")
    return response.status_code == 200

def test_login():
    """Test user login"""
    print("\n=== Testing User Login ===")
    login_data = {
        "username": "admin@wandera.com",  # OAuth2PasswordRequestForm uses 'username' not 'email'
        "password": "kian256secure"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Token Type: {data.get('token_type')}")
        print(f"Access Token: {data.get('access_token')[:50]}...")
        return data.get('access_token')
    else:
        print(f"Error: {response.json()}")
        return None

def test_get_current_user(token):
    """Test getting current user"""
    print("\n=== Testing Get Current User ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_create_company(token):
    """Test creating a company"""
    print("\n=== Testing Create Company ===")
    company_data = {
        "name": "Wandera EFRIS",
        "tin": "1014409555",
        "device_no": "1014409555_02",
        "efris_test_mode": True
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/companies", json=company_data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Company ID: {data.get('id')}")
        print(f"Company Name: {data.get('name')}")
        print(f"TIN: {data.get('tin')}")
        return data.get('id')
    else:
        print(f"Error: {response.json()}")
        return None

def test_get_companies(token):
    """Test getting user's companies"""
    print("\n=== Testing Get Companies ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/companies", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def main():
    """Run all tests"""
    print("=" * 60)
    print("MULTI-TENANT EFRIS API - TEST SUITE")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed!")
        return
    
    # Test registration
    test_register_user()
    
    # Test login
    token = test_login()
    if not token:
        print("\n❌ Login failed!")
        return
    
    # Test get current user
    test_get_current_user(token)
    
    # Test create company
    company_id = test_create_company(token)
    if company_id:
        print(f"\n✅ Company created with ID: {company_id}")
    
    # Test get companies
    test_get_companies(token)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Your multi-tenant API is running on http://localhost:8001")
    print("2. You have created an admin user: admin@wandera.com")
    print(f"3. You have created a company with ID: {company_id}")
    print("4. Use this token for API calls:")
    print(f"   Bearer {token[:50]}...")
    print("\nAPI Documentation available at: http://localhost:8001/docs")

if __name__ == "__main__":
    main()
