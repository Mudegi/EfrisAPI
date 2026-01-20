"""Check and fix EFRIS invoices FDN in the database"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import json
sys.path.insert(0, '.')
from database.models import EFRISInvoice

engine = create_engine('postgresql://postgres:kian256@localhost:5432/efris_multitenant')
Session = sessionmaker(bind=engine)
db = Session()

invs = db.query(EFRISInvoice).filter(EFRISInvoice.company_id == 1, EFRISInvoice.status == 'success').all()
print(f'Found {len(invs)} successful EFRIS invoices')

fixed_count = 0
for i in invs:
    if not i.fdn and i.efris_response:
        decrypted = i.efris_response.get('data', {}).get('decrypted_content', {})
        basic_info = decrypted.get('basicInformation', {})
        fdn = basic_info.get('invoiceNo', '')
        invoice_id = basic_info.get('invoiceId', '')
        
        if fdn:
            print(f'  Fixing QB ID: {i.qb_invoice_id}, QB#: {i.qb_invoice_number} => FDN={fdn}')
            i.fdn = fdn
            i.efris_invoice_id = invoice_id
            fixed_count += 1

if fixed_count > 0:
    db.commit()
    print(f'\n✅ Fixed {fixed_count} invoices')
else:
    print('\n✓ No invoices needed fixing')

db.close()
