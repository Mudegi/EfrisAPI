"""
Test script to verify Units of Measure from EFRIS
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

def get_units_of_measure(token, company_id=1):
    """Get units of measure from EFRIS"""
    url = f"{API_BASE}/api/companies/{company_id}/code-list?code_type=103"
    print(f"Calling: {url}\n")
    
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Response received")
        print(f"  Return Code: {data.get('returnStateInfo', {}).get('returnCode')}")
        print(f"  Return Message: {data.get('returnStateInfo', {}).get('returnMessage')}")
        print(f"  Interface Code: {data.get('dataDescription', {}).get('codeType', 'N/A')}")
        
        if 'data' in data and 'decrypted_content' in data['data']:
            content = data['data']['decrypted_content']
            print(f"\n✓ Decrypted content type: {type(content)}")
            print(f"  Content keys: {content.keys() if isinstance(content, dict) else 'Not a dict'}")
            
            # Check if units are in a specific field
            if isinstance(content, dict):
                # Try common field names
                units = content.get('codeList') or content.get('list') or content.get('records') or content.get('data') or []
                
                if isinstance(units, list):
                    print(f"\n✓ Found {len(units)} units of measure:")
                    
                    # Show the first unit structure
                    if units:
                        print(f"\n  Sample unit structure:")
                        print(f"  {json.dumps(units[0], indent=4)}")
                    
                    # Display first 20 units
                    for i, unit in enumerate(units[:20], 1):
                        # Try all possible field combinations
                        code = (unit.get('code') or unit.get('codeType') or unit.get('codeCategoryCode') or 
                               unit.get('codeNo') or unit.get('id'))
                        name = (unit.get('name') or unit.get('codeName') or unit.get('description') or 
                               unit.get('codeCategoryName') or unit.get('text'))
                        print(f"  {i:2}. Code: {code or 'N/A':10} - {name or 'Unknown'}")
                    
                    if len(units) > 20:
                        print(f"  ... and {len(units) - 20} more units")
                else:
                    print(f"\n⚠ Units field is not a list: {type(units)}")
                    print(f"  Available fields: {list(content.keys())}")
                    print(f"  Content sample: {json.dumps(content, indent=2)[:500]}")
            
            return content
        else:
            print("\n⚠ No decrypted content found in response")
            print(f"Response keys: {data.keys()}")
            if 'data' in data:
                print(f"Data keys: {data['data'].keys()}")
    else:
        print(f"✗ Failed to get units: {response.status_code}")
        print(response.text)
    
    return None

if __name__ == "__main__":
    print("Testing Units of Measure Endpoint")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        exit(1)
    
    # Get units
    units = get_units_of_measure(token)
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
