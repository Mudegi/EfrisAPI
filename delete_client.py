"""
Delete client and all associated data from the system
"""
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from database.connection import SessionLocal
from database.models import User, Company, CompanyUser, Product, Invoice, PurchaseOrder, CreditMemo, EFRISGood, EFRISInvoice, ExciseCode, AuditLog

db = SessionLocal()

try:
    # Find the client
    client = db.query(User).filter(User.email == 'client@wandera.com').first()
    
    if not client:
        print("❌ Client not found")
        exit()
    
    print("\n" + "="*70)
    print("DELETING CLIENT AND ALL ASSOCIATED DATA")
    print("="*70)
    print(f"\nClient: {client.full_name} ({client.email})")
    print(f"User ID: {client.id}")
    
    # Find and delete associated records
    
    # 1. Find companies owned by this client
    companies = db.query(Company).filter(Company.owner_id == client.id).all()
    
    print(f"\n[1/6] Found {len(companies)} companies owned by client")
    
    company_ids = [c.id for c in companies]
    
    for company in companies:
        print(f"      - {company.name} (TIN: {company.tin})")
        
        # Delete CompanyUser links for this company
        print(f"        Deleting CompanyUser links")
        db.query(CompanyUser).filter(CompanyUser.company_id == company.id).delete()
        
        # Delete excise codes
        excise_codes = db.query(ExciseCode).filter(ExciseCode.company_id == company.id).all()
        print(f"        Deleting {len(excise_codes)} excise codes")
        for code in excise_codes:
            db.delete(code)
        
        # Delete audit logs
        audit_logs = db.query(AuditLog).filter(AuditLog.company_id == company.id).all()
        print(f"        Deleting {len(audit_logs)} audit logs")
        for log in audit_logs:
            db.delete(log)
        
        # Delete EFRIS goods
        efris_goods = db.query(EFRISGood).filter(EFRISGood.company_id == company.id).all()
        print(f"        Deleting {len(efris_goods)} EFRIS goods")
        for good in efris_goods:
            db.delete(good)
        
        # Delete EFRIS invoices
        efris_invoices = db.query(EFRISInvoice).filter(EFRISInvoice.company_id == company.id).all()
        print(f"        Deleting {len(efris_invoices)} EFRIS invoices")
        for einv in efris_invoices:
            db.delete(einv)
        
        # Delete products
        products = db.query(Product).filter(Product.company_id == company.id).all()
        print(f"        Deleting {len(products)} products")
        for product in products:
            db.delete(product)
        
        # Delete invoices
        invoices = db.query(Invoice).filter(Invoice.company_id == company.id).all()
        print(f"        Deleting {len(invoices)} invoices")
        for invoice in invoices:
            db.delete(invoice)
        
        # Delete purchase orders
        pos = db.query(PurchaseOrder).filter(PurchaseOrder.company_id == company.id).all()
        print(f"        Deleting {len(pos)} purchase orders")
        for po in pos:
            db.delete(po)
        
        # Delete credit memos
        memos = db.query(CreditMemo).filter(CreditMemo.company_id == company.id).all()
        print(f"        Deleting {len(memos)} credit memos")
        for memo in memos:
            db.delete(memo)
        
        # Delete the company
        print(f"        Deleting company: {company.name}")
        db.delete(company)
    
    # 2. Delete any remaining CompanyUser links for this user
    print(f"\n[2/6] Deleting any remaining CompanyUser links for user")
    db.query(CompanyUser).filter(CompanyUser.user_id == client.id).delete()
    
    # 3. Delete the client user
    print(f"\n[3/6] Deleting client user: {client.email}")
    db.delete(client)
    
    # Commit all deletions
    print(f"\n[4/6] Committing changes to database...")
    db.commit()
    
    print(f"[5/6] Verifying deletion...")
    verify = db.query(User).filter(User.email == 'client@wandera.com').first()
    
    if verify:
        print("❌ Deletion failed - client still exists")
    else:
        print("✅ Client successfully deleted!")
    
    print(f"\n[6/6] Clean up complete!")
    
    print("\n" + "="*70)
    print("SUCCESS - CLIENT AND ALL DATA DELETED")
    print("="*70)
    print("\n✨ Database is clean! Ready to add a new client.")
    print("\n📝 Next Steps:")
    print("   1. Login as owner at: http://localhost:8001/login")
    print("   2. Email: owner@efrisplatform.com")
    print("   3. Password: OwnerSecure2026!")
    print("   4. Go to owner portal and add a new client")
    print("\n" + "="*70 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
