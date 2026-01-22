from database.connection import SessionLocal
from database.models import EFRISInvoice
from efris_client import EFRISManager
from database.models import Company
from datetime import datetime

db = SessionLocal()

# Check current state
inv = db.query(EFRISInvoice).filter(EFRISInvoice.qb_invoice_number == '1014').first()

if inv:
    print(f"\n=== Current State of Invoice 1014 ===")
    print(f"Status: {inv.status}")
    print(f"FDN: {inv.fdn}")
    print(f"Invoice No: {inv.invoice_no}")
    print(f"Buyer Legal Name: {inv.buyer_legal_name}")
    print(f"Buyer Business Name: {inv.buyer_business_name}")
    print(f"Gross Amount: {inv.gross_amount}")
    print(f"Tax Amount: {inv.tax_amount}")
    print(f"Net Amount: {inv.net_amount}")
    print(f"Currency: {inv.currency}")
    
    # Query EFRIS for the full details
    if inv.fdn:
        print(f"\n=== Querying EFRIS for FDN {inv.fdn} ===")
        company = db.query(Company).filter(Company.id == inv.company_id).first()
        manager = EFRISManager(
            tin=company.tin,
            device_no=company.device_no,
            private_key_path=company.private_key_path,
            cert_path=company.cert_path,
            cert_password=company.cert_password,
            aes_key_path=company.aes_key_path,
            environment='test'
        )
        
        # Query for invoices with this FDN
        result = manager.query_invoices({'pageNo': '1', 'pageSize': '50'})
        
        if isinstance(result, dict) and 'data' in result:
            efris_data = result['data'].get('decrypted_content', {})
            records = efris_data.get('records', [])
            
            # Find the matching invoice
            matching_record = None
            for record in records:
                if record.get('invoiceNo') == inv.fdn:
                    matching_record = record
                    break
            
            if matching_record:
                print(f"\n=== Found EFRIS Record ===")
                print(f"Invoice No: {matching_record.get('invoiceNo')}")
                print(f"Buyer Legal Name: {matching_record.get('buyerLegalName')}")
                print(f"Buyer Business Name: {matching_record.get('buyerBusinessName')}")
                print(f"Gross Amount: {matching_record.get('grossAmount')}")
                print(f"Tax Amount: {matching_record.get('taxAmount')}")
                print(f"Net Amount: {matching_record.get('netAmount')}")
                print(f"Currency: {matching_record.get('currency')}")
                print(f"Reference No: {matching_record.get('referenceNo')}")
                
                # Update the database record
                print(f"\n=== Updating Database ===")
                inv.buyer_legal_name = matching_record.get('buyerLegalName')
                inv.buyer_business_name = matching_record.get('buyerBusinessName')
                inv.buyer_tin = matching_record.get('buyerTin')
                inv.currency = matching_record.get('currency')
                inv.gross_amount = float(matching_record.get('grossAmount', 0))
                inv.tax_amount = float(matching_record.get('taxAmount', 0))
                inv.net_amount = float(matching_record.get('netAmount', 0)) if matching_record.get('netAmount') else None
                
                # Parse issued date
                try:
                    if matching_record.get('issuedDate'):
                        inv.issued_date = datetime.strptime(matching_record.get('issuedDate'), '%d/%m/%Y %H:%M:%S')
                except:
                    pass
                
                inv.efris_data = matching_record
                inv.updated_at = datetime.now()
                
                db.commit()
                print("✓ Invoice updated successfully!")
            else:
                print(f"\n✗ Invoice {inv.fdn} not found in EFRIS records")
                print(f"Total records found: {len(records)}")
else:
    print("Invoice 1014 not found in database")

db.close()
