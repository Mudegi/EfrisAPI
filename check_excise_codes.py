import json

with open('excise_duty_reference.json', 'r') as f:
    data = json.load(f)

codes = [x for x in data['data']['decrypted_content']['exciseDutyList'] if x['isLeafNode'] == '1']
print(f'Total leaf node codes: {len(codes)}')

led190 = [x for x in codes if x['exciseDutyCode'].startswith('LED190')]
print(f'\nLED190xxx codes: {len(led190)}')

if led190:
    print('\nAvailable LED190xxx codes:')
    for code in led190[:15]:
        print(f"  {code['exciseDutyCode']}: {code['goodService']}")
        
# Check if LED190100 exists
led190100 = [x for x in codes if x['exciseDutyCode'] == 'LED190100']
if led190100:
    print(f'\n✓ LED190100 exists: {led190100[0]["goodService"]}')
else:
    print('\n✗ LED190100 does NOT exist in the reference data')
