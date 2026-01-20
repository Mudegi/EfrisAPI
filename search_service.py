"""Search for specific service in EFRIS to verify registration"""
from efris_client import EfrisManager
import json

# Initialize EFRIS client
manager = EfrisManager(tin='1014409555', test_mode=True)

print("=" * 80)
print("SEARCHING FOR TESTSERVICE1 IN EFRIS")
print("=" * 80)

# Search by goodsCode "TestService1"
print("\n1. Searching by goodsCode='TestService1'...")
result = manager.get_goods_and_services(page_no=1, page_size=100, goods_code="TestService1")

if isinstance(result, dict):
    decrypted = result.get('data', {}).get('decrypted_content', {})
    records = decrypted.get('records', [])
    
    if records:
        print(f"✅ FOUND {len(records)} record(s)!")
        for record in records:
            print(f"\n  - goodsCode: {record.get('goodsCode')}")
            print(f"  - goodsName: {record.get('goodsName')}")
            print(f"  - goodsTypeCode: {record.get('goodsTypeCode')} (102=Service)")
            print(f"  - measureUnit: {record.get('measureUnit')}")
            print(f"  - id: {record.get('id')}")
            print(f"  - statusCode: {record.get('statusCode')}")
            print(f"  - source: {record.get('source')}")
            print(f"  - createDate: {record.get('createDate')}")
    else:
        print("❌ NOT FOUND by goodsCode")
else:
    print(f"Error: {result}")

# Also search all services (goodsTypeCode=102)
print("\n" + "=" * 80)
print("2. Fetching ALL items from EFRIS (page 1-3)...")
print("=" * 80)

all_items = []
for page in range(1, 4):
    result = manager.get_goods_and_services(page_no=page, page_size=50)
    if isinstance(result, dict):
        decrypted = result.get('data', {}).get('decrypted_content', {})
        records = decrypted.get('records', [])
        all_items.extend(records)
        print(f"\nPage {page}: Found {len(records)} items")
    else:
        break

# Filter for services and TestService1
services = [item for item in all_items if item.get('goodsTypeCode') == '102']
test_service = [item for item in all_items if 'TestService1' in str(item.get('goodsCode', '')) or 'TestService1' in str(item.get('goodsName', ''))]

print(f"\n" + "=" * 80)
print(f"SUMMARY:")
print(f"=" * 80)
print(f"Total items in EFRIS: {len(all_items)}")
print(f"Services (goodsTypeCode=102): {len(services)}")
print(f"Items containing 'TestService1': {len(test_service)}")

if services:
    print(f"\n📋 ALL SERVICES FOUND:")
    for svc in services:
        print(f"  - {svc.get('goodsCode')} | {svc.get('goodsName')} | Status: {svc.get('statusCode')} | ID: {svc.get('id')}")

if test_service:
    print(f"\n✅ TESTSERVICE1 DETAILS:")
    print(json.dumps(test_service[0], indent=2))
else:
    print(f"\n❌ TestService1 NOT FOUND in EFRIS")
    print(f"\nAll goodsCodes in EFRIS:")
    for item in all_items[:20]:  # Show first 20
        print(f"  - {item.get('goodsCode')}")
