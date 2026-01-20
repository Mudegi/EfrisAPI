#!/usr/bin/env python3
"""Test T104 endpoint through the API"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"
TIN = "1014409555"

def test_t104_endpoint():
    """Test the T104 key exchange through the API endpoint"""
    print("=" * 80)
    print("T104 KEY EXCHANGE API TEST")
    print("=" * 80)
    print()
    
    # Test the isolated T104 endpoint
    endpoint = f"{BASE_URL}/api/test/t104-key-exchange"
    
    print(f"[1] Testing T104 endpoint: {endpoint}")
    try:
        response = requests.post(f"{endpoint}?token=test_token")
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    Response received: ✓")
            
            # Check response structure
            if 'status' in data:
                print(f"    Status: {data['status']}")
            
            if 'returnCode' in data:
                print(f"    Return Code: {data['returnCode']}")
                
                if data['returnCode'] == '00':
                    print(f"    ✓ SUCCESS!")
                    
                    # Check if key was obtained
                    if 'passwordDes_length' in data:
                        print(f"    Encrypted key length: {data['passwordDes_length']} bytes")
                    
                    if 'sign_length' in data:
                        print(f"    Signature length: {data['sign_length']} bytes")
                    
                    print()
                    print("=" * 80)
                    print("T104 ENDPOINT TEST PASSED ✓")
                    print("=" * 80)
                    return True
                else:
                    print(f"    ✗ FAILED - Server returned error code: {data['returnCode']}")
            
            if 'error' in data:
                print(f"    Error: {data['error']}")
        else:
            print(f"    ✗ HTTP Error: {response.status_code}")
            print(f"    Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"    ✗ Connection error - is the server running on {BASE_URL}?")
        return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False

def test_registration_details():
    """Test registration details endpoint"""
    print()
    print("=" * 80)
    print("REGISTRATION DETAILS API TEST")
    print("=" * 80)
    print()
    
    endpoint = f"{BASE_URL}/api/{TIN}/registration-details"
    print(f"[2] Testing endpoint: {endpoint}")
    
    try:
        response = requests.get(endpoint)
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✓ Response received")
            
            # Check for business details
            if isinstance(data, dict):
                if 'legalName' in data or 'Legal Name' in data:
                    print(f"    ✓ Business details found")
                    return True
        
        print(f"    Response: {response.text[:200]}")
        
    except Exception as e:
        print(f"    ✗ Error: {e}")
    
    return False

if __name__ == "__main__":
    # Wait a moment for server to fully start
    print("Waiting for server to initialize...")
    time.sleep(2)
    
    t104_ok = test_t104_endpoint()
    
    if t104_ok:
        print()
        print("Proceeding to test dependent endpoints...")
        test_registration_details()
    else:
        print()
        print("T104 test failed. Cannot proceed with other tests.")
