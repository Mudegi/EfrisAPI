"""
Quick script to check cement excise duty unit in EFRIS
"""
from efris_client import EfrisManager
import json

manager = EfrisManager(
    tin="1014409555",
    test_mode=True,
    cert_path="keys/wandera.pfx"
)

# Query excise duties
print("Querying excise duties...")
result = manager.query_excise_duty()

print("\nRaw result keys:", result.keys())
print("\nReturn code:", result.get('returnStateInfo', {}).get('returnCode'))

if result.get('returnStateInfo', {}).get('returnCode') == '00':
    data = result.get('data', {})
    print("\nData keys:", data.keys())
    
    excise_list = data.get('exciseDutyList', [])
    print(f"\nExcise list type: {type(excise_list)}")
    print(f"Excise list length: {len(excise_list)}")
    
    if excise_list:
        print(f"\nFirst few excise codes:")
        for i, excise in enumerate(excise_list[:5]):
            print(f"  {i+1}. {excise.get('exciseDutyCode')} - {excise.get('exciseDutyName')}")
        
        # Find LED050000 (Cement)
        for excise in excise_list:
            if excise.get('exciseDutyCode') == 'LED050000':
                print(f"\n{'='*60}")
                print(f"CEMENT EXCISE DUTY (LED050000)")
                print(f"{'='*60}")
                print(json.dumps(excise, indent=2))
                print(f"{'='*60}")
                print(f"\n** Unit Code for cement: {excise.get('exciseDutyMeaUnitCode')} **")
                break
    else:
        print("\nExcise list is empty!")
        print("Full data:", json.dumps(data, indent=2)[:1000])
else:
    print(f"Error: {result}")
