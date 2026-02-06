"""
Delete client by email and all associated data
Usage: py delete_client_by_email.py <email>
"""
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from database.connection import SessionLocal
from database.models import User, Company, CompanyUser, Product, Invoice, PurchaseOrder, CreditMemo, EFRISGood, EFRISInvoice, ExciseCode, AuditLog

if len(sys.argv) < 2:
    print("Usage: py delete_client_by_email.py <email>")
    print("\nExample: py delete_client_by_email.py wanderaemmanuel@gmail.com")
    exit()

client_email = sys.argv[1]

db = SessionLocal()

try:
    # Find the client
    client = db.query(User).filter(User.email == client_email).first()
    
    if not client:
        print(f"❌ Client not found with email: {client_email}")
        exit()
    
    print("\n" + "="*70)
    print("DELETING CLIENT AND ALL ASSOCIATED DATA")
    print("="*70)
    print(f"\nClient: {client.full_name} ({client.email})")
    print(f"User ID: {client.id}")
    
    # Find all companies owned by this client
    companies = db.query(Company).filter(Company.owner_id == client.id).all()
    
    if companies:
        print(f"\nCompanies to delete: {len(companies)}")
        for company in companies:
            print(f"  - {company.name} (ID: {company.id}, TIN: {company.tin})")
            
            # Delete ExciseCodes first (they reference company)
            excise_codes = db.query(ExciseCode).filter(ExciseCode.company_id == company.id).all()
            if excise_codes:
                print(f"    ➜ Deleting {len(excise_codes)} excise codes...")
                for code in excise_codes:
                    db.delete(code)
            
            # Delete AuditLogs (they reference company)
            audit_logs = db.query(AuditLog).filter(AuditLog.company_id == company.id).all()
            if audit_logs:
                print(f"    ➜ Deleting {len(audit_logs)} audit logs...")
                for log in audit_logs:
                    db.delete(log)
            
            # Delete EFRIS goods
            efris_goods = db.query(EFRISGood).filter(EFRISGood.company_id == company.id).all()
            if efris_goods:
                print(f"    ➜ Deleting {len(efris_goods)} EFRIS goods...")
                for good in efris_goods:
                    db.delete(good)
            
            # Delete EFRIS invoices
            efris_invoices = db.query(EFRISInvoice).filter(EFRISInvoice.company_id == company.id).all()
            if efris_invoices:
                print(f"    ➜ Deleting {len(efris_invoices)} EFRIS invoices...")
                for invoice in efris_invoices:
                    db.delete(invoice)
            
            # Delete products
            products = db.query(Product).filter(Product.company_id == company.id).all()
            if products:
                print(f"    ➜ Deleting {len(products)} products...")
                for product in products:
                    db.delete(product)
            
            # Delete invoices
            invoices = db.query(Invoice).filter(Invoice.company_id == company.id).all()
            if invoices:
                print(f"    ➜ Deleting {len(invoices)} invoices...")
                for invoice in invoices:
                    db.delete(invoice)
            
            # Delete purchase orders
            purchase_orders = db.query(PurchaseOrder).filter(PurchaseOrder.company_id == company.id).all()
            if purchase_orders:
                print(f"    ➜ Deleting {len(purchase_orders)} purchase orders...")
                for po in purchase_orders:
                    db.delete(po)
            
            # Delete credit memos
            credit_memos = db.query(CreditMemo).filter(CreditMemo.company_id == company.id).all()
            if credit_memos:
                print(f"    ➜ Deleting {len(credit_memos)} credit memos...")
                for memo in credit_memos:
                    db.delete(memo)
            
            # Delete company_users links
            company_users = db.query(CompanyUser).filter(CompanyUser.company_id == company.id).all()
            if company_users:
                print(f"    ➜ Deleting {len(company_users)} company-user links...")
                for cu in company_users:
                    db.delete(cu)
            
            # Delete the company itself
            print(f"    ➜ Deleting company: {company.name}")
            db.delete(company)
    
    # Delete the client user
    print(f"\n➜ Deleting client user: {client.email}")
    db.delete(client)
    
    # Commit all deletions
    db.commit()
    
    print("\n" + "="*70)
    print("✅ CLIENT AND ALL DATA DELETED SUCCESSFULLY")
    print("="*70)

except Exception as e:
    db.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
