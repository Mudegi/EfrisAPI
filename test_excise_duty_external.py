"""
Test the external EFRIS API excise-duty endpoint after ERROR-001 fix
"""
import requests
import json
from database.db_access import get_db_connection, get_company_by_id

def test_excise_duty_endpoint():
    """Test the GET /api/external/efris/excise-duty endpoint"""
    
    print("=" * 70)
    print("TESTING EXTERNAL API: GET /api/external/efris/excise-duty")
    print("=" * 70)
    
    # Get API credentials from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get Demo Company credentials
    cursor.execute("""
        SELECT api_key, token 
        FROM companies 
        WHERE id = 'cmkr0wbeq0001vl95dodsfurp'
    """)
    result = cursor.fetchone()
    
    if not result:
        print("❌ Error: Demo Company not found in database")
        return
    
    api_key, token = result
    conn.close()
    
    # API endpoint
    base_url = "https://efrisintegration.nafacademy.com/api/external/efris"
    endpoint = f"{base_url}/excise-duty"
    
    # Request parameters
    params = {
        "token": token
    }
    
    # Headers
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }
    
    print("\n📤 REQUEST:")
    print(f"URL: {endpoint}")
    print(f"Method: GET")
    print(f"Headers: {{'X-API-Key': '***', 'Accept': 'application/json'}}")
    print(f"Params: {params}")
    
    try:
        # Make the request
        print("\n⏳ Sending request...")
        response = requests.get(endpoint, params=params, headers=headers, timeout=30)
        
        print(f"\n🔍 RESPONSE:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Try to parse JSON
        try:
            data = response.json()
            print(f"\n📥 Response Body:")
            print(json.dumps(data, indent=2))
            
            # Check if successful
            if response.status_code == 200 and data.get("success"):
                excise_list = data.get("data", {}).get("exciseDutyList", [])
                print(f"\n✅ SUCCESS! Received {len(excise_list)} excise duty codes")
                
                # Show first 3 examples
                if excise_list:
                    print("\n📋 Sample Codes:")
                    for i, code in enumerate(excise_list[:3]):
                        print(f"\n  {i+1}. {code.get('goodService')}")
                        print(f"     Code: {code.get('exciseDutyCode')}")
                        print(f"     Rate: {code.get('rateText')}")
                
                return True
            else:
                print(f"\n❌ FAILED: {data.get('detail', data.get('message', 'Unknown error'))}")
                return False
                
        except json.JSONDecodeError:
            print(f"\n❌ ERROR: Response is not valid JSON")
            print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ ERROR: Request timed out after 30 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_excise_duty_endpoint()
