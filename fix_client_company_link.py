"""
Fix missing CompanyUser link for client
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
    
    # Find their company
    company = db.query(Company).filter(Company.owner_id == client.id).first()
    
    if not company:
        print("❌ No company found for this client")
        exit()
    
    print("\n" + "="*70)
    print("FIXING CLIENT COMPANY LINK")
    print("="*70)
    print(f"\nClient: {client.full_name}")
    print(f"Company: {company.name} (TIN: {company.tin})")
    
    # Check if link already exists
    existing_link = db.query(CompanyUser).filter(
        CompanyUser.user_id == client.id,
        CompanyUser.company_id == company.id
    ).first()
    
    if existing_link:
        print("\n✅ CompanyUser link already exists")
        print(f"   Role: {existing_link.role}")
    else:
        # Create the missing link
        print("\n🔧 Creating CompanyUser link...")
        
        company_user = CompanyUser(
            user_id=client.id,
            company_id=company.id,
            role='admin'  # Client is admin of their own company
        )
        
        db.add(company_user)
        db.commit()
        
        print("✅ CompanyUser link created successfully!")
        print(f"   User ID: {client.id}")
        print(f"   Company ID: {company.id}")
        print(f"   Role: admin")
    
    print("\n" + "="*70)
    print("SUCCESS - Client can now access their company!")
    print("="*70)
    print("\n💡 Client should now see their company in the dropdown")
    print("   when they login at: http://localhost:8001/client/login\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
