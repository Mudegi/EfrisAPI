import sqlite3

conn = sqlite3.connect('efris_multitenant.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT id, name, tin, device_no, efris_cert_path, api_key, efris_test_mode
    FROM companies 
    WHERE tin = ?
''', ('1014409555',))

row = cursor.fetchone()

if row:
    print(f'ID: {row[0]}')
    print(f'Name: {row[1]}')
    print(f'TIN: {row[2]}')
    print(f'Device: {row[3]}')
    print(f'Cert Path: {row[4]}')
    print(f'API Key: {row[5][:50] if row[5] else "None"}...')
    print(f'Test Mode: {row[6]}')
else:
    print('Company not found for TIN 1014409555')

conn.close()
