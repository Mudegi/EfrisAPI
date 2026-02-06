"""
Check client's company associations
"""
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from database.connection import SessionLocal
from database.models import User, Company, CompanyUser

db = SessionLocal()

try:
    # Find the client
    client = db.query(User).filter(User.email == 'client@wandera.com').first()
    
    if not client:
        print("❌ Client not found")
        exit()
    
    print("\n" + "="*70)
    print("CLIENT COMPANY ASSOCIATION CHECK")
    print("="*70)
    print(f"\nClient: {client.full_name} ({client.email})")
    print(f"User ID: {client.id}")
    
    # Check CompanyUser links
    company_links = db.query(CompanyUser).filter(
        CompanyUser.user_id == client.id
    ).all()
    
    print(f"\nCompany Links Found: {len(company_links)}")
    
    if company_links:
        for i, link in enumerate(company_links, 1):
            company = db.query(Company).filter(Company.id == link.company_id).first()
            print(f"\n--- Company #{i} ---")
            print(f"  Company ID:   {link.company_id}")
            print(f"  Role:         {link.role}")
            if company:
                print(f"  Name:         {company.name}")
                print(f"  TIN:          {company.tin}")
                print(f"  Device No:    {company.device_no}")
                print(f"  Active:       {company.is_active}")
            else:
                print(f"  ⚠️  Company record not found!")
    else:
        print("\n⚠️  NO COMPANY LINKS FOUND!")
        
    # Check if there are companies owned by this user
    owned_companies = db.query(Company).filter(Company.owner_id == client.id).all()
    print(f"\nCompanies Owned by User: {len(owned_companies)}")
    
    if owned_companies:
        for company in owned_companies:
            print(f"\n  - {company.name} (TIN: {company.tin})")
            print(f"    ID: {company.id}, Active: {company.is_active}")
            
            # Check if there's a CompanyUser link
            link_exists = db.query(CompanyUser).filter(
                CompanyUser.user_id == client.id,
                CompanyUser.company_id == company.id
            ).first()
            
            if not link_exists:
                print(f"    ⚠️  Missing CompanyUser link!")
    
    # List all companies in database
    all_companies = db.query(Company).all()
    print(f"\nTotal Companies in Database: {len(all_companies)}")
    
    if all_companies:
        print("\nAll Companies:")
        for company in all_companies:
            print(f"  - ID: {company.id}, Name: {company.name}, TIN: {company.tin}, Owner ID: {company.owner_id}")
    
    print("\n" + "="*70)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
